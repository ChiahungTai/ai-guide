"""mail_waiter 測試（AIR-266 S4＋AIR-268 kind-filter 修復）。

EP＝ai-analysis/_tasks/10-07-mail-waiter/ep.md。涵蓋：
- 喚醒契約（W1）：wait exit 0（中斷器觸發）→ kinded events 計數 → 尾行
  JSON state=mail＋new 清單（門牌×事件數）＋rearm 命令；雙 cursor 各自
  推進（unkinded＝wait 軸取 wait 頁 nextCursor；kinded＝計數軸取對滾終點）。
- 處理波吞噬（swallow）：wait 成功頁（任意事件種類）但 kinded 計數 0
  （bound/prepared/acked 回音）＝內部消化——推進雙 cursor 續輪、不 exit、
  不計新事件；後續真信到照常喚醒（不丟事件）。
- timeout 消化（W2）：連續 class-6 ×N 內部續輪（不 exit），事件到才 exit 0。
- stop flag（W3）：desired=stopped 下 worker 輪＝安靜退、尾行 state=stopped、
  零 face 呼叫。
- fail-loud（W4）：class-2 usage → exit 2＋尾行 state=fail-loud。
- 跳輪（W5）：class-4 storage 一輪＝跳輪＋last_round_failed；恢復輪照常
  喚醒＋標記清除。
- generation CAS（W6）：worker A 活著再 start（gen+1）＝A 下輪見 gen 不匹配
  安靜退（superseded、不寫 state）；寫入邊 guard＝stale worker 不覆蓋新
  generation 的 cursor（不回退——雙欄同驗）。
- 冷啟（W7）：state 缺席／損壞＝雙軸初始化（plain events 對滾取 unkinded
  head token＋kinded 全量對滾計數）＋首輪彙總 exit（寧重不漏）；空 mailbox
  取不到 token（空頁不發 cursor）＝睡切片續輪。
- 唯讀結構證（W8）：全生命週期 dutymail 呼叫面 allowlist＝wait/events
  （零 holder 綁定／批次預取／回執／送信面——invariant 1 紅線）；coalesce
  快照只推 kinded 軸（unkinded cursor 不動——計數恆由 kinded 軸決定）。
- stop 權威（W9）：desired=stopped 落下後 re-arm＝新 worker 首輪即退 stopped。
- 架構釘（K，AIR-268）：wait argv 無 --kind（face 無此旗標）；計數面恆
  events --kind accepted（kinded）；unkinded 軸恆無 --kind；state 雙欄
  （cursor/accepted_cursor）在場——kinded 與 unkinded cursor 不可互混。
- 跨形態舊 state：entry 缺 accepted_cursor 欄位（單 cursor 版遺留——
  kind-ness 無從判定）視同冷啟重掃，不把舊值餵 wait（防 class-2
  cursor-scope-mismatch fail-loud 迴圈 wedge）。

測試形態：injectable runner（fake dutymail 回固定 JSON／typed failure）
＋tmp state dir 注入＋sleep 注入（冷啟空頁續輪不等 60s 切片）——零真 store
往返、禁碰真 ~/.local/state。
"""

import io
import json
import os
import stat
import threading
import time

from conftest import load_module

mod = load_module("scripts/mail_waiter.py")

ADDR = "ai-guide-marshal"


# ── fake dutymail runner／state helpers ────────────────────────────────


def _item(seq, kind="mail.accepted"):
    return {"eventSeq": seq, "kind": kind, "payloadJson": "{}",
            "atUs": seq * 1000}


def _ok_page(seqs, next_cursor=None, kind="mail.accepted"):
    """events/wait 成功 stdout（凍結形：items＋nextCursor；無 cursor=None）。"""
    return json.dumps({
        "schemaVersion": 1, "ok": True,
        "result": {"items": [_item(s, kind) for s in seqs],
                   "nextCursor": next_cursor},
    })


def _face_err(code, error_class, exit_code, message="typed failure"):
    return mod.core.DutymailFaceError(
        code=code, error_class=error_class, message=message,
        retryable=error_class == "wait-timeout", exit_code=exit_code,
    )


class ScriptRunner:
    """injectable runner：steps 依呼叫序（JSON str 或 Exception 或
    (answer, side_effect)）；超出步數＝AssertionError（釘呼叫面）。"""

    def __init__(self, steps):
        self.steps = list(steps)
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        if len(self.calls) > len(self.steps):
            raise AssertionError("unexpected call: " + repr(list(argv)))
        step = self.steps[len(self.calls) - 1]
        side = None
        if isinstance(step, tuple):
            step, side = step
        if side is not None:
            side()
        if isinstance(step, Exception):
            raise step
        return step


def _state_file(base):
    return mod.state_file_path(str(base))


