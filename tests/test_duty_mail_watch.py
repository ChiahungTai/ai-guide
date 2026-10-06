"""mail-watch daemon 測試（AIR-265 S4——TC-W1..W9＋tri-panel 修復項）。

EP＝ai-analysis/_tasks/10-06-mail-watch/ep.md。涵蓋：
- 觸發語義（W1/W2/W3）：冷啟一次（state 缺席/損壞＝baseline 0 起算）、
  rising edge＋同值靜默＋baseline 落下同步更新、restart 接手（stop→
  新信→start＝say 一次 4>2、無冷啟重複通知）。
- fail-soft/fail-loud（W4）：storage typed failure＝跳輪＋心跳標記、
  baseline 不動、不崩；usage 類＝fail-loud raise（壞配置不硬跑）；
  say 失敗＝log 續跑＋baseline 不前進＋say_pending 標記（下輪重試
  ——恢復後一次通知最新值）。
- 監督契約（W5/W6/W7）：singleton（daemon 活著二次 start＝拒絕帶現
  PID）、kill -9 後 flock 自動釋放（crash 清理免費）、SIGTERM 乾淨
  退出（exit 0＋鎖釋放＋state.json 保留＋pid/started_at 清場）；ready
  信號＝首輪 poll 完成（pid 就位＋last_poll_at 在場）——壞配置 daemon
  首輪 fail-loud＝start 帶 exit code 報失敗；W5/W7 收尾斷言 face
  呼叫記錄全行 `receive status --address`（subprocess 面 allowlist）。
- say 慣例（W8）：`say -v Meijia -r 180`＋中性句 ≤20 字（去空白計）
  ＋無稱謂；長 alias label 截 8 字。
- 唯讀結構證（W9）：全生命週期（冷啟輪→rising→falling→restart→
  status live probe）dutymail 呼叫面只出現 `receive status --address`。

測試形態同 tests/test_duty_receive.py：injectable runner（fake
dutymail 回固定 JSON）＋tmp state dir 注入＋say stub 捕獲（禁測試
實播語音）。W5/W6/W7 走真 subprocess daemon——DUTYMAIL_BIN 指向
stub binary（成功態回 pending=0 凍結 JSON——daemon 零通知零 say；
每呼叫 argv 記錄至 face-calls.log 供 allowlist 斷言）、--state-dir
注入 tmp 路徑（不碰真 ~/.local/state）。
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


def _seed_state(base, addresses=None, pid=None, last_poll_at=None,
                last_round_failed=None):
    os.makedirs(str(base), exist_ok=True)
    doc = {"addresses": addresses if addresses is not None else {},
           "interval": mod.MIN_INTERVAL_SECONDS}
    if pid is not None:
        doc["pid"] = pid
    if last_poll_at is not None:
        doc["last_poll_at"] = last_poll_at
    if last_round_failed is not None:
        doc["last_round_failed"] = last_round_failed
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
    """stub binary：恆回 pendingCount 凍結 JSON（pending=0＝daemon 零通知
    零 say）；每呼叫一行 append argv 至 ../face-calls.log（W5/W7 收尾
    allowlist 斷言消費——subprocess 面）。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "dutymail"
    script.write_text(
        "#!/bin/sh\n"
        'echo "$@" >> "$(dirname "$0")/../face-calls.log"\n'
        "echo '"
        + json.dumps(
            {"schemaVersion": 1, "ok": True, "result": {"pendingCount": pending}}
        )
        + "'\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return str(script)


def _bad_config_dutymail(tmp_path):
    """stub binary：恆回 usage typed failure（stderr JSON＋exit 2）——
    daemon 首輪 fail-loud、ready 前退出（start 帶 exit code 報失敗）。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "dutymail"
    script.write_text(
        "#!/bin/sh\n"
        "echo '"
        + json.dumps(
            {"schemaVersion": 1, "ok": False,
             "error": {"code": "unknown-flag", "class": "usage",
                       "message": "bad flag", "retryable": False}}
        )
        + "' >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return str(script)


def _assert_only_status_face_calls(tmp_path, aliases=(ADDR,)):
    """face-calls.log 全行皆 `receive status --address <alias>`——
    subprocess 面 allowlist（W5/W7 收尾）。"""
    log = tmp_path / "face-calls.log"
    assert log.exists(), "face 呼叫記錄缺席——daemon 未完成任何輪"
    lines = log.read_text(encoding="utf-8").splitlines()
    assert lines, "face 呼叫記錄空——ready 判準含首輪，至少一行"
    allowed = {f"receive status --address {alias}" for alias in aliases}
    for line in lines:
        assert line in allowed, line


def _wait_ready(base, pid, timeout=10.0):
    """ready＝首輪 poll 完成後的 state（pid 就位＋last_poll_at 在場）。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = mod.core.load_state(_state_file(base))
        if (
            state
            and state.get("pid") == pid
            and isinstance(state.get("last_poll_at"), (int, float))
            and not isinstance(state.get("last_poll_at"), bool)
        ):
            return state
        time.sleep(0.05)
    raise AssertionError(
        f"daemon pid {pid} 未在 {timeout}s 內就緒（首輪 poll 未完成）"
    )


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

    def test_say_failure_fail_soft_baseline_holds(self, tmp_path, capsys):
        """say 失敗＝log 續跑＋baseline 不前進＋say_pending 標記（下輪
        count>baseline 仍成立→重試——恢復後一次通知最新值）。"""
        base = tmp_path / "st"
        runner = ScriptRunner([_ok_pending(3)])
        say = SayRecorder(fail=True)
        notified = mod.poll_round(
            {"addresses": {}}, [ADDR], runner, say, _state_file(base)
        )
        assert notified == []  # say 失敗——未列入已通知
        assert len(say.calls) == 1  # 呼叫了但失敗
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["baseline"] == 0  # 冷啟起算值不前進
        assert entry["last_seen"] == 3
        assert entry["say_pending"] is True
        assert "say" in capsys.readouterr().err  # log 註記

    def test_say_failure_retry_next_round_notifies_latest(
        self, tmp_path, capsys
    ):
        """say 失敗一輪→baseline 不動；下輪 say 恢復→補通知＋baseline
        前進＋say_pending 清除。"""
        base = tmp_path / "st"
        _seed_state(base, addresses={ADDR: {"baseline": 2, "last_seen": 2}})
        runner = ScriptRunner([_ok_pending(5), _ok_pending(5)])
        notified, _failing = _poll(base, runner, say=SayRecorder(fail=True))
        assert notified == []
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["baseline"] == 2  # 不前進
        assert entry["say_pending"] is True
        recovered = SayRecorder()
        notified, _say = _poll(base, runner, say=recovered)
        assert notified == [(ADDR, 5)]  # 5>2——補通知
        assert "5" in recovered.calls[0][-1]
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["baseline"] == 5  # 前進
        assert "say_pending" not in entry  # 標記清除
        assert "say" in capsys.readouterr().err  # 失敗輪 log 註記

    def test_say_failure_persistent_recovers_to_latest(self, tmp_path):
        """say 連續失敗兩輪（pending 續升 5→7）→第三輪恢復＝一次通知
        最新值 7（正確語義——不逐輪補播）。"""
        base = tmp_path / "st"
        _seed_state(base, addresses={ADDR: {"baseline": 2, "last_seen": 2}})
        runner = ScriptRunner(
            [_ok_pending(5), _ok_pending(7), _ok_pending(7)]
        )
        for _round in range(2):
            notified, _failing = _poll(
                base, runner, say=SayRecorder(fail=True)
            )
            assert notified == []
        assert _read_state(base)["addresses"][ADDR]["baseline"] == 2
        notified, say = _poll(base, runner)  # 第三輪恢復
        assert notified == [(ADDR, 7)]
        text = say.calls[0][-1]
        assert "7" in text  # 一次通知最新值
        entry = _read_state(base)["addresses"][ADDR]
        assert entry["baseline"] == 7
        assert "say_pending" not in entry

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
            _assert_only_status_face_calls(tmp_path)

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
        """SIGTERM＝exit 0、鎖釋放、state.json 保留（pid/started_at 清場
        ；baseline 跨 stop 存活）＋face 呼叫面全行 receive status。"""
        monkeypatch.setenv("DUTYMAIL_BIN", _fake_dutymail(tmp_path))
        base = str(tmp_path / "st")
        proc = subprocess.Popen(
            mod.daemon_argv([ADDR], mod.MIN_INTERVAL_SECONDS, base),
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            state = _wait_ready(base, proc.pid)
            assert isinstance(state.get("last_poll_at"), float)  # 首輪完成
            assert mod.cmd_stop(base) == mod.EXIT_OK
            assert proc.wait(
                timeout=mod.STOP_GRACE_SECONDS + 5
            ) == 0  # SIGTERM 乾淨退出
            fd = mod.try_lock(mod.lock_path(base))
            assert fd is not None  # 鎖已釋放
            os.close(fd)
            st = _read_state(base)  # state.json 保留（baseline 跨 stop 存活）
            assert st["addresses"][ADDR]["baseline"] == 0
            assert st.get("pid") is None  # runtime 殘留清場（baseline 保留）
            assert st.get("started_at") is None
            assert "stopped" in capsys.readouterr().out
            _assert_only_status_face_calls(tmp_path)
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)

    def test_start_bad_config_fails_before_ready(
        self, tmp_path, monkeypatch, capsys
    ):
        """壞配置（usage typed failure）＝daemon 首輪 fail-loud、ready 前
        退出——start 報失敗帶 exit code＋log 路徑。"""
        monkeypatch.setenv("DUTYMAIL_BIN", _bad_config_dutymail(tmp_path))
        base = str(tmp_path / "st")
        rc = mod.cmd_start([ADDR], mod.MIN_INTERVAL_SECONDS, base)
        err = capsys.readouterr().err
        assert rc == mod.EXIT_FAIL
        assert "start 失敗" in err
        assert "exit 2" in err  # daemon fail-loud exit code 帶回
        state = mod.core.load_state(mod.state_file_path(base))
        assert state is not None  # pid state 已寫
        assert "last_poll_at" not in state  # ready 從未成立（首輪未完成）


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

    def test_w8_long_alias_label_truncated(self, tmp_path):
        """長 alias（southchariot-sc-310-marshal）→ label 截 8 字
        （southcha）——去空白後仍 ≤20 字。"""
        alias = "southchariot-sc-310-marshal"
        base = tmp_path / "st"
        runner = ScriptRunner([_ok_pending(3)])
        say = SayRecorder()
        mod.poll_round(
            {"addresses": {}}, [alias], runner, say, _state_file(base)
        )
        text = say.calls[0][-1]
        assert text.startswith("southcha ")
        assert len(text.replace(" ", "")) <= 20


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

    def test_status_fresh_dir_zero_residue(self, tmp_path, capsys):
        """fresh state 目錄（不存在／空目錄）上 status＝零殘留——lock 探測
        無 O_CREAT（不建目錄不建檔）。"""
        absent = tmp_path / "absent" / "st"
        assert mod.cmd_status(
            str(absent), [], runner=ScriptRunner([])
        ) == mod.EXIT_OK
        assert "not running" in capsys.readouterr().out
        assert not os.path.exists(str(absent))  # 不建目錄
        empty = tmp_path / "empty-st"
        empty.mkdir()
        assert mod.cmd_status(
            str(empty), [], runner=ScriptRunner([])
        ) == mod.EXIT_OK
        assert os.listdir(str(empty)) == []  # 不建 lock/state 檔

    def test_heartbeat_marks_last_round_failed(self, tmp_path, capsys):
        """last_round_failed=True → heartbeat 行附「上輪 face 失敗」註記。"""
        base = str(tmp_path / "st")
        _seed_state(
            base, pid=os.getpid(), last_poll_at=time.time() - 5,
            last_round_failed=True,
        )
        fd = mod.try_lock(mod.lock_path(base))
        assert fd is not None
        try:
            assert mod.cmd_status(
                base, [], runner=ScriptRunner([])
            ) == mod.EXIT_OK
            out = capsys.readouterr().out
            assert "fresh" in out
            assert "上輪 face 失敗" in out
        finally:
            os.close(fd)


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
