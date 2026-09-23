"""AIR-181 批次三回歸（F-A／F-E／F7／F4／F6／F3／F5）。

批次三＝install.py 錯誤契約收尾批（muse/codex 討論共識落地）：
- F-A：manifest 缺席／surfaces+registrations 其餘 KeyError 家族／模板檔缺席
  → _exec_error（EXIT_EXEC(4)；build_plan/check 面不帶 journal 指針）
- F-E：apply_plan 契約＝回 EXIT_OK 或 raise，永不回非零（dead code 清除）
- F7：缺 uv 訊息補安裝指引；F4：journal 檔名加 pid（防同秒互覆）
- F6：codex per-unit parse 收斂＋縮排 header 立約（守衛）＋byte-parity
- F3：codex 面殘留掃描（套件腳本現身非模板 group → drift）
- F5：sudo/HOME 守衛（euid=0 且 HOME→/root 時寫入面 fail-loud EXIT_GUARD）
"""

import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import load_module

mod = load_module("governance/install.py")


def _codex_live(template_text: str, state_key: str | None = None) -> str:
    state = "[hooks.state]\n" + (f'"{state_key}" = "sha256:x"\n' if state_key else "\n")
    return state + "\n" + template_text


def _codex_manifest(target: Path) -> dict:
    return {
        "registrations": {
            "codex": {"target": str(target), "template": "registrations/codex.toml"}
        }
    }


def _rendered_codex_template() -> str:
    return mod.render((mod.MANIFEST_PATH.parent / "registrations/codex.toml").read_text())


# ── 批 1 F-A：殘留 lookup 失敗收斂 _exec_error（EXIT_EXEC 面）────────


def test_fa_load_manifest_missing_file_converged(tmp_path, monkeypatch):
    """load_manifest 檔缺席（先前裸 FileNotFoundError）→ 乾淨 GovernanceError。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "nope.toml")
    with pytest.raises(mod.GovernanceError, match="缺席") as ei:
        mod.load_manifest()
    assert "manifest" in str(ei.value)
    assert str(mod.JOURNAL_DIR) in str(ei.value)  # load 面（批次二同款）帶指針


def test_fa_build_plan_missing_surfaces_skills_converged():
    """build_plan skills 面 surfaces.skills KeyError → GovernanceError（無 journal 指針）。"""
    with pytest.raises(mod.GovernanceError, match="skills") as ei:
        mod.build_plan({"registrations": {}}, "skills", "install")
    assert "surfaces.skills" in str(ei.value)
    assert str(mod.JOURNAL_DIR) not in str(ei.value)  # build_plan 階段 journal 未寫


def test_fa_build_plan_missing_symlink_fields_converged():
    """symlinks 條目缺 link/target 欄位 → 同家族收斂。"""
    manifest = {"surfaces": {"skills": {"symlinks": [{"target": "x"}]}}}
    with pytest.raises(mod.GovernanceError, match="link") as ei:
        mod.build_plan(manifest, "skills", "install")
    assert str(mod.JOURNAL_DIR) not in str(ei.value)


def test_fa_build_plan_missing_surfaces_monitor_converged():
    """build_plan monitor 面 surfaces.monitor KeyError → GovernanceError。"""
    with pytest.raises(mod.GovernanceError, match="monitor") as ei:
        mod.build_plan({"registrations": {}}, "monitor", "install")
    assert "surfaces.monitor" in str(ei.value)
    assert str(mod.JOURNAL_DIR) not in str(ei.value)


def test_fa_check_json_face_missing_registration_converged():
    """check_json_face 的 registrations[harness] KeyError → GovernanceError。"""
    drifts: list[tuple[str, str]] = []
    with pytest.raises(mod.GovernanceError, match=r"registrations.*cc") as ei:
        mod.check_json_face({"registrations": {}}, "cc", drifts)
    assert str(mod.JOURNAL_DIR) not in str(ei.value)  # check 面不帶 journal 噪音


def test_fa_check_codex_face_missing_registration_converged():
    """check_codex_face 的 registrations['codex'] KeyError → GovernanceError。"""
    drifts: list[tuple[str, str]] = []
    with pytest.raises(mod.GovernanceError, match="codex"):
        mod.check_codex_face({"registrations": {}}, drifts)


def test_fa_apply_target_missing_template_json_converged(tmp_path, monkeypatch):
    """json 面 apply 時模板檔缺席 → GovernanceError（含模板名＋journal 指針）。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    target = tmp_path / "settings.json"
    target.write_text('{"other": 1}')
    t = {
        "kind": "json-subtree:cc",
        "target": str(target),
        "template": "missing-template.json",
        "merge_root": "hooks",
    }
    with pytest.raises(mod.GovernanceError, match="missing-template.json") as ei:
        mod._apply_target({}, t, "install")
    assert str(mod.JOURNAL_DIR) in str(ei.value)  # apply 面 journal 已寫本次 entry


