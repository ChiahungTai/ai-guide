"""governance install.py verify probe 測試（AIR-116 S3——AC-3.3 negative 腿）。

oracle 獨立性：muse probe 判定語義對標 AIR-100 S-E monitor evaluate()
（已吸收——scripts/muse_approve_monitor.py 已退役），非待測實作自證；pipe probe 以真 hook subprocess 實跑＋
放行場景（exit 0）必報 FAIL 防恆綠。codex L1/L2/L3 live 驗收歸 AC-3.2/3.4
receipt（host-level fixture 需真 codex runtime，不入單元測試）。
"""

import json
import subprocess
from types import SimpleNamespace

from conftest import load_module

mod = load_module("governance/install.py")


def _muse_doc(status: str, cap_id: str = "memory-inbox") -> str:
    return json.dumps({
        "runtime_capabilities": [
            {"candidate": {"capability_id": cap_id}, "status": status}
        ]
    })


def _patch_run(monkeypatch, *, returncode=0, stdout="", stderr=""):
    fake = SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    calls = []
    monkeypatch.setattr(mod, "subprocess",
                        SimpleNamespace(run=lambda *a, **k: (calls.append((a, k)), fake)[1]))
    return calls


# ── muse probe（AC-3.3：mock 非 trusted → FAIL）──────────────────


def test_muse_probe_pass_all_trusted(monkeypatch):
    _patch_run(monkeypatch, stdout=_muse_doc("trusted_enabled"))
    assert mod.probe_muse("muse-memory-governance")[0] == "PASS"


def test_muse_probe_non_trusted_is_fail(monkeypatch):
    _patch_run(monkeypatch, stdout=_muse_doc("trusted_disabled"))
    status, detail = mod.probe_muse("muse-memory-governance")
    assert status == "FAIL"
    assert "re-approve" in detail


def test_muse_probe_modified_status_is_fail(monkeypatch):
    _patch_run(monkeypatch, stdout=_muse_doc("modified"))
    assert mod.probe_muse("muse-memory-governance")[0] == "FAIL"


def test_muse_probe_empty_capabilities_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout=json.dumps({"runtime_capabilities": []}))
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_missing_key_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout=json.dumps({"record": {}}))
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_bad_json_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout="not-json")
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_non_dict_payload_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout='[1, 2]')
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_inspect_nonzero_is_fail(monkeypatch):
    _patch_run(monkeypatch, returncode=1, stderr="boom")
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_cli_missing_is_guard(monkeypatch):
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    assert mod.probe_muse("x")[0] == "GUARD"


# ── pipe payload probe（真 hook 實跑＋放行場景必 FAIL 防恆綠）────────


def test_pipe_payload_probe_real_hook_pass():
    status, _ = mod.probe_pipe_payload("hooks/block-memory-index-write.py")
    assert status == "PASS"


def test_pipe_payload_probe_missing_script_is_guard():
    assert mod.probe_pipe_payload("hooks/__no_such_hook__.py")[0] == "GUARD"


def test_pipe_payload_probe_hook_allow_is_fail(monkeypatch):
    """hook 放行（exit 0）時 probe 必報 FAIL——probe 對恆綠免疫的自我驗證。"""

    def fake_run(*a, **k):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=fake_run))
    status, detail = mod.probe_pipe_payload("hooks/block-memory-index-write.py")
    assert status == "FAIL"
    assert "0" in detail


def test_pipe_payload_probe_timeout_is_fail(monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="hook", timeout=30)

    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=fake_run, TimeoutExpired=subprocess.TimeoutExpired))
    assert mod.probe_pipe_payload("hooks/block-memory-index-write.py")[0] == "FAIL"


# ── codex mixed-rep 掃描（codex ⑦——TC-10 P10-2 報告腿）──────────────


def _group(event: str, matcher: str, script: str) -> str:
    return (f"[[hooks.{event}]]\nmatcher = \"{matcher}\"\n\n"
            f"[[hooks.{event}.hooks]]\ntype = \"command\"\n"
            f"command = \"python3 /Users/x/ai-guide/hooks/{script}\"\n\n")


