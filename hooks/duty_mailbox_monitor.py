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
`holder status`（binding active 偵測；AIR-288：3.8.0 欄位 bound、
3.7.0 live——core.holder_active get-or-fallback 雙版同判定）＋
`receive status`（pendingCount 現值）；events face 消費（accepted 事件
史計數）全面退役——事件史不因 ack 消失，對他方 holding 的門牌會誤報、
且與 duty_receive 衝突行（「處理面照舊由現 holder 承擔」）同邊界並存時
自相矛盾。

**monitor ≠ holder（三軸不互代理——EP invariant）**：本 hook 只消費唯讀
face，禁 bind/prepare/ack（holder 家命令一律不觸達——收信處理面單一源＝
duty_receive 處理器）；advisory 語義＝「本 session 提醒到哪」（session
local baseline），絕不宣稱 global 狀態、不觸碰 human seen/done。count-
only——pendingCount 整數以外絕不進輸出。

決策表（per address；每次觸發過 eligibility gate 後逐門牌）：
1. `holder status` binding active=True（3.8.0 bound／3.7.0 live——本
   session hold——duty-receive state epoch==status.epoch，或他方
   holding）→ 靜默（covered：處理面由 holder 承擔）＋`last_pending`
   baseline 歸零＋pending-age 帳清（AIR-294——stall 語義限 holderless）。
2. active=False（**holderless**——B′ 常態：pending 在 INBOX 等人判讀）→
   `receive status` pendingCount：
   - >0 且 ≠ baseline → 一行 advisory `[duty-monitor] <alias>：
     holderless pending N 封（pending 在 INBOX 等人判讀——B′：workspace
     信終點＝durable INBOX；dutymail receive status 可查）`＋baseline=N；
   - >0 且 == baseline（未變化）→ 靜默（防每 prompt 轟炸）；
   - ==0 → 靜默＋baseline 歸零＋pending-age 帳清（drain 發生——
     帳窗結束；episode token 不變，邊界定義單一源＝下 fencing 段）。
3. face 失敗（store 缺席／unknown-address／pendingCount 形漂移）→ 該門牌
   stderr 註記＋零 stdout，續跑其他門牌（fail-soft；per-address 容錯）。
4. **pending 停留呈報（AIR-294 c——holderless stall）**：holderless
   pending>0 時核對跨 session 共享年齡帳 `pending-age.json`——首見＝
   seed `first_pending_at_us`（年齡未知不呈報）；停留逾
   `PENDING_STALL_REPORT_HOURS`（6h——具名常數）且本帳窗未呈報過
   → 一行 `[duty-monitor] <alias>：pending 停留已逾 6 小時（…升 human
   判讀）`＋`stall_reported` flag 落帳（每帳窗一報——防轟炸；帳窗＝
   seed→drain／清帳，drain 後重積＝新帳窗可再報——寧重複不漏）。
   年齡源＝monitor 自持帳（`receive status` 無時間戳欄；runner 呼叫面
   凍結兩唯讀 face 零新增——年齡由帳面推導非新查詢；episode token
   ＝holder status 回應在場的 `bindingEpoch`，零新 face）；事件史消費
   仍退役（上段裁定不變）。併發姿態：跨 session 並寫＝atomic replace
   last-writer-wins＋**episode fencing（AIR-297——本段＝episode 邊界
   定義單一源）**。episode token＝`holder status` 的 `bindingEpoch`
   （bind/rebind 即新 episode；drain 清帳不改 token——同 binding 內
   drain→重積＝同 episode 新帳窗，故寫側另需下述 CAS）。兩層防線：
   (1) 讀側帳條目帶 `episode_id`，token 不匹配（跨 binding 延遲寫入
   殘留／pre-fencing 舊 schema 條目）→ 視為 stale 清帳重建；(2) 寫側
   **doc-rev CAS**——帳文件帶單調 `rev` 欄（每次成功存檔 +1；無欄
   舊檔＝rev 0 冷啟動相容），monitor 讀時 snapshot、commit 時重讀
   比對，不符＝決策快照過期（他方 drain／seed 已推進帳）→ 本輪帳
   寫入整批丟棄＋stderr 註記——同 epoch write-after-clear 的
   `stall_reported` 復活與陳期 seed 蓋新 seed（年齡虛胖早報）同類
   stale-read overwrite 封閉；丟棄方向＝至多重複一報、不漏報。殘餘
   窗口＝commit 內 CAS 比對與存檔之間的微秒窗（atomic replace
   last-writer-wins 仍在），方向同前。