def test_fa_apply_target_missing_template_codex_converged(tmp_path, monkeypatch):
    """codex 面 apply 時模板檔缺席 → 同家族收斂。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n")
    t = {"kind": "toml-groups", "target": str(target), "template": "missing-template.toml"}
    with pytest.raises(mod.GovernanceError, match="missing-template.toml"):
        mod._apply_target({}, t, "install")


def test_fa_check_json_face_missing_template_reports_drift(tmp_path, monkeypatch):
    """check 面模板缺席 → drift（exit-1 契約），非 FileNotFoundError traceback。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    settings = tmp_path / "settings.json"
    settings.write_text('{"hooks": {}}')
    manifest = {
        "registrations": {
            "cc": {
                "target": str(settings),
                "template": "missing-template.json",
                "merge_root": "hooks",
            }
        }
    }
    drifts: list[tuple[str, str]] = []
    mod.check_json_face(manifest, "cc", drifts)
    assert len(drifts) == 1
    assert "missing-template.json" in drifts[0][1]


def test_fa_check_codex_face_missing_template_reports_drift(tmp_path, monkeypatch):
    """check codex 面模板缺席 → drift（措辭不再誤稱 resolver 失敗）。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    target = tmp_path / "config.toml"
    target.write_text(_codex_live("[[hooks.Stop]]\n\n[[hooks.Stop.hooks]]\n"))
    manifest = {
        "registrations": {
            "codex": {"target": str(target), "template": "missing-template.toml"}
        }
    }
    drifts: list[tuple[str, str]] = []
    mod.check_codex_face(manifest, drifts, codex_home=tmp_path)
    assert len(drifts) == 1
    assert "missing-template.toml" in drifts[0][1]
    assert "缺席" in drifts[0][1]


def test_fa_probe_codex_missing_template_converged(tmp_path, monkeypatch):
    """--verify codex probe 模板缺席 → GovernanceError（非裸 FileNotFoundError）。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n")
    manifest = {
        "registrations": {
            "codex": {"target": str(target), "template": "missing-template.toml"}
        }
    }
    with pytest.raises(mod.GovernanceError, match="missing-template.toml"):
        mod.probe_codex(manifest)


# ── 批 1 F-E：apply_plan 契約＝回 EXIT_OK 或 raise，永不回非零 ────────


def test_fe_apply_plan_contract_returns_ok_or_raises(tmp_path, monkeypatch):
    """target 級失敗 → raise（不回非零）；全部成功 → EXIT_OK。"""
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path / "journal")
    calls: list[str] = []

    def fake_target(reg, t, mode):
        calls.append(t["name"])
        if t["name"] == "boom":
            raise mod.GovernanceError("target boom")
        return "written"

    monkeypatch.setattr(mod, "_apply_target", fake_target)
    ok_plan = {
        "surface": "hooks",
        "mode": "install",
        "targets": [{"name": "a", "kind": "fake"}, {"name": "b", "kind": "fake"}],
    }
    assert mod.apply_plan({}, ok_plan) == mod.EXIT_OK
    boom_plan = {
        "surface": "hooks",
        "mode": "install",
        "targets": [
            {"name": "a", "kind": "fake"},
            {"name": "boom", "kind": "fake"},
            {"name": "never-reached", "kind": "fake"},
        ],
    }
    with pytest.raises(mod.GovernanceError, match="target boom"):
        mod.apply_plan({}, boom_plan)
    assert calls == ["a", "b", "a", "boom"]  # 失敗即停——後續 target 不執行


