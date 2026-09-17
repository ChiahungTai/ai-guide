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
