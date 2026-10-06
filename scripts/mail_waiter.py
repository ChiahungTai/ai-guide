#!/usr/bin/env python3
"""mail_waiter — session 級信件喚醒 watcher（AIR-266）。

一句話：session 內 arm 一個背景 shell worker 對 per-address mailbox 掛哨
（dutymail wait），新事件到＝exit 0 喚醒本 session（尾行單行 JSON——唯一
機判面）；wait-timeout 恆內部消化續輪，絕不外洩；處理面恆歸
`duty_receive process`（唯一 consuming authority 鏈）——本 watcher 是純
觀察軸，絕不碰 holder 綁定面、批次預取面、回執面與對外送信面。

waiter 家族契約（與 bridge_waiter／harness_waiter 同一族——細節單一源＝
skills/mail-watch/SKILL.md「waiter 家族憲章」節）：
- 背景 shell exit＝唯一 push 原語；exit 0＝新事件喚醒（尾行 JSON 帶
  re-arm 命令）；timeout（dutymail class-6）內部 re-arm 不外洩。
- 處置權恆歸 caller（woken LLM）——watcher 只喚醒不處理。
- 喚醒回合 invariant（skill 明文合約）：①跑 `duty_receive process`
  ②成功 re-arm——兩者完成才算喚醒回合結束。

核心不變量（EP invariants 對應）：
- 純觀察軸（invariant 1）：dutymail 呼叫面 allowlist 只有 wait／events；
  events 觀察游標與收信面的 delivery 游標分屬兩軸（invariant 2）——本
  檔只推進自己的 events cursor，絕不代推收信游標。
- typed-failure 四分流（invariant 3）：class-6 wait-timeout 內部續輪；
  class 4/5（storage/fencing）跳輪＋last_round_failed 標記；class 2/3
  （usage/admission）與契約外形狀漂移＝fail-loud exit 2（壞配置不硬跑）。
- 開關語義（invariant 5）：`start`＝寫 desired=running＋generation+=1 並
  印 arm 命令（worker 形，供 skill/LLM 直接複製到背景 shell）；`stop`＝
  落 flag（desired=stopped）——flag 權威：worker 下輪（或寫入 guard）
  遇 flag 即安靜退，尾行回報 stopped。
- generation CAS（invariant 6）：每次 start 推進 generation；worker 每輪
  開頭驗 state.generation 仍＝自己的代，每次 state 寫入前重讀比對
  （read-modify-write guard）——不匹配＝已被新 arm 取代，靜默退（不寫
  state、cursor 不回退）。雙 arm 後舊 worker 自退。
- session 級生命週期（invariant 7）：背景 shell 隨 session/app 存亡——
  start 的承諾僅及本 session 存活期間；新 session 以 status 見 worker
  stale（armed_at 距今 > 輪詢週期×3）時提示 re-arm。
- coalesce（invariant 8）：喚醒時對其餘門牌做 events 非阻塞快照併入同
  一輪彙總＋cursor 推進——一次 exit 報該輪全部新事件，re-arm 從新
  cursor 起，舊信不再觸發；不需額外合併窗口。

State schema（EP 凍結；XDG state 機器級、0600 atomic 寫）：
`$ {XDG_STATE_HOME:-~/.local/state}/ai-guide/mail-waiter/state.json`
{"desired": "running|stopped", "generation": <int>, "armed_at": <unix>,
 "addresses": {"<alias>": {"cursor": "<events token|null=冷啟>",
 "last_event_seq": <int>}}, "last_exit": {"code","reason","at"}|null,
 "last_round_failed": <bool>}
- armed_at＝worker 活性證據（start 初始化、worker 每輪刷新——staleness
  判準消費面）；冷啟（cursor null）＝events 由頭對滾到 head（寧重不漏
  ：歷史事件照計入首輪彙總）；state 損壞視同冷啟（generation 歸零重 arm）。

dutymail face 消費面（凍結語義，實作引用——真相源＝delegate-bridge repo
dutymail CLI）：`wait --address <alias> --cursor <tok> --deadline-ms <ms>`
（cap 600000；成功＝exit 0＋非空頁；deadline 盡＝class-6）與
`events --address <alias> [--cursor <tok>] [--limit <n>]`（keyset paging，
event_seq 遞增；payload 無 body）。成功頁形＝{items:[{eventSeq,kind,
payloadJson,atUs}...], nextCursor}——nextCursor 恒由頁末項編碼，故對滾
到底判準＝空頁（不依賴 rust 端 DEFAULT_LIMIT 鏡像）。binary 解析與 typed
contract（DutymailFaceError code/class/exit_code）經同源 import
scripts/duty_receive.py 複用，不複製邏輯。

測試形態：核心函式吃 injectable runner 與 sleep（fake dutymail 回固定
頁／typed failure；冷啟空頁續輪不等 60s 切片）——見
tests/test_mail_waiter.py（TC-W1..W9＋控制面）。
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from functools import partial

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# binary 解析（DUTYMAIL_BIN → PATH → plugin cache 版本最新）／stdout 契約
# 解析／state 慣例（0600 atomic 寫）單一源＝scripts/duty_receive.py——
# 以檔案路徑載入（自建模組名，不進 sys.modules["duty_receive"]；與
# hooks 的核心載入慣例同式）。
_CORE_SPEC = importlib.util.spec_from_file_location(
    "_mail_waiter_core", os.path.join(_REPO, "scripts", "duty_receive.py")
)
core = importlib.util.module_from_spec(_CORE_SPEC)
_CORE_SPEC.loader.exec_module(core)

TAG = "mail-waiter"
DEFAULT_ADDRESS = "ai-guide-marshal"
STATE_DIRNAME = "mail-waiter"
STATE_FILENAME = "state.json"
# EP S1：wait 內層 deadline 取短切片 60s（cap 600000 內）逐門牌輪轉
# （wait 無原生批次）；冷啟空頁輪末睡同一切片防 busy loop。
POLL_SLICE_MS = 60_000
POLL_SLICE_SECONDS = POLL_SLICE_MS / 1000.0
# events 對滾翻頁大小（到底判準＝空頁，不依賴此值——僅頁大小選擇）
EVENTS_PAGE_LIMIT = 100
# staleness 判準（invariant 7）：armed_at 距今 > 輪詢週期×門牌數×3
STALENESS_ROUNDS = 3
EXIT_OK = 0
EXIT_FAIL_LOUD = 2

WAIT_FACE = "wait"
EVENTS_FACE = "events"
# waiter 純觀察軸（invariant 1）：dutymail 呼叫面 allowlist 只有這兩 face。
OBSERVED_FACES = frozenset({WAIT_FACE, EVENTS_FACE})
# typed-failure 分流（invariant 3）：class-6 內部續輪；class 4/5 跳輪＋
# last_round_failed；class 2/3 與契約外（unknown／shape-drift）fail-loud。
WAIT_TIMEOUT_CLASS = "wait-timeout"
SKIP_ROUND_CLASSES = frozenset({"storage", "fencing"})
FAIL_LOUD_CLASSES = frozenset({"usage", "admission"})


# ── state 路徑與載入（XDG state／ai-guide/mail-waiter；可注入）─────────


def state_base_dir(base_dir=None):
    """state 目錄（base_dir 可注入——測試 tmp state dir，不碰真 store）。"""
    if base_dir is not None:
        return base_dir
    root = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(root, "ai-guide", STATE_DIRNAME)


def state_file_path(base_dir=None):
    return os.path.join(state_base_dir(base_dir), STATE_FILENAME)


def _fresh_state(generation, addresses):
    """fresh state（start 首次／state 缺席）——per-address 冷啟 entry。"""
    return {
        "desired": "running",
        "generation": generation,
        "armed_at": time.time(),
        "addresses": {
            alias: {"cursor": None, "last_event_seq": 0}
            for alias in addresses
        },
        "last_exit": None,
        "last_round_failed": False,
    }


def _entry_cursor(entries, address):
    """該 address 的 events cursor → str | None（無紀錄/形漂移＝冷啟）。"""
    entry = entries.get(address) if isinstance(entries, dict) else None
    if not isinstance(entry, dict):
        return None
    cursor = entry.get("cursor")
    return cursor if isinstance(cursor, str) and cursor else None


# ── 觀察軸 face 包裝（argv 凍結語義；allowlist＝wait/events）───────────


def _wait_face_argv(address, cursor, deadline_ms):
    return [
        WAIT_FACE, "--address", address, "--cursor", cursor,
        "--deadline-ms", str(int(deadline_ms)),
    ]


def _events_face_argv(address, cursor):
    argv = [EVENTS_FACE, "--address", address,
            "--limit", str(EVENTS_PAGE_LIMIT)]
    if cursor is not None:
        argv += ["--cursor", cursor]
    return argv


def _page_items(result):
    """成功頁 items（形漂移 fail-loud raise——寧崩不靜默歸零）。"""
    items = result.get("items")
    if not isinstance(items, list):
        raise core.DutymailFaceError(
            "shape-drift", "unknown",
            f"face result items 非 list：{result!r}", False, 0,
        )
    return items


def _page_next(result):
    tok = result.get("nextCursor")
    return tok if isinstance(tok, str) and tok else None


def _classify_face_error(exc):
    """typed failure →（動作, 種類）：digest＝內部續輪、skip＝跳輪、
    其餘（usage/admission/unknown/shape-drift）fail-loud raise。"""
    if exc.error_class == WAIT_TIMEOUT_CLASS:
        return "digest"
    if exc.error_class in SKIP_ROUND_CLASSES:
        return "skip"
    raise exc


def advance_to_head(runner, address, seen, tok):
    """續翻到 head（事件計數＋cursor 推進）——到底判準＝空頁。

    seen＝已計數事件數、tok＝最後一頁 nextCursor；回 (total, cursor)。
    空頁時 cursor 維持前一頁 token（該 token 之後已無事件）。
    """
    total = seen
    while tok is not None:
        result = core._call(runner, _events_face_argv(address, tok))
        items = _page_items(result)
        total += len(items)
        if not items:
            break
        tok = _page_next(result)
    return total, tok


def watch_address(runner, address, cursor):
    """單門牌掛哨 →（count, cursor, kind）。

    cursor null＝冷啟：events 由頭對滾（寧重不漏——歷史事件照計入），
    空頁＝空 mailbox 續輪。有 cursor＝wait 掛哨（class-6 內部消化回
    (0, cursor)）；wait 成功頁起續翻到 head（一次喚醒報全部新事件）。
    typed-failure 分流見 _classify_face_error；fail-loud 類原樣 raise。
    """
    if cursor is None:
        result = core._call(runner, _events_face_argv(address, None))
        items = _page_items(result)
        if not items:
            return 0, None, "empty"
        count, tok = advance_to_head(
            runner, address, len(items), _page_next(result)
        )
        return count, tok, "mail"
    try:
        result = core._call(
            runner, _wait_face_argv(address, cursor, POLL_SLICE_MS)
        )
    except core.DutymailFaceError as exc:
        action = _classify_face_error(exc)
        if action == "digest":
            return 0, cursor, "timeout"
        return 0, cursor, "skip"
    items = _page_items(result)
    count, tok = advance_to_head(
        runner, address, len(items), _page_next(result)
    )
    return count, tok, "mail"


def snapshot_address(runner, address, cursor):
    """非阻塞快照（喚醒時 coalesce 掃其餘門牌）→ (count, cursor)。

    events 對滾（不 wait——喚醒不延遲）；typed failure 比照分流消化
    （usage/admission 類 raise 交上層 fail-loud）。
    """
    try:
        result = core._call(runner, _events_face_argv(address, cursor))
        items = _page_items(result)
        if not items:
            return 0, cursor
        return advance_to_head(
            runner, address, len(items), _page_next(result)
        )
    except core.DutymailFaceError as exc:
        action = _classify_face_error(exc)
        if action == "digest":
            return 0, cursor
        return 0, cursor  # skip 類：快照面靜默跳過（主輪標記由觸發門牌路徑負責）


# ── generation CAS：guarded read-modify-write（invariant 6）───────────


def _guarded_update(state_file, generation, mutate):
    """寫入前重讀比對 generation——不匹配＝已被新 arm 取代，回 False
    （呼叫端 superseded 靜默退、不寫 state）。state 缺席＝無衝突證據
    （冷啟面）以 fresh schema 為底照寫。"""
    current = core.load_state(state_file)
    if current is None:
        current = _fresh_state(generation, [])
    elif current.get("generation") != generation:
        return False
    mutate(current)
    core.save_state(state_file, current)
    return True


def _record_exit(state_file, generation, code, reason):
    """worker 退出時落 last_exit（generation-guarded；superseded 例外——
    invariant 6 靜默退不寫，guard False 即略過）。"""
    _guarded_update(
        state_file, generation,
        partial(_apply_exit, code=code, reason=reason, now=time.time()),
    )


def _apply_exit(st, code, reason, now):
    st["last_exit"] = {"code": code, "reason": reason, "at": now}


def _apply_advance(st, advanced, now, round_failed):
    """喚醒輪寫入：cursor 推進＋last_event_seq 累加＋心跳＋跳輪標記。"""
    entries = st.setdefault("addresses", {})
    for alias, (count, tok) in advanced.items():
        entry = entries.setdefault(
            alias, {"cursor": None, "last_event_seq": 0}
        )
        entry["cursor"] = tok
        entry["last_event_seq"] = int(entry.get("last_event_seq") or 0) + count
    st["armed_at"] = now
    st["last_round_failed"] = round_failed


def _apply_beat(st, now, round_failed):
    """輪末心跳：armed_at 刷新（活性證據）＋跳輪標記（cursor 不動）。"""
    st["armed_at"] = now
    st["last_round_failed"] = round_failed


def _emit_tail(out, payload):
    """尾行單行 JSON＝唯一機判面（同 bridge_waiter CollectionReceipt
    慣例——stdout 最後一行）。"""
    out.write(json.dumps(payload, ensure_ascii=False,
                         separators=(",", ":")) + "\n")
    out.flush()


# ── worker 主迴圈（背景 shell 主體——start 印的命令即 worker 形）───────


def run_worker(addresses, generation, base_dir=None, runner=None,
               stdout=None, stderr=None, sleep=time.sleep):
    """worker loop（per address 輪轉）→ exit code。

    每輪：load state → desired=stopped／generation 不匹配＝安靜退（尾行
    state=stopped|superseded）→ 逐門牌 watch_address（wait 掛哨 60s 切片）
    → 新事件：coalesce 快照其餘門牌 → guarded 寫（cursor 推進＋心跳）
    → exit 0＋尾行 {"state":"mail","new":[{address,count}...],"rearm":...}
    。整輪 timeout/空頁＝內部消化（冷啟空頁輪末睡切片）；class 4/5＝跳輪
    ＋last_round_failed；class 2/3／形漂移＝exit 2 fail-loud。
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    run = runner if runner is not None else core._default_runner
    state_file = state_file_path(base_dir)

    def _superseded():
        _emit_tail(out, {"state": "superseded", "generation": generation})
        _emit_diag(err, "superseded——新 arm 已接管（generation 前進），"
                        "本 worker 靜默退（不寫 state）")
        return EXIT_OK

    def _stopped():
        _record_exit(state_file, generation, EXIT_OK, "stop flag")
        _emit_tail(out, {"state": "stopped"})
        _emit_diag(err, "stopped——stop flag 權威（desired=stopped），"
                        "worker 安靜退")
        return EXIT_OK

    while True:
        state = core.load_state(state_file)
        if state is None:
            # state 缺席/損壞＝冷啟（generation 歸零重 arm 的 worker 面：
            # 視 argv generation 為當代——寧重不漏對滾，寫入仍走 guard）
            state = _fresh_state(generation, addresses)
        else:
            if state.get("desired") == "stopped":
                return _stopped()
            if state.get("generation") != generation:
                return _superseded()
        entries = state.get("addresses")
        if not isinstance(entries, dict):
            entries = {}

        round_failed = False
        saw_empty_cold_start = False
        new_events = []
        advanced = {}
        try:
            for index, address in enumerate(addresses):
                cursor = _entry_cursor(entries, address)
                count, tok, kind = watch_address(run, address, cursor)
                if kind == "mail":
                    new_events.append({"address": address, "count": count})
                    advanced[address] = (count, tok)
                    # coalesce（invariant 8）：其餘門牌非阻塞快照——
                    # 一次 exit 報該輪全部新事件
                    for other in addresses[index + 1:]:
                        o_cursor = _entry_cursor(entries, other)
                        o_count, o_tok = snapshot_address(run, other, o_cursor)
                        if o_count:
                            new_events.append(
                                {"address": other, "count": o_count}
                            )
                            advanced[other] = (o_count, o_tok)
                    break
                if kind == "skip":
                    round_failed = True
                if kind == "empty":
                    saw_empty_cold_start = True
        except core.DutymailFaceError as exc:
            # fail-loud 面（usage/admission/形漂移）——壞配置不硬跑
            _record_exit(state_file, generation, EXIT_FAIL_LOUD, str(exc))
            _emit_diag(err, f"fail-loud（{exc.error_class}）：{exc}")
            _emit_tail(out, {"state": "fail-loud",
                             "reason": f"{exc.error_class}: {exc}"})
            return EXIT_FAIL_LOUD

        if new_events:
            if not _guarded_update(
                state_file, generation,
                partial(_apply_advance, advanced=advanced, now=time.time(),
                        round_failed=round_failed),
            ):
                return _superseded()
            _record_exit(state_file, generation, EXIT_OK, "mail")
            _emit_tail(out, {
                "state": "mail",
                "new": new_events,
                "rearm": arm_command(addresses, generation, base_dir),
            })
            return EXIT_OK

        # 整輪無新事件：輪末心跳（armed_at 刷新＝活性證據；跳輪標記）
        if not _guarded_update(
            state_file, generation,
            partial(_apply_beat, now=time.time(), round_failed=round_failed),
        ):
            return _superseded()
        if saw_empty_cold_start:
            # 冷啟空 mailbox：wait 面未自帶等待（無 cursor 可掛哨）——
            # 睡一切片防 busy loop（timeout 輪不吃此睡：wait 已等 60s）
            sleep(POLL_SLICE_SECONDS)


