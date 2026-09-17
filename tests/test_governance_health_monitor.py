"""governance health monitor 測試（AIR-116 S5——TC-7 告警腿）。

monitor＝薄編排層（消費 install.py --verify＋--check）——測退出碼彙整與
告警行；判定語義本身歸 test_governance_verify/test_governance_check。
"""

import subprocess
from types import SimpleNamespace

from conftest import load_module

mod = load_module("scripts/governance_health_monitor.py")


def _patch(monkeypatch, results):
    """results：逐 mode 的 (returncode, stdout)；順序對應 MODES。"""
    it = iter(results)

    def fake_run(*a, **k):
        rc, out = next(it)
        return SimpleNamespace(returncode=rc, stdout=out, stderr="")

    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=fake_run, TimeoutExpired=subprocess.TimeoutExpired))


def test_monitor_pass_exit_zero(monkeypatch, capsys):
    _patch(monkeypatch, [(0, "[verify] 全部 PASS"), (0, "[check] 五面 parity 綠")])
    assert mod.main() == 0
    assert "PASS" in capsys.readouterr().out


def test_monitor_verify_fail_alerts(monkeypatch, capsys):
    _patch(monkeypatch, [(1, "[verify:muse] FAIL——x"), (0, "[check] 綠")])
    assert mod.main() == 1
    assert "FAIL" in capsys.readouterr().out


def test_monitor_check_fail_alerts(monkeypatch, capsys):
    _patch(monkeypatch, [(0, "[verify] PASS"), (1, "[check] 1 項 drift")])
    assert mod.main() == 1


def test_monitor_both_fail_alerts(monkeypatch, capsys):
    _patch(monkeypatch, [(1, "verify fail"), (1, "check fail")])
    assert mod.main() == 1
    out = capsys.readouterr().out
    assert "verify" in out and "check" in out


def test_monitor_timeout_fail_loud(monkeypatch, capsys):
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="install.py", timeout=900)

    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=fake_run, TimeoutExpired=subprocess.TimeoutExpired))
    assert mod.main() == 1
    assert "timeout" in capsys.readouterr().out