**session-local baseline**：state＝`${XDG_STATE_HOME:-~/.local/state}/
ai-guide/duty-monitor/<safe_session_id>.json`（形 `{"addresses":
{"<alias>": {"last_pending": int}}}`；0600 atomic 寫；路徑可注入）。
兩 session baseline 互不干擾；safe session id sanitizer 與 duty-receive
同源（import scripts/duty_receive 的 state_path，不複製）。**舊全域單檔
（AIR-225.1 面）隨本重寫停用——不刪不改零讀取**（留歷史對帳）。

**pending 停留帳（AIR-294 c——跨 session 共享）**：同目錄
`pending-age.json`（形 `{"rev": int 單調遞增（doc-rev CAS——AIR-297）,
"addresses": {"<alias>": {"first_pending_at_us": int,
"stall_reported": bool, "episode_id": int＝bindingEpoch episode
fencing（AIR-297）}}}`；0600 atomic 寫）。baseline 是「本 session
提醒到哪」（session-local 語義不變）；年齡帳是 mailbox 事實（跨
session 共享——新 session 接手即知停留年齡，不重計時）。兩帳同一
commit 面推進、各自 fail-soft。

**閒置完全安靜（AIR-233 降級裁定）**：註冊面即邊界——無 session 觸發＝
零查詢；程式碼無背景迴圈／watcher／wait 呼叫（badge 數字源是 SC 側投影
，非本 hook）。

決策表（hook 運作面 stdout 皆協議 JSON 或空、exit 恆 0；唯一例外＝註冊
args 誤用）：

| 情境 | stdout | exit |
|---|---|---|
| holderless pending N 封且值變化（每門牌一行） | hookSpecificOutput | 0 |
| active=True（holding／他方 holding）／pending==0／同值／無 --address／缺 session_id | 空（靜默） | 0 |
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
import time

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

# pending 停留呈報門檻（AIR-294 c——具名常數非散落魔數；卡面建議 6h）。
PENDING_STALL_REPORT_HOURS = 6
HOURS_US = 3_600_000_000
# pending 停留帳（跨 session 共享 mailbox 事實；與 session baseline 同目錄）。
AGE_STATE_BASENAME = "pending-age.json"


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


def pending_age_state_path(state_file=None, base_dir=None):
    """pending 停留帳路徑（AIR-294 c——duty-monitor/pending-age.json）。

    跨 session 共享的 mailbox 事實（對比 session-local baseline 的「本
    session 提醒到哪」語義）：holderless pending 首見時刻＋每帳窗一報
    flag。state_file 注入時取其同目錄（測試隔離同源）；否則落
    duty-monitor state 根。"""
    if state_file is not None:
        return os.path.join(os.path.dirname(state_file), AGE_STATE_BASENAME)
    root = base_dir if base_dir is not None else _state_base_dir()
    return os.path.join(root, AGE_STATE_BASENAME)


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


# ── pending 停留帳（AIR-294 c——holderless stall 年齡）─────────────────


def _doc_rev(doc, path=None):
    """帳文件單調 revision（AIR-297 doc-rev CAS fencing）→ int。

    讀側 snapshot、commit 端重讀比對：中間被任何他方推進（rev 不同）
    ＝決策快照過期——本輪帳寫入整批丟棄（stale-read overwrite 防線
    ：同 epoch write-after-clear 的 stall flag 復活、陳期 seed 蓋新
    seed 同類封閉；寧重複不漏報）。缺 `rev` 欄舊檔＝rev 0（冷啟動
    相容，不打爆）；在場但非非負整數＝形漂移，stderr 註記後視 0
    （保守——與健全 rev 比對大機率不等即丟棄，不靜默覆寫）。"""
    rev = doc.get("rev")
    if rev is None:
        return 0  # pre-CAS 舊檔無欄——rev 0 冷啟動
    if isinstance(rev, int) and not isinstance(rev, bool) and rev >= 0:
        return rev
    print(
        f"[{HOOK_TAG}] pending-age 帳 rev 欄形漂移——視 0 處理"
        f"（路徑 {path}）",
        file=sys.stderr,
    )
    return 0


def _age_entry_raw(doc, address):
    """取該門牌年齡條目 raw → dict | None（無條目＝None）。"""
    entry = doc.get("addresses", {}).get(address)
    return entry if isinstance(entry, dict) else None


def _episode_of(status):
    """holder status 回應的 `bindingEpoch` → episode token（AIR-297
    fencing——bind/rebind 即新 episode，epoch 單調遞增）。非負整數驗證
    （0 合法——fresh address unbound e=0，S3 實測）；形漂移 raise
    shape-drift（同 core bindingEpoch 驗證先例，交 per-address
    fail-soft——禁靜默當 0）。零新增 dutymail face：epoch 源＝既有
    holder status 回應在場欄位。"""
    epoch = status.get("bindingEpoch")
    if not core._non_negative_int(epoch):
        raise core.DutymailFaceError(
            "shape-drift", "unknown",
            f"holder status bindingEpoch 非非負整數：{status!r}",
            False, 0,
        )
    return epoch