def _emit_diag(err, text):
    err.write(f"[{TAG}] {text}\n")
    err.flush()


# ── start／stop／status（subcommand 實作；AC2 五欄）────────────────────


def arm_command(addresses, generation, base_dir=None):
    """start 印出的 arm 命令（worker 形，背景 shell 用——cwd＝repo）。"""
    parts = ["uv", "run", "python", "scripts/mail_waiter.py", "worker"]
    for address in addresses:
        parts += ["--address", address]
    parts += ["--generation", str(generation),
              "--state-dir", state_base_dir(base_dir)]
    return " ".join(parts)


def cmd_start(addresses, base_dir=None):
    """arm：desired=running＋generation+=1 → 印 arm 命令（可直接複製）。

    既有 per-address cursor 保留（coalesce 延續——舊信不再觸發）；state
    缺席/損壞＝generation 歸零重 arm（1 起）。
    """
    state_file = state_file_path(base_dir)
    existing = core.load_state(state_file)
    generation = 1 if existing is None else int(
        existing.get("generation") or 0
    ) + 1
    state = _fresh_state(generation, addresses)
    if existing is not None:
        kept = existing.get("addresses")
        if isinstance(kept, dict):
            state["addresses"] = kept
        for address in addresses:
            state["addresses"].setdefault(
                address, {"cursor": None, "last_event_seq": 0}
            )
        last_exit = existing.get("last_exit")
        if last_exit is not None:
            state["last_exit"] = last_exit
    core.save_state(state_file, state)
    print(f"[{TAG}] armed：generation {generation}、"
          f"addresses {','.join(addresses)}、state {state_file}")
    print(arm_command(addresses, generation, base_dir))
    return EXIT_OK


