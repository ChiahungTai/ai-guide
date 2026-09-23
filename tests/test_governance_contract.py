"""governance S6 契約與收尾測試（AC-6.2 對帳＋SM-14 前移警告）。

bootstrap 契約＝public contract（AIR-110 消費）：argv 面（CLI_SURFACES／
CLI_FLAGS／EXIT_* 常數）與 manifest 面（[bootstrap_cli]）逐項對帳——兩面
失同步即契約 drift，測試紅燈。
"""

import copy
import json
import shlex
import subprocess
import tomllib
from pathlib import Path

import pytest
from conftest import load_module

mod = load_module("governance/install.py")


@pytest.fixture(params=["plain", "space", "quotes", "hash"])
def codex_path_contract(request, tmp_path, monkeypatch):
    names = {
        "plain": ("repo", "python312"),
        "space": ("repo space", "python 312"),
        "quotes": ("repo 'single' and \"double\"", "python '312' \"managed\""),
        "hash": ("repo # literal", "python #312"),
    }
    repo_name, python_name = names[request.param]
    repo = Path("/virtual") / repo_name
    interpreter = str(Path("/virtual/runtime") / python_name / "bin" / "python3.12")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(repo): repo})
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", interpreter)
    manifest = mod.load_manifest()
    target = tmp_path / "config.toml"
    manifest["registrations"]["codex"]["target"] = str(target)
    template = manifest["registrations"]["codex"]["template"]
    raw = (mod.MANIFEST_PATH.parent / template).read_text()
    external = (
        "[[hooks.Stop]]\n\n[[hooks.Stop.hooks]]\n"
        'type = "command"\ncommand = "/vendor/external-stop"\n\n'
    )
    target.write_text("[hooks.state]\n\n" + external)
    action = {"kind": "toml-groups", "target": str(target), "template": template}
    return manifest, target, action, external, raw, repo, interpreter


def test_codex_quoted_paths_install_preserves_external(
    codex_path_contract, monkeypatch
):
    """S: IR1 ownership contract: same event/matcher never owns a vendor hook."""
    manifest, target, action, external, _raw, repo, interpreter = codex_path_contract
    mod._apply_target(manifest["registrations"], action, "install")
    installed = target.read_text()
    assert external in installed
    hooks = tomllib.loads(installed)["hooks"]
    assert len(hooks["Stop"]) == 2
    assert sum(len(v) for k, v in hooks.items() if k != "state") == 5
    for group in hooks["PreToolUse"]:
        for handler in group["hooks"]:
            argv = shlex.split(handler["command"])
            assert argv[0] == interpreter
            assert Path(argv[1]).parent == repo / "hooks"
    mod._apply_target(manifest["registrations"], action, "install")
    assert target.read_text() == installed
    drifts = []
    mod.check_codex_face(manifest, drifts, codex_home=target.parent)
    assert drifts == []
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", None)
    monkeypatch.setattr(mod, "resolve_hook_python", _boom_resolver)
    mod._apply_target(manifest["registrations"], action, "uninstall")
    remaining = target.read_text()
    assert external in remaining
    assert tomllib.loads(remaining)["hooks"] == {
        "state": {},
        "Stop": [{"hooks": [{"type": "command", "command": "/vendor/external-stop"}]}],
    }


def test_codex_quoted_paths_check_requires_owned_groups(codex_path_contract):
    """S: IR1 check parity: a vendor Stop cannot satisfy the package Stop."""
    manifest, target, _action, _external, _raw, _repo, _python = codex_path_contract
    drifts = []
    mod.check_codex_face(manifest, drifts, codex_home=target.parent)
    assert len(drifts) == 4
    assert all("缺 group" in message for _, message in drifts)


def test_codex_quoted_paths_uninstall_resolver_free(codex_path_contract, monkeypatch):
    """S: IR1 rollback: remove all four owned groups, preserve vendor bytes."""
    manifest, target, action, external, raw, _repo, _python = codex_path_contract
    installed = mod.render_codex(raw)
    target.write_text(target.read_text() + installed)
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", None)
    monkeypatch.setattr(mod, "resolve_hook_python", _boom_resolver)
    removal = mod.render_codex(raw, resolve_python=False)
    identities = [
        [mod._codex_group_identity(u["text"]) for u in mod.codex_group_units(text)[1]]
        for text in (installed, removal)
    ]
    assert identities[0] == identities[1]
    assert all(identity[2] for identity in identities[0])
    removed, _ = mod.merge_codex_text(installed, removal, remove=True)
    assert mod.codex_group_units(removed)[1] == []
    mod._apply_target(manifest["registrations"], action, "uninstall")
    remaining = target.read_text()
    assert external in remaining
    assert tomllib.loads(remaining)["hooks"] == {
        "state": {},
        "Stop": [{"hooks": [{"type": "command", "command": "/vendor/external-stop"}]}],
    }


