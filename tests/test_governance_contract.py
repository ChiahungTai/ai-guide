"""governance S6 契約與收尾測試（AC-6.2 對帳＋SM-14 前移警告）。

bootstrap 契約＝public contract（AIR-110 消費）：argv 面（CLI_SURFACES／
CLI_FLAGS／EXIT_* 常數）與 manifest 面（[bootstrap_cli]）逐項對帳——兩面
失同步即契約 drift，測試紅燈。
"""

import json
from pathlib import Path

import pytest

from conftest import load_module

mod = load_module("governance/install.py")


# ── AC-6.2：--help 面與 [bootstrap_cli] 投影逐項一致 ────────────────


def _bootstrap_cli() -> dict:
    return mod.load_manifest()["bootstrap_cli"]


def test_contract_surfaces_match():
    assert _bootstrap_cli()["surfaces"] == mod.CLI_SURFACES


def test_contract_flags_match():
    assert _bootstrap_cli()["flags"] == mod.CLI_FLAGS


def test_contract_exit_codes_match_constants():
    codes = _bootstrap_cli()["exit_codes"]
    assert set(codes) == {"0", "1", "2", "3", "4"}  # 鍵＝退出碼枚舉（值為語義描述）
    assert (mod.EXIT_OK, mod.EXIT_DRIFT, mod.EXIT_GUARD,
            mod.EXIT_NOT_IMPL, mod.EXIT_EXEC) == (0, 1, 2, 3, 4)


def test_contract_command_shape():
    bc = _bootstrap_cli()
    assert bc["command"] == "uv run python governance/install.py"


# ── 乾淨機器缺席語義（AC-6.3 fixture 實證三 bug 之回歸守衛）──────────


def test_json_install_absent_file_creates_from_template(tmp_path):
    target = tmp_path / "settings.json"
    m = {"registrations": {"cc": {
        "target": str(target), "template": "registrations/cc.json",
        "merge_root": "hooks", "target_is_symlink": False}}}
    t = {"kind": "json-subtree:cc", "target": str(target),
         "template": "registrations/cc.json", "merge_root": "hooks", "action": "merge"}
    outcome = mod._apply_target(m["registrations"], t, "install")
    assert outcome == "written"
    doc = json.loads(target.read_text())
    assert "PreToolUse" in doc["hooks"]


def test_json_uninstall_absent_file_leaves(tmp_path):
    target = tmp_path / "nope.json"
    m = {"registrations": {"cc": {
        "target": str(target), "template": "registrations/cc.json",
        "merge_root": "hooks", "target_is_symlink": False}}}
    t = {"kind": "json-subtree:cc", "target": str(target),
         "template": "registrations/cc.json", "merge_root": "hooks", "action": "remove"}
    assert mod._apply_target(m["registrations"], t, "uninstall") == "not-present（leave）"
    assert not target.exists()


def test_apply_text_change_absent_file_no_backup(tmp_path):
    target = tmp_path / "new.toml"
    assert mod.apply_text_change(target, "a = 1\n", toml_validate=True) == "written"
    assert target.read_text() == "a = 1\n"
    assert list(tmp_path.glob("*.bak-*")) == []  # 缺席檔無備份（僅變更備份語義）


# ── C-1：all-uninstall 反裝面完整性（review C-1——EP rollback 契約）──


def test_build_plan_uninstall_all_includes_muse_and_monitor():
    manifest = mod.load_manifest()
    kinds = [t["kind"] for t in mod.build_plan(manifest, "all", "uninstall")["targets"]]
    assert "muse-disable" in kinds
    assert "launchd-plist" in kinds


def test_build_plan_install_all_excludes_monitor_and_muse_disable():
    """monitor＝顯式排程面（README bootstrap 步驟 7）；muse-disable 僅 uninstall 語義。"""
    manifest = mod.load_manifest()
    kinds = [t["kind"] for t in mod.build_plan(manifest, "all", "install")["targets"]]
    assert "muse-disable" not in kinds
    assert "launchd-plist" not in kinds


def test_apply_plan_dry_run_guard_covers_all_kinds(tmp_path, monkeypatch):
    """I-2：dry-run 斷言上移 plan 層——symlink/plist 面同受結構防線。"""
    monkeypatch.setattr(mod, "_DRY_RUN", True)
    with pytest.raises(mod.GovernanceError, match="第二層"):
        mod.apply_plan({"registrations": {}},
                       {"surface": "x", "mode": "install", "targets": []})


def test_verify_probe_set_mismatch_guard():
    """S-3：manifest 新增 probe 未排程 → fail-loud 非靜默跳過。"""
    manifest = {"probes": {"claude": {"type": "pipe-payload", "script": "x"},
                           "zcode": {"type": "pipe-payload", "script": "x"},
                           "muse": {"type": "muse-inspect", "plugin_id": "x"},
                           "codex": {"type": "codex-three-layer"},
                           "extra": {"type": "muse-inspect", "plugin_id": "x"}}}
    assert mod.cmd_verify(manifest, "all") == mod.EXIT_GUARD


# ── SM-14：uninstall positional 前移警告 ───────────────────────────


def _owned_group(matcher: str, script: str) -> str:
    return ('[[hooks.PreToolUse]]\n'
            f'matcher = "{matcher}"\n\n'
            '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
            f'command = "python3 /Users/x/ai-guide/hooks/{script}"\n\n')


def test_positional_shift_warns_following_groups():
    template = _owned_group("apply_patch", "codex_memory_path_deny.py")
    other = ('[[hooks.PreToolUse]]\n'
             'matcher = "Bash"\n\n'
             '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
             'command = "/usr/bin/other-tool"\n\n')
    live = "[hooks.state]\n\n" + template + other  # 非套件 group 在套件之後
    warnings = mod.codex_positional_shift_warnings(live, template)
    assert len(warnings) == 1
    assert "positional 前移" in warnings[0] and "re-approve" in warnings[0]
    assert "#0→#-1" not in warnings[0]  # 套件 group #0 移除後，後續 #1→#0


def test_positional_shift_no_warning_when_follower_precedes():
    template = _owned_group("apply_patch", "codex_memory_path_deny.py")
    other = ('[[hooks.PreToolUse]]\n'
             'matcher = "Bash"\n\n'
             '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
             'command = "/usr/bin/other-tool"\n\n')
    live = "[hooks.state]\n\n" + other + template  # 非套件 group 在套件之前——不受前移
    assert mod.codex_positional_shift_warnings(live, template) == []


def test_positional_shift_clean_when_no_followers():
    template = _owned_group("apply_patch", "codex_memory_path_deny.py")
    live = "[hooks.state]\n\n" + template
    assert mod.codex_positional_shift_warnings(live, template) == []
