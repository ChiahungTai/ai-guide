"""check_single_source 的 invariant 檢查單元測試（T1-2/T1-3）。"""

import inspect
import json
import re
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
    monkeypatch.setenv("HOME", str(tmp_path))  # 隔離 live ~ 路徑面（AIR-120）
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
    monkeypatch.setenv("HOME", str(tmp_path))  # 隔離 live ~ 路徑面（AIR-120）
    assert css.check_hook_registration(_hook_inv()) == []


def test_hook_registration_missing_reg_file_skipped(tmp_path, monkeypatch):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "a.py").write_text("pass")
    # settings.json 不存在（local/gitignored 機器）→ skip 不 false positive，
    # 但 governance/registrations/zcode.json 也不存在時仍應全部抓孤兒
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))  # 隔離 live ~ 路徑面（AIR-120）
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
    tpl_dir = tmp_path / "governance" / "registrations"
    tpl_dir.mkdir(parents=True)
    (tpl_dir / "zcode.json").write_text(json.dumps(TPL_JSON), encoding="utf-8")


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


# ---------------------------------------------------------------------------
# AIR-120：hook_registration 補 codex 註冊面（模板 codex.toml＋live ~/.codex/config.toml）
# 誤報實例：codex_memory_path_deny.py 已註冊於 governance/registrations/codex.toml
# （AIR-100 S-A 落地），舊 checker 只認 CC/ZCode 兩面 → 誤報孤兒 CRITICAL。
# ---------------------------------------------------------------------------

CODEX_TPL_TOML = (
    "[[hooks.PreToolUse]]\n"
    'matcher = "apply_patch"\n\n'
    "[[hooks.PreToolUse.hooks]]\n"
    'type = "command"\n'
    'command = "python3 {{REPO}}/hooks/codex_memory_path_deny.py"\n'
    "timeout = 10\n"
)


def _write_codex_tpl(tmp_path, text=CODEX_TPL_TOML):
    d = tmp_path / "governance" / "registrations"
    d.mkdir(parents=True, exist_ok=True)
    (d / "codex.toml").write_text(text, encoding="utf-8")


def test_hook_registration_inv_includes_codex_face():
    """AIR-120：registrations 需含 codex 模板與 live 兩個第三面條目。"""
    regs = _hook_inv()["registrations"]
    assert "governance/registrations/codex.toml" in regs
    assert "~/.codex/config.toml" in regs


def test_hook_registration_codex_toml_zero_orphan(tmp_path, monkeypatch):
    """AIR-120 RED→GREEN 主測試：codex.toml 模板註冊的 hook 不誤報孤兒。

    誤報形態重現：codex_memory_path_deny.py 只註冊於 codex 面（CC/ZCode 兩面
    皆無）——補面後零 findings。
    """
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "codex_memory_path_deny.py").write_text("pass")
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert css.check_hook_registration(_hook_inv()) == []


def test_hook_registration_inv_includes_cc_face():
    """0919 誤報更正：registrations 需含 Claude 端 repo 模板（cc.json）。

    settings.json 是 gitignored local-only（只在 main checkout）——非 main
    checkout 唯一可驗的 Claude 註冊證據＝cc.json（bi 雙腿 0919：加面即足，
    non-main 降權不採——降權把真孤兒一起靜默）。
    """
    regs = _hook_inv()["registrations"]
    assert "governance/registrations/cc.json" in regs