def test_mixed_rep_duplicate_inline_group_warns():
    live = _group("PreToolUse", "apply_patch", "codex_memory_path_deny.py") * 2
    warnings = mod.codex_mixed_rep_warnings(live, codex_home=None)
    assert any("重複 inline group" in w for w in warnings)


def test_mixed_rep_hooks_json_copy_warns(tmp_path):
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "hooks.json").write_text("{}")
    warnings = mod.codex_mixed_rep_warnings(_group("Stop", "", "stop-notification.sh"),
                                            codex_home=tmp_path)
    assert any("hooks.json copy" in w for w in warnings)


def test_mixed_rep_clean_config_no_warnings(tmp_path):
    (tmp_path / ".codex").mkdir()  # 無 hooks.json
    live = _group("PreToolUse", "apply_patch", "codex_memory_path_deny.py")
    assert mod.codex_mixed_rep_warnings(live, codex_home=tmp_path) == []


# ── codex L2 trust 診斷（HANDLER_HEADER MULTILINE 回歸守衛——
#    缺旗標時 handlers 恆 0、診斷整段消失，live verify 首跑實證）────────


def _codex_toml_with_state(state_key: str) -> tuple[str, str]:
    template = _group("PreToolUse", "apply_patch", "codex_memory_path_deny.py")
    live = ('[hooks.state]\n'
            f'"{state_key}" = "sha256:abc"\n\n' + template)
    return live, template


def test_codex_trust_diagnostics_reports_trusted():
    key = f"{mod.Path.home()}/.codex/config.toml:pre_tool_use:0:0"
    live, tmpl = _codex_toml_with_state(key)
    lines = mod.codex_trust_diagnostics(live, tmpl)
    assert len(lines) == 1
    assert "Trusted" in lines[0] and "pre_tool_use:0:0" in lines[0]


def test_codex_trust_diagnostics_reports_untrusted():
    key = "some-other-source:pre_tool_use:0:0"
    live, tmpl = _codex_toml_with_state(key)
    lines = mod.codex_trust_diagnostics(live, tmpl)
    assert len(lines) == 1
    assert "Untrusted" in lines[0]


def test_codex_trust_diagnostics_multi_handler_keys():
    merged = ('[[hooks.PreToolUse]]\nmatcher = "Bash"\n\n'
              '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
              'command = "python3 /Users/x/ai-guide/hooks/block-python-c-comment.py"\n\n'
              '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
              'command = "python3 /Users/x/ai-guide/hooks/block-python-file-write.py"\n\n')
    live = '[hooks.state]\n\n' + merged
    lines = mod.codex_trust_diagnostics(live, merged)
    assert len(lines) == 2
    assert "pre_tool_use:0:0" in lines[0]
    assert "pre_tool_use:0:1" in lines[1]
    assert all("Untrusted" in ln for ln in lines)


def test_probe_codex_cli_absent_guard_with_l1(tmp_path, monkeypatch):
    """launchd PATH 無 codex 場（live 實證）：GUARD 非 crash，L1 仍如實報告。"""
    tmpl = mod.render((mod.MANIFEST_PATH.parent / "registrations/codex.toml").read_text())
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n" + tmpl)
    manifest = {"registrations": {"codex": {"target": str(target),
                                            "template": "registrations/codex.toml"}}}
    monkeypatch.setattr(mod.shutil, "which", lambda n: None)
    status, _detail, lines = mod.probe_codex(manifest)
    assert status == "GUARD"
    assert any("[L1] 在場" in ln for ln in lines)
    assert any("[L3] GUARD" in ln for ln in lines)


# ── cmd_verify surface 映射與退出碼 ────────────────────────────────


def test_cmd_verify_no_probe_surfaces_exit_ok():
    manifest = {"probes": {}}
    assert mod.cmd_verify(manifest, "rules") == mod.EXIT_OK
    assert mod.cmd_verify(manifest, "skills") == mod.EXIT_OK


def test_cmd_verify_missing_probe_def_is_fail():
    manifest = {"probes": {}}
    assert mod.cmd_verify(manifest, "memory") == mod.EXIT_DRIFT


def test_cmd_verify_monitor_stub_not_impl():
    assert mod.cmd_verify({}, "monitor") == mod.EXIT_NOT_IMPL
