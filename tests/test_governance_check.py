"""governance install.py --check 五面 parity 測試（AIR-116 S4）。

fixture 腿：AC-4.2（缺/多/內容差條目）、AC-4.3（muse approve/hash 腿 mock）、
AC-4.4（codex Modified class＋mixed-rep）、AC-4.6（live config 缺席→drift 不
crash）。live 態驗收歸 AC-4.1/4.2/4.5 receipt（真 config mutation＋復原）。
"""

import copy
import json
import plistlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import load_module

mod = load_module("governance/install.py")


def _rendered(rel: str) -> str:
    return mod.render((mod.MANIFEST_PATH.parent / rel).read_text())


def _real_hooks_scripts() -> list[str]:
    import tomllib
    m = tomllib.loads((mod.MANIFEST_PATH.parent / "manifest.toml").read_text())
    return m["surfaces"]["hooks"]["scripts"]


def _cc_manifest(cc_target: Path) -> dict:
    return {"registrations": {"cc": {
        "target": str(cc_target), "template": "registrations/cc.json",
        "merge_root": "hooks", "target_is_symlink": False}}}


def _write(tmp_path: Path, name: str, obj) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    return p


# ── JSON 面（CC）──────────────────────────────────────────────────


def test_check_json_clean(tmp_path):
    tmpl = json.loads(_rendered("registrations/cc.json"))
    target = _write(tmp_path, "settings.json", {"hooks": tmpl, "other": {"keep": 1}})
    drifts: list = []
    mod.check_json_face(_cc_manifest(target), "cc", drifts)
    assert drifts == []


def test_check_json_missing_entry(tmp_path):
    tmpl = json.loads(_rendered("registrations/cc.json"))
    del tmpl["FileChanged"]
    target = _write(tmp_path, "settings.json", {"hooks": tmpl})
    drifts: list = []
    mod.check_json_face(_cc_manifest(target), "cc", drifts)
    assert any("缺條目" in m and "FileChanged" in m for _, m in drifts)


def test_check_json_content_diff(tmp_path):
    tmpl = json.loads(_rendered("registrations/cc.json"))
    tmpl["PreToolUse"][1]["hooks"][0]["timeout"] = 11
    target = _write(tmp_path, "settings.json", {"hooks": tmpl})
    drifts: list = []
    mod.check_json_face(_cc_manifest(target), "cc", drifts)
    assert any("內容差" in m and "PreToolUse" in m for _, m in drifts)


def test_check_json_extra_package_group(tmp_path):
    tmpl = json.loads(_rendered("registrations/cc.json"))
    extra = copy.deepcopy(tmpl["PreToolUse"][1])
    extra["matcher"] = "Write"  # 同套件腳本、異 identity＝重複/變體 copy
    tmpl["PreToolUse"].append(extra)
    target = _write(tmp_path, "settings.json", {"hooks": tmpl})
    drifts: list = []
    mod.check_json_face(_cc_manifest(target), "cc", drifts)
    assert any("多條目" in m for _, m in drifts)


def test_check_json_missing_subtree(tmp_path):
    target = _write(tmp_path, "settings.json", {"env": {}})
    drifts: list = []
    mod.check_json_face(_cc_manifest(target), "cc", drifts)
    assert any("子樹缺席" in m for _, m in drifts)


def test_codex_group_identity_follows_repo_root(tmp_path, monkeypatch):
    """codex 面同步腿（雙根版）：`_codex_group_identity` 與 `_group_scripts`
    共用 `_hook_path_pattern()`（canonical＋本 checkout 雙根——0918 合併
    裁決後單一定義源，air-110 單根實作已退役）。"""
    repo = tmp_path / "checkout-not-named-ai-guide"
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(repo): repo})
    monkeypatch.setattr(mod, "_HOOK_PATTERN_CACHE", {})
    text = (f'[[hooks.Stop]]\nmatcher = ""\n[[hooks.Stop.hooks]]\n'
            f'type = "command"\ncommand = "python3 {repo}/hooks/post-build-gate.py"\n')
    assert mod._codex_group_identity(text) == ("Stop", "", frozenset({"post-build-gate.py"}))


def test_group_scripts_identity_diverges_across_checkouts(tmp_path, monkeypatch):
    """R2 item8（muse F-1）：多 checkout 語義——同一 config group 在兩個 REPO_ROOT
    下 identity 認知分叉（A 的套件腳本＝B 的外來腳本）：每個 checkout 只認自己
    hooks/ 路徑。這是 bootstrap preflight canonical-checkout FAIL 守衛（codex#8）
    的根據——card WT 安裝會在共享 home config 留重複 group。"""
    repo_a = tmp_path / "ai-guide"
    repo_b = tmp_path / "ai-guide-air-999"
    group = {"matcher": "", "hooks": [
        {"type": "command", "command": f"{repo_a}/hooks/stop-notification.sh"}]}
    monkeypatch.setattr(mod, "REPO_ROOT", repo_a)
    ident_a = mod._group_identity(group)
    monkeypatch.setattr(mod, "REPO_ROOT", repo_b)
    ident_b = mod._group_identity(group)
    assert ident_a[1] == frozenset({"stop-notification.sh"})
    assert ident_b[1] == frozenset()
    assert ident_a != ident_b  # 分叉：B 側不認得 A 的套件腳本