def cmd_stop(base_dir=None):
    """落 flag（desired=stopped；generation 不動）——worker 下輪自退，
    尾行回報 stopped。"""
    state_file = state_file_path(base_dir)
    state = core.load_state(state_file)
    if state is None:
        state = _fresh_state(0, [])
        state["generation"] = 0
    state["desired"] = "stopped"
    core.save_state(state_file, state)
    print(f"[{TAG}] stop flag 落下（desired=stopped；state {state_file}）"
          "——worker 下輪自退，尾行回報 stopped")
    return EXIT_OK


def _staleness_mark(state, now=None):
    """armed_at 距今 vs 輪詢週期×門牌數×3 →（mark, age_seconds）。"""
    now = now if now is not None else time.time()
    entries = state.get("addresses")
    rounds = max(1, len(entries)) if isinstance(entries, dict) else 1
    threshold = POLL_SLICE_SECONDS * rounds * STALENESS_ROUNDS
    armed = state.get("armed_at")
    if not isinstance(armed, (int, float)) or isinstance(armed, bool):
        return "unknown（state 缺 armed_at）", None
    age = max(0.0, now - armed)
    if state.get("desired") == "stopped":
        return "n/a（desired=stopped——worker 不在場是預期）", age
    if age > threshold:
        return f"stale——建議 re-arm（threshold {threshold:.0f}s）", age
    return f"fresh（threshold {threshold:.0f}s）", age


