"""mail-watch daemon 測試（AIR-265 S4——TC-W1..W9）。

EP＝ai-analysis/_tasks/10-06-mail-watch/ep.md。涵蓋：
- 觸發語義（W1/W2/W3）：冷啟一次（state 缺席/損壞＝baseline 0 起算）、
  rising edge＋同值靜默＋baseline 落下同步更新、restart 接手（stop→
  新信→start＝say 一次 4>2、無冷啟重複通知）。
- fail-soft/fail-loud（W4）：storage typed failure＝跳輪＋心跳標記、
  baseline 不動、不崩；usage 類＝fail-loud raise（壞配置不硬跑）；
  say 失敗＝log 續跑＋baseline 已更新不回滾。
- 監督契約（W5/W6/W7）：singleton（daemon 活著二次 start＝拒絕帶現
  PID）、kill -9 後 flock 自動釋放（crash 清理免費）、SIGTERM 乾淨
  退出（exit 0＋鎖釋放＋state.json 保留）。
- say 慣例（W8）：`say -v Meijia -r 180`＋中性句 ≤20 字（去空白計）
  ＋無稱謂。
- 唯讀結構證（W9）：全生命週期（冷啟輪→rising→falling→restart→
  status live probe）dutymail 呼叫面只出現 `receive status --address`。

測試形態同 tests/test_duty_receive.py：injectable runner（fake
dutymail 回固定 JSON）＋tmp state dir 注入＋say stub 捕獲（禁測試
實播語音）。W5/W6/W7 走真 subprocess daemon——DUTYMAIL_BIN 指向
pending=0 的 stub binary（daemon 全程零通知零 say）、--state-dir 注入
tmp 路徑（不碰真 ~/.local/state）。
"""

import json
import os
import signal
import stat
import subprocess
import time

import pytest
from conftest import load_module

mod = load_module("scripts/duty_mail_watch.py")

ADDR = "ai-guide-marshal"
TITLES = ("主人", "帥哥", "前輩", "道友", "陛下", "道祖")  # 稱謂清單——中性句禁出現


# ── fake dutymail runner／say stub／state helpers ──────────────────────


def _ok_pending(count):
    return json.dumps(
        {"schemaVersion": 1, "ok": True, "result": {"pendingCount": count}}
    )


def _face_err(code, error_class, exit_code=4, message="typed failure"):
    return mod.core.DutymailFaceError(
        code=code, error_class=error_class, message=message,
        retryable=False, exit_code=exit_code,
    )


class ScriptRunner:
    """injectable runner：steps 依呼叫序（JSON str 或 Exception）；超出
    步數＝AssertionError（釘呼叫面）。"""

    def __init__(self, steps):
        self.steps = list(steps)
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        if len(self.calls) > len(self.steps):
            raise AssertionError("unexpected call: " + repr(list(argv)))
        step = self.steps[len(self.calls) - 1]
        if isinstance(step, Exception):
            raise step
        return step


class SayRecorder:
    """say stub——捕獲完整 argv（voice/rate/文案斷言；禁實播語音）。"""

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, argv):
        self.calls.append(list(argv))
        if self.fail:
            raise RuntimeError("say unavailable")


def _state_file(base):
    return mod.state_file_path(str(base))