# ── 批 2 F7／F4：缺 uv 指引＋journal pid ─────────────────────────────


def test_f7_missing_uv_message_has_install_guidance(monkeypatch):
    """缺 uv 訊息須含可操作的安裝指引（curl 安裝行），不只說「先安裝 uv」。"""
    monkeypatch.setattr(mod, "_HOOK_PYTHON_CACHE", None)
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    with pytest.raises(mod.GovernanceError) as ei:
        mod.resolve_hook_python()
    msg = str(ei.value)
    assert "astral.sh/uv/install.sh" in msg  # 安裝指引一行
    assert "uv python install 3.12" in msg  # 既有指引保留（批次前測試釘住）


def test_f4_journal_filename_carries_pid(tmp_path, monkeypatch):
    """journal 檔名加 pid——同秒雙 run 不互覆（仿 backup_target 形態）。"""
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path)
    jp = mod.journal_path("hooks")
    assert f"-{os.getpid()}-" in jp.name
    assert jp.name.endswith("-hooks.json")
    assert re.fullmatch(r"\d{8}-\d{6}-\d+-hooks\.json", jp.name)  # ts 前綴契約不變
    other = mod.journal_path("rules")
    assert other != jp  # 同秒不同面不互覆


# ── 批 3 F6：per-unit parse 收斂＋縮排 header 立約＋byte-parity ───────


def test_f6_malformed_group_unit_converged():
    """group unit TOML 壞 → GovernanceError（非裸 TOMLDecodeError）。"""
    with pytest.raises(mod.GovernanceError, match="不可解析"):
        mod._codex_group_identity("[[hooks.PreToolUse]]\nbroken = [unclosed\n")


def test_f6_group_unit_missing_hooks_structure_converged():
    """group unit 缺 hooks 結構（無 header／bare key）→ 收斂，非裸 KeyError。"""
    with pytest.raises(mod.GovernanceError, match="缺 hooks 結構"):
        mod._codex_group_identity('matcher = "x"\n')


def test_f6_indented_header_refused():
    """縮排（非 column-0）的 [[hooks.*]] header → 守衛 fail-loud 拒解析。"""
    with pytest.raises(mod.GovernanceError, match="縮排") as ei:
        mod.codex_group_units("x = 1\n\n  [[hooks.Stop]]\nmatcher = \"\"\n")
    assert "column-0" in str(ei.value)


def test_f6_group_units_roundtrip_byte_parity():
    """byte-parity：單位切分重組須逐字還原（禁重排）——模板＋混合 live 兩形。"""
    raw = (mod.MANIFEST_PATH.parent / "registrations/codex.toml").read_text()
    mixed = "[hooks.state]\n\n[projects.\"p\"]\nkey = 1\n\n" + raw + "\n[preamble-after]\nz = 2\n"
    for text in (raw, mixed):
        preamble, units = mod.codex_group_units(text)
        assert preamble + "".join(u["text"] for u in units) == text


