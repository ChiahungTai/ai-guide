#!/usr/bin/env python3
"""dutymail 信箱 monitor 提醒 hook（AIR-254.4——AIR-233 提醒面降級重寫）。

trigger 骨架沿用 AIR-225.1：UserPromptSubmit（每次 user 打字）與
SessionStart（session 回場）兩個 interaction boundary，單一 script 服務
兩事件——stdin 的 hook_event_name 決定輸出的 hookEventName；兩註冊條目
皆 sync（additionalContext 通道 sync-only）。資料面由從未落地的 receipts
face（stub 恆靜默）降級重寫為 **dutymail 唯讀 face**（AIR-254.4 裁定）：
`events --kind accepted`（新信事件 timeline，keyset paging）＋`holder
status`（hold 偵測）。舊提醒 hook 檔（AIR-225.1/233 面）已隨本重寫退役。

**monitor ≠ holder（三軸不互代理——EP invariant）**：本 hook 只消費唯讀
face，禁 bind/prepare/ack（holder 家命令一律不觸達——收信處理面單一源＝
duty_receive 處理器）；advisory 語義＝「本 session 提醒到哪」（session
local 游標），絕不宣稱 global 狀態、不觸碰 human seen/done。count-only
——事件 payload 內容絕不進輸出。

**session-local 游標**：state＝`${XDG_STATE_HOME:-~/.local/state}/
ai-guide/duty-monitor/<safe_session_id>.json`（形 `{"addresses":
{"<alias>": {"events_cursor": str|null}}}`；0600 atomic 寫；路徑可注入）。
兩 session 游標互不干擾；safe session id sanitizer 與 duty-receive 同源
（import scripts/duty_receive 的 state_path，不複製）。**舊全域單檔
（AIR-225.1 面）隨本重寫停用——不刪不改零讀取**（留歷史對帳）。

**閒置完全安靜（AIR-233 降級裁定）**：註冊面即邊界——無 session 觸發＝
零查詢；程式碼無背景迴圈／watcher／wait 呼叫（badge 數字源是 SC 側投影
，非本 hook）。

每次觸發（過 eligibility gate）對每個 --address：
1. **hold 偵測**：duty-receive per-session state（本 session）在場且
   `holder status` 的 bindingEpoch==state.epoch 且 live=true → 本 session
   holding → 靜默＋游標推進至 head（查 events 拿最新 retained cursor
   存入，不輸出——值星收信由 duty_receive 處理器負責，提醒面安靜）。
2. 未 hold（無 state／epoch 不符／live=False／status 失敗）→ 查 events
   `--kind accepted`（自 session 游標起）：新事件 N>0 → 一行 advisory
   `[duty-monitor] <alias>：本 session 未 hold——新到 N 封信（recovery
   window；開 duty session 處理或「dutymail receive status」查看待處理）`
   ；N=0 → 靜默（游標已在 head）。冷啟動（無游標）掃到 head 只建游標
   不告警（防歷史洪水——與 AIR-225.1 同款取捨）。

dutymail events face 凍結語義（3.1.0 實測）：有 items 的頁恆帶非 null
nextCursor（內嵌 lastSeq 的 retained token）；空頁 nextCursor=null＝head
。續翻以 nextCursor 非空為準；retained cursor＝最後收到的非 null token。
單次上限 10 頁（防 face 異常無限迴圈——超限 raise 落 fail-soft）。

決策表（hook 運作面 stdout 皆協議 JSON 或空、exit 恆 0；唯一例外＝註冊
args 誤用）：

| 情境 | stdout | exit |
|---|---|---|
| 未 hold＋新到 N 封（每門牌一行） | hookSpecificOutput | 0 |
| holding／冷啟動／N=0／無 --address／缺 session_id | 空（靜默） | 0 |
| store 缺席（storage class）／face 失敗／形漂移 | 空＋stderr 註記帶錯誤摘要 | 0 |
| eligibility gate 不過（cwd 在 repo 外） | 空（零查詢零輸出零推進） | 0 |
| monitor state 損壞（讀壞／形漂移） | 視同冷啟動（stderr 註記、靜默重建） | 0 |
| 游標推進失敗（state 寫失敗） | 提醒照出（寧重不漏——下次重複提醒） | 0 |
| stdin 壞 JSON／缺或未知 hook_event_name | 空（fail-soft） | 0 |
| 註冊 args 誤用（argparse 拒絕） | 空（stderr 用法） | 2（大聲、刻意——misconfig 歸註冊單一源修復） |

advance-after-emit：stdout 寫出成功後才 atomic（tmp+rename＋0600）推進
游標；推進失敗不擋 turn——下次重複提醒（寧可重複、不可漏）。

monitor eligibility gate（AIR-225.1 模式）：hook 註冊在 user 層、跨專案
每次打字都觸發；session cwd（stdin payload `cwd`）不在 script 所在 repo
內＝非法 monitor invocation——零查詢、零輸出、不碰 state（防錯誤 session
吃掉游標）。fail-closed：cwd 缺席亦不推進。script 所在 repo 含卡 WT（
registrations 絕對路徑指向哪個 checkout，鎖就落在該 checkout——含
authoring WT 自測）。

監看面邊界：本 script 不 hardcode 門牌——--address 可重複，subscription
由各 repo 註冊條目顯式宣告（ai-guide 註冊 ai-guide-marshal）。人工輪詢
（`dutymail receive status`）保留為 point-in-time fallback。

ZCode 協議（ref-docs/harness/zcode hooks.md）：stdin 一行 JSON；只有去
空白後以 { 開頭的合法 JSON 被協議解析，hookSpecificOutput.additionalContext
注入 context；本條目為獨立 group（不與 compact-restore-inject 或
duty_receive 同 group）。部署 runtime 由 governance installer 解析
uv-managed Python 3.12（hooks/AGENTS.md）；mixed-session／rollback 窗期
維持 Python 3.9 語法相容。
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
for _path in (_HERE, os.path.join(_REPO, "scripts")):
    if _path not in sys.path:
        sys.path.insert(0, _path)
import duty_receive as core  # state 面／runner／holder status 單一源（import 不複製）
import hook_payload_compat as compat

HOOK_TAG = "duty-monitor"
SUPPORTED_EVENTS = ("UserPromptSubmit", "SessionStart")
EVENTS_PAGE_LIMIT = 100  # consumer 固定頁大小（events face --limit）
EVENTS_MAX_PAGES = 10  # 單次 invocation 分頁上限（防 face 異常無限迴圈；超限 raise → fail-soft）
STATE_DIRNAME = "duty-monitor"  # session-local 游標目錄（XDG state／ai-guide/ 下）


# ── monitor eligibility gate（AIR-225.1 模式：cwd/workspace 鎖）────────


def script_repo_root():
    """hook script 所在 repo 根——registrations 以絕對路徑引用本目錄腳本
    （hooks 不能 symlink），repo 根＝hooks/ 上一層。測試 monkeypatch 此函式
    換鎖。"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def is_eligible(cwd):
    """合法 monitor invocation 判定：session cwd（payload `cwd`）必須在
    script 所在 repo 內。fail-closed——cwd 缺席／非字串／repo 外皆 False
    （gate 不過＝零查詢零輸出零推進，防錯誤 session 吃掉游標）。"""
    if not isinstance(cwd, str) or not cwd:
        return False
    root = script_repo_root()
    real = os.path.realpath(cwd)
    return real == root or real.startswith(root + os.sep)