def cmd_status(base_dir=None):
    """唯讀五欄報告：desired／generation／armed_at（＋staleness）／
    per-address cursor（＋last_event_seq）／last_exit——可隨時跑、零寫入。"""
    state_file = state_file_path(base_dir)
    state = core.load_state(state_file)
    if state is None:
        print(f"[{TAG}] state 缺席（冷啟；{state_file}）")
        print(f"[{TAG}] desired=unknown（未 arm 過）")
        print(f"[{TAG}] generation=0")
        print(f"[{TAG}] armed_at=——（無活性證據；staleness unknown）")
        return EXIT_OK
    mark, age = _staleness_mark(state)
    age_txt = "—" if age is None else f"{age:.0f}s 前"
    print(f"[{TAG}] desired={state.get('desired', 'unknown')}")
    print(f"[{TAG}] generation={state.get('generation', 'unknown')}")
    print(f"[{TAG}] armed_at={state.get('armed_at')}（{age_txt}；{mark}）")
    entries = state.get("addresses")
    entries = entries if isinstance(entries, dict) else {}
    if entries:
        for alias, entry in sorted(entries.items()):
            cursor = entry.get("cursor") if isinstance(entry, dict) else None
            seq = entry.get("last_event_seq") if isinstance(entry, dict) \
                else None
            cursor_txt = cursor if isinstance(cursor, str) and cursor \
                else "<null=冷啟>"
            print(f"[{TAG}] address {alias}：cursor={cursor_txt}"
                  f"（last_event_seq={seq}）")
    else:
        print(f"[{TAG}] address（無紀錄——預設門牌 {DEFAULT_ADDRESS}）")
    last_exit = state.get("last_exit")
    if last_exit:
        print(f"[{TAG}] last_exit={last_exit}")
    return EXIT_OK


