"""governance F1/F2 回歸（AIR-178 深審 findings；AIR-174 批次二）。

F1 面獨立契約：install.py:1060 注釋「面與面獨立——單面失敗照常安裝其他面，
結束以最壞 rc 彙整報告」必須由行為兌現——任一面 GovernanceError 收進
face_failures 彙整（非 abort），總 exit EXIT_EXEC。

F2 fail-loud 契約：邊界例外（FileNotFoundError／JSONDecodeError／
TOMLDecodeError／KeyError／非 dict 子樹）收斂進 GovernanceError
（main 既有 mapping → EXIT_EXEC(4)），禁裸 traceback。
"""

import sys
from types import SimpleNamespace

import pytest
from conftest import load_module

mod = load_module("governance/install.py")


def _probe(hooks_rc: int = 1):
    """fake subprocess.run：hooksPath 探針回 hooks_rc；其餘（muse 等）回 0。"""

    def _run(argv, *a, **k):
        if any("hooksPath" in str(a) for a in argv):
            return SimpleNamespace(returncode=hooks_rc, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return _run


def _all_face_manifest() -> dict:
    return {
        "surfaces": {
            "rules": {"argv": ["wrap-rules"]},
            "agents": {"argv": ["wrap-agents"]},
            "memory": {"plugin_path": "p", "plugin_id": "x", "pool_setup": "s"},
        },
        "registrations": {"cc": {}, "zcode": {}, "codex": {}},
    }


# ── F1：面獨立——單面失敗照常裝其他面＋彙整 ──────────────────────────


def test_f1_memory_face_failure_does_not_block_other_faces(
    tmp_path, monkeypatch, capsys
):
    """memory 面 _require_muse_cli raise 不得 abort skills/rules/agents 面。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path / "journal")
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_probe()))
    wrapped: list[str] = []
    monkeypatch.setattr(
        mod, "run_wrap", lambda argv, extra=None: wrapped.append(argv[0]) or 0
    )
    plans: list[str] = []

    def fake_apply(manifest, plan, *, journal=True):
        plans.append(plan["surface"])
        return mod.EXIT_OK

    monkeypatch.setattr(mod, "apply_plan", fake_apply)
    monkeypatch.setattr(
        mod,
        "build_plan",
        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []},
    )
    rc = mod.cmd_install_uninstall(_all_face_manifest(), "all", "install")
    assert rc == mod.EXIT_EXEC  # 失敗面進彙整＋非零總 exit
    assert wrapped == ["wrap-rules", "wrap-agents"]  # wrap 面照裝
    assert plans == ["skills", "all"]  # skills 面照裝＋hooks/all-plan 照跑
    err = capsys.readouterr().err
    assert "部分面失敗" in err and "memory" in err  # 失敗面進彙整


def test_f1_skills_face_failure_does_not_block_other_faces(
    tmp_path, monkeypatch, capsys
):
    """skills 面 apply_plan raise 不得 abort rules/agents/memory 面。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path / "journal")
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: "/fake/muse"))
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_probe()))
    wrapped: list[str] = []
    monkeypatch.setattr(
        mod, "run_wrap", lambda argv, extra=None: wrapped.append(argv[0]) or 0
    )
    plans: list[str] = []

    def fake_apply(manifest, plan, *, journal=True):
        if plan["surface"] == "skills":
            raise mod.GovernanceError("skills 面 boom")
        plans.append(plan["surface"])
        return mod.EXIT_OK

    monkeypatch.setattr(mod, "apply_plan", fake_apply)
    monkeypatch.setattr(
        mod,
        "build_plan",
        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []},
    )
    rc = mod.cmd_install_uninstall(_all_face_manifest(), "all", "install")
    assert rc == mod.EXIT_EXEC
    assert wrapped == ["wrap-rules", "wrap-agents"]  # rules/agents 照裝
    assert plans == ["all"]  # hooks/all-plan 照跑
    err = capsys.readouterr().err
    assert "部分面失敗" in err and "skills" in err
    assert "skills 面 boom" in err  # 原委在場（非靜默吞掉）


def test_f1_hooks_face_failure_still_prints_manual_steps(tmp_path, monkeypatch, capsys):
    """hooks 面（末段 apply_plan）raise 不得跳過 manual steps／彙整。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path / "journal")
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_probe()))

    def fake_apply(manifest, plan, *, journal=True):
        raise mod.GovernanceError("hooks 面 boom")

    monkeypatch.setattr(mod, "apply_plan", fake_apply)
    monkeypatch.setattr(
        mod,
        "build_plan",
        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []},
    )
    rc = mod.cmd_install_uninstall(_all_face_manifest(), "hooks", "install")
    assert rc == mod.EXIT_EXEC
    cap = capsys.readouterr()
    assert "手動步驟" in cap.out  # print_manual_steps 仍執行
    assert "部分面失敗" in cap.err and "hooks" in cap.err


def test_f1_uninstall_face_failure_returns_exec_not_swallowed(
    tmp_path, monkeypatch, capsys
):
    """uninstall 面失敗同契約——彙整後 EXIT_EXEC，不被 mode gate 吞成 EXIT_OK。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path / "journal")
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_probe()))

    def fake_apply(manifest, plan, *, journal=True):
        raise mod.GovernanceError("hooks 面 boom")

    monkeypatch.setattr(mod, "apply_plan", fake_apply)
    monkeypatch.setattr(
        mod,
        "build_plan",
        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []},
    )
    rc = mod.cmd_install_uninstall(_all_face_manifest(), "hooks", "uninstall")
    assert rc == mod.EXIT_EXEC
    assert "部分面失敗" in capsys.readouterr().err


