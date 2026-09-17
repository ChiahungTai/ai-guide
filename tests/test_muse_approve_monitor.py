"""muse approve-drift monitor 契約測試（AIR-100 S-E——TC-7）。

muse governance plugin 每次 content update 後須重新 approve，否則 runtime 閘
靜默下線（fail-open 窗口）——monitor 對 `muse plugins inspect --json` 的
`runtime_capabilities[].status` 斷言 `trusted_enabled`；缺失/命令失敗一律
非零 exit＋告警行（fail-closed：查不到≠靜默綠）。

TC-7 以 mock inspect 輸出驅動判定函式（runner 注入），不動真 plugin；
真實 CLI 實跑（AC-E2）屬 L4 receipt，不在本檔。
"""

import json

import pytest
from conftest import load_module

_mod = load_module("scripts/muse_approve_monitor.py")


def _caps_doc(statuses: list[str]) -> dict:
    """構造 muse plugins inspect --json 的 runtime_capabilities 形狀（live 實測同構）。"""
    return {
        "runtime_capabilities": [
            {
                "candidate": {
                    "kind": "hook",
                    "plugin_id": "muse-memory-governance",
                    "capability_id": f"cap-{i}",
                    "stable_id": f"plugin:muse-memory-governance:hook:cap-{i}",
                },
                "status": s,
                "diagnostic": None,
            }
            for i, s in enumerate(statuses)
        ]
    }


class TestEvaluate:
    def test_trusted_enabled_passes(self):
        ok, _ = _mod.evaluate(_caps_doc(["trusted_enabled"]))
        assert ok

    def test_modified_fails(self):
        """TC-7 P7-1：update 後未重 approve＝modified——告警面。"""
        ok, reason = _mod.evaluate(_caps_doc(["modified"]))
        assert not ok
        assert "modified" in reason

    def test_empty_capabilities_fails(self):
        ok, _ = _mod.evaluate({"runtime_capabilities": []})
        assert not ok

    def test_missing_key_fails(self):
        ok, _ = _mod.evaluate({})
        assert not ok

    def test_partial_trusted_fails(self):
        """多 capability 任一非 trusted_enabled＝閘部分下線——fail-closed。"""
        ok, _ = _mod.evaluate(_caps_doc(["trusted_enabled", "modified"]))
        assert not ok

    def test_non_dict_payload_fails(self):
        ok, _ = _mod.evaluate("not-a-dict")
        assert not ok


class TestRunMonitor:
    def _runner_ok(self, cmd):
        assert "inspect" in cmd and "--json" in cmd
        return json.dumps(_caps_doc(["trusted_enabled"]))

    def test_trusted_exits_zero(self):
        code, lines = _mod.run_monitor("muse-memory-governance", runner=self._runner_ok)
        assert code == 0
        assert any("[OK]" in ln for ln in lines)

    def test_drift_alerts_and_exits_nonzero(self):
        """TC-7 P7-1：trusted_enabled 缺失 → 告警行＋非零 exit，不動真 plugin。"""

        def runner(cmd):
            return json.dumps(_caps_doc(["modified"]))

        code, lines = _mod.run_monitor("muse-memory-governance", runner=runner)
        assert code == 1
        joined = "\n".join(lines)
        assert "muse-approve-drift" in joined
        assert "approve" in joined

    def test_runner_failure_fails_closed(self):
        """命令失敗（muse 缺席/非零 exit）＝無法證明 trusted＝告警非靜默綠。"""

        def runner(cmd):
            raise RuntimeError("muse not found")

        code, lines = _mod.run_monitor("muse-memory-governance", runner=runner)
        assert code == 1
        assert any("muse-approve-drift" in ln for ln in lines)

    def test_invalid_json_fails_closed(self):
        def runner(cmd):
            return "not json {"

        code, _lines = _mod.run_monitor("muse-memory-governance", runner=runner)
        assert code == 1

    def test_default_runner_is_real_cli(self, monkeypatch):
        """F-10：預設 runner 行為斷言（取代 self-inspection）——以
        `["muse","plugins","inspect",<id>,"--json"]` 調用 subprocess.run（帶
        timeout＝F-15 錨點），真形 JSON → exit 0；monkeypatch 隔離，不真跑 CLI。"""
        from types import SimpleNamespace

        calls: list = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(_caps_doc(["trusted_enabled"])),
                stderr="",
            )

        monkeypatch.setattr(_mod.subprocess, "run", fake_run)
        code, lines = _mod.run_monitor("muse-memory-governance")
        assert code == 0
        assert any("[OK]" in ln for ln in lines)
        assert len(calls) == 1, f"預設 runner 應調用 subprocess.run 恰一次: {calls}"
        argv, kwargs = calls[0]
        assert argv == [
            "muse",
            "plugins",
            "inspect",
            "muse-memory-governance",
            "--json",
        ]
        assert kwargs.get("timeout") == 30, f"F-15 timeout 缺失: {kwargs}"


if __name__ == "__main__":
    pytest.main([__file__])