# ── CLI 面（模組＋subcommand：start／stop／status＋內部 worker）────────


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "mail_waiter：session 級信件喚醒 watcher（AIR-266——dutymail "
            "wait 挂哨＋尾行 JSON 喚醒；generation CAS；timeout 內部消化）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser(
        "start",
        help="arm：generation+=1＋印 worker 背景命令（可直接複製）",
    )
    start.add_argument(
        "--address", action="append", metavar="ALIAS",
        help=f"挂哨門牌（可重複；預設 {DEFAULT_ADDRESS}）",
    )
    start.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="state 目錄覆寫（預設 XDG state／~/.local/state；測試注入）",
    )
    stop = sub.add_parser(
        "stop", help="落 flag（desired=stopped）——worker 下輪自退"
    )
    stop.add_argument(
        "--state-dir", default=None, metavar="DIR", help="state 目錄覆寫"
    )
    status = sub.add_parser(
        "status", help="唯讀五欄報告（desired/generation/armed_at/cursor/"
        "staleness）"
    )
    status.add_argument(
        "--state-dir", default=None, metavar="DIR", help="state 目錄覆寫"
    )
    worker = sub.add_parser(
        "worker", help=argparse.SUPPRESS  # start 印的背景 shell 主體
    )
    worker.add_argument(
        "--address", action="append", metavar="ALIAS",
        help="挂哨門牌（可重複）",
    )
    worker.add_argument(
        "--generation", type=int, required=True, metavar="N",
        help="本 worker 的 generation（start 印出；CAS 驗代用）",
    )
    worker.add_argument(
        "--state-dir", default=None, metavar="DIR", help="state 目錄覆寫"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "start":
        return cmd_start(args.address or [DEFAULT_ADDRESS], args.state_dir)
    if args.command == "stop":
        return cmd_stop(args.state_dir)
    if args.command == "status":
        return cmd_status(args.state_dir)
    return run_worker(
        args.address or [DEFAULT_ADDRESS], args.generation, args.state_dir
    )


if __name__ == "__main__":
    raise SystemExit(main())
