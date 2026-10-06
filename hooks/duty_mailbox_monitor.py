#!/usr/bin/env python3
"""dutymail 信箱 monitor 提醒 hook（AIR-254.4——AIR-233 提醒面降級重寫；
AIR-258 B′ 解凍：holderless pending 語義改常態）。

trigger 骨架沿用 AIR-225.1：UserPromptSubmit（每次 user 打字）與
SessionStart（session 回場）兩個 interaction boundary，單一 script 服務
兩事件——stdin 的 hook_event_name 決定輸出的 hookEventName；兩註冊條目
皆 sync（additionalContext 通道 sync-only）。舊提醒 hook 檔（AIR-225.1/
233 面）已隨本重寫退役。

**語義裁定（marshal judge 採納）**：bounded monitor reports **holderless
pending**（AIR-258 B′ 解凍改常態語義——pending 在 INBOX 等人判讀；B′ 前
為 duty-active 異常窗口語義）。資料面只留兩個唯讀 face——
`holder status`（live 偵測）＋`receive status`（pendingCount 現值）；
events face 消費（accepted 事件史計數）全面退役——事件史不因 ack 消失，
對他方 holding 的門牌會誤報、且與 duty_receive 衝突行（「處理面照舊由
現 holder 承擔」）同邊界並存時自相矛盾。

**monitor ≠ holder（三軸不互代理——EP invariant）**：本 hook 只消費唯讀
face，禁 bind/prepare/ack（holder 家命令一律不觸達——收信處理面單一源＝
duty_receive 處理器）；advisory 語義＝「本 session 提醒到哪」（session
local baseline），絕不宣稱 global 狀態、不觸碰 human seen/done。count-
only——pendingCount 整數以外絕不進輸出。

決策表（per address；每次觸發過 eligibility gate 後逐門牌）：
1. `holder status` live=True（本 session hold——duty-receive state
   epoch==status.epoch，或他方 live）→ 靜默（covered：處理面由 holder
   承擔）＋`last_pending` baseline 歸零。
2. live=False（**holderless**——B′ 常態：pending 在 INBOX 等人判讀）→
   `receive status` pendingCount：
   - >0 且 ≠ baseline → 一行 advisory `[duty-monitor] <alias>：
     holderless pending N 封（pending 在 INBOX 等人判讀——B′：workspace
     信終點＝durable INBOX；dutymail receive status 可查）`＋baseline=N；
   - >0 且 == baseline（未變化）→ 靜默（防每 prompt 轟炸）；
   - ==0 → 靜默＋baseline 歸零。
3. face 失敗（store 缺席／unknown-address／pendingCount 形漂移）→ 該門牌
   stderr 註記＋零 stdout，續跑其他門牌（fail-soft；per-address 容錯）。

**session-local baseline**：state＝`${XDG_STATE_HOME:-~/.local/state}/
ai-guide/duty-monitor/<safe_session_id>.json`（形 `{"addresses":
{"<alias>": {"last_pending": int}}}`；0600 atomic 寫；路徑可注入）。
兩 session baseline 互不干擾；safe session id sanitizer 與 duty-receive
同源（import scripts/duty_receive 的 state_path，不複製）。**舊全域單檔
（AIR-225.1 面）隨本重寫停用——不刪不改零讀取**（留歷史對帳）。

**閒置完全安靜（AIR-233 降級裁定）**：註冊面即邊界——無 session 觸發＝
零查詢；程式碼無背景迴圈／watcher／wait 呼叫（badge 數字源是 SC 側投影
，非本 hook）。

決策表（hook 運作面 stdout 皆協議 JSON 或空、exit 恆 0；唯一例外＝註冊
args 誤用）：

| 情境 | stdout | exit |
|---|---|---|
| holderless pending N 封且值變化（每門牌一行） | hookSpecificOutput | 0 |
| live=True（holding／他方 live）／pending==0／同值／無 --address／缺 session_id | 空（靜默） | 0 |
| 單門牌 face 失敗（storage class／其他／形漂移） | 該門牌空＋stderr 註記（其他門牌照跑） | 0 |
| eligibility gate 不過（cwd 在 repo 外） | 空（零查詢零輸出零推進） | 0 |
| monitor state 損壞（讀壞／形漂移） | 視同冷啟動（stderr 註記、靜默重建） | 0 |
| baseline 寫入失敗（state 寫失敗） | 提醒照出（寧重不漏——下次重複提醒） | 0 |
| stdin 壞 JSON／缺或未知 hook_event_name | 空（fail-soft） | 0 |
| 註冊 args 誤用（argparse 拒絕） | 空（stderr 用法） | 2（大聲、刻意——misconfig 歸註冊單一源修復） |

advance-after-emit：stdout 寫出成功後才 atomic（tmp+rename＋0600）推進
baseline；推進失敗不擋 turn——下次重複提醒（寧可重複、不可漏）。

monitor eligibility gate（AIR-225.1 模式）：hook 註冊在 user 層、跨專案
每次打字都觸發；session cwd（stdin payload `cwd`）不在 script 所在 repo
內＝非法 monitor invocation——零查詢、零輸出、不碰 state（防錯誤 session
吃掉 baseline）。fail-closed：cwd 缺席亦不推進。script 所在 repo 含卡 WT（
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
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)  # hook_payload_compat（hooks/ 同目錄）
import hook_payload_compat as compat

# state 面／runner／holder＋receive status 單一源＝scripts/duty_receive.py
# ——以檔案路徑顯式載入（自建模組名 _duty_receive_core，不進
# sys.modules["duty_receive"]）：sys.path dance 下 `import duty_receive`
# 在 scripts/ 已在 path 時會解析回 hooks/ 自己（同名 circular import），
# 對 scripts/ 的 path 依賴整段退役（import 不複製核心邏輯）。
_core_spec = importlib.util.spec_from_file_location(
    "_duty_receive_core", os.path.join(_REPO, "scripts", "duty_receive.py")
)
core = importlib.util.module_from_spec(_core_spec)
_core_spec.loader.exec_module(core)

HOOK_TAG = "duty-monitor"
SUPPORTED_EVENTS = ("UserPromptSubmit", "SessionStart")
STATE_DIRNAME = "duty-monitor"  # session-local baseline 目錄（XDG state／ai-guide/ 下）


# ── monitor eligibility gate（AIR-225.1 模式：cwd/workspace 鎖）────────


def script_repo_root():
    """hook script 所在 repo 根——registrations 以絕對路徑引用本目錄腳本
    （hooks 不能 symlink），repo 根＝hooks/ 上一層。測試 monkeypatch 此函式
    換鎖。"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def is_eligible(cwd):
    """合法 monitor invocation 判定：session cwd（payload `cwd`）必須在
    script 所在 repo 內。fail-closed——cwd 缺席／非字串／repo 外皆 False
    （gate 不過＝零查詢零輸出零推進，防錯誤 session 吃掉 baseline）。"""
    if not isinstance(cwd, str) or not cwd:
        return False
    root = script_repo_root()
    real = os.path.realpath(cwd)
    return real == root or real.startswith(root + os.sep)