# ── session-local 游標 state（XDG state；0600 atomic 寫）──────────────


def _state_base_dir():
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(base, "ai-guide", STATE_DIRNAME)


def monitor_state_path(session_id, base_dir=None):
    """session-local 游標檔路徑（duty-monitor/<safe_session_id>.json）——
    safe session id sanitizer 與 duty-receive state 同源（core.state_path，
    import 不複製）；base_dir 可注入（測試 fake state）。"""
    root = base_dir if base_dir is not None else _state_base_dir()
    return core.state_path(session_id, base_dir=root)


def load_doc(path):
    """讀游標檔 → {"addresses": {...}}。缺檔＝冷啟動（{}——正常首輪）；
    壞 JSON／OSError／形狀漂移（非 dict／addresses 非 dict）＝視同冷啟動
    重建（stderr 註記——session-local 檔，重建後果＝該 session 重新
    baseline，方向安全）。不 raise——state 損壞不該擋 turn。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        print(
            f"[{HOOK_TAG}] 監看 state 損壞——視同冷啟動重建"
            f"（{exc!r}；路徑 {path}）",
            file=sys.stderr,
        )
        return {}
    if not isinstance(doc, dict) or not isinstance(doc.get("addresses"), dict):
        print(
            f"[{HOOK_TAG}] 監看 state 形狀漂移——視同冷啟動重建（路徑 {path}）",
            file=sys.stderr,
        )
        return {}
    return doc


def _stored_cursor(doc, address):
    """取該門牌已 retained 游標 → str | None。無條目／events_cursor 為
    null＝None（冷啟動路徑）；值形漂移（非字串非 null）＝stderr 註記後
    視同 None 重建。"""
    entry = doc.get("addresses", {}).get(address)
    cursor = entry.get("events_cursor") if isinstance(entry, dict) else None
    if cursor is not None and not (isinstance(cursor, str) and cursor):
        print(
            f"[{HOOK_TAG}] 游標值形漂移（{address}）——視同冷啟動重建",
            file=sys.stderr,
        )
        return None
    return cursor


# ── hold 偵測（唯讀：duty-receive state＋holder status）───────────────


def _session_holds(runner, session_id, address, holder_state_dir=None):
    """本 session 是否 holding <address>：duty-receive per-session state
    在場（token＋epoch＋address 對上——core._valid_holder_state）且
    `holder status` 的 bindingEpoch==state.epoch 且 live=true。status
    失敗（任何例外）＝未 hold——交 events 路徑（store 缺席時 events 同步
    失敗落 fail-soft，不誤判 holding 靜默吞信）。"""
    st = core.load_state(core.state_path(session_id, holder_state_dir))
    if not core._valid_holder_state(st, address):
        return False
    try:
        status = core.holder_status(runner, address)
    except Exception:
        return False
    return (
        status.get("bindingEpoch") == st.get("epoch")
        and status.get("live") is True
    )


# ── events face 查詢核心（唯讀；runner 注入）─────────────────────────


def _events_page(runner, address, cursor):
    """`events --address <a> --kind accepted --limit N [--cursor <tok>]`
    單頁查詢 → (items, next_cursor)。stdout 契約解析走 core._call；items
    ／nextCursor 形狀漂移 raise（交 fail-soft 統一路徑，禁靜默歸零）。"""
    argv = [
        "events", "--address", address,
        "--kind", "accepted", "--limit", str(EVENTS_PAGE_LIMIT),
    ]
    if cursor is not None:
        argv += ["--cursor", cursor]
    result = core._call(runner, argv)
    items = result.get("items")
    nxt = result.get("nextCursor")
    if not isinstance(items, list):
        raise core.DutymailFaceError(
            "shape-drift", "unknown",
            f"events face items 非 list：{result!r}", False, 0,
        )
    if nxt is not None and not isinstance(nxt, str):
        raise core.DutymailFaceError(
            "shape-drift", "unknown",
            f"events face nextCursor 形漂移：{nxt!r}", False, 0,
        )
    return items, nxt


def collect_events(runner, address, after_cursor):
    """自 cursor 起分頁收齊 accepted 事件 → (total_count, retained_cursor)。

    凍結語義：有 items 的頁恆帶非 null nextCursor（retained token）；空頁
    nextCursor=null＝head。續翻以 nextCursor 非空為準——retained cursor＝
    最後收到的非 null token（首頁即空＝after_cursor 原值——冷啟動空
    timeline 時 None，無游標可建）。頁數上限觸發 raise（fail-soft：不
    emit 不推進，寧重不漏）。"""
    cursor = after_cursor
    total = 0
    for _page in range(EVENTS_MAX_PAGES):
        items, nxt = _events_page(runner, address, cursor)
        total += len(items)
        if nxt is None:
            return total, cursor
        cursor = nxt
    raise RuntimeError(
        "events paging exceeded " + str(EVENTS_MAX_PAGES)
        + " pages for " + address
    )


# ── 輸出語義（advisory＝本 session 提醒到哪）─────────────────────────


def advisory_line(address, count):
    """單門牌 advisory 行——未 hold＋新到計數＋recovery window 語義＋
    讀取指針。語義＝「本 session 提醒到哪」：不宣稱 global 狀態、不觸
    human seen/done、非責任結清點。"""
    return (
        f"[{HOOK_TAG}] {address}：本 session 未 hold——新到 {count} 封信"
        "（recovery window；開 duty session 處理或 `dutymail receive"
        " status` 查看待處理）"
    )


def monitor_once(addresses, runner, session_id, state_file=None,
                 holder_state_dir=None):
    """逐門牌監看 → (advisory 行 list, 游標 updates)。

    holding → 靜默＋游標推進至 head；未 hold → 冷啟動（無游標）靜默建
    游標（防歷史洪水）、暖游標新事件 N>0 出一行 advisory；N=0 靜默（
    游標已在 head——零推進需求）。updates 交呼叫端在 stdout 寫出成功後
    commit（advance-after-emit）。"""
    path = state_file if state_file is not None else monitor_state_path(
        session_id
    )
    doc = load_doc(path)
    lines = []
    updates = {}
    for address in addresses:
        stored = _stored_cursor(doc, address)
        holding = _session_holds(runner, session_id, address,
                                 holder_state_dir)
        total, final_cursor = collect_events(runner, address, stored)
        if final_cursor is not None and final_cursor != stored:
            updates[address] = {"events_cursor": final_cursor}
        if holding or stored is None:
            continue  # holding 靜默推進；冷啟動靜默建游標
        if total > 0:
            lines.append(advisory_line(address, total))
    return lines, updates


def run(raw, addresses, runner=None, state_file=None, holder_state_dir=None):
    """stdin 原文 → (exit_code, stdout payload, commit | None)。

    永不 raise、exit 恆 0（唯一例外＝註冊 args 誤用由 argparse exit 2）。
    addresses＝註冊條目 --address 累積值（可重複；空＝無監看責任，靜默
    且零查詢）。commit＝游標推進 closure（無推進需求時 None）——呼叫端
    在 stdout 寫出成功後才執行（advance-after-emit；寫失敗寧可下次重複
    提醒）。事件名／session_id 經 hook_payload_compat 正規化（grok
    snake 值同款處理；本 hook 僅註冊 zcode 面，正規化為防禦性相容）。
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
        session_id = compat.session_id(payload)
        if not session_id:
            return 0, "", None
        run_fn = runner if runner is not None else core._default_runner
        lines, updates = monitor_once(
            addresses, run_fn, session_id,
            state_file=state_file, holder_state_dir=holder_state_dir,
        )
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
                path = state_file if state_file is not None else (
                    monitor_state_path(session_id)
                )
                doc = load_doc(path)
                doc.setdefault("addresses", {}).update(updates)
                core.save_state(path, doc)
        return 0, out, commit
    except core.DutymailFaceError as exc:
        kind = (
            "store 缺席（pre-migration）" if exc.is_storage
            else "dutymail face 失敗"
        )
        print(f"[{HOOK_TAG}] fail-soft：{kind}——{exc}", file=sys.stderr)
        return 0, "", None
    except Exception as exc:  # fail-soft by design——絕不擋 turn
        print(f"[{HOOK_TAG}] fail-soft（{exc!r}）", file=sys.stderr)
        return 0, "", None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "dutymail 信箱 monitor 提醒（AIR-254.4；SessionStart／"
            "UserPromptSubmit sync 兩事件）"
        )
    )
    parser.add_argument(
        "--address",
        action="append",
        default=[],
        metavar="ALIAS",
        help="要監看的門牌（可重複；由註冊條目顯式宣告，script 不 hardcode）",
    )
    return parser.parse_args(argv)


def main(argv=None, runner=None) -> int:
    args = parse_args(argv)
    _code, out, commit = run(sys.stdin.read(), args.address, runner=runner)
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    if commit is not None:
        try:
            commit()  # advance-after-emit：stdout 寫出成功後才推進游標
        except Exception as exc:  # 寧重不漏——推進失敗不擋 turn
            print(
                f"[{HOOK_TAG}] 游標推進失敗——下次將重複提醒（{exc!r}）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
