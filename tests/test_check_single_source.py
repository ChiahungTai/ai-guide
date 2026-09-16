"""check_single_source 的 invariant 檢查單元測試（T1-2/T1-3）。"""

import json
from pathlib import Path

import pytest
from conftest import load_module

css = load_module("skills/scan-project/scripts/check_single_source.py")


def test_extract_schema_block_found():
    text = '### DimensionVerdict schema\n\n```json\n{"a": 1}\n```\n'
    assert css.extract_schema_block(text, "DimensionVerdict") == '{"a": 1}'


def test_extract_schema_block_missing():
    assert css.extract_schema_block("no schema here", "X") is None


def _hook_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "hook_registration")


def test_hook_registration_orphan_detected(tmp_path, monkeypatch):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "ok.py").write_text("pass")
    (tmp_path / "hooks" / "orphan.py").write_text("pass")
    (tmp_path / "settings.json").write_text(
        '"command": "python3 /x/hooks/ok.py"', encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_hook_registration(_hook_inv())
    assert len(findings) == 1
    assert findings[0][1] == "critical"
    assert "orphan.py" in findings[0][2]


def test_hook_registration_all_registered(tmp_path, monkeypatch):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "a.py").write_text("pass")
    (tmp_path / "hooks" / "b.py").write_text("pass")
    (tmp_path / "settings.json").write_text("a.py b.py", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_hook_registration(_hook_inv()) == []


def test_hook_registration_missing_reg_file_skipped(tmp_path, monkeypatch):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "a.py").write_text("pass")
    # settings.json 不存在（local/gitignored 機器）→ skip 不 false positive，
    # 但 zcode-registration.json 也不存在時仍應全部抓孤兒
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_hook_registration(_hook_inv())
    assert len(findings) == 1


# ---------------------------------------------------------------------------
# zcode_live_parity：template 接線必須已部署 live（F8 形狀：註冊≠fire）
# ---------------------------------------------------------------------------


def _parity_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "zcode_live_parity")


TPL_JSON = {
    "hooks": {
        "events": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write",
                    "hooks": [
                        {
                            "type": "process",
                            "command": "python3",
                            "args": ["/x/hooks/ok.py"],
                        }
                    ],
                }
            ]
        }
    }
}


def _write_tpl(tmp_path):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "zcode-registration.json").write_text(
        json.dumps(TPL_JSON), encoding="utf-8"
    )


def _ok_group(matcher="Edit|Write", path="/x/hooks/ok.py"):
    return [
        {
            "matcher": matcher,
            "hooks": [{"type": "process", "command": "python3", "args": [path]}],
        }
    ]


def _live(tmp_path, events, enabled=True):
    live = tmp_path / "live.json"
    live.write_text(
        json.dumps({"hooks": {"enabled": enabled, "events": events}}), encoding="utf-8"
    )
    return live


def test_parity_missing_in_live_critical(tmp_path, monkeypatch):
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_zcode_live_parity(
        _parity_inv(), live_path=_live(tmp_path, events={})
    )
    assert len(findings) == 1
    assert findings[0][1] == "critical"
    assert "ok.py" in findings[0][2]


def test_parity_all_registered_ok(tmp_path, monkeypatch):
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = _live(tmp_path, events={"PreToolUse": _ok_group()})
    assert css.check_zcode_live_parity(_parity_inv(), live_path=live) == []