def test_check_json_malformed(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("{not json")
    drifts: list = []
    mod.check_json_face(_cc_manifest(p), "cc", drifts)
    assert any("malformed" in m for _, m in drifts)


def test_check_json_missing_file(tmp_path):
    drifts: list = []
    mod.check_json_face(_cc_manifest(tmp_path / "nope.json"), "cc", drifts)
    assert any("缺席" in m for _, m in drifts)


def test_check_json_symlink_health(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text("{}")  # 普通檔（斷鏈形）
    m = _cc_manifest(target)
    m["registrations"]["cc"]["target_is_symlink"] = True
    drifts: list = []
    mod.check_json_face(m, "cc", drifts)
    assert any("symlink" in m2 for _, m2 in drifts)


def test_check_json_zcode_enabled_mismatch(tmp_path):
    ztmpl = json.loads(_rendered("registrations/zcode.json"))
    ztmpl["enabled"] = False
    target = _write(tmp_path, "config.json", {"mcp": {}, "hooks": ztmpl})
    m = {"registrations": {"zcode": {
        "target": str(target), "template": "registrations/zcode.json",
        "merge_root": "hooks", "target_is_symlink": False}}}
    drifts: list = []
    mod.check_json_face(m, "zcode", drifts)
    assert any("enabled" in m2 for _, m2 in drifts)


# ── codex 面（AC-4.4：Modified class／缺 group／mixed-rep）──────────


def _codex_live(template_text: str, state_key: str | None = None) -> str:
    state = "[hooks.state]\n" + (f'"{state_key}" = "sha256:x"\n' if state_key else "\n")
    return state + "\n" + template_text


def _codex_manifest(target: Path) -> dict:
    return {"registrations": {"codex": {
        "target": str(target), "template": "registrations/codex.toml"}}}


def test_check_codex_duplicate_inline_group_drift(tmp_path):
    t = _rendered("registrations/codex.toml")
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(t + t))  # 整份模板寫兩次＝每 owned group 重複
    drifts: list = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert any("重複 inline group" in m for _, m in drifts)


def test_check_codex_clean(tmp_path):
    t = _rendered("registrations/codex.toml")
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(t))
    drifts: list = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert drifts == []


def test_check_codex_modified_class(tmp_path):
    t = _rendered("registrations/codex.toml")
    mutated = t.replace("timeout = 10", "timeout = 11", 1)
    key = f"{Path.home()}/.codex/config.toml:pre_tool_use:0:0"
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(mutated, state_key=key))
    drifts: list = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert any("Modified" in m and "再 approve" in m for _, m in drifts)


def test_check_codex_content_diff_without_state(tmp_path):
    t = _rendered("registrations/codex.toml")
    mutated = t.replace("timeout = 10", "timeout = 11", 1)
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(mutated))
    drifts: list = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert any("內容差" in m for _, m in drifts)
    assert not any("Modified" in m for _, m in drifts)


def test_check_codex_missing_group(tmp_path):
    t = _rendered("registrations/codex.toml")
    head, sep, tail = t.partition("[[hooks.Stop]]")
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(head))
    drifts: list = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert any("缺 group" in m and "Stop" in m for _, m in drifts)


def test_check_codex_mixed_rep_hooks_json(tmp_path):
    t = _rendered("registrations/codex.toml")
    (tmp_path / ".codex").mkdir(exist_ok=True)
    (tmp_path / ".codex" / "hooks.json").write_text("{}")
    target = tmp_path / "config.toml"
    target.write_text(_codex_live(t))
    drifts: list = []
    mod.check_codex_face(_codex_manifest(target), drifts, codex_home=tmp_path)
    assert any("mixed-rep" in m for _, m in drifts)


# ── muse 面（AC-4.3：approve 腿＋R6 hash 腿，mock inspect）──────────


def _muse_manifest_patch(tmp_path, cache_dir, monkeypatch):
    """mock：inspect 回在冊 record（source 指 tmp canonical）＋probe PASS＋REPO_ROOT=tmp。"""
    doc = {
        "record": {
            "id": "muse-memory-governance",
            "source": {"path": str(tmp_path / "muse-plugins/memory-governance")},
            "cache_path": str(cache_dir),
        },
    }
    fake = SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=lambda *a, **k: fake))
    import shutil as _shutil
    monkeypatch.setattr(mod, "shutil",
                        SimpleNamespace(which=lambda n: "/usr/bin/muse", copy2=_shutil.copy2))
    monkeypatch.setattr(mod, "probe_muse", lambda pid: ("PASS", "mocked"))
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    # subprocess 已被 stub——預種 canonical 快取，避免 _canonical_root 的 git
    # 呼叫吃到假物件（byte-leg/source.path 錨定 canonical）
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(tmp_path): tmp_path})
    monkeypatch.setattr(mod, "_HOOK_PATTERN_CACHE", {})


def _muse_face_manifest(tmp_path: Path, cache_dir: Path) -> dict:
    return {"surfaces": {"memory": {
        "plugin_id": "muse-memory-governance",
        "plugin_path": "muse-plugins/memory-governance"}}}


def test_check_muse_cache_stale(tmp_path, monkeypatch):
    src = tmp_path / "muse-plugins/memory-governance"
    (src / "hooks").mkdir(parents=True)
    (src / ".muse-plugin").mkdir()
    (src / "hooks/h.sh").write_text("v2")
    cache = tmp_path / "cache/package"
    (cache / "hooks").mkdir(parents=True)
    (cache / ".muse-plugin").mkdir()
    (cache / "hooks/h.sh").write_text("v1")  # 內容差
    (cache / "stale.md").write_text("x")     # cache 多檔
    _muse_manifest_patch(tmp_path, cache, monkeypatch)
    drifts: list = []
    mod.check_muse_face(_muse_face_manifest(tmp_path, cache), drifts)
    assert any("內容差" in m for _, m in drifts)
    assert any("cache 多檔" in m for _, m in drifts)


def test_check_muse_source_path_not_canonical(tmp_path, monkeypatch):
    src = tmp_path / "elsewhere"
    src.mkdir()
    cache = tmp_path / "cache/package"
    cache.mkdir(parents=True)
    _muse_manifest_patch(tmp_path, cache, monkeypatch)
    doc = {
        "record": {
            "id": "muse-memory-governance",
            "source": {"path": str(src)},
            "cache_path": str(cache),
        },
    }
    fake = SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=lambda *a, **k: fake))
    drifts: list = []
    mod.check_muse_face(_muse_face_manifest(tmp_path, cache), drifts)
    assert any("canonical" in m for _, m in drifts)


def test_check_muse_source_extra_file_and_approve_fail(tmp_path, monkeypatch):
    """S5 補腿：approve 態 FAIL 分支＋source 多檔（cache 舊）分支。"""
    src = tmp_path / "muse-plugins/memory-governance"
    (src / "hooks").mkdir(parents=True)
    (src / "a.md").write_text("v1")
    cache = tmp_path / "cache/package"
    cache.mkdir(parents=True)  # cache 空——source 多檔
    _muse_manifest_patch(tmp_path, cache, monkeypatch)
    monkeypatch.setattr(mod, "probe_muse", lambda pid: ("FAIL", "非 trusted_enabled（mock）"))
    drifts: list = []
    mod.check_muse_face(_muse_face_manifest(tmp_path, cache), drifts)
    assert any("approve 態" in m for _, m in drifts)
    assert any("source 多檔" in m for _, m in drifts)


