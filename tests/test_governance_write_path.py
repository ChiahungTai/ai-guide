"""governance 寫入側覆蓋（AIR-116 post-build audit I2/I3/I4——EP AC-2.6 承諾腿）。

oracle 獨立性：apply_text_change 安全語義（dry-run chokepoint／toml 拒寫／
lost-update／僅變更備份）直接對 EP Q3 安全模型條文；merge_codex_text 對
group 級文字手術契約（identity 碰撞拒合併——1201 事故 bug C 的防線）；
journal 對 R2 中途 kill 回滾契約。
"""

import json

import pytest

from conftest import load_module

mod = load_module("governance/install.py")


# ── merge_codex_text：group 級文字手術（I2）──────────────────────


def _owned_group(matcher: str, script: str, timeout: int = 10) -> str:
    return ('[[hooks.PreToolUse]]\n'
            f'matcher = "{matcher}"\n\n'
            '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
            f'command = "python3 /Users/x/ai-guide/hooks/{script}"\n'
            f'timeout = {timeout}\n\n')


def test_merge_codex_appends_missing_group():
    tmpl = _owned_group("apply_patch", "codex_memory_path_deny.py")
    new_text, messages = mod.merge_codex_text("", tmpl, remove=False)
    assert "appended group" in " ".join(messages)
    assert tmpl in new_text


def test_merge_codex_updates_content_diff():
    tmpl = _owned_group("apply_patch", "codex_memory_path_deny.py", timeout=11)
    live = _owned_group("apply_patch", "codex_memory_path_deny.py", timeout=10)
    new_text, messages = mod.merge_codex_text(live, tmpl, remove=False)
    assert any("updated group" in m for m in messages)
    assert "timeout = 11" in new_text


def test_merge_codex_noop_when_identical():
    tmpl = _owned_group("apply_patch", "codex_memory_path_deny.py")
    new_text, messages = mod.merge_codex_text(tmpl, tmpl, remove=False)
    assert messages == []
    assert new_text == tmpl


def test_merge_codex_remove_strips_owned_group():
    tmpl = _owned_group("apply_patch", "codex_memory_path_deny.py")
    live = "# ai-guide memory path-deny\n" + tmpl
    new_text, messages = mod.merge_codex_text(live, tmpl, remove=True)
    assert any("removed group" in m for m in messages)
    assert "ai-guide" not in new_text  # 註解隨 group 搬移（不殘留）


def test_merge_codex_identity_collision_rejected():
    dup = _owned_group("apply_patch", "codex_memory_path_deny.py") * 2
    with pytest.raises(mod.GovernanceError, match="identity 碰撞"):
        mod.merge_codex_text("", dup, remove=False)


def test_merge_codex_leaves_other_family_untouched():
    tmpl = _owned_group("apply_patch", "codex_memory_path_deny.py")
    other = ('[[hooks.Interrupt]]\nmatcher = "chatgpt-web"\n\n'
             '[[hooks.Interrupt.hooks]]\ntype = "command"\ncommand = "/x/other"\n\n')
    new_text, _ = mod.merge_codex_text(other + tmpl, tmpl, remove=False)
    assert other in new_text  # 他 family group 原樣保留


# ── apply_text_change 安全語義（I3——EP AC-2.6）───────────────────


def test_apply_dry_run_chokepoint_raises(tmp_path, monkeypatch):
    target = tmp_path / "c.json"
    target.write_text("{}")
    monkeypatch.setattr(mod, "_DRY_RUN", True)
    with pytest.raises(mod.GovernanceError, match="dry-run"):
        mod.apply_text_change(target, '{"a": 1}\n')
    assert target.read_text() == "{}"  # 未寫入


def test_apply_toml_validate_rejects_malformed_live(tmp_path):
    target = tmp_path / "c.toml"
    target.write_text("not [valid toml")
    with pytest.raises(mod.GovernanceError, match="malformed"):
        mod.apply_text_change(target, "a = 1\n", toml_validate=True)
    assert target.read_text() == "not [valid toml"  # byte 不變


def test_apply_rejects_new_text_unparsable(tmp_path):
    target = tmp_path / "c.toml"
    target.write_text("a = 1\n")
    with pytest.raises(mod.GovernanceError, match="parse 驗證失敗"):
        mod.apply_text_change(target, "not [valid", toml_validate=True)
    assert target.read_text() == "a = 1\n"