@pytest.mark.parametrize(
    "command_kind",
    [
        "apostrophe",
        "hook-path",
        "heredoc",
        "invalid",
        "non-string",
        "data-arg",
        "midword-hash",
    ],
)
def test_codex_foreign_command_preserves_vendor(
    codex_path_contract, monkeypatch, command_kind
):
    """S: IR2 unknown foreign syntax/comments cannot block or establish ownership."""
    manifest, target, action, _external, _raw, repo, _python = codex_path_contract
    command = {
        "apostrophe": "printf ok # don't alter vendor configuration",
        "hook-path": f"printf ok # {shlex.quote(str(repo / 'hooks' / 'stop-notification.sh'))}",
        "heredoc": "cat <<'EOF'\ndon't\nEOF\n",
        "invalid": "printf 'unterminated",
        "non-string": 123,
        "data-arg": f"/vendor/external-stop {shlex.quote(str(repo / 'hooks' / 'stop-notification.sh'))}",
        "midword-hash": f"/vendor/external-stop {shlex.quote(str(repo / 'hooks' / 'stop-notification.sh'))}#documentation",
    }[command_kind]
    if isinstance(command, str):
        syntax = subprocess.run(
            ["/bin/sh", "-n", "-c", command],
            capture_output=True,
            text=True,
            check=False,
        )
        assert (syntax.returncode == 0) == (command_kind != "invalid"), syntax.stderr
    external = (
        "[[hooks.Stop]]\n\n[[hooks.Stop.hooks]]\n"
        f'type = "command"\ncommand = {json.dumps(command)}\n\n'
    )
    target.write_text("[hooks.state]\n\n" + external)
    assert mod._codex_group_identity(external)[2] == frozenset()
    drifts = []
    mod.check_codex_face(manifest, drifts, codex_home=target.parent)
    assert len(drifts) == 4 and all("缺 group" in message for _, message in drifts)
    mod._apply_target(manifest["registrations"], action, "install")
    installed = target.read_text()
    assert external in installed
    assert len(tomllib.loads(installed)["hooks"]["Stop"]) == 2
    mod._apply_target(manifest["registrations"], action, "install")
    assert target.read_text() == installed
    drifts = []
    mod.check_codex_face(manifest, drifts, codex_home=target.parent)
    assert drifts == []
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", None)
    monkeypatch.setattr(mod, "resolve_hook_python", _boom_resolver)
    mod._apply_target(manifest["registrations"], action, "uninstall")
    remaining = target.read_text()
    assert external in remaining
    assert tomllib.loads(remaining)["hooks"] == {
        "state": {},
        "Stop": [{"hooks": [{"type": "command", "command": command}]}],
    }


@pytest.mark.parametrize("remove", [False, True])
def test_codex_unrecognized_template_refuses_merge(remove):
    """S: IR2 an empty package identity cannot collide with an unowned vendor group."""
    external = (
        "[[hooks.Stop]]\n\n[[hooks.Stop.hooks]]\n"
        'type = "command"\ncommand = "/vendor/external-stop"\n'
    )
    with pytest.raises(mod.GovernanceError, match="模板.*ownership"):
        mod.merge_codex_text(external, external, remove=remove)


@pytest.mark.parametrize("defect", ["unrecognized", "duplicate"])
def test_codex_bad_template_rejected_by_check_and_apply(codex_path_contract, defect):
    """S: IR2 shared consumer gate: templates need nonempty, unique ownership."""
    manifest, target, action, external, raw, _repo, _python = codex_path_contract
    template = target.parent / "bad-template.toml"
    template.write_text(external if defect == "unrecognized" else raw * 2)
    manifest["registrations"]["codex"]["template"] = str(template)
    action = {**action, "template": str(template)}
    before = target.read_text()
    drifts = []
    mod.check_codex_face(manifest, drifts, codex_home=target.parent)
    assert len(drifts) == 1 and "模板" in drifts[0][1]
    for mode in ("install", "uninstall"):
        with pytest.raises(mod.GovernanceError, match="模板"):
            mod._apply_target(manifest["registrations"], action, mode)
        assert target.read_text() == before


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
    assert (
        mod.EXIT_OK,
        mod.EXIT_DRIFT,
        mod.EXIT_GUARD,
        mod.EXIT_NOT_IMPL,
        mod.EXIT_EXEC,
    ) == (0, 1, 2, 3, 4)


