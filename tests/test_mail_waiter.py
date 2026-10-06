"""mail_waiter 測試（AIR-266 S4——TC-W1..W9＋控制面）。

EP＝ai-analysis/_tasks/10-07-mail-waiter/ep.md。涵蓋：
- 喚醒契約（W1）：wait exit 0 帶新事件 → 尾行 JSON state=mail＋new 清單
  （門牌×事件數）＋rearm 命令；events cursor 推進。
- timeout 消化（W2）：連續 class-6 ×N 內部續輪（不 exit），事件到才 exit 0。
- stop flag（W3）：desired=stopped 下 worker 輪＝安靜退、尾行 state=stopped、
  零 face 呼叫。
- fail-loud（W4）：class-2 usage → exit 2＋尾行 state=fail-loud。
- 跳輪（W5）：class-4 storage 一輪＝跳輪＋last_round_failed；恢復輪照常
  喚醒＋標記清除。
- generation CAS（W6）：worker A 活著再 start（gen+1）＝A 下輪見 gen 不匹配
  安靜退（superseded、不寫 state）；寫入邊 guard＝stale worker 不覆蓋新
  generation 的 cursor（不回退）。
- 冷啟（W7）：state 缺席／損壞＝events head 對滾＋首輪彙總 exit（寧重不漏）。
- 唯讀結構證（W8）：全生命週期 dutymail 呼叫面 allowlist＝wait/events
  （零 holder 綁定／批次預取／回執／送信面——invariant 1 紅線）。
- stop 權威（W9）：desired=stopped 落下後 re-arm＝新 worker 首輪即退 stopped。

測試形態：injectable runner（fake dutymail 回固定 JSON／typed failure）
＋tmp state dir 注入＋sleep 注入（冷啟空頁續輪不等 60s 切片）——零真 store
往返、禁碰真 ~/.local/state。
"""

import io
import json
import os
import stat
import time

from conftest import load_module

mod = load_module("scripts/mail_waiter.py")

ADDR = "ai-guide-marshal"


# ── fake dutymail runner／state helpers ────────────────────────────────


def _item(seq):
    return {"eventSeq": seq, "kind": "mail.accepted", "payloadJson": "{}",
            "atUs": seq * 1000}