def test_apply_lost_update_detected(tmp_path, monkeypatch):
    """併發寫入者模擬：backup 窗口期 live 被改（ZCode runtime 併發重寫——事故實證形）。"""
    target = tmp_path / "c.json"
    target.write_text('{"v": 1}\n')
    real_mutate = mod.backup_target

    def concurrent_writer(real):
        real.write_text('{"v": "concurrent"}\n')  # preimage 讀後、寫入前被改
        return real_mutate(real)

    monkeypatch.setattr(mod, "backup_target", concurrent_writer)
    with pytest.raises(mod.GovernanceError, match="lost-update"):
        mod.apply_text_change(target, '{"v": 2}\n')
    assert target.read_text() == '{"v": "concurrent"}\n'  # 非新內容（fail 未覆蓋）


def test_apply_backup_created_on_change(tmp_path):
    target = tmp_path / "c.json"
    target.write_text('{"v": 1}\n')
    assert mod.apply_text_change(target, '{"v": 2}\n') == "written"
    baks = list(tmp_path.glob("*.bak-*-gov"))
    assert len(baks) == 1 and json.loads(baks[0].read_text())["v"] == 1


def test_apply_noop_content_equal(tmp_path):
    target = tmp_path / "c.json"
    target.write_text('{"v": 1}\n')
    assert mod.apply_text_change(target, '{"v": 1}\n') == "noop"
    assert list(tmp_path.glob("*.bak-*")) == []  # R7：僅變更備份


# ── plan journal（I3——R2）────────────────────────────────────────


def test_journal_roundtrip_and_done_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path)
    jp = mod.journal_path("hooks")
    plan = {"ts": "t", "surface": "hooks", "mode": "install",
            "targets": [{"kind": "a"}, {"kind": "b"}]}
    mod.write_journal(jp, plan)
    mod.mark_done(jp, plan, 0)
    reloaded = json.loads(jp.read_text())
    assert reloaded["targets"][0].get("done") is True
    assert "done" not in reloaded["targets"][1]  # 未完成分野可辨


def test_journal_prune_keeps_recent(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "JOURNAL_DIR", tmp_path)
    for i in range(mod.JOURNAL_KEEP + 2):
        p = tmp_path / f"20260917-0000{i % 10}-s.json"
        p.write_text("{}")
        p.touch()
    mod._prune_glob(tmp_path, "*.json", mod.JOURNAL_KEEP)
    assert len(list(tmp_path.glob("*.json"))) == mod.JOURNAL_KEEP


# ── symlink 建立腿（I4——TC-12 P12-1/P12-2 單元化）────────────────


def test_symlink_target_create_and_idempotent(tmp_path):
    skills = tmp_path / "repo-skills"
    skills.mkdir()
    link = tmp_path / "cfg" / "skills"  # 父目錄不存在——建立路徑須自補
    t = {"kind": "symlink", "link": str(link), "target": str(skills), "action": "merge"}
    reg: dict = {}
    assert mod._apply_target(reg, t, "install") == "created"
    assert link.is_symlink() and link.resolve() == skills.resolve()  # P12-1
    assert mod._apply_target(reg, t, "install") == "noop"  # P12-2 冪等


def test_symlink_wrong_target_fail_loud(tmp_path):
    skills = tmp_path / "repo-skills"
    skills.mkdir()
    other = tmp_path / "elsewhere"
    other.mkdir()
    link = tmp_path / "skills"
    link.symlink_to(other)
    t = {"kind": "symlink", "link": str(link), "target": str(skills), "action": "merge"}
    with pytest.raises(mod.GovernanceError, match="指錯"):
        mod._apply_target({}, t, "install")


def test_symlink_uninstall_symmetric(tmp_path):
    skills = tmp_path / "repo-skills"
    skills.mkdir()
    link = tmp_path / "skills"
    link.symlink_to(skills)
    t = {"kind": "symlink", "link": str(link), "target": str(skills), "action": "remove"}
    assert mod._apply_target({}, t, "uninstall") == "removed"
    assert not link.exists()
    assert mod._apply_target({}, t, "uninstall") == "absent（冪等——nothing to remove）"