# ── session-local baseline state（XDG state；0600 atomic 寫）───────────


def _state_base_dir():
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(base, "ai-guide", STATE_DIRNAME)


def monitor_state_path(session_id, base_dir=None):
    """session-local baseline 檔路徑（duty-monitor/<safe_session_id>.json）
    ——safe session id sanitizer 與 duty-receive state 同源（core.state_path
    ，import 不複製）；base_dir 可注入（測試 fake state）。"""
    root = base_dir if base_dir is not None else _state_base_dir()
    return core.state_path(session_id, base_dir=root)


def load_doc(path):
    """讀 baseline 檔 → {"addresses": {...}}。缺檔＝冷啟動（{}——正常首輪）
    ；壞 JSON／OSError／形狀漂移（非 dict／addresses 非 dict）＝視同冷啟動
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


def _stored_last_pending(doc, address):
    """取該門牌 baseline → int | None。無條目＝None（冷啟動路徑）；值形
    漂移（非非負整數）＝stderr 註記後視同 None 重建。"""
    entry = doc.get("addresses", {}).get(address)
    value = entry.get("last_pending") if isinstance(entry, dict) else None
    if value is None:
        return None
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        print(
            f"[{HOOK_TAG}] baseline 值形漂移（{address}）——視同冷啟動重建",
            file=sys.stderr,
        )
        return None
    return value


# ── holderless pending 查詢（唯讀 receive status；runner 注入）────────


def _pending_count(runner, address):
    """`receive status --address <a>` → pendingCount（非負整數）。pendingCount
    形漂移 raise（shape-drift——交 per-address fail-soft 統一路徑，禁靜默
    歸零）。"""
    result = core.receive_status(runner, address)
    count = result.get("pendingCount")
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
    ):
        raise core.DutymailFaceError(
            "shape-drift", "unknown",
            f"receive status pendingCount 非非負整數：{result!r}", False, 0,
        )
    return count


# ── 輸出語義（advisory＝本 session 提醒到哪）─────────────────────────


def advisory_line(address, count):
    """單門牌 advisory 行——holderless pending 計數＋常態語義（B′：
    workspace 信終點＝durable INBOX，pending 等人判讀非異常）＋查詢
    指針。語義＝「本 session 提醒到哪」：不宣稱 global 狀態、不觸
    human seen/done、非責任結清點。"""
    return (
        f"[{HOOK_TAG}] {address}：holderless pending {count} 封"
        "（pending 在 INBOX 等人判讀——B′：workspace 信終點＝durable INBOX；"
        "dutymail receive status 可查）"
    )


def monitor_once(addresses, runner, session_id, state_file=None):
    """逐門牌監看（決策表見 module docstring）→ (advisory 行 list,
    baseline updates)。

    live=True → 靜默＋baseline 歸零（僅在現值非 0 時寫入）；holderless →
    pendingCount 值變化才出 advisory＋推進 baseline（同值防轟炸）；==0 歸零
    。單門牌 face 失敗＝stderr 註記續跑其他（per-address 容錯）。updates
    交呼叫端在 stdout 寫出成功後 commit（advance-after-emit）。"""
    path = state_file if state_file is not None else monitor_state_path(
        session_id
    )
    doc = load_doc(path)
    lines = []
    updates = {}
    for address in addresses:
        try:
            last = _stored_last_pending(doc, address)
            status = core.holder_status(runner, address)
            if status.get("live") is True:
                # 本 session hold（duty-receive state epoch==status.epoch）
                # 或他方 live——處理面由 holder 承擔：靜默＋baseline 歸零。
                if last is not None and last != 0:
                    updates[address] = {"last_pending": 0}
                continue
            pending = _pending_count(runner, address)
        except core.DutymailFaceError as exc:
            kind = (
                "store 缺席（pre-migration）" if exc.is_storage
                else "dutymail face 失敗"
            )
            print(
                f"[{HOOK_TAG}] {address} fail-soft：{kind}——{exc}",
                file=sys.stderr,
            )
            continue
        except Exception as exc:  # per-address fail-soft——續跑其他門牌
            print(
                f"[{HOOK_TAG}] {address} fail-soft（{exc!r}）",
                file=sys.stderr,
            )
            continue
        if pending == 0:
            if last is not None and last != 0:
                updates[address] = {"last_pending": 0}
            continue
        if pending == last:
            continue  # 同值未變化——防每 prompt 轟炸（baseline 保留）
        lines.append(advisory_line(address, pending))
        updates[address] = {"last_pending": pending}
    return lines, updates


def run(raw, addresses, runner=None, state_file=None):
    """stdin 原文 → (exit_code, stdout payload, commit | None)。

    永不 raise、exit 恆 0（唯一例外＝註冊 args 誤用由 argparse exit 2）。
    addresses＝註冊條目 --address 累積值（可重複；空＝無監看責任，靜默
    且零查詢）。commit＝baseline 推進 closure（無推進需求時 None）——
    呼叫端在 stdout 寫出成功後才執行（advance-after-emit；寫失敗寧可
    下次重複提醒）。事件名／session_id 經 hook_payload_compat 正規化（grok
    snake 值同款處理；本 hook 僅註冊 zcode 面，正規化為防禦性相容）。"""
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
            addresses, run_fn, session_id, state_file=state_file,
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
    except Exception as exc:  # fail-soft by design——絕不擋 turn
        print(f"[{HOOK_TAG}] fail-soft（{exc!r}）", file=sys.stderr)
        return 0, "", None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "dutymail 信箱 monitor 提醒（AIR-254.4；holderless pending"
            "——SessionStart／UserPromptSubmit sync 兩事件）"
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
            commit()  # advance-after-emit：stdout 寫出成功後才推進 baseline
        except Exception as exc:  # 寧重不漏——推進失敗不擋 turn
            print(
                f"[{HOOK_TAG}] baseline 寫入失敗——下次將重複提醒（{exc!r}）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