def test_hook_registration_cc_tpl_zero_orphan_non_main_checkout(tmp_path, monkeypatch):
    """0919 誤報更正主測試：settings.json 缺場＋cc.json 在場→零孤兒 findings。

    重現 0919 誤報形態：memory-dirty-sensor.py／memory-watch-seed.py 只註冊於
    CC 面（settings.json gitignored，非 main checkout 缺場）——cc.json 補面後
    任何 checkout 零 findings。fixture 用真實模板形（{{REPO}} 佔位符）——
    basename word-boundary 收斂正是要測的行為。
    """
    (tmp_path / "hooks").mkdir()
    reg_dir = tmp_path / "governance" / "registrations"
    reg_dir.mkdir(parents=True)
    for name in ("memory-dirty-sensor.py", "memory-watch-seed.py"):
        (tmp_path / "hooks" / name).write_text("pass")
    (reg_dir / "cc.json").write_text(
        '{"SessionStart": [{"type": "command", '
        '"command": "python3 {{REPO}}/hooks/memory-watch-seed.py"}], '
        '"FileChanged": [{"type": "command", '
        '"command": "python3 {{REPO}}/hooks/memory-dirty-sensor.py"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))  # live 面全缺場
    assert css.check_hook_registration(_hook_inv()) == []


def test_hook_registration_claude_only_is_absence_guard(tmp_path, monkeypatch):
    """claude_only＝缺席-證據 guard 非 allowlist：settings.json 在場但全模板
    面缺席的 claude_only 成員仍報 critical（豁免只在 Claude 面缺場時生效；
    bi 雙腿 0919——收緊契約文字防「懶得接線」蒙混）。以合成 inv 釘機制
    （REGISTRY 現名單已清空——tri F1）。"""
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "compact-tail-inject.py").write_text("pass")
    (tmp_path / "settings.json").write_text(
        '{"hooks": {"PostToolUse": [{"command": "python3 /x/hooks/other.py"}]}}',
        encoding="utf-8",
    )  # Claude 面在場但無本 hook 條目
    inv = dict(_hook_inv())
    inv["claude_only"] = ["compact-tail-inject.py"]  # 合成成員釘豁免機制
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    out = css.check_hook_registration(inv)
    assert any("compact-tail-inject.py" in msg for _, _, msg in out)


def test_hook_registration_claude_only_members_absent_from_templates():
    """tri F1 迴歸鎖：claude_only 成員不得出現在任何 tracked 模板面——
    名單與「已收編者禁列」契約自洽。"""
    inv = _hook_inv()
    template_texts = ""
    for rel in inv["registrations"]:
        if rel.startswith("~"):
            continue  # live 面非模板
        p = css.REPO_ROOT / rel
        if p.exists():
            template_texts += p.read_text(encoding="utf-8")
    for name in inv["claude_only"]:
        assert not re.search(rf"(?<![\w.-]){re.escape(name)}(?![\w.-])", template_texts), (
            f"claude_only 成員 {name} 已出現在 tracked 模板面——應移出豁免名單"
        )


def test_hook_registration_basename_edge_negative(tmp_path, monkeypatch):
    """tri F3：匹配器後緣防殘字樣——ok.py.bak／xa.py 殘形不算已註冊。"""
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "ok.py").write_text("pass")
    (tmp_path / "settings.json").write_text(
        '{"hooks": {"x": ["python3 /x/hooks/ok.py.bak", '
        '"python3 /x/hooks/xa.py"]}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    out = css.check_hook_registration(_hook_inv())
    assert any("ok.py" in msg for _, _, msg in out)


def test_hook_registration_live_tilde_face_counts(tmp_path, monkeypatch):
    """registrations 的 ~ 路徑（live config）在場時其文字也進註冊池。"""
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "a.py").write_text("pass")
    live_dir = tmp_path / ".codex"
    live_dir.mkdir()
    (live_dir / "config.toml").write_text(
        'command = "python3 /x/hooks/a.py"', encoding="utf-8"
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))  # ~ 展開指 tmp_path（live 在場）
    assert css.check_hook_registration(_hook_inv()) == []


# ---------------------------------------------------------------------------
# codex_live_parity（AIR-120）：codex.toml 模板接線必須已部署 live config
# （zcode_live_parity 的 codex 對應面——TOML 解析＋wiring 三元組對帳）
# ---------------------------------------------------------------------------


def _codex_parity_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "codex_live_parity")


def _codex_live(tmp_path, text):
    live = tmp_path / "codex-live.toml"
    live.write_text(text, encoding="utf-8")
    return live