def _read_state(base):
    with open(_state_file(base), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _seed_state(base, addresses=None, pid=None, last_poll_at=None):
    os.makedirs(str(base), exist_ok=True)
    doc = {"addresses": addresses if addresses is not None else {},
           "interval": mod.MIN_INTERVAL_SECONDS}
    if pid is not None:
        doc["pid"] = pid
    if last_poll_at is not None:
        doc["last_poll_at"] = last_poll_at
    with open(_state_file(base), "w", encoding="utf-8") as fh:
        json.dump(doc, fh)


def _poll(base, runner, say=None, addresses=(ADDR,)):
    """daemon loop 單輪的 in-process 驅動（load state→poll_round）。"""
    say = say if say is not None else SayRecorder()
    state = mod.core.load_state(_state_file(base)) or {"addresses": {}}
    notified = mod.poll_round(
        state, list(addresses), runner, say, _state_file(base)
    )
    return notified, say


# ── 真 subprocess daemon 支撐（W5/W6/W7）──────────────────────────────


def _fake_dutymail(tmp_path, pending=0):
    """stub binary：恆回 pendingCount=0 的凍結 JSON——daemon 零通知零 say。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "dutymail"
    script.write_text(
        "#!/bin/sh\necho '"
        + json.dumps(
            {"schemaVersion": 1, "ok": True, "result": {"pendingCount": pending}}
        )
        + "'\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return str(script)


def _wait_ready(base, pid, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = mod.core.load_state(_state_file(base))
        if state and state.get("pid") == pid:
            return state
        time.sleep(0.05)
    raise AssertionError(f"daemon pid {pid} 未在 {timeout}s 內就緒")


def _wait_lock_free(base, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        fd = mod.try_lock(mod.lock_path(str(base)))
        if fd is not None:
            os.close(fd)
            return
        time.sleep(0.1)
    raise AssertionError("lock 仍被持")


# ── W1/W2/W3：觸發語義（rising edge＋冷啟＋restart 接手）───────────────


class TestEdgeSemantics:
    def test_w1_cold_start_notifies_once(self, tmp_path):
        """state 缺席、pending=3 → say 一次（文案含 3）、baseline=3。"""
        base = tmp_path / "st"
        runner = ScriptRunner([_ok_pending(3)])
        notified, say = _poll(base, runner)
        assert len(say.calls) == 1
        text = say.calls[0][-1]
        assert "3" in text and "信箱" in text
        assert notified == [(ADDR, 3)]
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 3
        assert len(runner.calls) == 1  # 單 face：一輪一門牌恰一次查詢

    def test_w2_rising_falling_sequence(self, tmp_path):
        """0→2→2→4→0→1：say@2、靜默@2、say@4、靜默@0（baseline 落 0）、say@1。"""
        base = tmp_path / "st"
        seq = [0, 2, 2, 4, 0, 1]
        runner = ScriptRunner([_ok_pending(n) for n in seq])
        say = SayRecorder()
        for _value in seq:
            _notified, say = _poll(base, runner, say=say)
        assert len(say.calls) == 3
        texts = [c[-1] for c in say.calls]
        assert "2" in texts[0]
        assert "4" in texts[1]
        assert "1" in texts[2]
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 1

    def test_w3_restart_new_mail_says_once(self, tmp_path):
        """baseline=2 stop→新信至 4→start：say 一次（4>2）——restart 接手。"""
        base = tmp_path / "st"
        _seed_state(base, addresses={ADDR: {"baseline": 2, "last_seen": 2}})
        runner = ScriptRunner([_ok_pending(4)])
        _notified, say = _poll(base, runner)
        assert len(say.calls) == 1
        assert "4" in say.calls[0][-1]
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 4

    def test_w3_restart_same_count_silent(self, tmp_path):
        """restart 後同值（pending==baseline=2）→ 靜默——無冷啟重複通知。"""
        base = tmp_path / "st"
        _seed_state(base, addresses={ADDR: {"baseline": 2, "last_seen": 2}})
        runner = ScriptRunner([_ok_pending(2)])
        _notified, say = _poll(base, runner)
        assert say.calls == []
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 2


# ── W4＋fail-soft 面：storage 跳輪／usage fail-loud／say 失敗／壞 state ──


class TestFailSoft:
    def test_w4_storage_failure_skips_round(self, tmp_path):
        """storage typed failure＝跳輪＋心跳標記、不崩、baseline 不動；
        下輪恢復照常 rising edge。"""
        base = tmp_path / "st"
        _seed_state(base, addresses={ADDR: {"baseline": 2, "last_seen": 2}})
        runner = ScriptRunner([
            _face_err("store-incompatible", "storage", exit_code=4),
            _ok_pending(3),
        ])
        say = SayRecorder()
        _poll(base, runner, say=say)
        assert say.calls == []  # 跳輪零通知
        st = _read_state(base)
        assert st["addresses"][ADDR]["baseline"] == 2  # baseline 不動
        assert st["last_round_failed"] is True  # 心跳失敗標記
        assert isinstance(st["last_poll_at"], float)  # 心跳照寫
        _poll(base, runner, say=say)
        assert len(say.calls) == 1  # 3>2——恢復輪照常觸發
        assert _read_state(base)["last_round_failed"] is False

    def test_w4_usage_failure_fail_loud(self, tmp_path):
        """usage 類 typed failure＝fail-loud raise（壞配置不硬跑——daemon
        面 exit 2；poll_round 原樣傳出）。"""
        base = tmp_path / "st"
        runner = ScriptRunner([_face_err("unknown-flag", "usage", exit_code=2)])
        with pytest.raises(mod.core.DutymailFaceError):
            mod.poll_round(
                {"addresses": {}}, [ADDR], runner, SayRecorder(),
                _state_file(base),
            )

    def test_say_failure_fail_soft_baseline_advances(self, tmp_path, capsys):
        """say 失敗＝log 續跑＋baseline 已更新不回滾（寧重不漏——殘缺通知
        由冷啟/stale 週期補，下輪不重試本輪）。"""
        base = tmp_path / "st"
        runner = ScriptRunner([_ok_pending(3)])
        say = SayRecorder(fail=True)
        mod.poll_round(
            {"addresses": {}}, [ADDR], runner, say, _state_file(base)
        )
        assert len(say.calls) == 1  # 呼叫了但失敗
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 3
        assert "say" in capsys.readouterr().err  # log 註記

    def test_corrupt_state_cold_start(self, tmp_path):
        """state 損壞（壞 JSON）視同冷啟——baseline 0 起算＋通知一次。"""
        base = tmp_path / "st"
        os.makedirs(str(base), exist_ok=True)
        with open(_state_file(base), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        runner = ScriptRunner([_ok_pending(2)])
        _notified, say = _poll(base, runner)
        assert len(say.calls) == 1
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 2


# ── W5/W6/W7：singleton／stale 釋放／stop 乾淨（真 subprocess daemon）──


class TestSingletonLifecycle:
    def test_w5_second_start_rejected_with_pid(
        self, tmp_path, monkeypatch, capsys
    ):
        """daemon 活著二次 start＝拒絕＋訊息含現 PID、exit≠0。"""
        monkeypatch.setenv("DUTYMAIL_BIN", _fake_dutymail(tmp_path))
        base = str(tmp_path / "st")
        assert mod.cmd_start(
            [ADDR], mod.MIN_INTERVAL_SECONDS, base
        ) == mod.EXIT_OK
        try:
            capsys.readouterr()
            rc = mod.cmd_start([ADDR], mod.MIN_INTERVAL_SECONDS, base)
            assert rc != 0
            err = capsys.readouterr().err
            assert "already running" in err
            assert str(_read_state(base)["pid"]) in err
        finally:
            assert mod.cmd_stop(base) == mod.EXIT_OK

    def test_w6_kill9_then_start_succeeds(self, tmp_path, monkeypatch):
        """kill -9 daemon 後再 start：鎖已釋（flock 隨 fd 消亡——crash 清理
        免費）、start 成功。"""
        monkeypatch.setenv("DUTYMAIL_BIN", _fake_dutymail(tmp_path))
        base = str(tmp_path / "st")
        assert mod.cmd_start(
            [ADDR], mod.MIN_INTERVAL_SECONDS, base
        ) == mod.EXIT_OK
        old_pid = _read_state(base)["pid"]
        os.kill(old_pid, signal.SIGKILL)
        _wait_lock_free(base)
        assert mod.cmd_start(
            [ADDR], mod.MIN_INTERVAL_SECONDS, base
        ) == mod.EXIT_OK
        assert _read_state(base)["pid"] != old_pid
        assert mod.cmd_stop(base) == mod.EXIT_OK

    def test_w7_stop_clean_exit0_lock_released_state_kept(
        self, tmp_path, monkeypatch, capsys
    ):
        """SIGTERM＝exit 0、鎖釋放、state.json 保留。"""
        monkeypatch.setenv("DUTYMAIL_BIN", _fake_dutymail(tmp_path))
        base = str(tmp_path / "st")
        proc = subprocess.Popen(
            mod.daemon_argv([ADDR], mod.MIN_INTERVAL_SECONDS, base),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            _wait_ready(base, proc.pid)
            assert mod.cmd_stop(base) == mod.EXIT_OK
            assert proc.wait(
                timeout=mod.STOP_GRACE_SECONDS + 5
            ) == 0  # SIGTERM 乾淨退出
            fd = mod.try_lock(mod.lock_path(base))
            assert fd is not None  # 鎖已釋放
            os.close(fd)
            st = _read_state(base)  # state.json 保留（baseline 跨 stop 存活）
            assert st["addresses"][ADDR]["baseline"] == 0
            assert "stopped" in capsys.readouterr().out
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)


# ── W8：say 慣例（voice/rate/中性句/長度/無稱謂）──────────────────────


class TestSayConvention:
    def test_w8_say_meijia_180_neutral_short(self, tmp_path):
        base = tmp_path / "st"
        runner = ScriptRunner([_ok_pending(3)])
        _notified, say = _poll(base, runner)
        (call,) = say.calls
        assert call[:5] == ["say", "-v", "Meijia", "-r", "180"]
        text = call[5]
        for title in TITLES:
            assert title not in text  # 無稱謂（中性句）
        assert len(text.replace(" ", "")) <= 20  # ≤20 字（去空白計）
        assert text == "ai-guide 信箱有 3 封新信待判讀"


# ── W9：唯讀結構證（allowlist runner——全生命週期只 receive status）────


class TestReadOnlyFace:
    def test_w9_only_receive_status_calls(self, tmp_path, capsys):
        """daemon 全生命週期（冷啟輪→rising→同值→falling→restart 同值→
        status live probe）——dutymail 呼叫面 allowlist：只准
        `receive status --address <alias>`。"""
        base = tmp_path / "st"
        seq = [3, 5, 5, 2, 2]
        cursor = {"i": 0}

        def runner(argv):
            assert argv[0:3] == ["receive", "status", "--address"], argv
            assert argv[3] == ADDR
            value = seq[cursor["i"] % len(seq)]
            cursor["i"] += 1
            return _ok_pending(value)

        say = SayRecorder()
        for _value in seq:
            _poll(base, runner, say=say)
        assert mod.cmd_status(base, None, runner=runner) == mod.EXIT_OK
        capsys.readouterr()
        # 全生命週期呼呼叫面清一色 receive status（start/stop 不觸達 face）
        assert mod.cmd_stop(base) == mod.EXIT_OK  # 無 daemon——零 face 呼叫


# ── status 報告（AC3：PID 活性＋last_poll_at 新鮮度＋baseline＋現值）───


class TestStatusReport:
    def test_full_report_with_lock_held(self, tmp_path, capsys):
        base = str(tmp_path / "st")
        _seed_state(
            base, addresses={ADDR: {"baseline": 2, "last_seen": 2}},
            pid=os.getpid(), last_poll_at=time.time() - 5,
        )
        fd = mod.try_lock(mod.lock_path(base))
        assert fd is not None
        try:
            runner = ScriptRunner([_ok_pending(4)])
            assert mod.cmd_status(base, None, runner=runner) == mod.EXIT_OK
            out = capsys.readouterr().out
            assert "running" in out and str(os.getpid()) in out
            assert "alive" in out
            assert "fresh" in out  # last_poll 5s 前 < interval×3
            assert "baseline=2" in out and "pending=4" in out
        finally:
            os.close(fd)

    def test_stale_heartbeat_warning(self, tmp_path, capsys):
        base = str(tmp_path / "st")
        _seed_state(
            base, pid=os.getpid(),
            last_poll_at=time.time() - 10 * mod.DEFAULT_INTERVAL_SECONDS,
        )
        fd = mod.try_lock(mod.lock_path(base))
        assert fd is not None
        try:
            assert mod.cmd_status(
                base, [], runner=ScriptRunner([])
            ) == mod.EXIT_OK
            assert "stale-heartbeat" in capsys.readouterr().out
        finally:
            os.close(fd)

    def test_not_running_still_reports_baseline(self, tmp_path, capsys):
        base = str(tmp_path / "st")
        _seed_state(base, addresses={ADDR: {"baseline": 2, "last_seen": 2}})
        runner = ScriptRunner([_ok_pending(4)])
        assert mod.cmd_status(base, None, runner=runner) == mod.EXIT_OK
        out = capsys.readouterr().out
        assert "not running" in out
        assert "baseline=2" in out and "pending=4" in out


# ── state 慣例（0600 atomic；多門牌獨立 edge）─────────────────────────


class TestStateHygiene:
    def test_state_file_0600_atomic_no_tmp_leftovers(self, tmp_path):
        base = tmp_path / "st"
        mod.poll_round(
            {"addresses": {}}, [ADDR], ScriptRunner([_ok_pending(1)]),
            SayRecorder(), _state_file(base),
        )
        mode = stat.S_IMODE(os.stat(_state_file(base)).st_mode)
        assert mode == 0o600
        leftovers = [f for f in os.listdir(str(base)) if f.endswith(".tmp")]
        assert leftovers == []  # atomic 寫不留 tmp 殘屍

    def test_two_addresses_independent_edges(self, tmp_path):
        base = tmp_path / "st"
        other = "other-marshal"
        runner = ScriptRunner([_ok_pending(0), _ok_pending(5)])
        say = SayRecorder()
        mod.poll_round(
            {"addresses": {}}, [ADDR, other], runner, say, _state_file(base)
        )
        assert len(say.calls) == 1  # 只有 other 上升（ADDR 靜默）
        assert say.calls[0][-1] == "other 信箱有 5 封新信待判讀"
        st = _read_state(base)
        assert st["addresses"][ADDR]["baseline"] == 0
        assert st["addresses"][other]["baseline"] == 5
