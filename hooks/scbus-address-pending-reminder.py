#!/usr/bin/env python3
"""scbus 門牌 receipt-timeline 監看提醒 hook（AIR-233 消費面重寫；AIR-225.1 骨架）。

trigger 骨架沿用 AIR-225.1：UserPromptSubmit（每次 user 打字）與 SessionStart
（session 回場）兩個 interaction boundary 的 liveness 提醒面，單一 script 服務
兩事件——stdin 的 hook_event_name 決定輸出的 hookEventName；兩註冊條目皆 sync
（無 async 鍵——additionalContext 通道 sync-only）。查詢核心由 mailbox
snapshot（`address ls --pending`）重寫為 **delivery-event timeline**：
`scbus address receipts --address <addr> --after-cursor <cursor> --limit N`
（AIR-221 三方收斂架構 A；設計權威 .agent-tmp/mail-arch/verdict-codex.md）。

三軸互不代理（架構 invariant，單一源＝governance/scbus-address-ownership.md
「Holder ≠ monitor」）：transport ack（acked_at）／human seen/done（mailbox
lifecycle）／AI notification（emitted_cursor）各自持 cursor。本 hook 的
consumer-owned 狀態只宣稱 **reminder emitted**（非 AI seen、非 processed——
hook host 無「模型已讀」ACK，advisory badge 非責任結清點）。count-only 禁
body／preview；禁 recv/ack/lease 操作（monitor ≠ holder）。

stub-first：receipts face 尚未存在於上游 sc-router（提案信已寄
sc-router-marshal），script 呼叫面照 face 草規實作；face 失敗一律落
**degraded** 路徑（零 stdout exit 0；stderr 分註：缺席型——CLI 拒絕子命令
——「receipts face 未落地——sc-router 卡追蹤中」，其他失敗型中性文案帶
實際錯誤摘要）——**不**退化相容 `ls --pending`（mailbox snapshot 與
delivery-event timeline 語義不同，雙路徑 fallback 已裁示不採）。測試／整合以
可注入 runner 驅動：`_query_receipts(..., runner=…)` 函式注入，或
SCBUS_MONITOR_RUNNER 環境變數指向 shim 執行檔（真 subprocess 整合面）。

決策表（hook 運作面 stdout 皆協議 JSON 或空、exit 恆 0；唯一例外＝註冊
args 誤用，見末行）：

| 情境                                              | stdout            | exit |
|---------------------------------------------------|-------------------|------|
| 自上次知會後新到 N 封（N>0；每門牌一行，可多行）  | hookSpecificOutput | 0   |
| 無新／冷啟動（只建 cursor）／未傳 --address       | 空（靜默）        | 0    |
| cursor 損壞（state 讀壞／形漂移——重建）           | 重建注記行「（cursor 重建）」＋stderr 警示 | 0 |
| eligibility gate 不過（cwd 在 repo 外）           | 空（靜默、零查詢、零推進） | 0 |
| receipts face 失敗（缺席／非零 exit／壞 JSON／形漂移） | 空（degraded——stderr 分註缺席型／其他失敗型） | 0 |
| cursor 推進失敗（state 寫失敗）                   | 提醒照出（寧重不漏——下次重複提醒） | 0 |
| stdin 壞 JSON／缺或未知 hook_event_name           | 空（fail-soft）   | 0    |
| 註冊 args 誤用（argparse 拒絕）                   | 空（stderr 用法）  | 2（大聲、刻意——misconfig 歸註冊單一源修復） |

advance-after-emit：stdout 寫出成功後才 atomic（tmp+rename）推進 cursor；
推進失敗不擋 turn——下次重複提醒（寧可重複、不可漏）。冷啟動與 cursor 損壞
分離敘述：冷啟動（無 state 檔或該門牌無 cursor——正常首輪）掃至 timeline
尾端只建 cursor、靜默（防歷史洪水）；cursor 損壞（state 檔讀壞／cursor 值
形漂移）同樣視同冷啟動重建，但屬**已知 miss window**——last-good-save 後
未提醒事件整批錯過（非寧重不漏，self-heal 取捨記錄在案）：stderr 明顯警示
＋該次提醒行帶「（cursor 重建）」注記，請人工核對 `scbus address ls`。

已知限制：state 檔無鎖——多 address／多 consumer 並發擴張時需補
filelock/CAS（現行單 address 風險低——後果恆為重複提醒）。

monitor eligibility gate（最低限度 cwd/workspace 鎖）：hook 註冊在 user 層、
跨專案每次打字都觸發；session cwd（stdin payload `cwd`）不在 script 所在
repo 內＝非法 monitor invocation——零查詢、零輸出、不碰 state（防錯誤 session
吃掉 watermark）。fail-closed：cwd 缺席亦不推進。card WT 路徑不在字面前綴鎖
內（屬最低限度取捨——WT session 不提醒不推進，方向安全：寧重不漏）。

監看面邊界：本 script 不 hardcode 門牌——--address 可重複，monitor
subscription 由各 repo 註冊條目顯式宣告（ai-guide 註冊 ai-guide-marshal 單
值）；cursor 推進只代表本 invocation 的 reminder emitted。人工輪詢
（`scbus address ls --pending`）仍是 point-in-time fallback（hook 未註冊機器
／degraded 靜默時），兩面語義見 ownership doc monitor 段。

ZCode 協議（ref-docs/harness/zcode hooks.md）：stdin 一行 JSON；只有去空白後
以 { 開頭的合法 JSON 被協議解析，hookSpecificOutput.additionalContext 注入
context；同源多 hook 按陣列順序執行（本條目為獨立 group，不與 sc-router
canonical scbus hook 條目或 compact-restore-inject group 同 group——sc-router
installer 以精確 command equality 認 ownership，包進 wrapper 會與其 repair
機制打架）。部署 runtime 由 governance installer 解析 uv-managed Python 3.12
（hooks/AGENTS.md）；mixed-session／rollback 窗期維持 Python 3.9 語法相容。
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_payload_compat as compat

HOOK_TAG = "scbus-monitor"
SCBUS_TIMEOUT_SECONDS = 8  # hook 條目 timeoutMs=10000；內層更短留收尾餘裕
SUPPORTED_EVENTS = ("UserPromptSubmit", "SessionStart")
RECEIPTS_PAGE_LIMIT = 100  # face 草規 cursor+limit 從第一版就在——consumer 固定頁大小
RECEIPTS_MAX_PAGES = 50  # 單次 invocation 分頁上限（防 face 異常無限迴圈；超限 raise → fail-soft）
STATE_DIR = "ai-guide"
STATE_FILENAME = "scbus-address-monitor.json"
RUNNER_ENV = "SCBUS_MONITOR_RUNNER"  # shim 執行檔——face 未落地的環境變數注入點
DEGRADED_NOTE = "receipts face 不可用（細節見 stderr）"  # 其他失敗型——中性文案
FACE_ABSENT_NOTE = "receipts face 未落地——sc-router 卡追蹤中"  # 缺席型
FACE_ABSENT_MARKERS = (  # CLI 明確拒絕子命令的缺席訊號（stderr 分註 advisory）
    "invalid choice",
    "no such command",
    "unrecognized",
    "unknown command",
)


class ReceiptsFaceUnavailable(RuntimeError):
    """receipts timeline face 呼叫失敗（缺席／非零 exit／壞 JSON／形狀漂移）。

    上游 face（sc-router `address receipts`）落地前，真機呼叫必落此徑——
    不退化相容 `ls --pending`，以 degraded 訊息顯性標記交 fail-soft 靜默。
    """


# ── consumer-owned emitted_cursor 狀態（XDG state；atomic 寫）─────────


def state_path():
    """consumer-owned 狀態檔路徑（命名＝emitted_cursor 語義——禁
    last-seen/processed：只宣稱 reminder emitted，非 AI seen）。"""
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(base, STATE_DIR, STATE_FILENAME)


def _warn_cursor_rebuilt(detail):
    """cursor 損壞重建警示——stderr 明顯分離（corruption ≠ 冷啟動靜默；
    請人工核對 pending 快照補漏）。"""
    print(
        HOOK_TAG + ": cursor 損壞已重建——期間可能有漏提醒，請人工核對"
        " scbus address ls（" + detail + "）",
        file=sys.stderr,
    )


def load_state(path):
    """讀狀態檔 → (doc, rebuilt)；doc＝{address: {"emitted_cursor": str}}。

    缺檔＝冷啟動（rebuilt=False——正常首輪，無 miss window）。壞 JSON／
    非 dict／OSError＝cursor 損壞已重建（rebuilt=True）——**已知 miss
    window**：last-good-save 後未提醒事件整批靜默錯過，非寧重不漏（
    self-heal 取捨記錄在案——stderr 明顯警示，請人工核對 scbus address ls）。
    不 raise——state 損壞不該擋 turn。
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return {}, False
    except (OSError, ValueError) as exc:
        _warn_cursor_rebuilt(repr(exc))
        return {}, True
    if not isinstance(doc, dict):
        _warn_cursor_rebuilt("形狀漂移（非 dict）")
        return {}, True
    return doc, False