def test_check_muse_not_registered(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    _muse_manifest_patch(tmp_path, cache, monkeypatch)
    doc = {"record": {"id": "other-plugin"}}
    fake = SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=lambda *a, **k: fake))
    drifts: list = []
    mod.check_muse_face(_muse_face_manifest(tmp_path, cache), drifts)
    assert any("不在冊" in m for _, m in drifts)


# ── rules／skills 面 ──────────────────────────────────────────────


def test_check_rules_parity(tmp_path, monkeypatch):
    stub = SimpleNamespace(expected_bundle_for=lambda p: b"EXPECTED")
    monkeypatch.setattr(mod, "_DEPLOY_AGENTS_MOD", stub)
    target = tmp_path / "AGENTS.md"
    m = {"surfaces": {"rules": {"deployed_targets": [str(target)]}}}
    target.write_bytes(b"EXPECTED")
    drifts: list = []
    mod.check_rules_face(m, drifts)
    assert drifts == []
    target.write_bytes(b"DRIFTED")
    drifts = []
    mod.check_rules_face(m, drifts)
    assert any("bundle 漂移" in m2 for _, m2 in drifts)
    target.unlink()
    drifts = []
    mod.check_rules_face(m, drifts)
    assert any("缺席" in m2 for _, m2 in drifts)


def test_check_skills_symlinks(tmp_path):
    want = str(tmp_path / "skills")
    link = tmp_path / "skills-link"
    m = {"surfaces": {"skills": {"symlinks": [
        {"link": str(link), "target": want}]}}}
    drifts: list = []
    mod.check_skills_face(m, drifts)  # 缺席
    assert any("缺席" in m2 for _, m2 in drifts)
    link.symlink_to(want)
    drifts = []
    mod.check_skills_face(m, drifts)  # 正確（want 不存在也可 symlink）
    assert drifts == []
    link.unlink()
    link.symlink_to(str(tmp_path / "elsewhere"))
    drifts = []
    mod.check_skills_face(m, drifts)  # 指錯
    assert any("指錯" in m2 for _, m2 in drifts)


# ── cmd_check（AC-4.6：缺席容錯不 crash）──────────────────────────


def test_cmd_check_missing_configs_exit_drift_not_crash(tmp_path):
    m = {"registrations": {
        "cc": {"target": str(tmp_path / "a.json"), "template": "registrations/cc.json",
               "merge_root": "hooks", "target_is_symlink": False},
        "zcode": {"target": str(tmp_path / "b.json"),
                  "template": "registrations/zcode.json",
                  "merge_root": "hooks", "target_is_symlink": False},
        "codex": {"target": str(tmp_path / "c.toml"),
                  "template": "registrations/codex.toml"},
    }}
    rc = mod.cmd_check(m, "hooks")
    assert rc == mod.EXIT_DRIFT


def test_cmd_check_monitor_face_wired():
    """monitor check 轉正（AIR-110 G4）——缺席面走 drift 語義非 stub；行為腿見
    本檔「AIR-110 G4」段。"""
    drifts: list = []
    m = {"surfaces": {"monitor": {
        "plist_source": "deploy/nope.plist", "label": "x",
        "install_root": str(Path(mod.REPO_ROOT).parent / "nope-la")}}}
    mod.check_monitor_face(m, drifts)
    assert any("版控源缺席" in msg for _, msg in drifts)


def test_cmd_check_clean_exit_ok(tmp_path, monkeypatch):
    """TC-4 P4-2 對稱腿：全面乾淨 → cmd_check EXIT_OK（drifts 空路徑）。"""
    stub = SimpleNamespace(expected_bundle_for=lambda p: b"B")
    monkeypatch.setattr(mod, "_DEPLOY_AGENTS_MOD", stub)
    deployed = tmp_path / "AGENTS.md"
    deployed.write_bytes(b"B")
    skills = tmp_path / "skills"
    skills.mkdir()
    link = tmp_path / "skills-link"
    link.symlink_to(skills)
    tmpl_cc = json.loads(_rendered("registrations/cc.json"))
    cc = _write(tmp_path, "settings.json", {"hooks": tmpl_cc})
    tmpl_zc = json.loads(_rendered("registrations/zcode.json"))
    zc = _write(tmp_path, "config.json", {"mcp": {}, "plugins": {}, "hooks": tmpl_zc})
    ct = _rendered("registrations/codex.toml")
    cx = tmp_path / "config.toml"
    cx.write_text("[hooks.state]\n\n" + ct)
    monkeypatch.setattr(mod, "run_wrap", lambda argv, extra=None: 0)
    monkeypatch.setattr(mod, "check_muse_face", lambda m, d: None)  # muse 腿 mock 層另測
    manifest = {"registrations": {
        "cc": {"target": str(cc), "template": "registrations/cc.json",
               "merge_root": "hooks", "target_is_symlink": False},
        "zcode": {"target": str(zc), "template": "registrations/zcode.json",
                  "merge_root": "hooks", "target_is_symlink": False},
        "codex": {"target": str(cx), "template": "registrations/codex.toml"}},
        "surfaces": {"rules": {"deployed_targets": [str(deployed)]},
                     # 反向腿語義：真模板引用+空 scripts＝真 drift——fixture 對齊
                     # 真 manifest 的 scripts（檔案在真 REPO_ROOT/hooks 皆存在）
                     "hooks": {"scripts": _real_hooks_scripts()},
                     "skills": {"symlinks": [{"link": str(link), "target": str(skills)}]},
                     "agents": {"argv": ["true"], "check_args": []},
                     "memory": {"plugin_id": "x", "plugin_path": "p"}}}
    assert mod.cmd_check(manifest, "all") == mod.EXIT_OK


# ── basename-agnostic 錨定（0917 深審弧 A2-F1 回歸）───────────────
# 根因：HOOK_MARKER="/ai-guide/hooks/" 耦合 checkout basename——card WT／fork
# clone 的 identity 塌縮→check 假 drift／merge 重複 append。修復＝render 錨定
# canonical root（git common dir）＋identity pattern 錨定 canonical/本 checkout 兩根。