# ── F2：邊界例外收斂 GovernanceError（EXIT_EXEC(4) 面，禁裸 traceback）──


def test_f2_run_wrap_missing_binary_converged(tmp_path, monkeypatch):
    """run_wrap 缺執行檔（uv 面）：FileNotFoundError → 乾淨 GovernanceError。"""
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    with pytest.raises(mod.GovernanceError, match="definitely-missing-cmd-xyz") as ei:
        mod.run_wrap(["definitely-missing-cmd-xyz"])
    assert "PATH" in str(ei.value)  # 可操作指引
    assert str(mod.JOURNAL_DIR) in str(ei.value)  # journal 指針


def test_f2_apply_target_broken_template_json_converged(tmp_path, monkeypatch):
    """render 後 json.loads 的 JSONDecodeError → GovernanceError（拒寫 fail-loud）。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    target = tmp_path / "settings.json"
    target.write_text('{"other": 1}')
    (tmp_path / "broken.json").write_text('{"hooks": ')
    t = {
        "kind": "json-subtree:cc",
        "target": str(target),
        "template": "broken.json",
        "merge_root": "hooks",
    }
    with pytest.raises(mod.GovernanceError, match="broken.json") as ei:
        mod._apply_target({}, t, "install")
    assert str(mod.JOURNAL_DIR) in str(ei.value)


def test_f2_merge_hooks_non_dict_subtree_converged():
    """live「hooks」子樹非 dict（hooks: false）→ GovernanceError，禁靜默覆寫。"""
    with pytest.raises(mod.GovernanceError, match="hooks"):
        mod.merge_json_hooks(
            {"hooks": False}, {"enabled": True, "events": {}}, "hooks", remove=False
        )


def test_f2_merge_hooks_non_list_event_groups_converged():
    """live event 條目非 list（setdefault 後 .append AttributeError 形）→ 收斂。"""
    with pytest.raises(mod.GovernanceError, match="Stop"):
        mod.merge_json_hooks(
            {"hooks": {"events": {"Stop": False}}},
            {"events": {"Stop": [{"matcher": "Bash", "hooks": []}]}},
            "hooks",
            remove=False,
        )


def test_f2_load_manifest_malformed_toml_converged(tmp_path, monkeypatch):
    """load_manifest 的 TOMLDecodeError → GovernanceError（非裸 traceback）。"""
    bad = tmp_path / "manifest.toml"
    bad.write_text("keys = [unclosed")
    monkeypatch.setattr(mod, "MANIFEST_PATH", bad)
    with pytest.raises(mod.GovernanceError, match="manifest") as ei:
        mod.load_manifest()
    assert str(mod.JOURNAL_DIR) in str(ei.value)


def test_f2_build_plan_missing_registration_converged():
    """build_plan 的 reg[harness] KeyError → GovernanceError（含補齊指引）。"""
    with pytest.raises(mod.GovernanceError, match=r"registrations\.?\s*cc|cc"):
        mod.build_plan({"registrations": {}}, "hooks", "install")


def test_f2_check_json_face_broken_template_reports_drift(tmp_path, monkeypatch):
    """共用 helper 的 check 側：壞模板 → drift 清單（exit-1 契約），不 traceback。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    settings = tmp_path / "settings.json"
    settings.write_text('{"hooks": {}}')
    (tmp_path / "broken.json").write_text("{oops")
    manifest = {
        "registrations": {
            "cc": {
                "target": str(settings),
                "template": "broken.json",
                "merge_root": "hooks",
            }
        }
    }
    drifts: list[tuple[str, str]] = []
    mod.check_json_face(manifest, "cc", drifts)
    assert len(drifts) == 1
    assert "broken.json" in drifts[0][1]


def test_f2_missing_registration_exits_exec_not_traceback(
    tmp_path, monkeypatch, capsys
):
    """main 層整合：缺 registration → exit 4 乾淨訊息，非 KeyError traceback。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "load_manifest", lambda: {"registrations": {}})
    monkeypatch.setattr(sys, "argv", ["install.py", "--surface", "hooks"])
    rc = mod.main()
    assert rc == mod.EXIT_EXEC
    err = capsys.readouterr().err
    assert "FAIL" in err
    assert "cc" in err
    assert "Traceback" not in err


def test_f2_main_load_manifest_failure_exits_exec(tmp_path, monkeypatch, capsys):
    """main 層整合：load_manifest 在 try 內——損壞 manifest → exit 4 非 traceback。"""
    bad = tmp_path / "manifest.toml"
    bad.write_text("keys = [unclosed")
    monkeypatch.setattr(mod, "MANIFEST_PATH", bad)
    monkeypatch.setattr(sys, "argv", ["install.py", "--surface", "rules"])
    rc = mod.main()
    assert rc == mod.EXIT_EXEC
    err = capsys.readouterr().err
    assert "FAIL" in err and "manifest" in err
    assert str(mod.JOURNAL_DIR) in err  # journal 指針在場
    assert "Traceback" not in err