def _ok_page(seqs, next_cursor=None):
    """events/wait 成功 stdout（凍結形：items＋nextCursor；無 cursor=None）。"""
    return json.dumps({
        "schemaVersion": 1, "ok": True,
        "result": {"items": [_item(s) for s in seqs], "nextCursor": next_cursor},
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
    os.makedirs(str(base), exist_ok=True)
    doc = {
        "desired": desired,
        "generation": generation,
        "armed_at": armed_at if armed_at is not None else time.time(),
        "addresses": {
            alias: {"cursor": cur, "last_event_seq": 0}
            for alias, cur in (cursors or {}).items()
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


def _wait_face_call(alias=ADDR, cursor="tok0", deadline_ms=60000):
    return ["wait", "--address", alias, "--cursor", cursor,
            "--deadline-ms", str(deadline_ms)]


def _events_face_call(alias=ADDR, cursor=None):
    argv = ["events", "--address", alias, "--limit",
            str(mod.EVENTS_PAGE_LIMIT)]
    if cursor is not None:
        argv += ["--cursor", cursor]
    return argv


# ── W1/W2：喚醒契約＋timeout 消化 ──────────────────────────────────────


class TestWakeupContract:
    def test_w1_wait_event_wakes_with_tail_json(self, tmp_path):
        """wait exit 0（2 新事件）→ events 續翻（1 筆→空頁到底）→ exit 0；
        尾行 state=mail＋new=[{address,count=3}]＋rearm worker 命令（同
        generation）；state cursor 推進至 head token。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: "tok0"})
        runner = ScriptRunner([
            _ok_page([11, 12], "tok1"),  # wait：非空頁（2 新事件）
            _ok_page([13], "tok2"),      # events --cursor tok1（1 筆）
            _ok_page([], None),          # events --cursor tok2（空頁＝到底）
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 3}]
        assert "scripts/mail_waiter.py worker" in tail["rearm"]
        assert "--generation 1" in tail["rearm"]
        assert runner.calls[0] == _wait_face_call()
        assert runner.calls[1] == _events_face_call(cursor="tok1")
        assert runner.calls[2] == _events_face_call(cursor="tok2")
        st = _read_state(base)
        assert st["addresses"][ADDR]["cursor"] == "tok2"  # cursor 推進
        assert st["addresses"][ADDR]["last_event_seq"] == 3

    def test_w1_rearm_command_directly_copyable(self, tmp_path):
        """rearm 命令含 worker 形完整參數（--address/--generation/--state-dir）
        ——skill/LLM 可直接複製到背景 shell。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: "tok0"})
        runner = ScriptRunner([
            _ok_page([7], "tok1"),
            _ok_page([], None),
        ])
        _rc, tail, _out = _run(base, runner)
        assert tail["rearm"].startswith("uv run python scripts/mail_waiter.py")
        assert f"--address {ADDR}" in tail["rearm"]
        assert f"--state-dir {base}" in tail["rearm"]

    def test_w2_consecutive_timeouts_digested_then_wake(self, tmp_path):
        """連續 class-6 ×3 內部消化（不 exit）——第 4 輪事件到才 exit 0。"""
        base = tmp_path / "st"
        _seed_state(base, cursors={ADDR: "tok0"})
        timeout = _face_err("wait-timeout", "wait-timeout", 6)
        runner = ScriptRunner([
            timeout, timeout, timeout,
            _ok_page([21], "tok1"),  # 第 4 輪 wait：新事件
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]
        wait_calls = [c for c in runner.calls if c[0] == "wait"]
        assert len(wait_calls) == 4  # 3 次 timeout 全在內部續輪消化


# ── W3/W9：stop flag 權威 ──────────────────────────────────────────────


class TestStopFlag:
    def test_w3_stopped_flag_quiet_exit(self, tmp_path):
        """desired=stopped 下 worker 輪＝安靜退（exit 0＋尾行 state=stopped）
        ＋零 face 呼叫＋last_exit 落檔。"""
        base = tmp_path / "st"
        _seed_state(base, desired="stopped", cursors={ADDR: "tok0"})
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
        _seed_state(base, desired="running", cursors={ADDR: "tok0"})
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
        _seed_state(base, cursors={ADDR: "tok0"})
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
        _seed_state(base, cursors={ADDR: "tok0"})
        storage = _face_err("store-incompatible", "storage", 4)
        mid = {}

        def _capture_failed_flag():
            mid["last_round_failed"] = _read_state(base)["last_round_failed"]

        runner = ScriptRunner([
            storage,                                  # 第 1 輪 wait：跳輪
            (_ok_page([31], "tok1"), _capture_failed_flag),  # 第 2 輪 wait 前查
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert mid["last_round_failed"] is True  # 跳輪輪末標記
        st = _read_state(base)
        assert st["last_round_failed"] is False  # 恢復輪清除
        assert st["addresses"][ADDR]["cursor"] == "tok1"


# ── W6：generation CAS（雙 arm 舊退新續、cursor 不回退）───────────────


class TestGenerationCas:
    def test_w6_superseded_quiet_exit_next_round(self, tmp_path):
        """worker A（gen 1）活著再 start（gen+1）＝A 下輪見 gen 不匹配安靜退
        （尾行 superseded、exit 0、不寫 state——last_exit 不落、cursor 不動）。"""
        base = tmp_path / "st"
        _seed_state(base, generation=1, cursors={ADDR: "tok0"})
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
        assert st["addresses"][ADDR]["cursor"] == "tok0"  # cursor 不動
        assert st["last_exit"] is None  # superseded 不寫 state（invariant 6）

    def test_w6_stale_worker_never_overwrites_cursor(self, tmp_path):
        """寫入邊 guard：A 讀過 state（gen 1）後新 arm 已推進 cursor——A 的
        彙總寫入被 guard 攔下，新 cursor 不回退（superseded 退）。"""
        base = tmp_path / "st"
        _seed_state(base, generation=1, cursors={ADDR: "tok0"})

        def _new_worker_advances():
            # 模擬新代 worker（gen 2）已把 cursor 推進到 newtok
            _seed_state(base, generation=2, cursors={ADDR: "newtok"})

        runner = ScriptRunner([
            (_ok_page([41], "tokA"), _new_worker_advances),
            _ok_page([], None),  # A 的續翻（guard 在寫入邊才攔）
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "superseded"
        st = _read_state(base)
        assert st["generation"] == 2
        assert st["addresses"][ADDR]["cursor"] == "newtok"  # 不回退


# ── W7：冷啟（state 缺席／損壞）───────────────────────────────────────


class TestColdStart:
    def test_w7_absent_state_head_scroll_wake(self, tmp_path):
        """state 缺席＝冷啟：events（無 cursor）首頁對滾到 head＋首輪彙總
        exit（寧重不漏——歷史事件全計入 new）。"""
        base = tmp_path / "st"
        runner = ScriptRunner([
            _ok_page([1, 2], "tok1"),  # 冷啟首頁（不帶 --cursor）
            _ok_page([3], "tok2"),
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 3}]
        assert runner.calls[0] == _events_face_call(cursor=None)
        st = _read_state(base)
        assert st["generation"] == 1  # worker 落地自己的 generation
        assert st["addresses"][ADDR]["cursor"] == "tok2"

    def test_w7_corrupt_state_treated_as_cold_start(self, tmp_path):
        """state 損壞（壞 JSON）視同冷啟——對滾喚醒（寧重不漏）。"""
        base = tmp_path / "st"
        os.makedirs(str(base), exist_ok=True)
        with open(_state_file(base), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        runner = ScriptRunner([
            _ok_page([5], "tok1"),
            _ok_page([], None),
        ])
        rc, tail, _out = _run(base, runner)
        assert rc == 0
        assert tail["state"] == "mail"
        assert tail["new"] == [{"address": ADDR, "count": 1}]

    def test_cold_start_empty_mailbox_digested(self, tmp_path):
        """冷啟空 mailbox（events 空頁）＝續輪內部消化（不 exit）——
        後續 wait 有事件才喚醒。冷啟輪末 sleep 切片（注入 no-op）。"""
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
        assert slept == [mod.POLL_SLICE_SECONDS] * 2  # 空頁輪末睡切片


# ── W8：唯讀結構證（allowlist——invariant 1 紅線）─────────────────────


class TestReadOnlyFace:
    def test_w8_full_lifecycle_only_wait_events_faces(self, tmp_path):
        """全生命週期（冷啟對滾輪→wait 喚醒→再喚醒輪）dutymail 呼叫面
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

        # 生命週期：冷啟（3 步）→ re-arm wait 喚醒（2 步）
        steps = [
            _ok_page([1], "t1"), _ok_page([], None),          # 冷啟輪
            _ok_page([2, 3], "t2"), _ok_page([], None),       # wait 喚醒輪
        ]
        calls = []
        rc1 = mod.run_worker(
            [ADDR], 1, base_dir=str(base), runner=runner,
            stdout=io.StringIO(), stderr=io.StringIO(),
            sleep=lambda _s: None,
        )
        assert rc1 == 0
        st = _read_state(base)
        assert st["addresses"][ADDR]["cursor"] == "t1"
        rc2 = mod.run_worker(
            [ADDR], st["generation"], base_dir=str(base), runner=runner,
            stdout=io.StringIO(), stderr=io.StringIO(),
            sleep=lambda _s: None,
        )
        assert rc2 == 0
        assert _read_state(base)["addresses"][ADDR]["cursor"] == "t2"
        # 收尾複核：全生命週期清一色 wait/events
        assert calls
        assert all(c[0] in ("wait", "events") for c in calls)

    def test_w8_two_addresses_coalesce_wake(self, tmp_path):
        """雙門牌：A 門牌 wait 喚醒時 B 門牌以 events 非阻塞快照併入同一輪
        彙總（coalesce——一次 exit 報該輪全部新事件；invariant 8）。"""
        base = tmp_path / "st"
        other = "other-marshal"
        _seed_state(base, cursors={ADDR: "a0", other: "b0"})
        runner = ScriptRunner([
            _ok_page([11], "a1"),        # 1. wait A：新事件（1 筆）
            _ok_page([], None),          # 2. A 續翻到底（空頁）
            _ok_page([21, 22], "b1"),    # 3. B 快照首頁（非阻塞）
            _ok_page([], None),          # 4. B 續翻到底
        ])
        rc, tail, _out = _run(base, runner, addresses=(ADDR, other))
        assert rc == 0
        assert tail["state"] == "mail"
        got = {(row["address"], row["count"]) for row in tail["new"]}
        assert got == {(ADDR, 1), (other, 2)}
        st = _read_state(base)
        assert st["addresses"][ADDR]["cursor"] == "a1"
        assert st["addresses"][other]["cursor"] == "b1"


# ── 控制面：start／stop／status（AC2 五欄）────────────────────────────


class TestControlPlane:
    def test_start_first_arm_prints_copyable_command(self, tmp_path, capsys):
        """fresh state → start：generation=1＋desired=running＋armed_at＋
        per-address 冷啟 entry；stdout 印可直接複製的 worker 背景命令。"""
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
        assert st["addresses"][ADDR] == {"cursor": None, "last_event_seq": 0}

    def test_start_generation_increments_preserves_cursor(
        self, tmp_path, capsys
    ):
        """既有 gen 5＋cursor → start：gen 6（CAS 鏈）＋cursor 保留
        （coalesce 延續——舊信不再觸發）。"""
        base = str(tmp_path / "st")
        _seed_state(base, generation=5, cursors={ADDR: "keep9"})
        assert mod.cmd_start([ADDR], base) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "--generation 6" in out
        st = _read_state(base)
        assert st["generation"] == 6
        assert st["addresses"][ADDR]["cursor"] == "keep9"

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
        _seed_state(base, generation=7, cursors={ADDR: "tok0"})
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
            base, generation=3, cursors={ADDR: "tok8"},
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
            base, cursors={ADDR: "tok0"},
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
        _seed_state(base, cursors={ADDR: "tok0"})
        runner = ScriptRunner([
            _ok_page([1], "tok1"),
            _ok_page([], None),
        ])
        _rc, _tail, _out = _run(base, runner)
        mode = stat.S_IMODE(os.stat(_state_file(base)).st_mode)
        assert mode == 0o600
        leftovers = [f for f in os.listdir(str(base)) if f.endswith(".tmp")]
        assert leftovers == []