def save_state(path, doc):
    """atomic 寫（pid 後綴 tmp + os.replace）；失敗 raise——呼叫端以
    「不推進 cursor、下次重複提醒」吸收（寧重不漏）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True)
    os.replace(tmp, path)


def _stored_cursor(state, address):
    """取該門牌已 emitted cursor → (cursor, rebuilt)；無條目回
    (None, False)——冷啟動路徑（正常首輪，無 miss window）。

    條目在場但 cursor 非非空字串＝cursor 損壞——stderr 顯性警示後重建
    （rebuilt=True——已知 miss window，非寧重不漏；取捨同 load_state）。
    """
    entry = state.get(address)
    if entry is None:
        return None, False
    cursor = entry.get("emitted_cursor") if isinstance(entry, dict) else None
    if not isinstance(cursor, str) or not cursor:
        _warn_cursor_rebuilt(address)
        return None, True
    return cursor, False


# ── monitor eligibility gate（最低限度 cwd/workspace 鎖）──────────────


def script_repo_root():
    """hook script 所在 repo 根——registrations 以絕對路徑引用本目錄腳本
    （hooks 不能 symlink），repo 根＝hooks/ 上一層。測試 monkeypatch 此函式
    換鎖。"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def is_eligible(cwd):
    """合法 monitor invocation 判定：session cwd（payload `cwd`）必須在
    script 所在 repo 內。fail-closed——cwd 缺席／非字串／repo 外皆 False
    （gate 不過＝零查詢零輸出零推進，防錯誤 session 吃掉 watermark）。"""
    if not isinstance(cwd, str) or not cwd:
        return False
    root = script_repo_root()
    real = os.path.realpath(cwd)
    return real == root or real.startswith(root + os.sep)


