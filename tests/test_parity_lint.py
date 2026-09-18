"""parity lint 測試（AIR-128）——三組單一源機械對帳。

三組：model token 對帳 catalog 集合／hook 三判準正典外重抄／outward
紅線枚舉正典外重抄。lint 實作住 sync_agents.py（--check 面承載，
「不建新框架」）；fixture 形態＝tmp 樹直接放 skills/rules 檔＋測試
自帶 catalog token 集合（lint 契約只吃 frozenset[str]，不依賴 catalog
物件——單向依賴：main(check) 衍生集合後呼叫 lint）。雙向驗證：植入
漂移被抓＋乾淨樹通過＋allowlist 豁免面承載。
"""

from pathlib import Path

from conftest import load_module

sync = load_module("scripts/sync_agents.py")

run_parity_lint = sync.run_parity_lint

CATALOG_TOKENS = frozenset(
    {
        "glm-5.3",
        "glm-5.3-flash",
        "claude-opus",
        "chatgpt-web-high",
        "gpt-5.6-sol",
        "gpt-6-astra",
        "fabel",
        "muse-spark-1.3",
        "chatgpt-web/high",
        "opus",
        "sonnet",
        "haiku",
    }
)


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / "skills" / "foo").mkdir(parents=True)
    (tmp_path / "rules").mkdir()
    return tmp_path


def write(tmp_path: Path, rel: str, text: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- 組1 model token 對帳 ---


def test_model_token_unknown_fails(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(repo, "skills/foo/SKILL.md", "派工用 gpt-9.9-phantom 處理。\n")
    violations = run_parity_lint(repo, CATALOG_TOKENS)
    assert any(
        "model-token" in v and "skills/foo/SKILL.md:1" in v for v in violations
    ), violations


def test_model_token_known_passes(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/foo/SKILL.md",
        "lite 機械段＝glm-5.3-flash；CC 詞彙＝sonnet。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_model_token_case_insensitive_canonicalizes(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(repo, "skills/foo/SKILL.md", "bridge 裸委派＝GLM-5.3-Flash。\n")
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_model_token_binding_slug_passes(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/foo/SKILL.md",
        "web 形態走 chatgpt-web/*（旗艦＝chatgpt-web/high）。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_model_token_policy_narrative_allowlisted(tmp_path: Path):
    """allowlist 真表覆蓋：model-routing 政策敘述的非 binding token 豁免。"""
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/model-routing/SKILL.md",
        "日常檔＝gpt-5.6-terra（政策敘述具名，catalog 未登記）。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_model_token_agent_workflow_format_allowlisted(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/agent-workflow/SKILL.md",
        "| `claude-sonnet-*` | sonnet（lite） |\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


# --- 組2 hook 三判準正典外重抄 ---


def test_hook_criteria_rewrite_fails(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/foo/SKILL.md",
        "機制設計：純機械＋單一入口＋無語義例外 → hook。\n",
    )
    violations = run_parity_lint(repo, CATALOG_TOKENS)
    assert any(
        "hook-criteria" in v and "skills/foo/SKILL.md" in v for v in violations
    ), violations


def test_hook_criteria_canon_passes(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/memory-audit/SKILL.md",
        "機制設計：純機械＋單一入口＋無語義例外 → hook。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_hook_criteria_partial_mention_passes(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(repo, "skills/foo/SKILL.md", "遷移非純機械替換。\n")
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_hook_criteria_argument_allowlisted(tmp_path: Path):
    """allowlist 真表覆蓋：instruction-writing 論證面（memory-audit 正典指針承接）。"""
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/instruction-writing/SKILL.md",
        "hook 三判準：單一入口、無語義例外、純機械。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


# --- 組3 outward 紅線枚舉正典外重抄 ---


def test_outward_redline_enum_fails(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(repo, "skills/foo/SKILL.md", "禁止：force push、付費操作不自主執行。\n")
    violations = run_parity_lint(repo, CATALOG_TOKENS)
    assert any(
        "outward-redline" in v and "skills/foo/SKILL.md" in v for v in violations
    ), violations


def test_outward_redline_in_other_rule_fails(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(repo, "rules/foo.md", "禁 force push 與 rm -rf。\n")
    violations = run_parity_lint(repo, CATALOG_TOKENS)
    assert any("outward-redline" in v and "rules/foo.md" in v for v in violations), (
        violations
    )


def test_outward_redline_single_mention_passes(tmp_path: Path):
    """單一 token 技術語境（rebase 安全欄杆論證）非枚舉表——閾值下 pass。"""
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/foo/SKILL.md",
        "trunk 已 push 時 rebase 就是 force-push 災難。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_outward_redline_allowlist_autonomous(tmp_path: Path):
    """allowlist 真表覆蓋：outward rule 明載的快查子集豁免。"""
    repo = make_repo(tmp_path)
    write(
        repo,
        "skills/autonomous-execution/SKILL.md",
        "紅線：rm -rf、git push --force、付費操作。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


def test_outward_redline_canon_in_rules_passes(tmp_path: Path):
    repo = make_repo(tmp_path)
    write(
        repo,
        "rules/outward-action-consent.md",
        "刪共享資料、付費、DB schema 皆 outward。\n",
    )
    assert run_parity_lint(repo, CATALOG_TOKENS) == []


# --- 整合：--check 面輸出契約（標記前綴——main 印出時即 parity gate 面） ---


def test_lint_output_contract_prefix(tmp_path: Path):
    """植入漂移的 fixture 案例能被抓，且輸出帶 [parity-lint] 標記前綴
    （main check 印出時即 parity gate 面可辨識）。"""
    repo = make_repo(tmp_path)
    write(repo, "skills/foo/SKILL.md", "派工用 gpt-9.9-phantom 處理。\n")
    violations = run_parity_lint(repo, CATALOG_TOKENS)
    assert violations, "植入漂移應被抓"
    assert all(v.startswith("[parity-lint]") for v in violations), violations