CODEX_LIVE_TOML = (
    "[[hooks.PreToolUse]]\n"
    'matcher = "apply_patch"\n\n'
    "[[hooks.PreToolUse.hooks]]\n"
    'type = "command"\n'
    'command = "python3 /Users/x/ai-guide/hooks/codex_memory_path_deny.py"\n'
)


def test_codex_parity_all_deployed_ok(tmp_path, monkeypatch):
    """template wiring 全數在 live（{{REPO}} 佔位符 vs 絕對路徑由 basename 收斂）。"""
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert (
        css.check_codex_live_parity(
            _codex_parity_inv(), live_path=_codex_live(tmp_path, CODEX_LIVE_TOML)
        )
        == []
    )


def test_codex_parity_missing_in_live_critical(tmp_path, monkeypatch):
    """template 有、live 無（bare live 無該 hook）＝註冊≠fire critical。"""
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_codex_live_parity(
        _codex_parity_inv(), live_path=_codex_live(tmp_path, "# empty\n")
    )
    assert len(findings) == 1
    assert findings[0][1] == "critical"
    assert "codex_memory_path_deny.py" in findings[0][2]


def test_codex_parity_wrong_matcher_critical(tmp_path, monkeypatch):
    """檔名在 live 但掛錯 matcher（apply_patch 掛成 Bash）＝未部署。"""
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    wrong = CODEX_LIVE_TOML.replace('matcher = "apply_patch"', 'matcher = "Bash"')
    findings = css.check_codex_live_parity(
        _codex_parity_inv(), live_path=_codex_live(tmp_path, wrong)
    )
    assert len(findings) == 1
    assert findings[0][1] == "critical"


def test_codex_parity_live_absent_skip(tmp_path, monkeypatch):
    """live config 缺場（非 codex 機器）skip 不 false positive。"""
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert (
        css.check_codex_live_parity(
            _codex_parity_inv(), live_path=tmp_path / "nope.toml"
        )
        == []
    )


def test_codex_parity_template_missing_important(tmp_path, monkeypatch):
    """template 缺席 → important（INVARIANTS 路徑 typo 不炸整個 checker）。"""
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_codex_live_parity(
        _codex_parity_inv(), live_path=tmp_path / "live.toml"
    )
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_codex_parity_bad_toml_important(tmp_path, monkeypatch):
    """live config 手改壞（非 TOML）→ important 非 crash。"""
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_codex_live_parity(
        _codex_parity_inv(), live_path=_codex_live(tmp_path, "not [ valid toml\n")
    )
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_codex_parity_state_zone_ignored(tmp_path, monkeypatch):
    """live 的 [hooks.state]（trust 區，非 list 結構）不參與對帳也不炸。"""
    _write_codex_tpl(tmp_path)
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    live_text = (
        CODEX_LIVE_TOML
        + '[hooks.state."/Users/x/.codex/config.toml:pre_tool_use:0:0"]\n'
        'hash = "abc"\n'
    )
    assert (
        css.check_codex_live_parity(
            _codex_parity_inv(), live_path=_codex_live(tmp_path, live_text)
        )
        == []
    )


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


# ---------------------------------------------------------------------------
# skill_allowlist_coverage 的 tracked 鏡像（AIR-140）：settings.json 是
# gitignored local-only（只有 main checkout 在場），非 main checkout 缺場
# 時舊 check_coverage 靜默 return []（false negative：rename drift 不可見）
# ——補 tracked 鏡像 governance/registrations/cc-allowlist.json 三態證據面
# ---------------------------------------------------------------------------


def _coverage_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "skill_allowlist_coverage")


def _write_skill(tmp_path, name="my-skill"):
    d = tmp_path / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\n---\nbody", encoding="utf-8")


def _write_mirror(tmp_path, entries):
    d = tmp_path / "governance" / "registrations"
    d.mkdir(parents=True)
    (d / "cc-allowlist.json").write_text(
        json.dumps({"permissions": {"allow": entries}}), encoding="utf-8"
    )


def _write_live_allow(tmp_path, entries):
    (tmp_path / "settings.json").write_text(
        json.dumps({"permissions": {"allow": entries}}), encoding="utf-8"
    )