def test_parity_live_absent_skip(tmp_path, monkeypatch):
    """SM-5：非 ZCode 機器（live config 缺場）skip 不 false positive。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert (
        css.check_zcode_live_parity(_parity_inv(), live_path=tmp_path / "nope.json")
        == []
    )


def test_parity_disabled_critical(tmp_path, monkeypatch):
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = _live(tmp_path, events={"PreToolUse": _ok_group()}, enabled=False)
    findings = css.check_zcode_live_parity(_parity_inv(), live_path=live)
    assert len(findings) == 1
    assert "enabled" in findings[0][2]


def test_parity_template_missing_important(tmp_path, monkeypatch):
    """Y4：template 缺席→important（INVARIANTS 路徑 typo 不炸整個 checker）。"""
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_zcode_live_parity(
        _parity_inv(), live_path=tmp_path / "live.json"
    )
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_parity_live_bad_json_important(tmp_path, monkeypatch):
    """A4：live config 手改壞→important（非 crash）。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = tmp_path / "live.json"
    live.write_text("not-json", encoding="utf-8")
    findings = css.check_zcode_live_parity(_parity_inv(), live_path=live)
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_parity_wrong_matcher_critical(tmp_path, monkeypatch):
    """C6③：檔名在 live 但掛錯 matcher（Edit|Write 掛成 Bash）＝未部署。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = _live(tmp_path, events={"PreToolUse": _ok_group(matcher="Bash")})
    findings = css.check_zcode_live_parity(_parity_inv(), live_path=live)
    assert len(findings) == 1
    assert findings[0][1] == "critical"


def test_parity_suffix_lookalike_critical(tmp_path, monkeypatch):
    """C6③：`ok.py.bak` 殘字樣不算 ok.py 已部署（negative lookahead）。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = _live(tmp_path, events={"PreToolUse": _ok_group(path="/x/hooks/ok.py.bak")})
    findings = css.check_zcode_live_parity(_parity_inv(), live_path=live)
    assert len(findings) == 1
    assert findings[0][1] == "critical"