def test_hook_identity_matches_checkout_root_any_basename(tmp_path, monkeypatch):
    fork = tmp_path / "my-guide-fork"  # 非 ai-guide basename
    (fork / "hooks").mkdir(parents=True)
    monkeypatch.setattr(mod, "REPO_ROOT", fork)
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(fork): fork})
    monkeypatch.setattr(mod, "_HOOK_PATTERN_CACHE", {})
    group = {"hooks": [{"command": f"{fork}/hooks/x.py"},
                       {"command": "/foreign/other/hooks/y.py"}]}
    assert mod._group_scripts(group) == frozenset({"x.py"})  # 自家根命中、外來路徑不認列


def test_render_anchors_canonical_root(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): tmp_path})
    assert mod.render("{{REPO}}/hooks/a.py") == f"{tmp_path}/hooks/a.py"


def test_install_guard_rejects_non_canonical(monkeypatch):
    monkeypatch.setattr(mod, "_CANONICAL_CACHE",
                        {str(mod.REPO_ROOT): mod.REPO_ROOT.parent / "elsewhere"})
    manifest = {"registrations": {}, "surfaces": {}}
    assert mod.cmd_install_uninstall(manifest, "hooks", "install") == mod.EXIT_GUARD


def test_hooks_scripts_reverse_leg(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(tmp_path): tmp_path})
    monkeypatch.setattr(mod, "_HOOK_PATTERN_CACHE", {})
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "a.py").write_text("# a")
    (tmp_path / "governance").mkdir()
    monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_path / "governance" / "manifest.toml")
    (tmp_path / "governance" / "t.json").write_text(
        json.dumps({"PreToolUse": [{"hooks": [{"command": f"{tmp_path}/hooks/b.py"}]}]}))
    manifest = {"surfaces": {"hooks": {"scripts": ["hooks/a.py"]}},
                "registrations": {"cc": {"template": "t.json"}}}
    drifts: list = []
    mod.check_hooks_scripts(manifest, drifts)
    assert any("未列" in m and "b.py" in m for _, m in drifts)  # 模板引用→manifest 漏接即報


def test_probe_empty_plan_skips_stage(monkeypatch, capsys):
    """0917 深審弧 A2-F9：plan 空（--reps-from > --reps）不 stage carrier——
    apiKey 絕不落 scratch。stage_carrier 被 mock 成炸彈：被呼叫即 fail。"""
    from conftest import load_module
    probe = load_module("scripts/skill_activation_probe.py")

    def _boom(*a, **k):
        raise AssertionError("plan 為空時不得 stage carrier")

    monkeypatch.setattr(probe, "find_zcode_cjs", lambda: "/fake/cjs")
    monkeypatch.setattr(probe, "stage_carrier", _boom)
    rc = probe.main(["--skill", "implement", "--reps-from", "2", "--reps", "1"])
    assert rc == 1
    assert "不 stage carrier" in capsys.readouterr().err


def test_hook_identity_cross_root_card_wt(tmp_path, monkeypatch):
    """A2-F1 主場景（復審 G-F2）：card WT 跑 check 時，pattern 經 canonical
    交替腿認出 canonical 錨定的 live 條目——canonical≠REPO_ROOT 的跨根匹配。"""
    canonical = tmp_path / "ai-guide"          # canonical 根
    card_wt = tmp_path / "ai-guide-air-116"    # 本 checkout（不同 basename）
    monkeypatch.setattr(mod, "REPO_ROOT", card_wt)
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(card_wt): canonical})
    monkeypatch.setattr(mod, "_HOOK_PATTERN_CACHE", {})
    group = {"hooks": [{"command": f"{canonical}/hooks/x.py"}]}  # live 側＝canonical 路徑
    assert mod._group_scripts(group) == frozenset({"x.py"})
# ── AIR-110 G2/G4/G5（面外缺口補齊）───────────────────────────────
# G2 四條 home symlink 擴 manifest skills 面（user 拍板③）：真 manifest entries
# 在場＋HOME-shim 全鏈行為（build_plan→_apply_target install/noop／check 綠）。
# G4 monitor plist 路徑參數化：{{REPO}}/{{HOME}} 佔位＋install.py render_plist
# （R2 codex#5：parse-modify-dump——只對已知路徑欄位替換 token，XML 註解隨
# dump 卸除）＋--check --surface monitor 轉正（live 與 render 期望 byte parity）。
# G5 backlog-cleanup plist 版控化（不入 installer——安裝形態＝清單列出）。


G2_ENTRIES = [
    ("~/.claude/CLAUDE.md", "{{REPO}}/ai-development-guide.md"),
    ("~/.claude/rules", "{{REPO}}/rules"),
    ("~/.claude/agents", "{{REPO}}/agents/claude"),
    ("~/.zcode/agents", "{{REPO}}/agents/zcode"),
]