def test_coverage_inv_has_tracked_mirror():
    """AIR-140：invariant 需宣告 tracked 鏡像路徑＋note 誠實標示鏡像語義。"""
    inv = _coverage_inv()
    assert inv["tracked_mirror"] == "governance/registrations/cc-allowlist.json"
    assert "鏡像" in inv["note"]


def test_coverage_mirror_file_projection_shape():
    """AC#1：tracked 鏡像檔 tracked 在場，形＝permissions.allow 投影。"""
    mirror = css.REPO_ROOT / "governance" / "registrations" / "cc-allowlist.json"
    assert mirror.exists()
    data = json.loads(mirror.read_text(encoding="utf-8"))
    allow = data.get("permissions", {}).get("allow")
    assert isinstance(allow, list)
    assert allow, "鏡像 allow 不得為空（settings.json permissions.allow 非空投影）"


def test_coverage_mirror_only_missing_skill_important(tmp_path, monkeypatch):
    """缺 settings.json＋鏡像在場→照驗：skill 不在鏡像→important（rename drift
    在非 main checkout 可見——AIR-140 主訴求）。finding 誠實標示證據面為鏡像。"""
    _write_skill(tmp_path, "renamed-skill")
    _write_mirror(tmp_path, ["Skill(old-skill)", "Bash(git status:*)"])
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)  # settings.json 缺場
    findings = css.check_coverage(_coverage_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "renamed-skill" in findings[0][2]
    assert "cc-allowlist.json" in findings[0][2]


def test_coverage_mirror_only_synced_zero(tmp_path, monkeypatch):
    """缺 settings.json＋鏡像在場→skill 已覆蓋→零 finding。"""
    _write_skill(tmp_path, "my-skill")
    _write_mirror(tmp_path, ["Skill(my-skill)", "Bash(git status:*)"])
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_coverage(_coverage_inv()) == []


def test_coverage_both_faces_synced_zero(tmp_path, monkeypatch):
    """兩面都在場且同步→零 finding（不誤報 drift）。"""
    _write_skill(tmp_path, "my-skill")
    _write_mirror(tmp_path, ["Skill(my-skill)", "Bash(git status:*)"])
    _write_live_allow(tmp_path, ["Skill(my-skill)", "Bash(git status:*)"])
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_coverage(_coverage_inv()) == []


def test_coverage_both_faces_drift_important(tmp_path, monkeypatch):
    """兩面都在場且 allow 集合不一致→important（鏡像 stale）。"""
    _write_skill(tmp_path, "my-skill")
    _write_mirror(tmp_path, ["Skill(my-skill)"])
    _write_live_allow(tmp_path, ["Skill(my-skill)", "Skill(new-skill)", "Bash(git diff:*)"])
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_coverage(_coverage_inv())
    drift = [f for f in findings if "鏡像" in f[2]]
    assert len(drift) == 1
    assert drift[0][1] == "important"
    assert "Skill(new-skill)" in drift[0][2]


def test_coverage_drift_diff_head_five(tmp_path, monkeypatch):
    """drift finding 附差集合前 5 個元素（超出截斷）。"""
    _write_skill(tmp_path, "my-skill")
    _write_mirror(tmp_path, ["Skill(my-skill)"])
    extra = [f"Skill(x{i})" for i in range(7)]
    _write_live_allow(tmp_path, ["Skill(my-skill)", *extra])
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_coverage(_coverage_inv())
    drift = [f for f in findings if "鏡像" in f[2]]
    assert len(drift) == 1
    assert "Skill(x4)" in drift[0][2]
    assert "Skill(x5)" not in drift[0][2]
    assert "…" in drift[0][2]


def test_coverage_both_faces_absent_skip(tmp_path, monkeypatch):
    """兩面皆缺（不預期）→skip 不 false positive。"""
    _write_skill(tmp_path, "my-skill")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)  # settings.json 與鏡像皆缺場
    assert css.check_coverage(_coverage_inv()) == []