# ── receipts face 查詢核心（stub-first；runner 注入）──────────────────


def _default_runner(argv):
    """真實 scbus 呼叫（無 shell）；SCBUS_MONITOR_RUNNER 設定時改經 shim
    執行檔（face 未落地的環境變數注入點——整合測試／上游落地前演練）。
    非零 exit＝失敗（raise → ReceiptsFaceUnavailable 包裝 → fail-soft）。"""
    shim = os.environ.get(RUNNER_ENV)
    if shim:
        cmd = [shim] + list(argv)
    else:
        cmd = list(argv)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=SCBUS_TIMEOUT_SECONDS,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()[:200]
        raise RuntimeError("scbus exit " + str(proc.returncode) + ": " + detail)
    return proc.stdout


def _parse_receipts_doc(out):
    """解析 receipts face 回應（codex 草規形）：items[]＋next_cursor＋
    has_more。形狀不符 raise TypeError（交 fail-soft 統一路徑，禁靜默歸零）。
    items 內容（envelope header/stages）在此層即丟棄——只留頁游標資訊，
    count-only 語義邊界的結構性防線。"""
    doc = json.loads(out)
    if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):
        raise TypeError("receipts face unexpected shape (items)")
    if not isinstance(doc.get("has_more"), bool):
        raise TypeError("receipts face unexpected shape (has_more)")
    cursor = doc.get("next_cursor")
    if cursor is not None and not isinstance(cursor, str):
        raise TypeError("receipts face unexpected shape (next_cursor)")
    return doc