def _shim_repo(tmp_path: Path, monkeypatch) -> Path:
    """HOME-shim＋fake repo：`~/...` 落 tmp HOME、{{REPO}} render 落 tmp repo。
    canonical cache 預種＝shim repo（0918 合併融合注記——render 錨 canonical，
    不預種會解到真 repo 根，G2 斷言路徑錯位）。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    repo = tmp_path / "repo"
    for d in ("skills", "rules", "agents/claude", "agents/zcode"):
        (repo / d).mkdir(parents=True)
    (repo / "ai-development-guide.md").write_text("guide\n")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(repo): repo})
    monkeypatch.setattr(mod, "_HOOK_PATTERN_CACHE", {})
    return repo


def test_g2_manifest_contains_four_home_symlinks():
    manifest = mod.load_manifest()
    entries = {(s["link"], s["target"]) for s in manifest["surfaces"]["skills"]["symlinks"]}
    for pair in G2_ENTRIES:
        assert pair in entries


def test_g2_install_creates_then_noop(tmp_path, monkeypatch):
    _shim_repo(tmp_path, monkeypatch)
    manifest = mod.load_manifest()
    plan = mod.build_plan(manifest, "skills", "install")
    symlinks = [t for t in plan["targets"] if t["kind"] == "symlink"]
    assert len(symlinks) == 6  # 兩條 skills 母鏈＋G2 四條 home symlink
    assert [mod._apply_target({}, t, "install") for t in symlinks] == ["created"] * 6
    assert [mod._apply_target({}, t, "install") for t in symlinks] == ["noop"] * 6


def test_g2_file_symlink_claude_md_created(tmp_path, monkeypatch):
    """CLAUDE.md＝檔案 symlink（非目錄母鏈）——機構泛型形態腿。"""
    _shim_repo(tmp_path, monkeypatch)
    manifest = mod.load_manifest()
    plan = mod.build_plan(manifest, "skills", "install")
    t = next(x for x in plan["targets"] if x["link"] == "~/.claude/CLAUDE.md")
    assert mod._apply_target({}, t, "install") == "created"
    link = Path.home() / ".claude" / "CLAUDE.md"
    assert link.is_symlink() and not link.is_dir()
    assert link.resolve() == (mod.REPO_ROOT / "ai-development-guide.md").resolve()


def test_g2_check_green_when_symlinks_correct(tmp_path, monkeypatch):
    _shim_repo(tmp_path, monkeypatch)
    manifest = mod.load_manifest()
    for t in mod.build_plan(manifest, "skills", "install")["targets"]:
        mod._apply_target({}, t, "install")
    drifts: list = []
    mod.check_skills_face(manifest, drifts)
    assert drifts == []


def test_g2_check_reports_wrong_target(tmp_path, monkeypatch):
    _shim_repo(tmp_path, monkeypatch)
    (tmp_path / "elsewhere").mkdir()
    rules_link = Path.home() / ".claude" / "rules"
    rules_link.parent.mkdir(parents=True, exist_ok=True)
    rules_link.symlink_to(tmp_path / "elsewhere")
    manifest = mod.load_manifest()
    drifts: list = []
    mod.check_skills_face(manifest, drifts)
    assert any("指錯" in m and ".claude/rules" in m for _, m in drifts)


MINIMAL_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>test.label</string>
    <key>ProgramArguments</key>
    <array><string>{{HOME}}/.local/bin/uv</string><string>run</string></array>
    <key>WorkingDirectory</key><string>{{REPO}}</string>
    <key>StartInterval</key><integer>86400</integer>
</dict>
</plist>
"""


def test_g4_render_home_token(monkeypatch):
    # render 錨 canonical（0918 融合）——預種 cache 使 canonical＝本 WT 根
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    assert mod.render("{{HOME}}/x") == f"{Path.home()}/x"
    assert mod.render("{{REPO}}/y") == f"{mod.REPO_ROOT}/y"


def test_g4_monitor_plist_source_parameterized(monkeypatch):
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    text = (mod.REPO_ROOT / "deploy/governance-health-monitor.plist").read_text()
    assert "{{REPO}}" in text and "{{HOME}}" in text
    assert "/Users/" not in text  # 源零機器絕對路徑（跨機器零手改）
    rendered = mod.render_plist(text)
    doc = plistlib.loads(rendered.encode())
    assert doc["WorkingDirectory"] == str(mod.REPO_ROOT)
    assert "<!--" not in rendered  # codex#5：XML 註解隨 dump 卸除


def _mon_setup(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """fake repo（版控 plist 源）＋live 安裝副本路徑。"""
    repo = tmp_path / "repo"
    (repo / "deploy").mkdir(parents=True)
    src = repo / "deploy/monitor.plist"
    src.write_text(MINIMAL_PLIST)
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    inst = tmp_path / "LaunchAgents/test.label.plist"
    return src, inst


def _mon_manifest(inst: Path) -> dict:
    return {"surfaces": {"monitor": {
        "plist_source": "deploy/monitor.plist", "label": "test.label",
        "install_root": str(inst.parent)}}}


def test_g4_check_monitor_missing_copy_drift(tmp_path, monkeypatch):
    _src, inst = _mon_setup(tmp_path, monkeypatch)
    drifts: list = []
    mod.check_monitor_face(_mon_manifest(inst), drifts)
    assert any("安裝副本缺席" in m for _, m in drifts)


def test_g4_check_monitor_missing_source_drift(tmp_path, monkeypatch):
    src, inst = _mon_setup(tmp_path, monkeypatch)
    src.unlink()
    drifts: list = []
    mod.check_monitor_face(_mon_manifest(inst), drifts)
    assert any("版控源缺席" in m for _, m in drifts)


def test_g4_check_monitor_drift_on_content_diff(tmp_path, monkeypatch):
    src, inst = _mon_setup(tmp_path, monkeypatch)
    inst.parent.mkdir(parents=True)
    inst.write_text(mod.render_plist(src.read_text()).replace("86400", "1"))  # 手改 live
    drifts: list = []
    mod.check_monitor_face(_mon_manifest(inst), drifts)
    assert any("plist 漂移" in m for _, m in drifts)


def test_g4_check_monitor_green_on_rendered_equal(tmp_path, monkeypatch):
    src, inst = _mon_setup(tmp_path, monkeypatch)
    inst.parent.mkdir(parents=True)
    inst.write_text(mod.render_plist(src.read_text()))
    drifts: list = []
    mod.check_monitor_face(_mon_manifest(inst), drifts)
    assert drifts == []


def test_g4_cmd_check_monitor_exit_codes(tmp_path, monkeypatch):
    """--check --surface monitor 轉正：drift→1／綠→0（stub EXIT_NOT_IMPL 退役）。"""
    src, inst = _mon_setup(tmp_path, monkeypatch)
    m = _mon_manifest(inst)
    assert mod.cmd_check(m, "monitor") == mod.EXIT_DRIFT  # live 缺席
    inst.parent.mkdir(parents=True)
    inst.write_text(mod.render_plist(src.read_text()))
    assert mod.cmd_check(m, "monitor") == mod.EXIT_OK


def test_g4_apply_launchd_plist_renders_tokens(tmp_path, monkeypatch):
    _src, inst = _mon_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(mod, "_launchctl", lambda *a: SimpleNamespace(
        returncode=0 if a[0] == "bootstrap" else 1, stderr=""))  # print→未載入
    t = {"kind": "launchd-plist", "target": str(inst), "source": "deploy/monitor.plist",
         "label": "test.label", "action": "merge"}
    assert mod._apply_target({}, t, "install") == "created＋bootstrapped"
    text = inst.read_text()
    assert "{{REPO}}" not in text and "{{HOME}}" not in text
    assert str(mod.REPO_ROOT) in text
    plistlib.loads(text.encode())  # 寫入副本仍合法 plist


def test_g4_render_plist_parse_modify_dump(tmp_path, monkeypatch):
    """R2 codex#5：render＝parse-modify-dump——只對已知路徑欄位（ProgramArguments
    元素／WorkingDirectory／Standard*Path／EnvironmentVariables 值）替換 token；
    XML 註解隨 dump 卸除（註解含 token 字樣／路徑含雙連字號不再毒化輸出）。"""
    repo = tmp_path / "repo"
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    src = MINIMAL_PLIST.replace(
        "<key>Label</key><string>test.label</string>",
        '<key>Label</key><string>{{REPO}}-keep</string>',
    ).replace(
        '<plist version="1.0">',
        '<plist version="1.0">\n<!-- 註解含 {{REPO}} 與 {{HOME}} 字樣 -->',
    )
    out = mod.render_plist(src)
    doc = plistlib.loads(out.encode())
    assert doc["WorkingDirectory"] == str(repo)
    assert doc["ProgramArguments"][0] == f"{Path.home()}/.local/bin/uv"
    assert doc["Label"] == "{{REPO}}-keep"  # 非路徑欄位——token 不替換
    assert "<!--" not in out  # 註解隨 dump 卸除
    assert out.count("{{REPO}}") == 1 and "{{HOME}}" not in out


def test_g4_render_plist_env_vars_renders_values(tmp_path, monkeypatch):
    """EnvironmentVariables 值屬路徑欄位——token 替換落地。"""
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path / "repo")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    src = MINIMAL_PLIST.replace(
        "<key>StartInterval</key><integer>86400</integer>",
        "<key>StartInterval</key><integer>86400</integer>\n"
        "<key>EnvironmentVariables</key>\n<dict>\n"
        "<key>HOME</key><string>{{HOME}}</string>\n"
        "<key>PATH</key><string>{{HOME}}/.local/bin:/usr/bin</string>\n"
        "</dict>",
    )
    doc = plistlib.loads(mod.render_plist(src).encode())
    assert doc["EnvironmentVariables"]["HOME"] == str(Path.home())
    assert doc["EnvironmentVariables"]["PATH"] == f"{Path.home()}/.local/bin:/usr/bin"