def test_coverage_malformed_mirror_important(tmp_path, monkeypatch):
    """鏡像在場但壞（非 JSON／結構缺）→important fail loud，不得靜默當零覆蓋。"""
    _write_skill(tmp_path, "my-skill")
    d = tmp_path / "governance" / "registrations"
    d.mkdir(parents=True)
    (d / "cc-allowlist.json").write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_coverage(_coverage_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
    assert "非 JSON" in findings[0][2]


# ---------------------------------------------------------------------------
# cc_live_parity（AIR-141）：cc.json 模板接線必須已部署 live settings.json
# （zcode/codex 面皆有 template→live 防線，CC 面補齊——cc.json 加接線、live
# 忘 merge → hook 從未 fire（F8 形狀）無人抓）。形態照抄 zcode_live_parity：
# wiring 三元組（event＋matcher＋script basename），{{REPO}} 佔位符與 live
# 絕對路徑由 basename 收斂；live 缺場（symlink 斷／非本機）skip 不 false
# positive；單向 template→live；CC 無 hooks.enabled 全域開關（無 enabled 檢查）
# ---------------------------------------------------------------------------


def _cc_parity_inv():
    return next(i for i in css.INVARIANTS if i["id"] == "cc_live_parity")


CC_TPL_JSON = {
    "Notification": [
        {
            "matcher": "",
            "hooks": [
                {"type": "command", "command": "{{REPO}}/hooks/notification.sh"}
            ],
        }
    ],
    "SessionStart": [
        {
            "matcher": "compact",
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 {{REPO}}/hooks/compact-tail-inject.py",
                }
            ],
        }
    ],
}


def _write_cc_tpl(tmp_path, data=CC_TPL_JSON):
    d = tmp_path / "governance" / "registrations"
    d.mkdir(parents=True)
    (d / "cc.json").write_text(json.dumps(data), encoding="utf-8")


def _write_cc_live(tmp_path, monkeypatch, events):
    """tri F1：live 檔寫在 $HOME/.claude/settings.json（CC 實讀路徑經 HOME hop）。"""
    d = tmp_path / ".claude"
    d.mkdir(parents=True, exist_ok=True)
    (d / "settings.json").write_text(json.dumps({"hooks": events}), encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))


def test_cc_parity_inv_registered():
    """AC#1：REGISTRY 新增 cc_live_parity invariant（形態對齊兩個既有 parity 面）。"""
    inv = _cc_parity_inv()
    assert inv["type"] == "cc_live_parity"
    assert inv["template"] == "governance/registrations/cc.json"
    assert inv["live"] == "~/.claude/settings.json"


def test_cc_parity_wired_into_main_loop():
    """新 invariant 接進主檢查迴圈（check_zcode_live_parity 被呼叫處照樣接）。"""
    src = inspect.getsource(css.main)
    assert "check_cc_live_parity(inv)" in src


def test_cc_parity_missing_in_live_critical(tmp_path, monkeypatch):
    """模板 hook live 缺→逐條 critical（F8 形狀：註冊≠fire）。"""
    _write_cc_tpl(tmp_path)
    _write_cc_live(tmp_path, monkeypatch, events={})
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_cc_live_parity(_cc_parity_inv())
    assert len(findings) == 2
    assert all(f[1] == "critical" for f in findings)
    assert any("notification.sh" in f[2] for f in findings)
    assert any("compact-tail-inject.py" in f[2] for f in findings)
    assert all("F8" in f[2] for f in findings)