def test_contract_command_shape():
    bc = _bootstrap_cli()
    assert bc["command"] == "uv run python governance/install.py"


# ── 乾淨機器缺席語義（AC-6.3 fixture 實證三 bug 之回歸守衛）──────────


def test_json_install_absent_file_creates_from_template(tmp_path):
    target = tmp_path / "settings.json"
    m = {
        "registrations": {
            "cc": {
                "target": str(target),
                "template": "registrations/cc.json",
                "merge_root": "hooks",
                "target_is_symlink": False,
            }
        }
    }
    t = {
        "kind": "json-subtree:cc",
        "target": str(target),
        "template": "registrations/cc.json",
        "merge_root": "hooks",
        "action": "merge",
    }
    outcome = mod._apply_target(m["registrations"], t, "install")
    assert outcome == "written"
    doc = json.loads(target.read_text())
    assert "PreToolUse" in doc["hooks"]


def test_json_uninstall_absent_file_leaves(tmp_path):
    target = tmp_path / "nope.json"
    m = {
        "registrations": {
            "cc": {
                "target": str(target),
                "template": "registrations/cc.json",
                "merge_root": "hooks",
                "target_is_symlink": False,
            }
        }
    }
    t = {
        "kind": "json-subtree:cc",
        "target": str(target),
        "template": "registrations/cc.json",
        "merge_root": "hooks",
        "action": "remove",
    }
    assert (
        mod._apply_target(m["registrations"], t, "uninstall") == "not-present（leave）"
    )
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
        mod.apply_plan(
            {"registrations": {}}, {"surface": "x", "mode": "install", "targets": []}
        )


def test_verify_probe_set_mismatch_guard():
    """S-3：manifest 新增 probe 未排程 → fail-loud 非靜默跳過。"""
    manifest = {
        "probes": {
            "claude": {"type": "pipe-payload", "script": "x"},
            "zcode": {"type": "pipe-payload", "script": "x"},
            "muse": {"type": "muse-inspect", "plugin_id": "x"},
            "codex": {"type": "codex-three-layer"},
            "extra": {"type": "muse-inspect", "plugin_id": "x"},
        }
    }
    assert mod.cmd_verify(manifest, "all") == mod.EXIT_GUARD


# ── SM-14：uninstall positional 前移警告 ───────────────────────────


def _owned_group(matcher: str, script: str) -> str:
    return (
        "[[hooks.PreToolUse]]\n"
        f'matcher = "{matcher}"\n\n'
        '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
        f'command = "python3 /Users/x/ai-guide/hooks/{script}"\n\n'
    )


def test_positional_shift_warns_following_groups():
    template = _owned_group("apply_patch", "codex_memory_path_deny.py")
    other = (
        "[[hooks.PreToolUse]]\n"
        'matcher = "Bash"\n\n'
        '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
        'command = "/usr/bin/other-tool"\n\n'
    )
    live = "[hooks.state]\n\n" + template + other  # 非套件 group 在套件之後
    warnings = mod.codex_positional_shift_warnings(live, template)
    assert len(warnings) == 1
    assert "positional 前移" in warnings[0] and "re-approve" in warnings[0]
    assert "#0→#-1" not in warnings[0]  # 套件 group #0 移除後，後續 #1→#0


def test_positional_shift_no_warning_when_follower_precedes():
    template = _owned_group("apply_patch", "codex_memory_path_deny.py")
    other = (
        "[[hooks.PreToolUse]]\n"
        'matcher = "Bash"\n\n'
        '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
        'command = "/usr/bin/other-tool"\n\n'
    )
    live = "[hooks.state]\n\n" + other + template  # 非套件 group 在套件之前——不受前移
    assert mod.codex_positional_shift_warnings(live, template) == []


def test_positional_shift_clean_when_no_followers():
    template = _owned_group("apply_patch", "codex_memory_path_deny.py")
    live = "[hooks.state]\n\n" + template
    assert mod.codex_positional_shift_warnings(live, template) == []


def _boom_resolver():
    raise mod.GovernanceError(
        "找不到已安裝的 uv-managed Python 3.12。"
        "先執行 `uv python install 3.12` 後重跑 governance installer。"
    )