def _query_receipts(address, after_cursor, runner=None):
    """`scbus address receipts --address <addr> [--after-cursor <c>]
    --limit N` 單頁查詢（純函式——資料進出全經參數與回傳值）。

    回傳 (items, next_cursor, has_more)；after_cursor=None＝冷啟動全
    timeline 掃描（face 草規：cursor 為 opaque token、--after-cursor
    exclusive）。任何失敗（缺席／非零 exit／壞 JSON／形狀漂移）一律包
    ReceiptsFaceUnavailable raise——degraded 訊息隨行，由 run() fail-soft
    吸收成靜默；**不退化相容 ls --pending**（語義不同，雙路徑已裁示不採）。
    """
    run = runner if runner is not None else _default_runner
    argv = [
        "scbus", "address", "receipts",
        "--address", address,
        "--limit", str(RECEIPTS_PAGE_LIMIT),
    ]
    if after_cursor is not None:
        argv += ["--after-cursor", after_cursor]
    try:
        out = run(argv)
        doc = _parse_receipts_doc(out)
    except ReceiptsFaceUnavailable:
        raise
    except Exception as exc:
        # 缺席型（CLI 明確拒絕子命令）與其他失敗型分訊——缺席保留「未落地
        # ——sc-router 卡追蹤中」語義，其他失敗帶實際錯誤摘要（repr 隨行）。
        if any(mark in str(exc) for mark in FACE_ABSENT_MARKERS):
            note = FACE_ABSENT_NOTE
        else:
            note = DEGRADED_NOTE
        raise ReceiptsFaceUnavailable(
            note + "（" + repr(exc) + "）"
        ) from exc
    return doc["items"], doc.get("next_cursor"), doc["has_more"]


def collect_new(address, after_cursor, runner=None):
    """自 cursor 起分頁收齊新 delivery events → (total_count, final_cursor)。

    has_more=true 續翻——cursor 只能推進到「已消費完」的位置，has_more 未盡
    停手會漏信，故翻到 has_more=false；頁數上限觸發 raise（fail-soft：不
    emit 不推進，寧重不漏）。has_more=true 而無 next_cursor＝形漂移 raise；
    has_more=false 而無 next_cursor＝face 未給端點 token——保留原 cursor
    （下輪重掃，寧重不漏）。after_cursor=None＝冷啟動。
    """
    cursor = after_cursor
    total = 0
    for _page in range(RECEIPTS_MAX_PAGES):
        items, cursor, has_more = _query_receipts(
            address, cursor, runner=runner
        )
        total += len(items)
        if has_more and cursor is None:
            raise TypeError(
                "receipts face: has_more without next_cursor for " + address
            )
        if not has_more:
            return total, (cursor if cursor is not None else after_cursor)
    raise RuntimeError(
        "receipts paging exceeded " + str(RECEIPTS_MAX_PAGES)
        + " pages for " + address
    )


# ── 輸出語義（accepted ≠ 送達 UI ≠ body 可讀——astra 邊界二）──────────


def reminder_line(address, count):
    """單門牌提醒行——新到收件紀錄計數＋語義校注＋讀取指針（含 snapshot
    範圍注記）＋禁權聲明。

    語義：本 hook 監看的是 delivery-event timeline（accepted 計數）——
    accepted 不等於送達 UI、更不等於內文可讀；讀取走人工輪詢指針——
    `ls --pending` 只映 new/ 快照（cur/ 已收信不在場，歷史對帳待 receipt
    face 查詢工具）。
    """
    return (
        "[" + HOOK_TAG + "] " + address + "：自上次知會後新到 " + str(count)
        + " 封收件紀錄（accepted≠送達 UI≠內文可讀）；讀取指針：scbus address"
        " ls --pending／SC UI（ls --pending 只映 new/；cur/ 已收信不在場，"
        "歷史對帳待 receipt face）。此提醒不授權 recv/ack/acquire"
    )