def test_cc_parity_all_deployed_ok(tmp_path, monkeypatch):
    """兩面同步→零 finding。"""
    _write_cc_tpl(tmp_path)
    _write_cc_live(
        tmp_path,
        monkeypatch,
        events={
            "Notification": [
                {
                    "matcher": "",
                    "hooks": [
                        {"type": "command", "command": "/abs/repo/hooks/notification.sh"}
                    ],
                }
            ],
            "SessionStart": [
                {
                    "matcher": "compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 /abs/repo/hooks/compact-tail-inject.py",
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_cc_live_parity(_cc_parity_inv()) == []


def test_cc_parity_live_absent_skip(tmp_path, monkeypatch):
    """live 缺場（非本機／symlink 斷——CC 部署＝symlink 型）→skip 不 false positive。"""
    _write_cc_tpl(tmp_path)  # settings.json 不存在
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_cc_live_parity(_cc_parity_inv()) == []


def test_cc_parity_basename_convergence(tmp_path, monkeypatch):
    """basename 收斂：template {{REPO}}/hooks/x.py vs live /Users/.../hooks/x.py→零 finding
    （路徑前綴不同不誤報；matcher 一致才收斂）。"""
    _write_cc_tpl(tmp_path, data={"SessionStart": CC_TPL_JSON["SessionStart"]})
    _write_cc_live(
        tmp_path,
        monkeypatch,
        events={
            "SessionStart": [
                {
                    "matcher": "compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 "
                            "/Users/ctai/Github/ai-guide/hooks/compact-tail-inject.py",
                        }
                    ],
                }
            ]
        },
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_cc_live_parity(_cc_parity_inv()) == []


def test_cc_parity_live_extra_not_reported(tmp_path, monkeypatch):
    """單向 template→live：live 端手加的 hook 不誤報。"""
    _write_cc_tpl(tmp_path, data={"Notification": CC_TPL_JSON["Notification"]})
    _write_cc_live(
        tmp_path,
        monkeypatch,
        events={
            "Notification": [
                {
                    "matcher": "",
                    "hooks": [
                        {"type": "command", "command": "/abs/hooks/notification.sh"},
                        {"type": "command", "command": "python3 /abs/hooks/extra.py"},
                    ],
                }
            ]
        },
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    assert css.check_cc_live_parity(_cc_parity_inv()) == []


def test_cc_parity_wrong_matcher_critical(tmp_path, monkeypatch):
    """檔名在 live 但掛錯 matcher＝未部署（wiring 三元組的 matcher 腳）。"""
    _write_cc_tpl(tmp_path, data={"Notification": CC_TPL_JSON["Notification"]})
    _write_cc_live(
        tmp_path,
        monkeypatch,
        events={
            "Notification": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {"type": "command", "command": "/abs/hooks/notification.sh"}
                    ],
                }
            ]
        },
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_cc_live_parity(_cc_parity_inv())
    assert len(findings) == 1
    assert findings[0][1] == "critical"


def test_cc_parity_suffix_lookalike_critical(tmp_path, monkeypatch):
    """`x.py.bak` 殘字樣不算 x.py 已部署（negative lookahead，同 _wiring）。"""
    _write_cc_tpl(tmp_path, data={"SessionStart": CC_TPL_JSON["SessionStart"]})
    _write_cc_live(
        tmp_path,
        monkeypatch,
        events={
            "SessionStart": [
                {
                    "matcher": "compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 /abs/hooks/compact-tail-inject.py.bak",
                        }
                    ],
                }
            ]
        },
    )
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_cc_live_parity(_cc_parity_inv())
    assert len(findings) == 1
    assert findings[0][1] == "critical"


def test_cc_parity_template_missing_important(tmp_path, monkeypatch):
    """template 缺場→important（INVARIANTS 路徑 typo 不炸整個 checker）。"""
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    findings = css.check_cc_live_parity(_cc_parity_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_cc_parity_bad_json_important(tmp_path, monkeypatch):
    """兩面 JSON parse 失敗→important 非 crash。"""
    _write_cc_tpl(tmp_path)
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "settings.json").write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    findings = css.check_cc_live_parity(_cc_parity_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"


def test_cc_parity_live_hooks_not_dict_important(tmp_path, monkeypatch):
    """live hooks 區塊結構異常（合法 JSON 非 object）→important 非 crash。"""
    _write_cc_tpl(tmp_path)
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "settings.json").write_text('{"hooks": [1]}', encoding="utf-8")
    monkeypatch.setattr(css, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    findings = css.check_cc_live_parity(_cc_parity_inv())
    assert len(findings) == 1
    assert findings[0][1] == "important"
