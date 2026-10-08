#!/usr/bin/env python3
"""consumer supervisor（AIR-287——db-99：處理停滯觀測→consumer health
alert→符合 escalation 條件才轉人類 intervention item）。

職責：掃 disposition ledger（唯讀——**不自動改任何信件狀態**），偵測
停滯（received／processing 停留超過 stale 閾值）→health alert（人類
可讀行，stdout／報告檔）；alert 持續超過 escalation 門檻→寫入人類
intervention item 清單（落檔）。operator 原則：「AI 讀取處理了就不用
顯示；人只處理需要人介入的」——supervisor 是消費者側觀測面，非面板
重做（SC 側已 80% 就位，db-99 裁定）。

唯讀邊界：只寫 `<root>/_meta/` 下自己的兩個觀測檔（escalation state＋
intervention 清單）——`<root>/<address>/` 全部檔案零觸碰（測試釘
content＋mtime 不變）。狀態推進永遠屬於消費端 session／人類（disposition
ledger 的寫入者），supervisor 只觀測與舉報。

兩個具名常數（可 CLI 覆寫——調參不必改碼）：
- DEFAULT_STALE_THRESHOLD_US＝24h：received／processing／needs-human
  距 updated_at_us 超過此值＝stale（嚴格大於——恰在閾值上＝未停滯，
  邊界算「還在動」）。needs-human 在監視面（AIR-287 bi 修復——GLM
  F1）：人類介入迴圈（forward→人類結案）停滯＝電子蹤跡——session
  死於 forward 前不得恆靜默；handled／failed 是已分流非停滯。
- DEFAULT_ESCALATION_AFTER_US＝48h（2× stale）：同一停滯項首次 alert
  （first_alert_at_us）距今超過此值＝alert 持續→escalation（人類
  intervention item）。第二次觀測即持續性證據（單次觀測不 escalate
  ——剛 stale 的項目可能正在被處理）。

escalation state：`<root>/_meta/supervisor-escalations.json`
    {"schema_version": 1, "items": {"<address>/<envelope_id>":
     {"address", "envelope_id", "state", "first_alert_at_us",
      "last_alert_at_us", "alert_runs", "escalated_at_us"|None}}}
項目不再 stale（消費端推進了狀態）＝resolved——自 state 移除＋清單
重生成（觀測面不保留歷史；處置歷史在 ledger 本體）。state 檔壞形＝
SupervisorStateCorrupt typed 錯誤（觀測權威檔 fail-closed——靜默重置
會把已 escalated 項目的持續性證據洗掉）；**逐 entry 全驗**（恰七鍵
ESC_ITEM_KEYS、型別、時間戳正 int、items key 與 entry 的
address/envelope_id 一致）——`items.get(key) or {...}` 靜默重置＝
同罪（AIR-287 bi 修復，codex F3）。

intervention 清單：`<root>/_meta/intervention-items.md`——每次掃描
從 escalation state 全量重生成（冪等；人類可讀；escalated 項目逐行
address／envelope_id／state／首次 alert 年齡）。

crash-only：address 目錄內任一壞 ledger 檔＝LedgerCorrupt typed 錯誤
整掃拒行（單一源裁定＝duty_disposition 模組 docstring——跳過壞檔＝
最需要被看見的停滯記錄可能正是壞的那筆）。

CLI（exit 0 掃描成功〔有無 alert 皆然——findings 是資料非工具失敗〕
／1 typed 錯誤／2 args 誤用）：
    scan [--base-dir DIR] [--now-us US] [--stale-threshold-hours N]
         [--escalation-after-hours N] [--report PATH] [--json]
--json＝機讀摘要（stale／escalated 計數與明細）；--report＝健康報告
落檔（人類可讀，與 stdout 同內容）。

測試形態：base_dir／now_us／兩閾值可注入——零真實 state 往返、零
時鐘依賴。
"""

import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))