def rebuild_notice_line(address):
    """cursor 損壞重建注記行——stdout 帶「（cursor 重建）」注記，把 miss
    window 顯性交給 consumer（stderr 警示之外的 context 注入面；非寧重
    不漏，self-heal 取捨見 load_state docstring）。"""
    return (
        "[" + HOOK_TAG + "] " + address
        + "：cursor 損壞已重建——期間可能有漏提醒，請人工核對 scbus address"
        " ls（cursor 重建）"
    )


def monitor_once(addresses, runner, state_file):
    """逐門牌查 receipts timeline → (提醒行 list, state 更新 dict)。

    冷啟動（state 無該門牌 cursor——正常首輪）：掃至 timeline 尾端只建
    cursor（updates 帶 emitted_cursor）、不產提醒行（防歷史洪水）。cursor
    損壞（state 檔讀壞／cursor 值漂移）：同樣只建 cursor，但該次另產
    「（cursor 重建）」注記行（已知 miss window——非寧重不漏，見
    load_state）。既有 cursor：新到 N 封才產提醒行並排入 updates——updates
    交呼叫端在 stdout 寫出成功後 commit（advance-after-emit）。
    """
    path = state_file if state_file is not None else state_path()
    state, file_rebuilt = load_state(path)
    lines = []
    updates = {}
    for address in addresses:
        stored, rebuilt = _stored_cursor(state, address)
        total, final_cursor = collect_new(address, stored, runner=runner)
        if stored is None:
            # 冷啟動／損壞重建：只建 cursor 不灌歷史（防洪水）；face 未給
            # 端點 token（final_cursor=None）則不寫——下輪重掃，寧重不漏。
            # 損壞重建另帶注記行（miss window 顯性化，有別冷啟動靜默）。
            if final_cursor is not None:
                updates[address] = {"emitted_cursor": final_cursor}
            if rebuilt or file_rebuilt:
                lines.append(rebuild_notice_line(address))
            continue
        if total > 0 and final_cursor is not None:
            lines.append(reminder_line(address, total))
            updates[address] = {"emitted_cursor": final_cursor}
    return lines, updates


def run(raw, addresses, runner=None, state_file=None):
    """stdin 原文 → (exit_code, stdout payload, commit)。

    永不 raise、exit 恆 0。addresses＝註冊條目 --address 累積值（可重複；
    空＝無監看責任，靜默且不呼叫 scbus）。commit＝cursor 推進 closure（無
    推進需求時 None）——**呼叫端在 stdout 寫出成功後才執行**（
    advance-after-emit；寫失敗寧可下次重複提醒）。事件名經
    hook_payload_compat 正規化（grok snake 值同款處理；本 hook 僅註冊 zcode
    面，正規化為防禦性相容非註冊面宣稱）。
    """
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise TypeError("stdin not a JSON object")
        event_name = compat.hook_event_name(payload)
        if event_name not in SUPPORTED_EVENTS or not addresses:
            return 0, "", None
        if not is_eligible(payload.get("cwd")):
            return 0, "", None
        lines, updates = monitor_once(addresses, runner, state_file)
        out = ""
        if lines:
            out = json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event_name,
                        "additionalContext": "\n".join(lines),
                    }
                },
                ensure_ascii=False,
            )
        commit = None
        if updates:
            def commit():
                path = state_file if state_file is not None else state_path()
                doc, _rebuilt = load_state(path)
                doc.update(updates)
                save_state(path, doc)
        return 0, out, commit
    except Exception as exc:  # fail-soft by design——絕不擋 turn
        print(HOOK_TAG + ": fail-soft（" + repr(exc) + "）", file=sys.stderr)
        return 0, "", None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "scbus 門牌 receipt-timeline 監看提醒（AIR-233；sync 兩事件）"
        )
    )
    parser.add_argument(
        "--address",
        action="append",
        default=[],
        metavar="ADDR",
        help="要監看的門牌（可重複；由註冊條目顯式宣告，script 不 hardcode）",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    _code, out, commit = run(sys.stdin.read(), args.address)
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    if commit is not None:
        try:
            commit()  # advance-after-emit：stdout 寫出成功後才推進 cursor
        except Exception as exc:  # 寧重不漏——推進失敗不擋 turn
            print(
                HOOK_TAG + ": cursor 推進失敗——下次將重複提醒（"
                + repr(exc) + "）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