def test_parity_live_hooks_not_dict_important(tmp_path, monkeypatch):
    """C5③：live hooks 區塊結構異常（合法 JSON 非 object）→important 非 crash。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = tmp_path / "live.json"
    live.write_text('{"hooks": [1]}', encoding="utf-8")
    findings = css.check_zcode_live_parity(_parity_inv(), live_path=live)
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_parity_command_string_wiring_ok(tmp_path, monkeypatch):
    """接線形態 robustness：Claude 式 command 字串（無 args）也算已部署。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = tmp_path / "live.json"
    live.write_text(
        json.dumps(
            {
                "hooks": {
                    "enabled": True,
                    "events": {
                        "PreToolUse": [
                            {
                                "matcher": "Edit|Write",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 /x/hooks/ok.py",
                                    }
                                ],
                            }
                        ]
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    assert css.check_zcode_live_parity(_parity_inv(), live_path=live) == []


def test_parity_hook_disabled_in_live_critical(tmp_path, monkeypatch):
    """F1①：live 單條 hook enabled:false＝看得到接線、看不到 fire（第三形態）。"""
    _write_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live = tmp_path / "live.json"
    live.write_text(
        json.dumps(
            {
                "hooks": {
                    "enabled": True,
                    "events": {
                        "PreToolUse": [
                            {
                                "matcher": "Edit|Write",
                                "hooks": [
                                    {
                                        "type": "process",
                                        "command": "python3",
                                        "args": ["/x/hooks/ok.py"],
                                        "enabled": False,
                                    }
                                ],
                            }
                        ]
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    findings = css.check_zcode_live_parity(_parity_inv(), live_path=live)
    assert len(findings) == 1
    assert findings[0][1] == "critical"


# --- agents_projection_sync（AIR-29）：subprocess 委派四路 ---


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _projection_inv():
    css = load_module("skills/scan-project/scripts/check_single_source.py")
    return next(i for i in css.INVARIANTS if i["id"] == "agents_projection_sync")


def _stub_generator(css, tmp_path, inv):
    gen = tmp_path / inv["generator"]
    gen.parent.mkdir(parents=True, exist_ok=True)
    gen.write_text("#!/usr/bin/env python3\n", encoding="utf-8")


def test_projection_sync_green(tmp_path, monkeypatch):
    css = load_module("skills/scan-project/scripts/check_single_source.py")
    inv = _projection_inv()
    _stub_generator(css, tmp_path, inv)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css.subprocess, "run", lambda *a, **k: _Proc())
    assert css.check_agents_projection_sync(inv) == []


def test_projection_sync_drift_critical(tmp_path, monkeypatch):
    css = load_module("skills/scan-project/scripts/check_single_source.py")
    inv = _projection_inv()
    _stub_generator(css, tmp_path, inv)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        css.subprocess,
        "run",
        lambda *a, **k: _Proc(returncode=1, stdout="agents/zcode/foo.md\n"),
    )
    findings = css.check_agents_projection_sync(inv)
    assert len(findings) == 1
    assert findings[0][1] == "critical"
    assert "foo.md" in findings[0][2]


def test_projection_sync_uv_missing_important(tmp_path, monkeypatch):
    css = load_module("skills/scan-project/scripts/check_single_source.py")
    inv = _projection_inv()
    _stub_generator(css, tmp_path, inv)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)

    def boom(*a, **k):
        raise FileNotFoundError("uv not in PATH")

    monkeypatch.setattr(css.subprocess, "run", boom)
    findings = css.check_agents_projection_sync(inv)
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_projection_sync_generator_missing_important(tmp_path, monkeypatch):
    css = load_module("skills/scan-project/scripts/check_single_source.py")
    inv = _projection_inv()
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)  # generator 不存在
    findings = css.check_agents_projection_sync(inv)
    assert len(findings) == 1
    assert findings[0][1] == "important"


# ---------------------------------------------------------------------------
# deploy_freshness：worktree authority——非 main worktree 的差異不誤報 stale
# （codex 09-06 審查 I-1：舊 worktree 跑 checker 曾把健康部署誤報 critical
# 並開出無條件 deploy 處方——會用非權威版本覆寫三個 harness）
# ---------------------------------------------------------------------------

_MARKER = "Generated by scripts/deploy_agents.py -- do not edit directly."


def _freshness_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "deploy_bundle_freshness")


def test_deploy_freshness_non_claude_paths_no_opencode():
    """AIR-102：非 Claude 三端檢查路徑＝~/.zcode、~/.codex、~/.config/muse
    （opencode 停用後殘留清掃——死路徑不得殘留於 invariant note）。"""
    note = _freshness_inv()["note"]
    assert "~/.zcode" in note
    assert "~/.codex" in note
    assert "~/.config/muse" in note
    assert "opencode" not in note.lower()


def _fake_deploy_repo(tmp_path: Path) -> Path:
    """tmp repo：假 deploy_agents.py（自帶 HEADER/TARGETS/build_bundle）＋已部署 target。"""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    target = tmp_path / "deployed.md"
    target.write_text(_MARKER + "\nSTALE", encoding="utf-8")
    (scripts / "deploy_agents.py").write_text(
        "from pathlib import Path\n"
        "RULES_DIR = Path(__file__).parent\n"
        f"HEADER = {_MARKER!r}\n"
        f"TARGETS = [Path({str(target)!r})]\n"
        "def discover_rules(d, scopes):\n    return []\n"
        "def build_bundle(paths, label):\n    return 'NEW-BUNDLE'\n",
        encoding="utf-8",
    )
    return tmp_path


def test_deploy_freshness_mismatch_in_main_worktree_is_critical(tmp_path, monkeypatch):
    _fake_deploy_repo(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css, "_main_worktree", lambda: tmp_path)
    monkeypatch.setattr(css, "_is_detached_head", lambda: False)
    findings = css.check_deploy_freshness(_freshness_inv())
    assert len(findings) == 1
    assert findings[0][1] == "critical"
    assert "deploy_agents.py" in findings[0][2]  # main worktree 才給 deploy 處方


def test_deploy_freshness_mismatch_in_linked_worktree_downgrades(tmp_path, monkeypatch):
    _fake_deploy_repo(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css, "_main_worktree", lambda: Path("/elsewhere/canonical"))
    findings = css.check_deploy_freshness(_freshness_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "非 main worktree" in findings[0][2]
    assert "勿在非 main worktree" in findings[0][2]  # 不得開無條件 deploy 處方


def test_deploy_freshness_worktree_undeterminable_downgrades(tmp_path, monkeypatch):
    _fake_deploy_repo(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css, "_main_worktree", lambda: None)
    findings = css.check_deploy_freshness(_freshness_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_deploy_freshness_detached_head_downgrades(tmp_path, monkeypatch):
    _fake_deploy_repo(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css, "_main_worktree", lambda: tmp_path)
    monkeypatch.setattr(css, "_is_detached_head", lambda: True)
    findings = css.check_deploy_freshness(_freshness_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "detached" in findings[0][2]


def _fake_variant_repo(tmp_path: Path) -> Path:
    """變體形態 fake：TARGETS＋expected_bundle_for（per-target 預期）。"""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    target = tmp_path / "deployed.md"
    (scripts / "deploy_agents.py").write_text(
        "from pathlib import Path\n"
        "RULES_DIR = Path(__file__).parent\n"
        f"HEADER = {_MARKER!r}\n"
        f"TARGETS = [Path({str(target)!r})]\n"
        "def discover_rules(d, scopes):\n    return []\n"
        "def build_bundle(paths, label, exclude=frozenset()):\n    return 'FULL:' + label\n"
        "def resolve_targets(home):\n    return []\n"
        "def expected_bundle_for(p):\n"
        f"    return ({_MARKER!r} + chr(10) + 'VARIANT').encode('utf-8')\n",
        encoding="utf-8",
    )
    return tmp_path


def test_deploy_freshness_variant_match_is_silent(tmp_path, monkeypatch):
    """muse 變體部署後 freshness 零誤報（F1：full bundle 比變體恆假的迴歸鎖）。"""
    _fake_variant_repo(tmp_path)
    target = tmp_path / "deployed.md"
    target.write_text(_MARKER + "\nVARIANT", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css, "_main_worktree", lambda: tmp_path)
    monkeypatch.setattr(css, "_is_detached_head", lambda: False)
    assert css.check_deploy_freshness(_freshness_inv()) == []


def test_deploy_freshness_variant_mismatch_is_critical(tmp_path, monkeypatch):
    _fake_variant_repo(tmp_path)
    target = tmp_path / "deployed.md"
    target.write_text(_MARKER + "\nSTALE", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css, "_main_worktree", lambda: tmp_path)
    monkeypatch.setattr(css, "_is_detached_head", lambda: False)
    findings = css.check_deploy_freshness(_freshness_inv())
    assert len(findings) == 1
    assert findings[0][1] == "critical"


# ---------------------------------------------------------------------------
# shell_provenance：殼 provenance gate 委派（followup B2c——lint 必須接進
# 機械閘門，不能只靠自身 unit test）
# ---------------------------------------------------------------------------


def _shell_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "report_shell_provenance")


def test_shell_provenance_violations_parsed_to_important(tmp_path, monkeypatch):
    import types

    css = load_module("skills/scan-project/scripts/check_single_source.py")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check_report_shells.py").write_text("pass\n")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css.shutil, "which", lambda _: "/usr/local/bin/uv")

    def fake_run(cmd, **kw):
        return types.SimpleNamespace(
            returncode=1,
            stdout="[FAIL] a/index.html: 同殼宣告多個互斥 projection SHA\n",
            stderr="",
        )

    monkeypatch.setattr(css.subprocess, "run", fake_run)
    findings = css.check_shell_provenance(_shell_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "互斥" in findings[0][2]


def test_shell_provenance_clean_returns_empty(tmp_path, monkeypatch):
    import types

    css = load_module("skills/scan-project/scripts/check_single_source.py")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check_report_shells.py").write_text("pass\n")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(css.shutil, "which", lambda _: "/usr/local/bin/uv")
    monkeypatch.setattr(
        css.subprocess,
        "run",
        lambda cmd, **kw: types.SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    assert css.check_shell_provenance(_shell_inv()) == []


def test_shell_provenance_script_missing_important(tmp_path, monkeypatch):
    css = load_module("skills/scan-project/scripts/check_single_source.py")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_shell_provenance(_shell_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"


# ------------------------------------------- bridge_model_vocab（AIR-78 AC#6）


def _vocab_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "bridge_model_vocab")


def _write_vocab_source(tmp_path):
    d = tmp_path / "skills" / "model-routing"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "glm 契約：--model native-ID-only；預設 GLM-5.3-Flash", encoding="utf-8"
    )


def _write_scan_skeleton(tmp_path):
    """建齊 invariant 的 scan entries——避免 dead-entry findings 污染計數斷言。"""
    _write_vocab_source(tmp_path)
    for entry in ("ai-development-guide.md", "AGENTS.md"):
        (tmp_path / entry).write_text("ok\n", encoding="utf-8")
    for d in ("rules", "agents", "hooks"):
        (tmp_path / d).mkdir(exist_ok=True)


def test_vocab_cc_flag_form_detected(tmp_path, monkeypatch):
    """AIR-78 AC#6：bridge `--model sonnet/opus` 殘留（VR-1 後＝bug）被抓。"""
    _write_scan_skeleton(tmp_path)
    (tmp_path / "skills" / "guide.md").write_text(
        '派發：task --family glm --model sonnet -- "p"', encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_vocab_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "sonnet" in findings[0][2]


def test_vocab_compound_slug_detected(tmp_path, monkeypatch):
    """vocabulary invariant：native＋alias 複合 slug 被抓（不分大小寫）。"""
    _write_scan_skeleton(tmp_path)
    (tmp_path / "rules" / "x.md").write_text(
        "錯誤示範 --model GLM-5.3-sonnet", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_vocab_inv())
    assert len(findings) == 1
    assert "複合" in findings[0][2] or "slug" in findings[0][2]


def test_vocab_cc_frontmatter_and_table_legal(tmp_path, monkeypatch):
    """CC 自身接線不誤報：`model: opus` frontmatter 形與 tier 表管道相鄰合法。"""
    _write_scan_skeleton(tmp_path)
    (tmp_path / "agents" / "role.md").write_text(
        "---\nmodel: opus\n---\nbody", encoding="utf-8"
    )
    (tmp_path / "skills" / "tier.md").write_text(
        "| lite | glm-5.3-flash | sonnet（CC 詞彙面） | haiku |", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_forbidden_pattern(_vocab_inv()) == []


def test_vocab_source_anchor_missing_critical(tmp_path, monkeypatch):
    """定義源 drift 自檢：契約錨點（must_contain_all）缺席＝critical。"""
    d = tmp_path / "skills" / "model-routing"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("（契約被洗掉的 drifted 內容）", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_vocab_inv())
    assert any(f[1] == "critical" and "native-ID-only" in f[2] for f in findings)


@pytest.mark.parametrize(
    ("line", "hit"),
    [
        ("task --family glm --model sonnet -- x", True),
        (
            "task --family glm --model Opus -- x",
            True,
        ),  # mixed case（VR-1 canonicalize 不分大小寫）
        ("task --family codex --model='SONNET' -- x", True),  # =/quote/case 形
        ("claude --model opus -p x", False),  # CC CLI 自身接線（vocabulary 句明文允許）
        ("model: opus", False),  # frontmatter 形
        ("| lite | glm-5.3-flash | sonnet（CC 詞彙面） | haiku |", False),  # tier 表
        ("觸發詞：opus、sonnet、haiku", False),  # description 觸發詞列舉
    ],
)
def test_vocab_flag_gate_matrix(tmp_path, monkeypatch, line, hit):
    """flag 形＝行級 gate（同行 --family 才算 bridge 面）＋case-insensitive（C-1/F4/F5）。"""
    _write_scan_skeleton(tmp_path)
    (tmp_path / "skills" / "guide.md").write_text(line + "\n", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f for f in css.check_forbidden_pattern(_vocab_inv()) if "guide.md" in f[2]
    ]
    assert bool(findings) is hit


@pytest.mark.parametrize(
    ("line", "hit"),
    [
        ("--model GLM-5.3-sonnet", True),  # native-first 複合
        ("--model sonnet-glm-5.3", True),  # alias-first 複合
        ("旗艦＝GLM-5.3；lite 用 sonnet（CC 詞彙面）", False),  # prose 相鄰非複合 token
    ],
)
def test_vocab_compound_matrix(tmp_path, monkeypatch, line, hit):
    _write_scan_skeleton(tmp_path)
    (tmp_path / "rules" / "x.md").write_text(line + "\n", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [f for f in css.check_forbidden_pattern(_vocab_inv()) if "x.md" in f[2]]
    assert bool(findings) is hit


def test_vocab_anchor_partial_missing_critical(tmp_path, monkeypatch):
    """must_contain_all 語義：只缺一個錨點也 critical（C-2——欄位名與 gate 語義一致）。"""
    _write_scan_skeleton(tmp_path)
    (tmp_path / "skills" / "model-routing" / "SKILL.md").write_text(
        "glm 契約：--model native-ID-only", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_vocab_inv())
    assert len(findings) == 1
    assert findings[0][1] == "critical"
    assert "GLM-5.3-Flash" in findings[0][2]


def test_vocab_source_file_absent_important(tmp_path, monkeypatch):
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_vocab_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "source 檔不存在" in findings[0][2]


def test_vocab_dead_scan_entry_important(tmp_path, monkeypatch):
    """scan entry 路徑死掉＝guard 面縮小，不得靜默（F6）。"""
    _write_vocab_source(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_vocab_inv())
    dead = [f for f in findings if "scan entry 不存在" in f[2]]
    assert dead, "死 entry 應各發一條 important"


# ---------------------- model_routing_current_doctrine（AIR-91 S4A）


def _doctrine_inv():
    return next(
        i for i in css.INVARIANTS if i["id"] == "model_routing_current_doctrine"
    )


def _write_doctrine_source(tmp_path):
    d = tmp_path / "skills" / "model-routing"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "AIR-91 doctrine：WorkUnitContract schema；供給事實＝catalog.toml；"
        "部署預設＝presets.toml",
        encoding="utf-8",
    )


def _write_doctrine_skeleton(tmp_path):
    """建齊 invariant 的 scan entries——避免 dead-entry findings 污染計數斷言。"""
    _write_doctrine_source(tmp_path)
    for entry in ("ai-development-guide.md", "AGENTS.md"):
        (tmp_path / entry).write_text("ok\n", encoding="utf-8")
    for d in ("rules", "agents", "hooks"):
        (tmp_path / d).mkdir(exist_ok=True)


def test_doctrine_tier_table_header_detected(tmp_path, monkeypatch):
    """AIR-91 S4：舊 tier 權威表 header（tier → (model,effort)／tier × provider）
    重現於任何 active .md＝current-doctrine drift（S2 已移除的權威形）。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "skills" / "guide.md").write_text(
        "## tier → (model, effort)\n", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f
        for f in css.check_forbidden_pattern(_doctrine_inv())
        if "guide.md" in f[2]
    ]
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_doctrine_tier_provider_header_detected(tmp_path, monkeypatch):
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "rules" / "x.md").write_text(
        "### tier × provider 權威表\n", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f for f in css.check_forbidden_pattern(_doctrine_inv()) if "x.md" in f[2]
    ]
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_doctrine_role_requirement_header_detected(tmp_path, monkeypatch):
    """role → requirement（tier）分配表 header＝舊 role→tier 兩跳權威形。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "skills" / "guide.md").write_text(
        "## role → requirement（tier）分配表\n", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f
        for f in css.check_forbidden_pattern(_doctrine_inv())
        if "guide.md" in f[2]
    ]
    assert len(findings) == 1


def test_doctrine_removal_marker_comment_not_flagged(tmp_path, monkeypatch):
    """S2 移除標記註解（<!-- ... legacy tier × provider 權威表已移除 -->）
    合法在場——header 錨定不誤中歷史標記（historical-exclusion）。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "skills" / "model-routing" / "SKILL.md").write_text(
        "WorkUnitContract；catalog.toml；presets.toml\n"
        "<!-- AIR-91 S2：legacy tier × provider 權威表已移除（等價 gate 通過）"
        "——legacy pins 填法表與 role→requirement 分配表已移除 -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_forbidden_pattern(_doctrine_inv()) == []


def test_doctrine_workflow_equals_tier_matrix(tmp_path, monkeypatch):
    """workflow 整體綁單一 tier（post-build=full 形）＝誤導整鏈單模型的舊寫法。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "skills" / "guide.md").write_text(
        "舊寫法：post-build=full\n", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f
        for f in css.check_forbidden_pattern(_doctrine_inv())
        if "guide.md" in f[2]
    ]
    assert len(findings) == 1

    (tmp_path / "skills" / "guide.md").write_text(
        "舊寫法：judge-review＝lite\n", encoding="utf-8"
    )
    findings = [
        f
        for f in css.check_forbidden_pattern(_doctrine_inv())
        if "guide.md" in f[2]
    ]
    assert len(findings) == 1


def test_doctrine_vision_tier_detected(tmp_path, monkeypatch):
    """vision tier＝把 capability filter 與強度列並排的舊單軸語義。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "agents" / "x.md").write_text(
        "vision tier 掛 CR 白名單\n", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f for f in css.check_forbidden_pattern(_doctrine_inv()) if "x.md" in f[2]
    ]
    assert len(findings) == 1


def test_doctrine_role_frontmatter_tier_tag_detected(tmp_path, monkeypatch):
    """S2 移除的 description tier tag 回歸（frontmatter `tier:` 形）被抓。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "agents" / "roles").mkdir(parents=True)
    (tmp_path / "agents" / "roles" / "r.md").write_text(
        "---\nname: r\ntier: full\n---\nbody\n", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = [
        f
        for f in css.check_forbidden_pattern(_doctrine_inv())
        if "roles" in f[2]
    ]
    assert len(findings) == 1


def test_doctrine_legal_compat_forms_not_flagged(tmp_path, monkeypatch):
    """相容形不誤報：presets requirement token 語義、lite-verify slug、
    handoff「建議執行 tier」欄、EP 規模 full、非 header 的 tier 詞彙 prose。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "agents" / "AGENTS.md").write_text(
        "requirement 相容 token（full/vision/lite）定義在 presets.toml allow_lists\n"
        "| lite-verify | lite | ✅ |\n"
        "| vision-review | vision | ✅ |\n",
        encoding="utf-8",
    )
    (tmp_path / "skills" / "handoff.md").write_text(
        "| 建議執行 tier | 條件式路由建議（非斷言、無模型名） |\n"
        "規模分級：standard/full\n"
        "spawn 並發以將 spawn 的 agent 所在 tier 為準（表在 model-routing）\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_forbidden_pattern(_doctrine_inv()) == []


def test_doctrine_anchor_missing_critical(tmp_path, monkeypatch):
    """定義源 drift 自檢：新 doctrine 錨點（must_contain_all）缺席＝critical。"""
    _write_doctrine_skeleton(tmp_path)
    (tmp_path / "skills" / "model-routing" / "SKILL.md").write_text(
        "（契約被洗掉的 drifted 內容）", encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_doctrine_inv())
    assert findings
    assert all(f[1] == "critical" for f in findings)
    assert any("WorkUnitContract" in f[2] for f in findings)


def test_doctrine_source_absent_important(tmp_path, monkeypatch):
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_doctrine_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "source 檔不存在" in findings[0][2]


def test_doctrine_dead_scan_entry_important(tmp_path, monkeypatch):
    """scan entry 死掉＝guard 面縮小，不得靜默（同 bridge_model_vocab F6 語義）。"""
    _write_doctrine_source(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_forbidden_pattern(_doctrine_inv())
    dead = [f for f in findings if "scan entry 不存在" in f[2]]
    assert dead
    assert all(f[1] == "important" for f in dead)