def _stored_age_entry(doc, address, episode):
    """取該門牌年齡條目（驗形＋episode fencing）→ dict | None。

    episode fencing（AIR-297）：條目 `episode_id` ≠ 現 episode token
    （跨 binding 延遲寫入殘留，含復活的 `stall_reported` flag；
    pre-fencing 舊 schema 條目無此欄同理）→ stderr 註記後視同 None
    （stale 清帳重建——跨 episode flag 不跨界壓制；年齡重 seed＝晚報
    方向）。first_pending_at_us 非正整數＝形漂移：stderr 註記後視同
    None（冷啟動重 seed——年齡不可信即不呈報，寧晚報不誤報）；
    stall_reported 非 True 一律視 False（丟 flag＝可能重複一報，寧重
    不漏方向）。"""
    entry = _age_entry_raw(doc, address)
    if entry is None:
        return None
    if entry.get("episode_id") != episode:
        print(
            f"[{HOOK_TAG}] pending-age 陳期條目（{address} episode "
            f"{entry.get('episode_id')!r} ≠ 現 {episode}）——視為 stale"
            " 清帳重建",
            file=sys.stderr,
        )
        return None
    first = entry.get("first_pending_at_us")
    if (
        not isinstance(first, int)
        or isinstance(first, bool)
        or first <= 0
    ):
        print(
            f"[{HOOK_TAG}] pending-age 條目形漂移（{address}）——視同冷啟動"
            "重 seed",
            file=sys.stderr,
        )
        return None
    return {"first_pending_at_us": first,
            "stall_reported": entry.get("stall_reported") is True,
            "episode_id": episode}


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


def stall_line(address, count):
    """單門牌 stall 呈報行（AIR-294 c）：holderless pending 停留逾門檻
    ——升 human 判讀。count-only 紀律同 advisory_line（整數以外零 face
    細節）；年齡源＝monitor 自持年齡帳（receive status 無時間戳欄），
    呈報措辭如實（觀察窗內停留）。"""
    return (
        f"[{HOOK_TAG}] {address}：pending 停留已逾 "
        f"{PENDING_STALL_REPORT_HOURS} 小時（holderless pending {count} 封"
        "持續未 drain——dutymail receive status 可查；升 human 判讀）"
    )


def monitor_once(addresses, runner, session_id, state_file=None, now_us=None):
    """逐門牌監看（決策表見 module docstring）→ (advisory 行 list,
    baseline updates, age updates, age_rev)。

    binding active=True（3.8.0 bound／3.7.0 live）→ 靜默＋baseline 歸零
    （僅在現值非 0 時寫入）＋年齡帳清（holder 涵蓋——stall 語義限
    holderless）；holderless → pendingCount 值變化才出 advisory＋推進
    baseline（同值防轟炸）；==0 歸零＋年齡帳清（drain——帳窗結束，
    episode token 不變）。AIR-294 stall：holderless pending>0 首見＝
    seed 年齡帳（年齡未知，本輪不呈報）；停留逾 PENDING_STALL_REPORT_
    HOURS 且本帳窗未呈報過＝一行 stall 呈報＋flag 落帳（每帳窗一報）
    。AIR-297 episode fencing＋doc-rev CAS（episode 邊界定義單一源＝
    module docstring fencing 段）：年齡帳條目帶 `episode_id`（＝
    holder status bindingEpoch，於 holderless 分支內驗證取用——形漂
    移交 per-address fail-soft），讀側不匹配＝stale 清帳重建；帳文件
    `rev` 讀時 snapshot 為第四回傳值 `age_rev`，commit 端比對不符＝
    丟棄本輪帳寫入（同 epoch write-after-clear 復活／陳期 seed 蓋新
    seed 封閉）。單門牌 face 失敗＝stderr
    註記續跑其他（per-address 容錯）。updates／age_updates 交呼叫端在
    stdout 寫出成功後 commit（advance-after-emit）；age updates 值為
    None＝清該門牌條目。"""
    if now_us is None:
        now_us = time.time_ns() // 1000
    path = state_file if state_file is not None else monitor_state_path(
        session_id
    )
    doc = load_doc(path)
    age_path = pending_age_state_path(state_file)
    age_doc = load_doc(age_path)
    age_rev = _doc_rev(age_doc, age_path)  # CAS snapshot（AIR-297）
    lines = []
    updates = {}
    age_updates = {}
    for address in addresses:
        try:
            last = _stored_last_pending(doc, address)
            status = core.holder_status(runner, address)
            if core.holder_active(status):
                # 本 session hold（duty-receive state epoch==status.epoch）
                # 或他方 holding——處理面由 holder 承擔：靜默＋baseline 歸零
                # ＋年齡帳清。
                if last is not None and last != 0:
                    updates[address] = {"last_pending": 0}
                if _age_entry_raw(age_doc, address) is not None:
                    age_updates[address] = None
                continue
            episode = _episode_of(status)  # AIR-297 fencing episode token
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
            if _age_entry_raw(age_doc, address) is not None:
                age_updates[address] = None  # drain——帳窗結束（episode
                #  token 不變；寫側復活面由 doc-rev CAS 封閉，見 fencing 段）
            continue
        if pending != last:
            lines.append(advisory_line(address, pending))
            updates[address] = {"last_pending": pending}
        entry = _stored_age_entry(age_doc, address, episode)
        if entry is None:
            # 首見／stale 清帳重建（AIR-297 fencing）＝seed 年齡帳
            # （年齡未知，本輪不呈報）——條目綁現 episode
            age_updates[address] = {
                "first_pending_at_us": now_us, "stall_reported": False,
                "episode_id": episode,
            }
        elif (
            now_us - entry["first_pending_at_us"]
            > PENDING_STALL_REPORT_HOURS * HOURS_US
            and not entry["stall_reported"]
        ):
            lines.append(stall_line(address, pending))
            age_updates[address] = {
                "first_pending_at_us": entry["first_pending_at_us"],
                "stall_reported": True,  # 每帳窗一報
                "episode_id": episode,  # AIR-297 fencing——條目綁 episode
            }
    return lines, updates, age_updates, age_rev