def test_f6_check_codex_face_broken_template_group_reports_drift(tmp_path, monkeypatch):
    """模板 group 壞 TOML → check 面 drift（exit-1 契約），非裸 TOMLDecodeError。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n")
    (tmp_path / "broken-template.toml").write_text(
        "[[hooks.PreToolUse]]\nbroken = [unclosed\n"
    )
    manifest = {
        "registrations": {
            "codex": {"target": str(target), "template": "broken-template.toml"}
        }
    }
    drifts: list[tuple[str, str]] = []
    mod.check_codex_face(manifest, drifts, codex_home=tmp_path)
    assert len(drifts) == 1
    assert "不可解析" in drifts[0][1]
    # F-2（judge 修正輪）：check 面 drift 訊息不帶 journal 指針
    assert str(mod.JOURNAL_DIR) not in drifts[0][1]


# ── 批 4 F3：codex 面殘留掃描（套件腳本現身非模板 group → drift）──────


def test_f3_codex_residual_package_scripts_reported(tmp_path):
    """identity 不符的 live group 含套件腳本 → 「多條目」drift（先前靜默忽略）。"""
    t = _rendered_codex_template()
    residual = (
        "[[hooks.PreToolUse]]\n"
        "matcher = \"WebSearch\"\n"
        "\n"
        "[[hooks.PreToolUse.hooks]]\n"
        "type = \"command\"\n"
        f"command = \"{mod._canonical_root()}/hooks/block-python-c-comment.py\"\n"
        "timeout = 10\n"
        "\n"
    )
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(t) + residual)
    drifts: list[tuple[str, str]] = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    hits = [m for _, m in drifts if "多條目" in m]
    assert len(hits) == 1
    assert "WebSearch" in hits[0] and "block-python-c-comment.py" in hits[0]
    assert not any("缺 group" in m for _, m in drifts)  # 套件 group 本體仍在場


def test_f3_foreign_group_not_reported(tmp_path):
    """vendor group（腳本集空）→ 不報——誤報控制負例。"""
    t = _rendered_codex_template()
    vendor = (
        "[[hooks.Stop]]\n"
        "\n"
        "[[hooks.Stop.hooks]]\n"
        "type = \"command\"\n"
        "command = \"/vendor/external-stop\"\n"
        "\n"
    )
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(t) + vendor)
    drifts: list[tuple[str, str]] = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert drifts == []


# ── 批 4 F5：sudo/HOME 守衛（寫入面 fail-loud EXIT_GUARD）────────────


def test_f5_sudo_home_guard_unit(monkeypatch):
    """偵測形態（judge F-3 修正）：euid==0 直接擋（無 HOME 比對——macOS root 家
    目錄＝/var/root，HOME 比對不跨平台）；euid≠0 → None。"""
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setenv("HOME", "/var/root")  # macOS root 家目錄形態
    assert mod.sudo_home_guard() is not None
    monkeypatch.setenv("HOME", "/Users/someone")  # HOME 保留（sudo -E 形）仍擋
    assert mod.sudo_home_guard() is not None
    monkeypatch.setattr(mod.os, "geteuid", lambda: 501)
    monkeypatch.setenv("HOME", "/root")
    assert mod.sudo_home_guard() is None  # 非 root → 不擋


def test_f5_main_blocks_install_under_root_euid(monkeypatch, capsys):
    """main 層：euid=0（不論 HOME）時 install → EXIT_GUARD＋可操作訊息。"""
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setenv("HOME", "/Users/ctai")  # HOME 非 /root 也擋（euid 判準）
    monkeypatch.setattr(sys, "argv", ["install.py", "--surface", "hooks"])
    assert mod.main() == mod.EXIT_GUARD
    err = capsys.readouterr().err
    assert "euid=0" in err or "root" in err
    assert "Traceback" not in err


def test_f5_main_not_blocked_without_sudo(monkeypatch, capsys):
    """main 層：非 root（縱使 HOME=/root）→ 不擋（走正常流程）。"""
    monkeypatch.setattr(mod.os, "geteuid", lambda: 501)
    monkeypatch.setenv("HOME", "/root")

    def _stop():
        raise mod.GovernanceError("sentinel-stop")

    monkeypatch.setattr(mod, "load_manifest", _stop)
    monkeypatch.setattr(sys, "argv", ["install.py", "--surface", "hooks"])
    assert mod.main() == mod.EXIT_EXEC  # 流程抵達 load_manifest（guard 未攔）
    err = capsys.readouterr().err
    assert "sentinel-stop" in err
    assert "sudo" not in err


# ── judge 修正輪（approve-with-findings 82/100）───────────────────────


def test_f1r_live_codex_indented_header_reports_drift(tmp_path):
    """F-1：live config 縮排 header（合法 TOML 但守衛拒切）→ check 面 drift，
    非 GovernanceError 穿出（M3 exit-1 drift-list 契約；--surface all 剩餘 faces
    不被中斷）。"""
    t = _rendered_codex_template()
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(t) + '  [[hooks.Stop]]\nmatcher = ""\n')
    drifts: list[tuple[str, str]] = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    hits = [m for _, m in drifts if "不可解析" in m]
    assert len(hits) == 1
    assert "live" in hits[0]


def test_f2r_probe_and_identity_no_journal_pointer_in_check_face(
    tmp_path, monkeypatch
):
    """F-2：journal_hint 透傳——probe 面直呼 _codex_group_identity 可帶 False。"""
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "manifest.toml")
    with pytest.raises(mod.GovernanceError, match="不可解析") as ei:
        mod._codex_group_identity("[[hooks.PreToolUse]]\nbroken = [unclosed\n")
    assert str(mod.JOURNAL_DIR) in str(ei.value)  # 預設（merge/apply 面）帶指針
    with pytest.raises(mod.GovernanceError) as ei2:
        mod._codex_group_identity(
            "[[hooks.PreToolUse]]\nbroken = [unclosed\n", journal_hint=False
        )
    assert str(mod.JOURNAL_DIR) not in str(ei2.value)  # check/probe 面不帶
    with pytest.raises(mod.GovernanceError) as ei3:
        mod._codex_template_groups(
            "[[hooks.PreToolUse]]\nbroken = [unclosed\n", journal_hint=False
        )
    assert str(mod.JOURNAL_DIR) not in str(ei3.value)  # 經 gate 透傳


def test_f4a_probe_codex_missing_registration_converged(tmp_path):
    """F-4a：probe_codex 的 registrations['codex'] KeyError → GovernanceError。"""
    with pytest.raises(mod.GovernanceError, match="registrations"):
        mod.probe_codex({"registrations": {}})


def test_f4b_check_json_face_registration_missing_fields_converged(tmp_path):
    """F-4b：registration 缺 target/template 欄位 → GovernanceError（非裸 KeyError）。"""
    settings = tmp_path / "settings.json"
    settings.write_text('{"hooks": {}}')
    manifest = {
        "registrations": {"cc": {"target": str(settings), "merge_root": "hooks"}}
    }
    drifts: list[tuple[str, str]] = []
    with pytest.raises(mod.GovernanceError, match="欄位") as ei:
        mod.check_json_face(manifest, "cc", drifts)
    assert str(mod.JOURNAL_DIR) not in str(ei.value)


def test_f4b_check_codex_face_registration_missing_fields_converged(tmp_path):
    """F-4b：codex registration 缺欄位 → 同家族收斂。"""
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n")
    manifest = {"registrations": {"codex": {"target": str(target)}}}
    drifts: list[tuple[str, str]] = []
    with pytest.raises(mod.GovernanceError, match="欄位"):
        mod.check_codex_face(manifest, drifts, codex_home=tmp_path)


def test_f5r_type_escape_yields_empty_scripts_not_crash():
    """F-5：identity 對型別逃逸（hooks 非 list／handler 非 dict）→ scripts 空集
    （非 ownership 主張），非 AttributeError/TypeError。"""
    ident = mod._codex_group_identity('[[hooks.Stop]]\nhooks = ["plain-string"]\n')
    assert ident[2] == frozenset()
    ident2 = mod._codex_group_identity('[[hooks.Stop]]\nhooks = "not-a-list"\n')
    assert ident2[2] == frozenset()