def test_g4_render_plist_malformed_source_fail_loud():
    with pytest.raises(mod.GovernanceError, match="版控源非合法 plist"):
        mod.render_plist("not a plist at all")


def test_g5_backlog_cleanup_plist_versioned_and_parameterized(monkeypatch):
    """版控源形態釘住 live plist（AIR-110 G5）：排程欄位＋script 路徑逐字對照。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    text = (mod.REPO_ROOT / "deploy/backlog-cleanup.plist").read_text()
    assert "{{REPO}}" in text and "{{HOME}}" in text
    assert "/Users/" not in text
    doc = plistlib.loads(mod.render(text).encode())
    assert doc["Label"] == "com.ai-guide.backlog-cleanup"
    assert doc["ProgramArguments"] == [
        "/bin/bash", f"{mod.REPO_ROOT}/deploy/scripts/run-backlog-cleanup.sh"]
    assert doc["StartCalendarInterval"] == {"Hour": 23, "Minute": 50}
    assert doc["ThrottleInterval"] == 600
    assert (mod.REPO_ROOT / "deploy/scripts/run-backlog-cleanup.sh").exists()


def test_g5_not_wired_into_installer():
    """G5 決策：本弧版控化不入 installer（monitor 面仍單 plist——安裝形態清單列出）。"""
    manifest = mod.load_manifest()
    mon_src = mod.REPO_ROOT / manifest["surfaces"]["monitor"]["plist_source"]
    assert "backlog-cleanup" not in mon_src.read_text()


def test_g5_install_form_listed_in_readme():
    """G5：backlog-cleanup 安裝形態＝README 面外清單列出（版控源＋手動裝載步驟）。"""
    text = (mod.REPO_ROOT / "governance/README.md").read_text()
    assert "deploy/backlog-cleanup.plist" in text
    assert "com.ai-guide.backlog-cleanup" in text
    assert "launchctl bootstrap" in text  # 手動裝載形態在場


# ── AIR-126：投放預設態顯性化（guard fail-open／monitor 缺席警示）──────
# 新 clone 預設態＝兩道防護 fail-open：hooksPath 未設（控制面 guard 不 fire）、
# --surface all 不含 monitor（健康警鈴未開）。install/check 結尾主動偵測並顯性
# 警示（非沉默）；警示只加資訊不改退出碼（README 退出碼契約凍結）。


def _git_hooks_probe(rc: int, out: str):
    """fake subprocess.run：hooksPath 探針回 (rc, out)；其他呼叫（muse 等）回 0。"""

    def _run(argv, *a, **k):
        if any("hooksPath" in str(a) for a in argv):
            return SimpleNamespace(returncode=rc, stdout=out, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return _run


def _air126_monitor_manifest(tmp_path: Path) -> dict:
    return {"surfaces": {"monitor": {
        "plist_source": "deploy/nope.plist", "label": "test.label",
        "install_root": str(tmp_path / "LaunchAgents")}}}


def test_air126_hooks_path_value_real_git(tmp_path):
    """探針契約：新 clone 未設＝空字串；已設＝值；非 git repo＝None（不警示）。"""
    import subprocess as sp

    sp.run(("git", "init", "-q", str(tmp_path)), check=True)
    assert mod.hooks_path_value(tmp_path) == ""  # 未設
    sp.run(("git", "-C", str(tmp_path), "config", "core.hooksPath", ".githooks"),
           check=True)
    assert mod.hooks_path_value(tmp_path) == ".githooks"
    assert mod.hooks_path_value(tmp_path / "nope") is None  # 非 git repo


def test_air126_guard_unset_warns(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    lines = mod.guard_failopen_lines(tmp_path)
    assert len(lines) == 1
    assert "guard 未啟用" in lines[0] and "core.hooksPath" in lines[0]
    assert "config core.hooksPath .githooks" in lines[0]  # 修復指令在場


def test_air126_guard_set_githooks_silent(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "subprocess",
                        SimpleNamespace(run=_git_hooks_probe(0, ".githooks\n")))
    assert mod.guard_failopen_lines(tmp_path) == []


def test_air126_guard_custom_value_warns(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(0, "custom-hooks\n")))
    lines = mod.guard_failopen_lines(tmp_path)
    assert len(lines) == 1 and "custom-hooks" in lines[0]


def test_air126_guard_undeterminable_warns(tmp_path, monkeypatch):
    """非 git repo／git 失敗（rc 128）＝無法判定——顯性警示不靜默
    （fail-visible 與 bootstrap G3 對齊；codex review 補抓 None-靜默洞）。"""
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(128, "")))
    lines = mod.guard_failopen_lines(tmp_path)
    assert len(lines) == 1
    assert "無法判定" in lines[0]
    assert "core.hooksPath" in lines[0]


def test_air126_monitor_absent_warns(tmp_path):
    lines = mod.monitor_absent_lines(_air126_monitor_manifest(tmp_path))
    assert len(lines) == 1
    assert "偵測網缺席" in lines[0]
    assert "install --surface monitor" in lines[0]  # 裝法在場
    assert "告警" in lines[0]  # 一行後果在場


def test_air126_monitor_present_silent(tmp_path):
    m = _air126_monitor_manifest(tmp_path)
    inst = tmp_path / "LaunchAgents" / "test.label.plist"
    inst.parent.mkdir(parents=True)
    inst.write_text("<plist/>")
    assert mod.monitor_absent_lines(m) == []


def test_air126_monitor_face_untouched_manifest_no_warn(tmp_path):
    assert mod.monitor_absent_lines({}) == []


def test_air126_cmd_check_all_prints_both_warnings(tmp_path, monkeypatch, capsys):
    for fn in ("check_rules_face", "check_skills_face", "check_hooks_scripts",
               "check_json_face", "check_codex_face", "check_agents_face",
               "check_muse_face"):
        monkeypatch.setattr(mod, fn, lambda *a, **k: None)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    assert mod.cmd_check(_air126_monitor_manifest(tmp_path), "all") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "guard 未啟用" in out
    assert "偵測網缺席" in out


def test_air126_cmd_check_single_surface_no_monitor_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "check_rules_face", lambda m, d: None)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    assert mod.cmd_check(_air126_monitor_manifest(tmp_path), "rules") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "guard 未啟用" in out
    assert "偵測網缺席" not in out  # monitor 提示限 --surface all


def test_air126_cmd_check_drift_branch_still_warns(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        mod, "check_rules_face",
        lambda m, d: d.append(("rules", "部署檔缺席：x")))
    monkeypatch.setattr(mod, "check_skills_face", lambda m, d: None)
    monkeypatch.setattr(mod, "check_hooks_scripts", lambda m, d: None)
    monkeypatch.setattr(mod, "check_json_face", lambda m, h, d: None)
    monkeypatch.setattr(mod, "check_codex_face", lambda m, d, **k: None)
    monkeypatch.setattr(mod, "check_agents_face", lambda m, d: None)
    monkeypatch.setattr(mod, "check_muse_face", lambda m, d: None)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    m = _air126_monitor_manifest(tmp_path)
    assert mod.cmd_check(m, "all") == mod.EXIT_DRIFT
    out = capsys.readouterr().out
    assert "guard 未啟用" in out and "偵測網缺席" in out


def test_air126_install_all_completion_prints_warnings(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "build_plan",
                        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []})
    monkeypatch.setattr(mod, "apply_plan", lambda m, plan, journal=True: mod.EXIT_OK)
    monkeypatch.setattr(mod, "run_wrap", lambda argv, extra=None: 0)
    monkeypatch.setattr(mod, "_require_muse_cli", lambda: None)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    m = _air126_monitor_manifest(tmp_path)
    m["surfaces"]["rules"] = {"argv": ["true"]}
    m["surfaces"]["agents"] = {"argv": ["true"]}
    m["surfaces"]["memory"] = {"plugin_path": "nope/plugin", "plugin_id": "x",
                               "pool_setup": "nope.sh"}
    m["registrations"] = {}
    assert mod.cmd_install_uninstall(m, "all", "install") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "guard 未啟用" in out
    assert "偵測網缺席" in out


def test_air126_install_single_surface_no_monitor_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "build_plan",
                        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []})
    monkeypatch.setattr(mod, "apply_plan", lambda m, plan, journal=True: mod.EXIT_OK)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    m = _air126_monitor_manifest(tmp_path)
    m["registrations"] = {"cc": {}, "zcode": {}, "codex": {}}
    assert mod.cmd_install_uninstall(m, "hooks", "install") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "guard 未啟用" in out
    assert "偵測網缺席" not in out


def test_air126_uninstall_and_dryrun_no_warnings(tmp_path, monkeypatch, capsys):
    """警示面限 install/check 完成輸出——uninstall／dry-run 不印。"""
    monkeypatch.setattr(mod, "_CANONICAL_CACHE", {str(mod.REPO_ROOT): mod.REPO_ROOT})
    monkeypatch.setattr(mod, "build_plan",
                        lambda m, s, mode: {"surface": s, "mode": mode, "targets": []})
    monkeypatch.setattr(mod, "apply_plan", lambda m, plan, journal=True: mod.EXIT_OK)
    monkeypatch.setattr(mod, "run_wrap", lambda argv, extra=None: 0)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=_git_hooks_probe(1, "")))
    m = _air126_monitor_manifest(tmp_path)
    m["surfaces"]["rules"] = {"argv": ["true"]}
    m["surfaces"]["agents"] = {"argv": ["true"]}
    m["registrations"] = {"cc": {}, "zcode": {}, "codex": {}}
    assert mod.cmd_install_uninstall(m, "all", "uninstall") == mod.EXIT_OK
    assert mod.cmd_install_uninstall(m, "all", "dry-run") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "guard 未啟用" not in out
    assert "偵測網缺席" not in out


def test_air126_readme_documents_default_failopen():
    """AC#4：README 同步——新 clone 預設態 fail-open 明示＋兩道警示語義。"""
    text = (mod.REPO_ROOT / "governance/README.md").read_text()
    assert "新 clone 預設態" in text
    assert "fail-open" in text
    assert "config core.hooksPath .githooks" in text  # guard 修復指令在場