TAG = "duty-supervisor"
DEFAULT_STALE_THRESHOLD_US = 24 * 60 * 60 * 1_000_000  # 24h
DEFAULT_ESCALATION_AFTER_US = 2 * DEFAULT_STALE_THRESHOLD_US  # 48h
# needs-human 在監視面（AIR-287 bi 修復——GLM F1）：人類介入迴圈
# （forward→人類結案）停滯＝電子蹤跡——session 死於 forward 前不得
# 恆靜默；handled／failed 是已分流非停滯。
STALE_STATES = frozenset({"received", "processing", "needs-human"})
ESC_SCHEMA_VERSION = 1
ESC_STATE_NAME = "supervisor-escalations.json"
INTERVENTION_NAME = "intervention-items.md"
# escalation entry 凍結七鍵（AIR-287 bi 修復——codex F3：entry 全驗）
ESC_ITEM_KEYS = frozenset({
    "address", "envelope_id", "state", "first_alert_at_us",
    "last_alert_at_us", "alert_runs", "escalated_at_us",
})


class SupervisorStateCorrupt(RuntimeError):
    """supervisor 自身觀測 state 檔壞形（非 JSON／schema 壞）——
    fail-closed：靜默重置＝已 escalated 項目持續性證據被洗掉。"""


def _load_dd():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_duty_disposition_sup_core",
        os.path.join(_HERE, "duty_disposition.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dd = _load_dd()


# ── 掃描（唯讀）──────────────────────────────────────────────────────


def scan_ledger(base_dir, now_us, stale_threshold_us=DEFAULT_STALE_THRESHOLD_US):
    """掃全部 address 目錄 → stale items（list of dict，按
    （address, envelope_id）排序——確定性輸出）。

    item：{address, envelope_id, state, updated_at_us, age_us}。
    stale 判準：state∈STALE_STATES（received／processing／needs-human
    ）且 (now - updated_at_us) > stale_threshold_us（嚴格大於——恰在
    閾值上＝未停滯）。壞檔＝LedgerCorrupt 傳出（fail-closed，見
    docstring）；_meta 與非目錄項不入掃描。
    """
    root = base_dir if base_dir is not None else dd._default_base_dir()
    items = []
    try:
        entries = sorted(os.listdir(root))
    except FileNotFoundError:
        return items
    for name in entries:
        path = os.path.join(root, name)
        if name == "_meta" or not os.path.isdir(path):
            continue
        for record in dd.list_records(name, base_dir=root):
            if record["state"] not in STALE_STATES:
                continue
            age = now_us - record["updated_at_us"]
            if age <= stale_threshold_us:
                continue
            items.append({
                "address": name,
                "envelope_id": record["envelope_id"],
                "state": record["state"],
                "updated_at_us": record["updated_at_us"],
                "age_us": age,
            })
    items.sort(key=lambda i: (i["address"], i["envelope_id"]))
    return items


# ── escalation state（唯二寫入面；atomic 0600）──────────────────────


def _esc_state_path(root):
    return os.path.join(root, "_meta", ESC_STATE_NAME)


def _atomic_write(path, text):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _load_esc_state(root):
    path = _esc_state_path(root)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return {"schema_version": ESC_SCHEMA_VERSION, "items": {}}
    except (OSError, ValueError) as exc:
        raise SupervisorStateCorrupt(
            f"supervisor state 檔不可解析：{path}（{exc!r}）"
        ) from exc
    if (
        not isinstance(doc, dict)
        or doc.keys() != {"schema_version", "items"}
        or doc["schema_version"] != ESC_SCHEMA_VERSION
        or not isinstance(doc["items"], dict)
    ):
        raise SupervisorStateCorrupt(f"supervisor state 壞形：{path}")
    for key, entry in doc["items"].items():
        _validate_esc_item(key, entry, path)
    return doc


def _validate_esc_item(key, entry, path):
    """entry 全驗（AIR-287 bi 修復——codex F3）：恰七鍵、型別、時間戳
    正 int、key 一致性（"<address>/<envelope_id>"）。任何壞形＝
    SupervisorStateCorrupt——`items.get(key) or {...}` 靜默重置會把
    已 escalated 項目的持續性證據洗掉（crash-only 禁）。"""
    where = f"{path}（{key}）"
    if not isinstance(entry, dict) or entry.keys() != ESC_ITEM_KEYS:
        raise SupervisorStateCorrupt(
            f"supervisor state entry 鍵集不符：{where}"
            f"（得 {sorted(entry) if isinstance(entry, dict) else type(entry)}"
            f"，應 {sorted(ESC_ITEM_KEYS)}）"
        )
    if not isinstance(entry["address"], str) or not entry["address"]:
        raise SupervisorStateCorrupt(
            f"supervisor state address 壞形：{where}"
        )
    if (
        not isinstance(entry["envelope_id"], str)
        or not entry["envelope_id"]
    ):
        raise SupervisorStateCorrupt(
            f"supervisor state envelope_id 壞形：{where}"
        )
    if key != f"{entry['address']}/{entry['envelope_id']}":
        raise SupervisorStateCorrupt(
            f"supervisor state key 與 entry 不一致：{where}"
        )
    if entry["state"] not in dd.STATES:
        raise SupervisorStateCorrupt(
            f"supervisor state state 非法：{where}（{entry['state']!r}）"
        )
    for field in ("first_alert_at_us", "last_alert_at_us"):
        if not dd._positive_int(entry[field]):
            raise SupervisorStateCorrupt(
                f"supervisor state {field} 非正整數：{where}"
                f"（{entry[field]!r}）"
            )
    if not dd._positive_int(entry["alert_runs"]):
        raise SupervisorStateCorrupt(
            f"supervisor state alert_runs 非正整數：{where}"
            f"（{entry['alert_runs']!r}）"
        )
    esc_at = entry["escalated_at_us"]
    if esc_at is not None and not dd._positive_int(esc_at):
        raise SupervisorStateCorrupt(
            f"supervisor state escalated_at_us 壞形：{where}"
            f"（{esc_at!r}）"
        )


def _render_intervention_md(items_doc):
    lines = [
        "# intervention items（duty supervisor——人類介入清單）",
        "",
        f"{len(items_doc)} items",
        "",
    ]
    for key in sorted(items_doc):
        it = items_doc[key]
        lines.append(
            f"- `{key}` state={it['state']}"
            f" first_alert={it['first_alert_at_us']}"
            f" escalated_at={it.get('escalated_at_us')}"
        )
    return "\n".join(lines) + "\n"


# ── supervise（觀測→alert→escalation；唯讀 ledger）───────────────────


class ScanResult:
    """supervise 結果（report_lines 人類可讀；stale_items／escalated
    機讀）。"""

    def __init__(self, report_lines, stale_items, escalated):
        self.report_lines = report_lines
        self.stale_items = stale_items
        self.escalated = escalated


def supervise(
    base_dir, now_us, stale_threshold_us=DEFAULT_STALE_THRESHOLD_US,
    escalation_after_us=DEFAULT_ESCALATION_AFTER_US,
):
    """一次掃描：停滯偵測→alert 行→escalation state 更新→清單重生成。

    stale 判準：state∈STALE_STATES 且 (now - updated_at_us) >
    stale_threshold_us。escalation 判準：同一項 (now - first_alert_at_us)
    > escalation_after_us（首次 alert 不 escalate）。項目不再 stale＝
    resolved（state 移除＋清單重生成）。
    """
    root = base_dir if base_dir is not None else dd._default_base_dir()
    stale_items = scan_ledger(root, now_us, stale_threshold_us)
    esc = _load_esc_state(root)
    items = esc["items"]
    stale_keys = set()
    escalated = []
    for it in stale_items:
        key = f"{it['address']}/{it['envelope_id']}"
        stale_keys.add(key)
        entry = items.get(key) or {
            "address": it["address"],
            "envelope_id": it["envelope_id"],
            "state": it["state"],
            "first_alert_at_us": now_us,
            "alert_runs": 0,
            "escalated_at_us": None,
        }
        entry["state"] = it["state"]
        entry["last_alert_at_us"] = now_us
        entry["alert_runs"] = entry.get("alert_runs", 0) + 1
        if (
            entry.get("escalated_at_us") is None
            and (now_us - entry["first_alert_at_us"]) > escalation_after_us
        ):
            entry["escalated_at_us"] = now_us
        if entry.get("escalated_at_us") is not None:
            escalated.append(dict(entry, key=key))
        items[key] = entry
    for key in [k for k in items if k not in stale_keys]:
        del items[key]  # resolved：不再 stale＝消費端已推進——移除
    _atomic_write(
        _esc_state_path(root),
        json.dumps(esc, ensure_ascii=False, sort_keys=True, indent=2),
    )
    md_path = os.path.join(root, "_meta", INTERVENTION_NAME)
    open_items = {
        k: v for k, v in items.items()
        if v.get("escalated_at_us") is not None
    }
    if open_items:
        # 清單檔存在＝有未決 intervention（人類面板語義：檔在即有待辦）
        _atomic_write(md_path, _render_intervention_md(open_items))
    else:
        try:
            os.unlink(md_path)
        except FileNotFoundError:
            pass
    report = _render_report(
        stale_items, escalated, now_us,
        stale_threshold_us, escalation_after_us,
    )
    return ScanResult(report, stale_items, escalated)


def _hours(us):
    return round(us / (60 * 60 * 1_000_000))


def _render_report(stale_items, escalated, now_us, stale_threshold_us,
                   escalation_after_us):
    lines = []
    if not stale_items:
        lines.append(
            f"[{TAG}] ledger clean：無停滯項（received/processing/"
            f"needs-human 皆在 stale 閾值 {_hours(stale_threshold_us)}h 內）"
        )
        return lines
    lines.append(
        f"[{TAG}] consumer health alert：{len(stale_items)} 件停滯"
        f"（> {_hours(stale_threshold_us)}h）"
    )
    for it in stale_items:
        lines.append(
            f"[{TAG}] - {it['address']}/{it['envelope_id']}"
            f" state={it['state']} 停滯 {_hours(it['age_us'])}h"
            "（duty-disposition set 推進狀態即解除）"
        )
    if escalated:
        lines.append(
            f"[{TAG}] escalation：{len(escalated)} 件 alert 持續超過"
            f" {_hours(escalation_after_us)}h——已落人類"
            " intervention 清單（_meta/intervention-items.md）"
        )
    return lines


# ── CLI 面 ───────────────────────────────────────────────────────────


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "consumer supervisor（AIR-287；停滯觀測→health alert→"
            "escalation——唯讀觀測面，不自動改信件狀態）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("scan", help="掃 disposition ledger 一次")
    p.add_argument("--base-dir", default=None, metavar="DIR",
                   help="ledger 根覆寫（預設 XDG state）")
    p.add_argument("--now-us", type=int, default=None, metavar="US",
                   help="now 注入（預設系統時鐘）")
    p.add_argument("--stale-threshold-hours", type=int, default=None,
                   metavar="N")
    p.add_argument("--escalation-after-hours", type=int, default=None,
                   metavar="N")
    p.add_argument("--report", default=None, metavar="PATH",
                   help="健康報告落檔（人類可讀）")
    p.add_argument("--json", action="store_true", help="機讀摘要 stdout")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        now_us = (
            args.now_us if args.now_us is not None
            else time.time_ns() // 1000
        )
        stale_us = (
            args.stale_threshold_hours * 60 * 60 * 1_000_000
            if args.stale_threshold_hours is not None
            else DEFAULT_STALE_THRESHOLD_US
        )
        esc_us = (
            args.escalation_after_hours * 60 * 60 * 1_000_000
            if args.escalation_after_hours is not None
            else DEFAULT_ESCALATION_AFTER_US
        )
        result = supervise(
            args.base_dir, now_us, stale_threshold_us=stale_us,
            escalation_after_us=esc_us,
        )
    except (
        dd.LedgerError, SupervisorStateCorrupt, OSError,
    ) as exc:
        print(f"[{TAG}] typed failure：{exc}", file=sys.stderr)
        return 1
    for line in result.report_lines:
        print(line)
    if args.json:
        print(json.dumps({
            "stale_count": len(result.stale_items),
            "escalated_count": len(result.escalated),
            "stale": result.stale_items,
        }, ensure_ascii=False, sort_keys=True))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write("\n".join(result.report_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