def run(raw, addresses, runner=None, state_file=None, now_us=None):
    """stdin 原文 → (exit_code, stdout payload, commit | None)。

    永不 raise、exit 恆 0（唯一例外＝註冊 args 誤用由 argparse exit 2）。
    addresses＝註冊條目 --address 累積值（可重複；空＝無監看責任，靜默
    且零查詢）。commit＝baseline＋pending-age 兩帳推進 closure（無推進
    需求時 None）——呼叫端在 stdout 寫出成功後才執行（advance-after-emit
    ；寫失敗寧可下次重複提醒；兩帳各自 try/except——一帳失敗不擋另一
    帳；pending-age 帳另過 doc-rev CAS——決策快照 rev 過期＝該帳寫入
    丟棄，AIR-297）。事件名／session_id 經 hook_payload_compat 正規
    化（grok snake 值同款處理；本 hook 僅註冊 zcode 面，正規化為
    防禦性相容）。now_us 可注入（AIR-294 stall 年齡計算——測試面）。"""
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
        lines, updates, age_updates, age_rev = monitor_once(
            addresses, run_fn, session_id, state_file=state_file,
            now_us=now_us,
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
        if updates or age_updates:
            def commit():
                path = state_file if state_file is not None else (
                    monitor_state_path(session_id)
                )
                if updates:
                    try:
                        doc = load_doc(path)
                        doc.setdefault("addresses", {}).update(updates)
                        core.save_state(path, doc)
                    except Exception as exc:
                        print(
                            f"[{HOOK_TAG}] baseline 寫入失敗——下次將重複"
                            f"提醒（{exc!r}）",
                            file=sys.stderr,
                        )
                if age_updates:
                    try:
                        age_path = pending_age_state_path(state_file)
                        age_doc = load_doc(age_path)
                        current_rev = _doc_rev(age_doc, age_path)
                        if current_rev != age_rev:
                            # AIR-297 doc-rev CAS：決策快照過期（他方
                            # drain／seed 已推進帳）——丟棄不覆寫
                            # （stale-read overwrite 防線）。
                            print(
                                f"[{HOOK_TAG}] pending-age 帳已被他方"
                                f"推進（rev {age_rev} → {current_rev}）"
                                "——丟棄本輪帳寫入（doc-rev CAS 防線；"
                                "寧重複不漏報）",
                                file=sys.stderr,
                            )
                        else:
                            age_doc["rev"] = current_rev + 1
                            merged = age_doc.setdefault("addresses", {})
                            for addr, entry in age_updates.items():
                                if entry is None:
                                    merged.pop(addr, None)
                                else:
                                    merged[addr] = entry
                            core.save_state(age_path, age_doc)
                    except Exception as exc:
                        print(
                            f"[{HOOK_TAG}] pending-age 寫入失敗——stall"
                            f" 呈報可能重複（{exc!r}）",
                            file=sys.stderr,
                        )
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