# ── AIR-133：agents 面機器活視圖探針＋memory drift 修復指引 ──────────
# agents 面只驗 repo 生成物 parity（sync_agents --check），機器活視圖（home
# symlink：~/.agents/skills 母鏈＋~/.claude/agents／~/.zcode/agents registry）
# 缺席時仍綠燈＝誤導「已防護」——補 [WARN] 存在性探針（警示不改退出碼，同
# AIR-126 契約；指對性歸 skills 面 drift）。memory 面「muse CLI 在但 plugins
# build 不支援」（inspect 非零）drift 訊息補一行修復指引（同 126 一行後果＋
# 裝法形態）。


def _air133_agents_manifest() -> dict:
    return {"surfaces": {
        "agents": {"argv": ["true"], "check_args": ["--check"]},
        "skills": {"symlinks": [
            {"link": "~/.agents/skills", "target": "{{REPO}}/skills"},
            {"link": "~/.claude/agents", "target": "{{REPO}}/agents/claude"},
            {"link": "~/.zcode/agents", "target": "{{REPO}}/agents/zcode"},
        ]}}}


def test_air133_agents_view_absent_warns(tmp_path, monkeypatch):
    """無 symlink 機器＝活視圖全缺→單行 [WARN]（路徑＋後果＋裝法在場）。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    lines = mod.agents_view_absent_lines(_air133_agents_manifest())
    assert len(lines) == 1
    assert "[WARN]" in lines[0]
    assert "~/.agents/skills" in lines[0] and "~/.zcode/agents" in lines[0]
    assert "install --surface skills" in lines[0]  # 裝法在場
    assert "parity 綠" in lines[0]  # 一行後果在場


def test_air133_agents_view_present_silent(tmp_path, monkeypatch):
    """三條 symlink 在場且指對 render(target)＋target 可達＝靜默。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    home = tmp_path / "home"
    for rel, token in ((".agents/skills", "{{REPO}}/skills"),
                       (".claude/agents", "{{REPO}}/agents/claude"),
                       (".zcode/agents", "{{REPO}}/agents/zcode")):
        link = home / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(Path(mod.render(token)))
    assert mod.agents_view_absent_lines(_air133_agents_manifest()) == []


