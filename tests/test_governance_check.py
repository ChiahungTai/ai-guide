"""governance install.py --check 五面 parity 測試（AIR-116 S4）。

fixture 腿：AC-4.2（缺/多/內容差條目）、AC-4.3（muse approve/hash 腿 mock）、
AC-4.4（codex Modified class＋mixed-rep）、AC-4.6（live config 缺席→drift 不
crash）。live 態驗收歸 AC-4.1/4.2/4.5 receipt（真 config mutation＋復原）。
"""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

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
    from types import SimpleNamespace as SN
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
    assert any("母鏈缺席" in m2 for _, m2 in drifts)
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


def test_cmd_check_monitor_stub():
    assert mod.cmd_check({}, "monitor") == mod.EXIT_NOT_IMPL


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