def _read_state(base):
    with open(_state_file(base), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _seed_state(base, desired="running", generation=1, cursors=None,
                armed_at=None, last_exit=None, last_round_failed=False):
    """seed state——cursors 值＝(unkinded, kinded) 二元組（雙 cursor 軸）。"""
    os.makedirs(str(base), exist_ok=True)
    doc = {
        "desired": desired,
        "generation": generation,
        "armed_at": armed_at if armed_at is not None else time.time(),
        "addresses": {
            alias: {"cursor": unkinded, "accepted_cursor": kinded,
                    "last_event_seq": 0}
            for alias, (unkinded, kinded) in (cursors or {}).items()
        },
        "last_exit": last_exit,
        "last_round_failed": last_round_failed,
    }
    with open(_state_file(base), "w", encoding="utf-8") as fh:
        json.dump(doc, fh)


def _run(base, runner, addresses=(ADDR,), generation=1):
    """in-process worker 驅動 → (exit_code, 尾行 dict, stdout)。"""
    out = io.StringIO()
    err = io.StringIO()
    rc = mod.run_worker(
        list(addresses), generation, base_dir=str(base), runner=runner,
        stdout=out, stderr=err, sleep=lambda _s: None,
    )
    lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
    assert lines, "worker 零 stdout 輸出——尾行 JSON 缺席"
    return rc, json.loads(lines[-1]), out.getvalue()


def _wait_face_call(alias=ADDR, cursor="u0", deadline_ms=60000):
    """wait argv（AIR-268）：無 --kind——wait face 無此旗標（CLI 凍結）。"""
    return ["wait", "--address", alias, "--cursor", cursor,
            "--deadline-ms", str(deadline_ms)]


def _kinded_events_face_call(alias=ADDR, cursor=None):
    """kinded 計數軸 argv：events --kind accepted（cursor 綁 kind）。"""
    argv = ["events", "--address", alias, "--kind", "accepted",
            "--limit", str(mod.EVENTS_PAGE_LIMIT)]
    if cursor is not None:
        argv += ["--cursor", cursor]
    return argv


def _plain_events_face_call(alias=ADDR, cursor=None):
    """unkinded 軸 argv（冷啟 head 定位）：events 無 --kind。"""
    argv = ["events", "--address", alias,
            "--limit", str(mod.EVENTS_PAGE_LIMIT)]
    if cursor is not None:
        argv += ["--cursor", cursor]
    return argv


def _cursor_of(call):
    """argv 中 --cursor 的值（釘 cursor 用）。"""
    return call[call.index("--cursor") + 1]


# ── K：雙軸架構釘（AIR-268——wait 中斷器＋events 真值）─────────────────


class TestKindFilterArchitecture:
    def test_k_wait_argv_has_no_kind_flag(self):
        """wait argv 恆無 --kind——wait face 無此旗標（dutymail CLI 凍結；
        帶了＝class-2 usage error），wait＝純中斷器（unkinded cursor 軸）。"""
        w = mod._wait_face_argv(ADDR, "u0", 60000)
        assert w == _wait_face_call()
        assert "--kind" not in w

    def test_k_events_dual_axis_kind_discipline(self):
        """events 雙軸 kind 紀律：計數軸恆 --kind accepted（kinded cursor
        綁 filter）；unkinded 軸恆無 --kind（餵 wait 用）。"""
        for cursor in (None, "k9"):
            kinded = mod._events_face_argv(ADDR, cursor, kind="accepted")
            assert "--kind" in kinded
            assert kinded[kinded.index("--kind") + 1] == "accepted"
            assert kinded == _kinded_events_face_call(cursor=cursor)
        for cursor in (None, "u9"):
            plain = mod._events_face_argv(ADDR, cursor)
            assert "--kind" not in plain
            assert plain == _plain_events_face_call(cursor=cursor)

    def test_k_state_schema_dual_cursor_fields(self):
        """state 結構面：per-address entry 恆雙 cursor 欄＋last_event_seq
        （kinded/unkinded 不可互混——兩欄在場是結構保證）。"""
        fresh = mod._fresh_state(1, [ADDR])
        assert fresh["addresses"][ADDR] == {
            "cursor": None, "accepted_cursor": None, "last_event_seq": 0,
        }

    def test_k_legacy_single_cursor_entry_normalized_to_cold_start(
        self, tmp_path,
    ):
        """跨形態舊 state（entry 缺 accepted_cursor——單 cursor 版遺留，
        kind-ness 無從判定）＝視同冷啟：首呼 plain events（無 cursor），
        舊 cursor 不餵 wait（防 class-2 cursor-scope-mismatch fail-loud
        迴圈 wedge）；重掃後雙軸落地新值（寧重不漏）。"""
        base = tmp_path / "st"
        os.makedirs(str(base), exist_ok=True)
        with open(_state_file(base), "w", encoding="utf-8") as fh:
            json.dump({
                "desired": "running", "generation": 1,
                "armed_at": time.time(),
                "addresses": {ADDR: {"cursor": "legacy-tok",
                                     "last_event_seq": 7}},
                "last_exit": None, "last_round_failed": False,
            }, fh)
        runner = ScriptRunner([
            _ok_page([1], "u1"),        # 1. plain events（無 cursor）冷啟
            _ok_page([], None),         # 2. plain 續翻到底
            _ok_page([1], "k1"),        # 3. kinded 全量對滾（無 cursor）
            _ok_page([], None),         # 4. kinded 到底
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert runner.calls[0] == _plain_events_face_call(cursor=None)
        for call in runner.calls:  # 舊 token 從未進任何 face
            if "--cursor" in call:
                assert _cursor_of(call) != "legacy-tok"
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "u1"
        assert entry["accepted_cursor"] == "k1"
        assert entry["last_event_seq"] == 7 + 1  # 計數欄延續累加


# ── W1/W2：喚醒契約＋timeout 消化 ──────────────────────────────────────


class TestWakeupContract:
    def test_w1_wait_event_wakes_with_tail_json(self, tmp_path):
        """wait exit 0（中斷器觸發——頁含回音＋新信）→ kinded 計數（1 筆
        accepted→續翻空頁到底）→ exit 0；尾行 state=mail＋new=[{address,
        count=1}]（count＝kinded 真值，wait 頁 items 不計數）＋rearm；雙
        cursor 各自推進（unkinded＝wait 頁 nextCursor；kinded＝對滾終點）。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _ok_page([11, 12], "u1", kind="mail.bound"),  # wait：中斷頁
            _ok_page([13], "k1"),                         # kinded --cursor k0
            _ok_page([], None),                           # kinded 到底
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]
        assert "scripts/mail_waiter.py worker" in tail["rearm"]
        assert "--generation 1" in tail["rearm"]
        assert runner.calls[0] == _wait_face_call()
        assert runner.calls[1] == _kinded_events_face_call(cursor="k0")
        assert runner.calls[2] == _kinded_events_face_call(cursor="k1")
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "u1"  # unkinded 軸推進至 wait 頁尾
        assert entry["accepted_cursor"] == "k1"  # kinded 軸推進至 head
        assert entry["last_event_seq"] == 1

    def test_w1_rearm_command_directly_copyable(self, tmp_path):
        """rearm 命令含 worker 形完整參數（--address/--generation/--state-dir）
        ——skill/LLM 可直接複製到背景 shell。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _ok_page([7], "u1"),
            _ok_page([7], "k1"),
            _ok_page([], None),
        ])
        _rc, tail, _out = _run(base, runner)
        assert tail["rearm"].startswith("uv run python scripts/mail_waiter.py")
        assert f"--address {ADDR}" in tail["rearm"]
        assert f"--state-dir {base}" in tail["rearm"]

    def test_w1_next_round_wait_uses_advanced_unkinded_cursor(
        self, tmp_path,
    ):
        """雙 cursor 語義（下輪 wait 用 unkinded——兩軸不互混）：喚醒
        exit 後 re-arm（第二次 worker run），其 wait argv 的 cursor＝
        unkinded 新值（非 kinded 終點）。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        timeout = _face_err("wait-timeout", "wait-timeout", 6)
        runner = ScriptRunner([
            _ok_page([5], "u1"),   # 1. wait（u0）中斷頁
            _ok_page([5], "k1"),   # 2. kinded（k0）計數
            _ok_page([], None),    # 3. kinded 到底 → mail exit
            timeout,               # 4. re-arm 輪 wait（u1）→timeout 續輪
        ])
        rc1 = mod.run_worker(
            [ADDR], 1, base_dir=str(base), runner=runner,
            stdout=io.StringIO(), stderr=io.StringIO(),
            sleep=lambda _s: None,
        )
        assert rc1 == 0  # 喚醒 exit（單次生命週期——下輪靠 re-arm）
        out = io.StringIO()
        try:
            mod.run_worker(  # re-arm：同 generation 新 worker
                [ADDR], 1, base_dir=str(base), runner=runner,
                stdout=out, stderr=io.StringIO(),
                sleep=lambda _s: None,
            )
        except AssertionError:
            pass  # timeout 輪續輪後再 wait 超出步數＝仍在掛哨
        assert len(runner.calls) == 5  # 第 5 次（步數外）已入冊
        for call in runner.calls[3:]:
            assert call[0] == "wait"
            assert _cursor_of(call) == "u1"  # unkinded 新值——非 k1
        assert out.getvalue() == ""  # timeout 內部消化零尾行

    def test_w2_consecutive_timeouts_digested_then_wake(self, tmp_path):
        """連續 class-6 ×3 內部消化（不 exit）——第 4 輪事件到才 exit 0。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        timeout = _face_err("wait-timeout", "wait-timeout", 6)
        runner = ScriptRunner([
            timeout, timeout, timeout,
            _ok_page([21], "u1"),  # 第 4 輪 wait：新事件
            _ok_page([21], "k1"),
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]
        wait_calls = [c for c in runner.calls if c[0] == "wait"]
        assert len(wait_calls) == 4  # 3 次 timeout 全在內部續輪消化


# ── swallow：處理波吞噬（AIR-268——kinded 計數 0 內部消化）─────────────


class TestSwallowWave:
    def test_swallow_processing_wave_digested_no_exit(self, tmp_path):
        """wait 成功頁全非 accepted（bound/prepared 回音）→ kinded 計數 0
        ＝純處理波：推進雙 cursor 續輪、不 exit（零尾行外洩）、不計新事件。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        timeout = _face_err("wait-timeout", "wait-timeout", 6)
        runner = ScriptRunner([
            _ok_page([11, 12], "u1", kind="mail.prepared"),  # 1. wait 回音頁
            _ok_page([], None),                              # 2. kinded 空
            timeout,                                         # 3. 下輪 wait
        ])
        out = io.StringIO()
        err = io.StringIO()
        try:
            mod.run_worker(
                [ADDR], 1, base_dir=str(base), runner=runner,
                stdout=out, stderr=err, sleep=lambda _s: None,
            )
        except AssertionError:
            pass  # 步數耗盡＝仍在續輪（swallow 未 exit）
        assert out.getvalue() == ""  # 零尾行外洩——喚醒仍是唯一 exit 面
        assert runner.calls[0] == _wait_face_call()
        assert runner.calls[1] == _kinded_events_face_call(cursor="k0")
        assert runner.calls[2] == _wait_face_call(cursor="u1")  # 推進後
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "u1"  # swallow 仍推進 unkinded（防重觸發）
        assert entry["accepted_cursor"] == "k0"  # kinded 無 accepted 不動
        assert entry["last_event_seq"] == 0  # 不計新事件
        st = _read_state(base)
        assert st["last_exit"] is None  # 未 exit 過

    def test_swallow_then_real_mail_wakes_no_event_lost(self, tmp_path):
        """swallow 後真信到：wait 從推進後 unkinded 掛哨、kinded 從原位
        計數——處理波吞噬不丟事件，新 accepted 照常喚醒。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _ok_page([11], "u1", kind="mail.bound"),  # 1. wait 回音頁
            _ok_page([], None),                       # 2. kinded 空→swallow
            _ok_page([21], "u2"),                     # 3. wait（u1）新信
            _ok_page([21], "k1"),                     # 4. kinded（k0）計數
            _ok_page([], None),                       # 5. kinded 到底
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "u2"
        assert entry["accepted_cursor"] == "k1"
        assert entry["last_event_seq"] == 1


# ── W3/W9：stop flag 權威 ──────────────────────────────────────────────


class TestStopFlag:
    def test_w3_stopped_flag_quiet_exit(self, tmp_path):
        """desired=stopped 下 worker 輪＝安靜退（exit 0＋尾行 state=stopped）
        ＋零 face 呼叫＋last_exit 落檔。"""
        base = tmp_path / "st"
        _seed_state(base, desired="stopped",
                    cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "stopped"
        assert runner.calls == []
        st = _read_state(base)
        assert st["desired"] == "stopped"
        assert st["last_exit"]["code"] == 0

    def test_w9_stop_authority_new_worker_exits_first_round(self, tmp_path):
        """desired=stopped 落下後 re-arm＝新 worker 首輪即退 stopped
        （flag 權威：不吃 generation/argv 面）。"""
        base = tmp_path / "st"
        _seed_state(base, desired="running", cursors={ADDR: ("u0", "k0")})
        assert mod.cmd_stop(str(base)) == mod.EXIT_OK  # flag 落下
        runner = ScriptRunner([])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "stopped"
        assert runner.calls == []  # flag 權威——未碰任何 face


# ── W4/W5：typed-failure 分流 ──────────────────────────────────────────


class TestFailureRouting:
    def test_w4_usage_fail_loud_exit2(self, tmp_path):
        """class-2 usage → exit 2＋尾行 state=fail-loud＋last_exit 記錄。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _face_err("unknown-flag", "usage", 2, "bad flag"),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == mod.EXIT_FAIL_LOUD
        assert tail["state"] == "fail-loud"
        assert "usage" in tail["reason"]
        st = _read_state(base)
        assert st["last_exit"]["code"] == mod.EXIT_FAIL_LOUD

    def test_w5_storage_skip_round_then_recover(self, tmp_path):
        """class-4 storage 一輪＝跳輪＋last_round_failed=True＋不崩；恢復輪
        照常喚醒＋標記清除。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        storage = _face_err("store-incompatible", "storage", 4)
        mid = {}

        def _capture_failed_flag():
            mid["last_round_failed"] = _read_state(base)["last_round_failed"]

        runner = ScriptRunner([
            storage,                                  # 第 1 輪 wait：跳輪
            (_ok_page([31], "u1"), _capture_failed_flag),  # 第 2 輪 wait 前
            _ok_page([31], "k1"),                     # kinded 計數
            _ok_page([], None),                       # kinded 到底
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert mid["last_round_failed"] is True  # 跳輪輪末標記
        entry = _read_state(base)["addresses"][ADDR]
        assert _read_state(base)["last_round_failed"] is False  # 恢復輪清除
        assert entry["cursor"] == "u1"
        assert entry["accepted_cursor"] == "k1"


# ── W6：generation CAS（雙 arm 舊退新續、cursor 不回退）───────────────


class TestGenerationCas:
    def test_w6_superseded_quiet_exit_next_round(self, tmp_path):
        """worker A（gen 1）活著再 start（gen+1）＝A 下輪見 gen 不匹配安靜退
        （尾行 superseded、exit 0、不寫 state——last_exit 不落、cursor 不動）。"""
        base = tmp_path / "st"
        _seed_state(base, generation=1, cursors={ADDR: ("u0", "k0")})
        timeout = _face_err("wait-timeout", "wait-timeout", 6)

        def _second_arm():
            # 第 2 輪 wait 進行中——新 arm 落地（generation 1→2）
            assert mod.cmd_start([ADDR], str(base)) == mod.EXIT_OK

        runner = ScriptRunner([timeout, (timeout, _second_arm)])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "superseded"
        st = _read_state(base)
        assert st["generation"] == 2  # A 未覆蓋新 arm 的 generation
        entry = st["addresses"][ADDR]
        assert entry["cursor"] == "u0"  # 雙 cursor 不動
        assert entry["accepted_cursor"] == "k0"
        assert st["last_exit"] is None  # superseded 不寫 state（invariant 6）

    def test_w6_stale_worker_never_overwrites_cursor(self, tmp_path):
        """寫入邊 guard：A 讀過 state（gen 1）後新 arm 已推進 cursor——A 的
        彙總寫入被 guard 攔下，新 cursor 不回退（雙欄同驗）。"""
        base = tmp_path / "st"
        _seed_state(base, generation=1, cursors={ADDR: ("u0", "k0")})

        def _new_worker_advances():
            # 模擬新代 worker（gen 2）已把雙 cursor 推進
            _seed_state(base, generation=2,
                        cursors={ADDR: ("newu", "newk")})

        runner = ScriptRunner([
            (_ok_page([41], "uA"), _new_worker_advances),  # wait＋新 arm 落地
            _ok_page([41], "kA"),  # kinded 計數（guard 在寫入邊才攔）
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "superseded"
        entry = _read_state(base)["addresses"][ADDR]
        assert _read_state(base)["generation"] == 2
        assert entry["cursor"] == "newu"  # 不回退
        assert entry["accepted_cursor"] == "newk"


# ── W7：冷啟（state 缺席／損壞——雙軸初始化）──────────────────────────


class TestColdStart:
    def test_w7_absent_state_dual_axis_scroll_wake(self, tmp_path):
        """state 缺席＝冷啟雙軸初始化：plain events（無 --kind）由頭對滾
        取 unkinded head token＋kinded 全量對滾計數→首輪彙總 exit（寧重
        不漏——new 只計 accepted 真值）。"""
        base = tmp_path / "st"
        runner = ScriptRunner([
            _ok_page([1, 2], "u1", kind="mail.bound"),  # plain 首頁
            _ok_page([3], "u2"),                        # plain 續翻
            _ok_page([], None),                         # plain 到底
            _ok_page([2], "k1"),                        # kinded 首頁（無 cursor）
            _ok_page([], None),                         # kinded 到底
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]  # kinded 真值
        assert runner.calls[0] == _plain_events_face_call(cursor=None)
        assert runner.calls[3] == _kinded_events_face_call(cursor=None)
        entry = _read_state(base)["addresses"][ADDR]
        assert _read_state(base)["generation"] == 1  # worker 落地自己的代
        assert entry["cursor"] == "u2"  # unkinded 軸＝head token
        assert entry["accepted_cursor"] == "k1"  # kinded 軸＝對滾終點

    def test_w7_zero_accepted_initializes_unkinded_to_wait_loop(
        self, tmp_path,
    ):
        """冷啟有事件但零 accepted：unkinded 軸照初始化（head token 落
        state）、kinded 計數 0＝不喚醒——下輪直接以 wait 掛哨（非重掃）。"""
        base = tmp_path / "st"
        timeout = _face_err("wait-timeout", "wait-timeout", 6)
        runner = ScriptRunner([
            _ok_page([1, 2, 3], "u1", kind="mail.bound"),  # plain 首頁
            _ok_page([], None),                            # plain 到底
            _ok_page([], None),                            # kinded 空（計 0）
            timeout,                                       # 下輪 wait（u1）
        ])
        out = io.StringIO()
        err = io.StringIO()
        try:
            mod.run_worker(
                [ADDR], 1, base_dir=str(base), runner=runner,
                stdout=out, stderr=err, sleep=lambda _s: None,
            )
        except AssertionError:
            pass  # 步數耗盡＝仍在續輪（零 accepted 不 exit）
        assert out.getvalue() == ""
        wait_calls = [c for c in runner.calls if c[0] == "wait"]
        assert len(wait_calls) == 2  # 冷啟後即進 wait 迴圈（unkinded 已初始化）
        assert _cursor_of(wait_calls[0]) == "u1"
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "u1"
        assert entry["accepted_cursor"] is None  # 零 accepted——kinded 無 token
        assert entry["last_event_seq"] == 0

    def test_w7_corrupt_state_treated_as_cold_start(self, tmp_path):
        """state 損壞（壞 JSON）視同冷啟——雙軸對滾喚醒（寧重不漏）。"""
        base = tmp_path / "st"
        os.makedirs(str(base), exist_ok=True)
        with open(_state_file(base), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        runner = ScriptRunner([
            _ok_page([5], "u1"),
            _ok_page([], None),
            _ok_page([5], "k1"),
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]

    def test_cold_start_empty_mailbox_digested(self, tmp_path):
        """冷啟空 mailbox（plain events 空頁——空頁不發 cursor，unkinded
        無從建立）＝續輪內部消化（不 exit）；冷啟輪末 sleep 切片防 busy
        loop（注入 no-op）。"""
        base = tmp_path / "st"
        runner = ScriptRunner([
            _ok_page([], None),  # 冷啟首頁空
            _ok_page([], None),  # 第 2 輪冷啟仍空
        ])
        out = io.StringIO()
        slept = []
        # 步數釘死 2：第 3 輪冷啟再查 events 會超出步數炸 AssertionError
        # ＝證明空頁被內部消化續輪（未 exit）。
        try:
            mod.run_worker(
                [ADDR], 1, base_dir=str(base), runner=runner,
                stdout=out, stderr=io.StringIO(),
                sleep=lambda s: slept.append(s),
            )
        except AssertionError:
            pass  # 步數耗盡＝仍在續輪——內部消化成立
        # 兩輪空頁消化後第 3 輪仍在續（runner 先記 argv 再炸——第 3 次已入冊）
        assert len(runner.calls) == 3
        assert all(c[0] == "events" for c in runner.calls)  # 冷啟不觸 wait
        assert all("--kind" not in c for c in runner.calls)  # 首呼＝plain 軸
        assert slept == [mod.POLL_SLICE_SECONDS] * 2  # 空頁輪末睡切片


# ── W8：唯讀結構證（allowlist——invariant 1 紅線）─────────────────────


class TestReadOnlyFace:
    def test_w8_full_lifecycle_only_wait_events_faces(self, tmp_path):
        """全生命週期（冷啟雙軸對滾輪→wait 喚醒輪）dutymail 呼叫面
        allowlist：只准 wait／events face——零 holder 綁定／批次預取／
        回執／送信面（invariant 1）。"""
        base = tmp_path / "st"

        def runner(argv):
            assert argv[0] in ("wait", "events"), argv  # allowlist 紅線
            assert "--address" in argv, argv
            calls.append(list(argv))
            step = steps[len(calls) - 1]
            if isinstance(step, Exception):
                raise step
            return step

        # 生命週期：冷啟（4 步）→ re-arm wait 喚醒（3 步）
        steps = [
            _ok_page([1], "t1"), _ok_page([], None),          # plain 對滾
            _ok_page([1], "k1"), _ok_page([], None),          # kinded 對滾
            _ok_page([2, 3], "t2"), _ok_page([2, 3], "k2"),   # wait＋kinded
            _ok_page([], None),
        ]
        calls = []
        rc1 = mod.run_worker(
            [ADDR], 1, base_dir=str(base), runner=runner,
            stdout=io.StringIO(), stderr=io.StringIO(),
            sleep=lambda _s: None,
        )
        assert rc1 == 0
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "t1"
        assert entry["accepted_cursor"] == "k1"
        rc2 = mod.run_worker(
            [ADDR], _read_state(base)["generation"],
            base_dir=str(base), runner=runner,
            stdout=io.StringIO(), stderr=io.StringIO(),
            sleep=lambda _s: None,
        )
        assert rc2 == 0
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "t2"
        assert entry["accepted_cursor"] == "k2"
        # 收尾複核：全生命週期清一色 wait/events
        assert calls
        assert all(c[0] in ("wait", "events") for c in calls)

    def test_w8_two_addresses_coalesce_wake(self, tmp_path):
        """雙門牌 coalesce：A 門牌 wait 喚醒時 B 門牌以 kinded events 非阻塞
        快照併入同一輪彙總（invariant 8）——快照只推 kinded 軸（B 的
        unkinded cursor 不動——計數恆由 kinded 軸決定）。"""
        base = tmp_path / "st"
        other = "other-marshal"
        _seed_state(base, cursors={ADDR: ("a0", "ka0"), other: ("b0", "kb0")})
        runner = ScriptRunner([
            _ok_page([11], "a1"),        # 1. wait A：中斷頁
            _ok_page([11], "ka1"),       # 2. kinded A 計數
            _ok_page([], None),          # 3. kinded A 到底
            _ok_page([21, 22], "kb1"),   # 4. B 快照（kinded，非阻塞）
            _ok_page([], None),          # 5. kinded B 到底
        ])
        rc, tail, _out = _run(base, runner, addresses=(ADDR, other))
        assert rc == 0
        assert tail["state"] == "mail"
        got = {(row["address"], row["count"]) for row in tail["new"]}
        assert got == {(ADDR, 1), (other, 2)}
        entries = _read_state(base)["addresses"]
        assert entries[ADDR]["cursor"] == "a1"
        assert entries[ADDR]["accepted_cursor"] == "ka1"
        assert entries[other]["cursor"] == "b0"  # 快照不推 unkinded 軸
        assert entries[other]["accepted_cursor"] == "kb1"


# ── 控制面：start／stop／status（AC2 五欄）────────────────────────────


class TestControlPlane:
    def test_start_first_arm_prints_copyable_command(self, tmp_path, capsys):
        """fresh state → start：generation=1＋desired=running＋armed_at＋
        per-address 冷啟 entry（雙 cursor 欄）；stdout 印可直接複製的
        worker 背景命令。"""
        base = str(tmp_path / "st")
        assert mod.cmd_start([ADDR], base) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "uv run python scripts/mail_waiter.py worker" in out
        assert f"--address {ADDR}" in out
        assert "--generation 1" in out
        assert f"--state-dir {base}" in out
        st = _read_state(base)
        assert st["desired"] == "running"
        assert st["generation"] == 1
        assert isinstance(st["armed_at"], float)
        assert st["addresses"][ADDR] == {
            "cursor": None, "accepted_cursor": None, "last_event_seq": 0,
        }

    def test_start_generation_increments_preserves_cursor(
        self, tmp_path, capsys
    ):
        """既有 gen 5＋雙 cursor → start：gen 6（CAS 鏈）＋雙 cursor 保留
        （coalesce 延續——舊信不再觸發）。"""
        base = str(tmp_path / "st")
        _seed_state(base, generation=5, cursors={ADDR: ("keep9", "keepk")})
        assert mod.cmd_start([ADDR], base) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "--generation 6" in out
        entry = _read_state(base)["addresses"][ADDR]
        assert _read_state(base)["generation"] == 6
        assert entry["cursor"] == "keep9"
        assert entry["accepted_cursor"] == "keepk"

    def test_start_corrupt_state_rebases_generation(self, tmp_path):
        """state 損壞視同冷啟（generation 歸零重 arm＝1）。"""
        base = str(tmp_path / "st")
        os.makedirs(base, exist_ok=True)
        with open(_state_file(base), "w", encoding="utf-8") as fh:
            fh.write("{broken")
        assert mod.cmd_start([ADDR], base) == mod.EXIT_OK
        assert _read_state(base)["generation"] == 1

    def test_stop_writes_flag_keeps_generation(self, tmp_path, capsys):
        """stop＝落 desired=stopped（generation 不動——flag 權威面）；
        印確認＋worker 下輪自退說明。"""
        base = str(tmp_path / "st")
        _seed_state(base, generation=7, cursors={ADDR: ("u0", "k0")})
        assert mod.cmd_stop(base) == mod.EXIT_OK
        st = _read_state(base)
        assert st["desired"] == "stopped"
        assert st["generation"] == 7  # flag 不推進 generation
        assert "stopped" in capsys.readouterr().out

    def test_stop_absent_state_creates_flag(self, tmp_path):
        """state 缺席下 stop＝落 flag（fresh minimal state）不炸。"""
        base = str(tmp_path / "st")
        assert mod.cmd_stop(base) == mod.EXIT_OK
        st = _read_state(base)
        assert st["desired"] == "stopped"

    def test_status_five_fields(self, tmp_path, capsys):
        """status 五欄在場：desired／generation／armed_at（＋staleness
        fresh）／per-address cursor。"""
        base = str(tmp_path / "st")
        _seed_state(
            base, generation=3, cursors={ADDR: ("tok8", "ktok8")},
            armed_at=time.time() - 5,
        )
        assert mod.cmd_status(base) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "desired=running" in out
        assert "generation=3" in out
        assert "armed_at" in out
        assert "fresh" in out
        assert "cursor=tok8" in out

    def test_status_stale_hint_suggests_rearm(self, tmp_path, capsys):
        """armed_at 距今 > 輪詢週期×3＝stale 提示 re-arm（invariant 7：
        worker stale 時引導新 session 重新 arm）。"""
        base = str(tmp_path / "st")
        _seed_state(
            base, cursors={ADDR: ("u0", "k0")},
            armed_at=time.time() - 10 * mod.POLL_SLICE_SECONDS,
        )
        assert mod.cmd_status(base) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "stale" in out
        assert "re-arm" in out

    def test_status_absent_state_reports_cold(self, tmp_path, capsys):
        """state 缺席＝冷啟報告（不炸、零殘留——status 唯讀）。"""
        base = str(tmp_path / "st")
        assert mod.cmd_status(base) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "desired=" in out
        assert "generation=" in out


# ── state 慣例（0600 atomic；worker 寫入）─────────────────────────────


class TestStateHygiene:
    def test_state_file_0600_atomic_no_tmp_leftovers(self, tmp_path):
        """worker 寫 state＝0600 atomic（pid tmp＋replace）——不留 tmp 殘屍。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _ok_page([1], "u1"),
            _ok_page([1], "k1"),
            _ok_page([], None),
        ])
        _rc, _tail, _out = _run(base, runner)
        mode = stat.S_IMODE(os.stat(_state_file(base)).st_mode)
        assert mode == 0o600
        leftovers = [f for f in os.listdir(str(base)) if f.endswith(".tmp")]
        assert leftovers == []


# ── tri-panel 修復（J-1..J-7——GLM-5.3 judge 8 findings）───────────────


class TestTriPanelFixes:
    def test_j1_runner_timeout_skip_round_real_stub(self, tmp_path,
                                                    monkeypatch):
        """J-1：stub binary 真睡 5s 超過 runner timeout（切片 1s＋margin
        2s＝3s）→ TimeoutExpired 歸 skip-round fail-soft——續輪不崩、skip
        輪零尾行外洩，第 3 輪事件到照常喚醒（waiter 自帶 runner，非
        core 固定 30s）。stub 區分雙軸：kinded events 首頁回事件、續翻
        回空頁；wait 前 2 次睡 5s。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        events_empty = json.dumps({
            "schemaVersion": 1, "ok": True,
            "result": {"items": [], "nextCursor": None},
        })
        wait_page = json.dumps({
            "schemaVersion": 1, "ok": True,
            "result": {"items": [_item(9)], "nextCursor": "u9"},
        })
        kinded_page = json.dumps({
            "schemaVersion": 1, "ok": True,
            "result": {"items": [_item(9)], "nextCursor": "k9"},
        })
        stub = tmp_path / "stub-dutymail"
        stub.write_text("\n".join([
            "#!/bin/sh",
            'n=$(cat "$STUB_CNT" 2>/dev/null || echo 0)',
            "n=$((n + 1))",
            'printf "%s" "$n" > "$STUB_CNT"',
            'if [ "$1" = "wait" ]; then',
            '  if [ "$n" -lt 3 ]; then sleep 5; fi',
            f"  printf '%s' '{wait_page}'",
            "  exit 0",
            "fi",
            'case " $* " in',
            '  *" --kind "*)',
            '    k=$(cat "$STUB_KCNT" 2>/dev/null || echo 0)',
            "    k=$((k + 1))",
            '    printf "%s" "$k" > "$STUB_KCNT"',
            '    if [ "$k" -eq 1 ]; then '
            f"printf '%s' '{kinded_page}'; else "
            f"printf '%s' '{events_empty}'; fi",
            "    ;;",
            f"  *) printf '%s' '{events_empty}' ;;",
            "esac",
        ]) + "\n", encoding="utf-8")
        stub.chmod(0o755)
        monkeypatch.setenv("DUTYMAIL_BIN", str(stub))
        monkeypatch.setenv("STUB_CNT", str(tmp_path / "calls"))
        monkeypatch.setenv("STUB_KCNT", str(tmp_path / "kinded"))
        monkeypatch.setattr(mod, "POLL_SLICE_MS", 1_000)
        monkeypatch.setattr(mod, "POLL_SLICE_SECONDS", 1.0)
        monkeypatch.setattr(mod, "RUNNER_TIMEOUT_MARGIN_SECONDS", 2.0)
        out = io.StringIO()
        err = io.StringIO()
        rc = mod.run_worker(
            [ADDR], 1, base_dir=str(base), stdout=out, stderr=err,
            sleep=lambda _s: None,
        )
        assert rc == mod.EXIT_OK
        lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
        assert len(lines) == 1  # skip 輪零尾行外洩——唯一尾行＝喚醒
        tail = json.loads(lines[0])
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]
        assert err.getvalue().count("runner timeout") == 2  # 兩輪 fail-soft
        entry = _read_state(base)["addresses"][ADDR]
        assert _read_state(base)["generation"] == 1
        assert entry["cursor"] == "u9"
        assert entry["accepted_cursor"] == "k9"
        assert _read_state(base)["last_exit"]["reason"] == "mail"
        assert _read_state(base)["last_round_failed"] is False

    def test_j2_concurrent_start_stop_update_consistency(self, tmp_path):
        """J-2：真 race——50 並發 start/stop/guarded-update 交錯，flock
        序列化下事後不變式：generation 恰＝種子＋start 次數（單調零
        lost update）、全部門牌不丟、desired＝最後寫入者勝（第二波純
        update——mutate 在 critical section 內記錄鎖序本體）。"""
        base = str(tmp_path / "st")
        _seed_state(base, generation=1, cursors={ADDR: ("u0", "k0")})
        state_file = _state_file(base)
        errors = []
        update_ok = []
        order = []  # (i, desired)——mutate 內 append＝flock 鎖序本體

        def _start(i):
            try:
                assert mod.cmd_start([f"start-{i}"], base) == mod.EXIT_OK
            except Exception as exc:
                errors.append(f"start-{i}: {exc!r}")

        def _stop():
            try:
                assert mod.cmd_stop(base) == mod.EXIT_OK
            except Exception as exc:
                errors.append(f"stop: {exc!r}")

        def _update(i):
            try:
                desired = "running" if i % 2 else "stopped"

                def mutate(st):
                    entries = st.setdefault("addresses", {})
                    entry = entries.setdefault(
                        f"upd-{i}",
                        {"cursor": None, "accepted_cursor": None,
                         "last_event_seq": 0},
                    )
                    entry["last_event_seq"] = (
                        int(entry.get("last_event_seq") or 0) + 1
                    )
                    st["desired"] = desired
                    order.append((i, desired))  # critical section 內＝鎖序

                current = mod.core.load_state(state_file)
                generation = current.get("generation") if current else 1
                if mod._guarded_update(state_file, generation, mutate):
                    update_ok.append(i)
            except Exception as exc:
                errors.append(f"upd-{i}: {exc!r}")

        threads = (
            [threading.Thread(target=_start, args=(i,))
             for i in range(16)]
            + [threading.Thread(target=_stop) for _ in range(16)]
            + [threading.Thread(target=_update, args=(i,))
               for i in range(18)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        st = _read_state(base)
        assert st["generation"] == 17  # 種子 1＋16 start——零 lost increment
        entries = st["addresses"]
        assert entries[ADDR]["cursor"] == "u0"  # 原始 cursor 不丟
        assert entries[ADDR]["accepted_cursor"] == "k0"
        for i in range(16):
            assert f"start-{i}" in entries  # start 門牌全在
        for i in update_ok:
            assert entries[f"upd-{i}"]["last_event_seq"] == 1  # update 不丟

        # 第二波：純 update（無 start/stop 干擾）——最後寫入者勝精確釘
        order.clear()
        wave2 = [
            threading.Thread(target=_update, args=(100 + i,))
            for i in range(20)
        ]
        for t in wave2:
            t.start()
        for t in wave2:
            t.join()
        assert errors == []
        st = _read_state(base)
        assert st["generation"] == 17  # 無人動 generation
        assert len(order) == 20
        assert st["desired"] == order[-1][1]  # 鎖序最後一筆＝終值

    def test_j3_coalesce_snapshots_addresses_before_trigger(self, tmp_path):
        """J-3：第一門牌 timeout 後第二門牌觸發——觸發門牌「之前」的門牌
        有新信也要併入本次 exit（快照＝觸發門牌以外全部，非 index+1
        之後）；快照只推 kinded 軸。"""
        base = tmp_path / "st"
        first, second, third = "m1", "m2", "m3"
        _seed_state(base, cursors={
            first: ("a0", "ka0"), second: ("b0", "kb0"), third: ("c0", "kc0"),
        })
        runner = ScriptRunner([
            _face_err("wait-timeout", "wait-timeout", 6),   # 1. wait m1
            _ok_page([21, 22], "b1"),                       # 2. wait m2：頁
            _ok_page([21, 22], "kb1"),                      # 3. kinded m2 計數
            _ok_page([], None),                             # 4. kinded m2 到底
            _ok_page([11], "ka1"),                          # 5. 快照 m1（前段）
            _ok_page([], None),                             # 6. kinded m1 到底
            _ok_page([], None),                             # 7. 快照 m3（後段）
        ])
        rc, tail, _out = _run(
            base, runner, addresses=(first, second, third)
        )
        assert rc == 0
        assert tail["state"] == "mail"
        got = {(row["address"], row["count"]) for row in tail["new"]}
        assert got == {(second, 2), (first, 1)}
        entries = _read_state(base)["addresses"]
        assert entries[first]["cursor"] == "a0"  # 快照不推 unkinded 軸
        assert entries[first]["accepted_cursor"] == "ka1"  # 前段 kinded 推進
        assert entries[second]["cursor"] == "b1"
        assert entries[second]["accepted_cursor"] == "kb1"
        assert entries[third]["cursor"] == "c0"  # 無新信不動
        assert entries[third]["accepted_cursor"] == "kc0"

    def test_j4_wait_page_nonempty_without_next_cursor_fail_loud(
        self, tmp_path,
    ):
        """J-4：wait 非空頁缺 nextCursor（契約違反——nextCursor 恒由頁末
        項編碼）＝shape-drift fail-loud——絕不回 None token（unkinded
        cursor 不退回冷啟 null）。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _ok_page([1, 2], None),  # 非空頁卻無 nextCursor
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == mod.EXIT_FAIL_LOUD
        assert tail["state"] == "fail-loud"
        assert "shape-drift" in tail["reason"]
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["cursor"] == "u0"  # 不退回 null
        assert _read_state(base)["last_exit"]["code"] == mod.EXIT_FAIL_LOUD

    def test_j4_events_page_nonempty_without_next_cursor_fail_loud(
        self, tmp_path,
    ):
        """J-4（kinded 續翻頁）：events 續翻非空頁缺 nextCursor 同契約
        違反——shape-drift fail-loud。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([
            _ok_page([1], "u1"),
            _ok_page([1], "k1"),
            _ok_page([2], None),  # 續翻頁非空卻無 nextCursor
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == mod.EXIT_FAIL_LOUD
        assert tail["state"] == "fail-loud"
        assert "shape-drift" in tail["reason"]

    def test_j5_superseded_precedes_stopped(self, tmp_path):
        """J-5：worker loop 頂先查 generation 再查 stopped——舊代 worker
        （gen 1）＋state 已停（gen 2、desired=stopped）→ 尾行 superseded
        非 stopped（stale worker 恆報 superseded）。"""
        base = tmp_path / "st"
        _seed_state(base, desired="stopped", generation=2,
                    cursors={ADDR: ("u0", "k0")})
        runner = ScriptRunner([])
        rc, tail, _out = _run(base, runner, generation=1)
        assert rc == 0
        assert tail["state"] == "superseded"
        assert runner.calls == []
        st = _read_state(base)
        assert st["last_exit"] is None  # superseded 不寫 state

    def test_j67_snapshot_failure_tolerated_round_failed(self, tmp_path):
        """J-6/J-7：主門牌 mail 後續 snapshot 撞 usage（原 fail-loud 類）
        ——快照面全容忍：照樣 exit 0 報 mail＋last_round_failed=True、
        該門牌雙 cursor 不推進（主 watch 路徑 fail-loud 行為不變）。"""
        base = tmp_path / "st"
        other = "other-marshal"
        _seed_state(base, cursors={ADDR: ("a0", "ka0"), other: ("b0", "kb0")})
        runner = ScriptRunner([
            _ok_page([11], "a1"),                        # 1. wait 主：頁
            _ok_page([11], "ka1"),                       # 2. kinded 主計數
            _ok_page([], None),                          # 3. kinded 主到底
            _face_err("unknown-flag", "usage", 2, "bad"),  # 4. 快照：usage
        ])
        rc, tail, _out = _run(base, runner, addresses=(ADDR, other))
        assert rc == 0  # 快照失敗不吞喚醒、不崩
        assert tail["state"] == "mail"
        got = {(row["address"], row["count"]) for row in tail["new"]}
        assert got == {(ADDR, 1)}
        st = _read_state(base)
        assert st["last_exit"]["reason"] == "mail"
        assert st["last_round_failed"] is True  # 快照失敗標記
        entry = st["addresses"][other]
        assert entry["cursor"] == "b0"  # 不推進（雙欄）
        assert entry["accepted_cursor"] == "kb0"