def test_air133_agents_dangling_symlink_warns(tmp_path, monkeypatch):
    """斷鏈 symlink（inode 在、target 不存在）＝不可達→WARN（codex finding：
    is_symlink() 單查會讓斷鏈靜默綠燈）。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    link = tmp_path / "home" / ".agents/skills"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(tmp_path / "nowhere")
    lines = mod.agents_view_absent_lines(_air133_agents_manifest())
    assert len(lines) == 1


def test_air133_agents_mispointed_symlink_warns(tmp_path, monkeypatch):
    """錯位 symlink（指對存在目錄但非 render(target)）→WARN。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    wrong = tmp_path / "home" / "wrong-dir"
    wrong.mkdir(parents=True)
    link = tmp_path / "home" / ".agents/skills"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(wrong)
    lines = mod.agents_view_absent_lines(_air133_agents_manifest())
    assert len(lines) == 1


def test_air133_agents_view_manifest_without_skills_no_warn():
    """manifest 無 skills 面（partial fixture）＝不警示（.get 鏈不崩）。"""
    assert mod.agents_view_absent_lines(
        {"surfaces": {"agents": {"argv": ["true"]}}}) == []


def test_air133_cmd_check_agents_surface_warns_but_exit_ok(tmp_path, monkeypatch, capsys):
    """AC#1 核心：--surface agents 綠燈但有顯性警示（警示不改退出碼，Plan ③）。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(mod, "run_wrap", lambda argv, extra=None: 0)
    monkeypatch.setattr(mod, "subprocess",
                        SimpleNamespace(run=_git_hooks_probe(0, ".githooks\n")))
    assert mod.cmd_check(_air133_agents_manifest(), "agents") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "agents 機器活視圖缺席" in out
    assert "install --surface skills" in out


def test_air133_agents_warning_surface_gate(tmp_path, monkeypatch, capsys):
    """agents 警示閘門：all/agents 印、skills/memory/hooks 不印（閘門覆蓋釘）。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    manifest = _air133_agents_manifest()
    for face in ("agents", "all"):
        mod._print_default_state_warnings(manifest, face)
        assert "agents 機器活視圖缺席" in capsys.readouterr().out
    for face in ("skills", "memory", "hooks"):
        mod._print_default_state_warnings(manifest, face)
        assert "agents 機器活視圖缺席" not in capsys.readouterr().out


def test_air133_cmd_check_true_drift_still_exit_1(tmp_path, monkeypatch, capsys):
    """真 drift（sync_agents --check 非零）仍 exit 1；警示並列不改退出碼契約。"""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(mod, "run_wrap", lambda argv, extra=None: 1)
    monkeypatch.setattr(mod, "subprocess",
                        SimpleNamespace(run=_git_hooks_probe(0, ".githooks\n")))
    assert mod.cmd_check(_air133_agents_manifest(), "agents") == mod.EXIT_DRIFT
    out = capsys.readouterr().out
    assert "agents 機器活視圖缺席" in out  # 警示與 drift 並列
    assert "sync_agents --check 非零" in out


def test_air133_muse_inspect_fail_has_fix_hint(tmp_path, monkeypatch):
    """AC#2：plugins build 不支援（inspect 非零）＝drift 訊息含修復指引——
    分流契約：unrecognized subcommand→升級指引；其他 stderr→通用指引（muse
    review finding：inspect 非零另有 plugin 未裝／daemon 異常常見成因）。"""
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: "/usr/bin/muse"))

    def _probe(stderr):
        return SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
            returncode=2, stdout="", stderr=stderr))

    monkeypatch.setattr(mod, "subprocess",
                        _probe("error: unrecognized subcommand 'plugins'"))
    drifts: list = []
    mod.check_muse_face(_muse_face_manifest(tmp_path, tmp_path / "cache"), drifts)
    assert any("inspect 不可判定" in m and "修復" in m for _, m in drifts)
    assert any("升級" in m and "plugins 子命令" in m and "重跑 --check" in m
               for _, m in drifts)

    monkeypatch.setattr(mod, "subprocess", _probe("permission denied"))
    drifts2: list = []
    mod.check_muse_face(_muse_face_manifest(tmp_path, tmp_path / "cache"), drifts2)
    assert any("daemon" in m for _, m in drifts2)
    assert not any("升級" in m for _, m in drifts2)