def test_hooks_uninstall_does_not_require_hook_python(tmp_path, monkeypatch):
    """C1: rollback identity (matcher+script) must not resolve the interpreter.

    CC/ZCode/Codex owned registrations uninstall cleanly with the resolver
    forced to raise; unrelated external groups survive byte-identical."""
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", "/virtual/runtime/bin/python3.12")
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    manifest = mod.load_manifest()
    reg = manifest["registrations"]
    rendered = {}
    for harness in ("cc", "zcode"):
        raw = (mod.MANIFEST_PATH.parent / reg[harness]["template"]).read_text()
        rendered[harness] = json.loads(mod.render(raw))
    codex_live = mod.render_codex(
        (mod.MANIFEST_PATH.parent / reg["codex"]["template"]).read_text()
    )
    ext_cc = {
        "matcher": "External",
        "hooks": [{"type": "command", "command": "/bin/echo hi"}],
    }
    rendered["cc"]["PreToolUse"].append(ext_cc)
    ext_zc = {
        "matcher": "External",
        "hooks": [
            {
                "type": "process",
                "command": "/bin/echo",
                "args": ["hi"],
                "timeoutMs": 1000,
            }
        ],
    }
    rendered["zcode"]["events"]["PreToolUse"].append(ext_zc)
    cc_target = tmp_path / "cc.json"
    cc_target.write_text(json.dumps({"hooks": rendered["cc"], "other": 1}))
    zc_target = tmp_path / "zc.json"
    zc_target.write_text(json.dumps({"hooks": rendered["zcode"]}))
    ext_cx = (
        '[[hooks.PreToolUse]]\nmatcher = "External"\n\n'
        '[[hooks.PreToolUse.hooks]]\ntype = "command"\ncommand = "/bin/echo hi"\n'
    )
    cx_target = tmp_path / "cx.toml"
    cx_target.write_text("[hooks.state]\n\n" + ext_cx + codex_live)
    # managed 3.12 gone at rollback time — resolver must not be consulted
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", None)
    monkeypatch.setattr(mod, "resolve_hook_python", lambda: _boom_resolver())
    for harness, target in (("cc", cc_target), ("zcode", zc_target)):
        t = {
            "kind": f"json-subtree:{harness}",
            "target": str(target),
            "template": reg[harness]["template"],
            "merge_root": "hooks",
            "action": "remove",
        }
        mod._apply_target(reg, t, "uninstall")
    t = {
        "kind": "toml-groups",
        "target": str(cx_target),
        "template": reg["codex"]["template"],
        "action": "remove",
    }
    mod._apply_target(reg, t, "uninstall")
    cc_live = json.loads(cc_target.read_text())
    assert cc_live["hooks"]["PreToolUse"] == [ext_cc]  # owned gone, external intact
    assert "Stop" not in cc_live["hooks"]  # emptied owned event pruned
    zc_live = json.loads(zc_target.read_text())
    assert zc_live["hooks"]["events"]["PreToolUse"] == [ext_zc]
    cx_text = cx_target.read_text()
    assert ext_cx in cx_text  # external group byte-identical
    for script in ("block-python-c-comment.py", "codex_memory_path_deny.py"):
        assert script not in cx_text  # owned groups removed


def test_zcode_user_prompt_submit_coexistence_round_trip(tmp_path, monkeypatch):
    """C6: external UserPromptSubmit group coexists with compact-restore.

    install preserves the external group and adds compact-restore; uninstall
    (resolver unavailable) removes only the compact group."""
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", "/virtual/runtime/bin/python3.12")
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    manifest = mod.load_manifest()
    reg = manifest["registrations"]
    external = {
        "matcher": "docs",
        "hooks": [
            {
                "type": "process",
                "command": "/usr/bin/docs-tool",
                "args": ["--check"],
                "timeoutMs": 5000,
            }
        ],
    }
    target = tmp_path / "config.json"
    target.write_text(
        json.dumps(
            {
                "hooks": {
                    "enabled": True,
                    "events": {"UserPromptSubmit": [copy.deepcopy(external)]},
                }
            }
        )
    )
    t = {
        "kind": "json-subtree:zcode",
        "target": str(target),
        "template": reg["zcode"]["template"],
        "merge_root": "hooks",
        "action": "merge",
    }
    mod._apply_target(reg, t, "install")
    groups = json.loads(target.read_text())["hooks"]["events"]["UserPromptSubmit"]
    assert external in groups  # external preserved
    assert sum("compact-restore-inject.py" in json.dumps(g) for g in groups) == 1
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", None)
    monkeypatch.setattr(mod, "resolve_hook_python", lambda: _boom_resolver())
    mod._apply_target(reg, {**t, "action": "remove"}, "uninstall")
    remaining = json.loads(target.read_text())["hooks"]["events"]["UserPromptSubmit"]
    assert remaining == [
        external
    ]  # only the compact group removed, semantically intact
