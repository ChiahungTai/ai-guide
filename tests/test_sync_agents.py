"""sync_agents.py 純投影器測試（AIR-29 S2）。

覆蓋：schema/render/check purity/map/add-edit-delete/fork-collision/
adopt-legacy/missing pin/idempotence/target 欄位洩漏負向；
model supply catalog schema／loader／供給面 eligibility（AIR-91 S1）；
deployment presets loader／catalog+preset projection／legacy⇄new 全量
等價矩陣（AIR-91 S2）。fixture 形態＝寫入 agents/presets.toml＋
catalog.toml 後走 main 單一 code path（無 requirements 注入後門）；
真 repo 拓撲由 LEGACY_* golden 凍結對帳（等價矩陣）。
"""

from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

sync = load_module("scripts/sync_agents.py")

FIXTURE_LEGACY = {"agents/zcode/t-lite.md", "agents/zcode/t-full.md"}

PRESETS_FIXTURE = """schema_version = 1

[allow_lists]
harnesses = ["zcode", "claude"]
requirements = ["full", "vision", "lite"]

[[preset]]
slug = "t-lite"
requirement = "lite"
harness = ["zcode", "claude"]
read_write = "read-only"
sandbox = "default"
background = true

[preset.default_binding.zcode]
ref = "zcode-glm-5.3-flash"
effort = "high"

[[preset]]
slug = "t-vision"
requirement = "vision"
harness = ["zcode", "claude"]
read_write = "read-only"
sandbox = "default"
background = false

[preset.default_binding.zcode]
ref = "zcode-glm-5.3-flash"
effort = "high"

[[preset]]
slug = "t-full"
requirement = "full"
harness = ["zcode", "claude"]
read_write = "read-write"
sandbox = "default"
background = true

[preset.default_binding.zcode]
ref = "zcode-glm-5.3"
effort = "high"

[preset.default_binding.claude]
ref = "cc-opus"
"""

ROLE_LITE = """---
name: t-lite
description: "lite 測試角色"
tools: Read, Bash, mcp__plugin_code-reality_code-reality__refs
background: true
---

## 目標

測試 lite 投影。

## 做法

- 機械執行
"""

ROLE_VISION = """---
name: t-vision
description: "vision 測試角色"
tools: Read, Bash
---

## 目標

測試 vision 投影。
"""

ROLE_FULL = """---
name: t-full
description: "full 測試角色"
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__context7__query-docs, mcp__plugin_code-reality_code-reality__refs
background: true
---

## 目標

測試 full 投影。
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    roles = tmp_path / "agents" / "roles"
    roles.mkdir(parents=True)
    (roles / "t-lite.md").write_text(ROLE_LITE, encoding="utf-8")
    (roles / "t-vision.md").write_text(ROLE_VISION, encoding="utf-8")
    (roles / "t-full.md").write_text(ROLE_FULL, encoding="utf-8")
    (tmp_path / "agents" / "zcode").mkdir()
    (tmp_path / "agents" / "claude").mkdir()
    (tmp_path / "agents" / "presets.toml").write_text(PRESETS_FIXTURE, encoding="utf-8")
    catalog = tmp_path / "skills" / "model-routing" / "catalog.toml"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(CATALOG_FIXTURE, encoding="utf-8")
    return tmp_path


def run(repo: Path, mode: str) -> int:
    return sync.main(repo, mode=mode, legacy_paths=FIXTURE_LEGACY)


def expected(repo: Path) -> dict[Path, str]:
    return sync.expected_projections(repo)


def pins(repo: Path, slug: str, harness: str):
    """fixture repo 的 (binding, effort) 解析——render 測試走與 prod 相同路徑。"""
    catalog = sync.load_catalog(repo)
    presets = sync.load_presets(repo)
    return sync.resolve_deployment(catalog, presets)[slug][harness]


# --- schema / render / exact bytes ---


def test_render_zcode_lite_adds_pins(repo: Path):
    binding, effort = pins(repo, "t-lite", "zcode")
    rendered = sync.render_registry("t-lite", ROLE_LITE, "zcode", binding, effort)
    assert rendered.startswith("---\n")
    assert "model: glm-5.3-flash" in rendered
    assert "thoughtLevel: high" in rendered
    # marker 僅在 closing fence 後（YAML 可解析性不因 marker 破壞）
    head = rendered.split("\n---\n", 1)[0]
    assert head.startswith("---\n")
    assert sync.OWNERSHIP_MARKER not in head
    assert sync.OWNERSHIP_MARKER in rendered.split("\n---\n", 1)[1][:80]
    # zcode 保留 CR MCP 全名
    assert "mcp__plugin_code-reality_code-reality__refs" in rendered


def test_render_zcode_full_pins_flagship(repo: Path):
    binding, effort = pins(repo, "t-full", "zcode")
    rendered = sync.render_registry("t-full", ROLE_FULL, "zcode", binding, effort)
    head = rendered.split("\n---\n")[0]
    # 精確斷言含結尾換行——防 "glm-5.3" ⊂ "glm-5.3-flash" 前綴假綠（EP R4）
    assert "model: glm-5.3\n" in head
    assert "thoughtLevel: high" in head


def test_render_claude_full_pins_alias_and_strips_cr_mcp(repo: Path):
    """CC 端 full 別名釘選（AIR-44）：model: opus（別名層——env 映射切
    provider 時 alias 直接可用、免重釘）；無 thoughtLevel（CC effort＝spawn-time
    enum 非 frontmatter）。CR MCP 剝除不變。"""
    binding, effort = pins(repo, "t-full", "claude")
    rendered = sync.render_registry("t-full", ROLE_FULL, "claude", binding, effort)
    head = rendered.split("\n---\n")[0]
    # 精確尾斷言——pin 是 frontmatter 最後一行，尾換行屬 --- 分隔符不在 head 內
    assert head.endswith("model: opus")
    assert "thoughtLevel" not in head
    assert "mcp__plugin_code-reality_code-reality__" not in rendered
    # 非 CR 的 MCP 全名保留（context7）
    assert "mcp__context7__query-docs" in rendered


def test_render_claude_lite_inherit_no_pins(repo: Path):
    """lite 在 claude 端無 default binding＝inherit（spawn-time model/effort）。"""
    binding, effort = pins(repo, "t-lite", "claude")
    assert binding is None and effort is None
    rendered = sync.render_registry("t-lite", ROLE_LITE, "claude", binding, effort)
    assert "model:" not in rendered.split("\n---\n")[0]


# --- missing policy key fail loud ---


def test_missing_requirement_fails_loud(repo: Path):
    (repo / "agents" / "roles" / "t-extra.md").write_text(
        ROLE_LITE.replace("t-lite", "t-extra"), encoding="utf-8"
    )
    with pytest.raises(AssertionError):
        expected(repo)


# --- check purity（零寫入 tripwire）---


def _snapshot_tree(root: Path) -> dict[Path, tuple[int, bytes]]:
    snap: dict[Path, tuple[int, bytes]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snap[path] = (path.stat().st_mtime_ns, path.read_bytes())
    return snap


def test_check_mode_never_writes(repo: Path):
    assert run(repo, "sync") == 0
    before = _snapshot_tree(repo)
    exit_code = run(repo, "check")
    assert exit_code == 0
    assert _snapshot_tree(repo) == before  # mtime+content tripwire


def test_check_reports_drift_nonzero_without_write(repo: Path):
    (repo / "agents" / "zcode" / "t-lite.md").write_text(
        "hand-edited", encoding="utf-8"
    )
    before = _snapshot_tree(repo)
    exit_code = run(repo, "check")
    assert exit_code == 1
    assert _snapshot_tree(repo) == before


# --- map ---


def test_map_fixed_columns_and_sorted_roles(repo: Path):
    table = sync.render_map(expected(repo), presets=sync.load_presets(repo))
    lines = table.splitlines()
    assert lines[0] == "role\trequirement\tzcode\tclaude"
    roles = [line.split("\t")[0] for line in lines[1:]]
    assert roles == sorted(roles)
    reqs = {line.split("\t")[0]: line.split("\t")[1] for line in lines[1:]}
    assert reqs == {"t-lite": "lite", "t-vision": "vision", "t-full": "full"}


def test_map_verbose_extends_columns(repo: Path):
    """--map --verbose：前四欄相容不變，擴充 preset/binding/token kind/capabilities。"""
    catalog = sync.load_catalog(repo)
    presets = sync.load_presets(repo)
    resolved = sync.resolve_deployment(catalog, presets)
    table = sync.render_map(
        expected(repo),
        presets=presets,
        resolved=resolved,
        catalog=catalog,
        verbose=True,
    )
    lines = table.splitlines()
    header = lines[0].split("\t")
    assert header[:4] == ["role", "requirement", "zcode", "claude"]
    extra = header[4:]
    assert extra == [
        "preset.zcode_binding",
        "preset.zcode_model",
        "preset.zcode_effort",
        "preset.zcode_token_kind",
        "preset.zcode_model_identity",
        "preset.claude_binding",
        "preset.claude_model",
        "preset.claude_effort",
        "preset.claude_token_kind",
        "preset.claude_model_identity",
        "model_capabilities",
    ]
    by_role = {
        line.split("\t")[0]: dict(zip(header, line.split("\t"))) for line in lines[1:]
    }
    full = by_role["t-full"]
    assert full["preset.zcode_binding"] == "zcode-glm-5.3"
    assert full["preset.zcode_model"] == "glm-5.3"
    assert full["preset.zcode_effort"] == "high"
    assert full["preset.zcode_token_kind"] == "provider_native"
    assert full["preset.claude_binding"] == "cc-opus"
    assert full["preset.claude_model"] == "opus"
    assert full["preset.claude_token_kind"] == "harness_alias"
    assert full["preset.claude_model_identity"] == "claude-opus"
    lite = by_role["t-lite"]
    assert lite["preset.claude_binding"] == "inherit"
    assert lite["preset.claude_model"] == "-"
    vision = by_role["t-vision"]
    assert vision["model_capabilities"] == "glm-5.3-flash:native_vision"


# --- sync / idempotence / add-edit-delete ---


def test_sync_then_check_green_and_idempotent(repo: Path):
    assert run(repo, "sync") == 0
    zcode = repo / "agents" / "zcode"
    claude = repo / "agents" / "claude"
    assert len(list(zcode.glob("*.md"))) == 3
    assert len(list(claude.glob("*.md"))) == 3
    assert run(repo, "check") == 0
    before = _snapshot_tree(repo)
    assert run(repo, "sync") == 0  # second run no diff
    assert _snapshot_tree(repo) == before


def test_edit_role_body_produces_drift_then_resync(repo: Path):
    assert run(repo, "sync") == 0
    body = (repo / "agents" / "roles" / "t-lite.md").read_text(encoding="utf-8")
    (repo / "agents" / "roles" / "t-lite.md").write_text(
        body + "\n新增一行\n", encoding="utf-8"
    )
    assert run(repo, "check") == 1
    assert run(repo, "sync") == 0
    assert run(repo, "check") == 0


def test_delete_role_cleans_marker_owned_only(repo: Path):
    assert run(repo, "sync") == 0
    # unmarked fork（人工檔）必須保留
    fork = repo / "agents" / "zcode" / "manual-fork.md"
    fork.write_text("---\nname: manual-fork\n---\nbody\n", encoding="utf-8")
    # 刪 role＝刪檔＋刪 preset（單側刪除被 mismatch fail loud 擋——exit 2）
    (repo / "agents" / "roles" / "t-vision.md").unlink()
    assert run(repo, "sync") == 2  # preset 仍含 t-vision → fatal
    start = PRESETS_FIXTURE.index('[[preset]]\nslug = "t-vision"')
    end = PRESETS_FIXTURE.index('[[preset]]\nslug = "t-full"')
    (repo / "agents" / "presets.toml").write_text(
        PRESETS_FIXTURE[:start] + PRESETS_FIXTURE[end:], encoding="utf-8"
    )
    assert run(repo, "sync") == 0
    assert not (repo / "agents" / "zcode" / "t-vision.md").exists()
    assert not (repo / "agents" / "claude" / "t-vision.md").exists()
    assert fork.exists()  # stale cleanup 只刪 marker-owned


# --- fork / collision ---


def test_unmarked_same_name_file_blocks_sync(repo: Path):
    (repo / "agents" / "zcode" / "t-lite.md").write_text(
        "---\nname: t-lite\n---\n任何內容\n", encoding="utf-8"
    )
    with pytest.raises(AssertionError):
        run(repo, "sync")


def test_exact_equal_unmarked_fork_still_blocks_default_sync(repo: Path):
    """F3-05：exact-byte 相等不能讓 default sync 靜默收編人工 fork。"""
    exp = expected(repo)
    target = repo / "agents" / "zcode" / "t-lite.md"
    target.write_text(
        exp[target].replace(sync.OWNERSHIP_MARKER + "\n", "", 1),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        run(repo, "sync")


# --- adopt-legacy ---


def test_adopt_legacy_exact_paths_only(repo: Path):
    exp = expected(repo)
    for rel in sorted(FIXTURE_LEGACY):
        target = repo / rel
        target.write_text(
            exp[target].replace(sync.OWNERSHIP_MARKER + "\n", "", 1),
            encoding="utf-8",
        )
    assert run(repo, "adopt-legacy") == 0
    assert run(repo, "check") == 0


def test_adopt_legacy_rejects_divergent_bytes(repo: Path):
    (repo / "agents" / "zcode" / "t-lite.md").write_text(
        "---\nname: t-lite\n---\ndivergent\n", encoding="utf-8"
    )
    with pytest.raises(AssertionError):
        run(repo, "adopt-legacy")


# --- parity（真 repo）：legacy dict↔skill 表 parity 測試已隨 AIR-91 S2 刪除
# --- （dict/parser/check_parity 同步移除；等價由 LEGACY_* golden 矩陣承接）---


def test_main_fatal_exits_2_not_1(repo: Path):
    """muse F1：parity/mismatch fatal 的 exit 語義與 drift（1）分離——checker 據此分級。"""
    (repo / "agents" / "roles" / "t-ghost.md").write_text(ROLE_LITE, encoding="utf-8")
    rc = run(repo, "check")  # fixture presets 缺 t-ghost → mismatch
    assert rc == 2


def test_split_frontmatter_reports_distinct_errors():
    """C-4：BOM／缺 frontmatter／未閉合／空 frontmatter／非法鍵分別報。"""
    with pytest.raises(AssertionError, match="BOM"):
        sync.split_frontmatter("t", "\ufeff---\nname: t\n---\nbody")
    with pytest.raises(AssertionError, match="缺 frontmatter"):
        sync.split_frontmatter("t", "name: t\n")
    with pytest.raises(AssertionError, match="未閉合"):
        sync.split_frontmatter("t", "---\nname: t\n")
    with pytest.raises(AssertionError, match="為空"):
        sync.split_frontmatter("t", "---\n---\nbody")
    with pytest.raises(AssertionError, match="白名單"):
        sync.split_frontmatter("t", "---\nname: t\nmodel: x\n---\nbody")


def test_claude_projection_all_cr_tools_fails_loud():
    """C-5：源 tools 只剩 CR MCP 全名時，claude 投影 fail 而非輸出空清單。"""
    role = ROLE_LITE.replace(
        "tools: Read, Bash, mcp__plugin_code-reality_code-reality__refs",
        "tools: mcp__plugin_code-reality_code-reality__refs",
    )
    with pytest.raises(AssertionError, match="tools 全空"):
        sync.render_registry("t-lite", role, "claude", None, None)


def test_map_reflects_disk_state_not_policy(repo: Path):
    """F2：map 的 registry 欄反映磁碟（owned）——手刪生成檔後該欄 no。"""
    exp = expected(repo)
    assert run(repo, "sync") == 0
    owned = sync.inventory_owned_outputs(repo)
    full_map = sync.render_map(exp, presets=sync.load_presets(repo), owned=owned)
    assert "t-lite\tlite\tyes\tyes" in full_map
    (repo / "agents" / "zcode" / "t-lite.md").unlink()
    owned = sync.inventory_owned_outputs(repo)
    after = sync.render_map(exp, presets=sync.load_presets(repo), owned=owned)
    assert "t-lite\tlite\tno\tyes" in after


def test_atomic_write_leaves_no_partial_file_on_error(repo: Path, monkeypatch):
    """C-1：寫入中途失敗不留半損檔（tmp 清除、原檔不動）。"""
    target = repo / "agents" / "zcode" / "t-lite.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("original", encoding="utf-8")

    def boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(sync.tempfile, "mkstemp", boom)
    with pytest.raises(RuntimeError):
        sync.atomic_write(target, "new content")
    assert target.read_text(encoding="utf-8") == "original"
    assert list(target.parent.glob(".*.tmp")) == []


# --- 真樹 snapshot（U-8）：9-role 集合與 requirement compat token 入庫釘住（AIR-74 退役渲染 agent 後 10→9） ---


def test_real_tree_map_snapshot():
    exp = sync.expected_projections(REPO_ROOT)
    owned = sync.inventory_owned_outputs(REPO_ROOT)
    table = sync.render_map(exp, presets=sync.load_presets(REPO_ROOT), owned=owned)
    lines = table.splitlines()
    roles = {line.split("\t")[0]: line.split("\t")[1] for line in lines[1:]}
    assert roles == LEGACY_ROLE_REQUIREMENTS
    assert len(roles) == 9
    assert all(
        line.split("\t")[2] == "yes" and line.split("\t")[3] == "yes"
        for line in lines[1:]
    )


# --- golden bytes（C-6）：全文手寫錨——獨立於被測 render ---


def test_render_golden_bytes_full_role(repo: Path):
    role = (
        "---\n"
        "name: golden\n"
        'description: "golden anchor"\n'
        "tools: Read, Bash\n"
        "background: true\n"
        "---\n"
        "\n## 目標\n\nanchor body。\n"
    )
    zcode_binding, zcode_effort = pins(repo, "t-lite", "zcode")
    zcode = sync.render_registry("golden", role, "zcode", zcode_binding, zcode_effort)
    assert zcode == (
        "---\n"
        "name: golden\n"
        'description: "golden anchor"\n'
        "tools: Read, Bash\n"
        "background: true\n"
        "model: glm-5.3-flash\n"
        "thoughtLevel: high\n"
        "---\n"
        f"{sync.OWNERSHIP_MARKER}\n"
        "\n## 目標\n\nanchor body。\n"
    )
    claude_binding, _ = pins(repo, "t-full", "claude")
    claude = sync.render_registry("golden", role, "claude", claude_binding, None)
    assert claude == (
        "---\n"
        "name: golden\n"
        'description: "golden anchor"\n'
        "tools: Read, Bash\n"
        "background: true\n"
        "model: opus\n"
        "---\n"
        f"{sync.OWNERSHIP_MARKER}\n"
        "\n## 目標\n\nanchor body。\n"
    )


def test_render_golden_bytes_full_role_pins(repo: Path):
    """golden bytes：zcode full 生成形態（AIR-43 釘選——model: glm-5.3＋thoughtLevel: high）；
    claude 對照（AIR-44——model: opus 別名釘選、無 thoughtLevel）。"""
    role = (
        "---\n"
        "name: golden-full\n"
        'description: "golden full anchor"\n'
        "tools: Read, Bash\n"
        "background: true\n"
        "---\n"
        "\n## 目標\n\nanchor body。\n"
    )
    zcode_binding, zcode_effort = pins(repo, "t-full", "zcode")
    zcode = sync.render_registry(
        "golden-full", role, "zcode", zcode_binding, zcode_effort
    )
    assert zcode == (
        "---\n"
        "name: golden-full\n"
        'description: "golden full anchor"\n'
        "tools: Read, Bash\n"
        "background: true\n"
        "model: glm-5.3\n"
        "thoughtLevel: high\n"
        "---\n"
        f"{sync.OWNERSHIP_MARKER}\n"
        "\n## 目標\n\nanchor body。\n"
    )
    claude_binding, _ = pins(repo, "t-full", "claude")
    claude = sync.render_registry("golden-full", role, "claude", claude_binding, None)
    assert claude == (
        "---\n"
        "name: golden-full\n"
        'description: "golden full anchor"\n'
        "tools: Read, Bash\n"
        "background: true\n"
        "model: opus\n"
        "---\n"
        f"{sync.OWNERSHIP_MARKER}\n"
        "\n## 目標\n\nanchor body。\n"
    )


# --- AIR-91 S1：model supply catalog——schema loader／validator／供給面 eligibility ---
#
# 行為契約：正式 resolver 是 model-routing skill 的 instruction protocol（權威）；
# 以下 parse／eligibility 測試只證 catalog schema 與機械選擇層（lite test＝規格
# 陳述），不高報為 model 品質證據；runtime failure injection 留 S3。

CATALOG_FIXTURE = """schema_version = 1

[allow_lists]
workloads = [
  "ep_synthesis",
  "adjudication",
  "implement_from_accepted_ep",
  "evidence_retrieval",
  "review_findings",
  "visual_observation",
]
harness_alias_tokens = ["sonnet", "haiku", "opus"]

[[model_identity]]
id = "glm-5.3"

[[model_identity]]
id = "glm-5.3-flash"
[[model_identity.capability]]
name = "native_vision"
evidence = "repo_observed"

[[model_identity]]
id = "claude-opus"

[[model_identity]]
id = "chatgpt-web-high"

[[model_identity]]
id = "gpt-5.6-sol"

[[model_identity]]
id = "muse-spark-1.3"
[[model_identity.capability]]
name = "native_vision"
evidence = "repo_observed"

[[dispatch_binding]]
id = "zcode-glm-5.3"
model_identity = "glm-5.3"
carrier = "zcode"
surface = "agent-definition"
token = "glm-5.3"
token_kind = "provider_native"
effort_encoding = "field"
effort_values = ["low", "high", "max"]

[[dispatch_binding]]
id = "zcode-glm-5.3-flash"
model_identity = "glm-5.3-flash"
carrier = "zcode"
surface = "agent-definition"
token = "glm-5.3-flash"
token_kind = "provider_native"
effort_encoding = "field"
effort_values = ["low", "high", "max"]
transport = ["image_transport"]

[[dispatch_binding]]
id = "cc-opus"
model_identity = "claude-opus"
carrier = "claude-code"
surface = "agent-definition"
token = "opus"
token_kind = "harness_alias"
effort_encoding = "param"
effort_values = ["low", "high"]

[[dispatch_binding]]
id = "bridge-glm-5.3"
model_identity = "glm-5.3"
carrier = "bridge"
surface = "glm-family"
token = "GLM-5.3"
token_kind = "provider_native"
effort_encoding = "unsupported"

[[dispatch_binding]]
id = "bridge-glm-5.3-flash"
model_identity = "glm-5.3-flash"
carrier = "bridge"
surface = "glm-family"
token = "GLM-5.3-Flash"
token_kind = "provider_native"
effort_encoding = "unsupported"

[[dispatch_binding]]
id = "bridge-codex-web-high"
model_identity = "chatgpt-web-high"
carrier = "bridge"
surface = "codex-family"
token = "chatgpt-web/high"
token_kind = "carrier_slug"
effort_encoding = "slug_fixed"
fixed_effort = "high"

[[dispatch_binding]]
id = "bridge-codex-sol"
model_identity = "gpt-5.6-sol"
carrier = "bridge"
surface = "codex-family"
token = "gpt-5.6-sol"
token_kind = "provider_native"
effort_encoding = "param"
effort_values = ["minimal", "low", "medium", "high", "xhigh"]

[[dispatch_binding]]
id = "bridge-muse-spark"
model_identity = "muse-spark-1.3"
carrier = "bridge"
surface = "muse-family"
token = "muse-spark-1.3"
token_kind = "provider_native"
effort_encoding = "param"
effort_values = ["low", "medium", "high", "xhigh", "ultra"]
transport = ["image_transport"]

[[qualification]]
workload = "ep_synthesis"
model_identity = "glm-5.3"
status = "qualified"
evidence_source = "user_observed"
binding_scope = ["*"]

[[qualification]]
workload = "ep_synthesis"
model_identity = "chatgpt-web-high"
status = "qualified"
evidence_source = "user_observed"
binding_scope = ["*"]
minimum_effective_effort = "high"

[[qualification]]
workload = "ep_synthesis"
model_identity = "gpt-5.6-sol"
status = "qualified"
evidence_source = "user_observed"
binding_scope = ["*"]
minimum_effective_effort = "high"

[[qualification]]
workload = "ep_synthesis"
model_identity = "muse-spark-1.3"
status = "conditional"
evidence_source = "user_observed"
binding_scope = ["bridge-muse-spark"]
minimum_effective_effort = "xhigh"

[[qualification]]
workload = "adjudication"
model_identity = "claude-opus"
status = "qualified"
evidence_source = "user_observed"
binding_scope = ["*"]

[[qualification]]
workload = "visual_observation"
model_identity = "glm-5.3-flash"
status = "qualified"
evidence_source = "user_observed"
binding_scope = ["zcode-glm-5.3-flash"]
"""


def load_fixture_catalog() -> "sync.ModelCatalog":
    return sync.parse_catalog(CATALOG_FIXTURE)


def mutated_catalog(anchor: str, replacement: str, *, append: str = "") -> str:
    """fixture 定點變異（錨點在場由斷言保證——防 fixture 漂移後假綠）。"""
    if append:
        assert not anchor and not replacement
        return CATALOG_FIXTURE + append
    assert anchor in CATALOG_FIXTURE, f"mutation anchor missing: {anchor!r}"
    return CATALOG_FIXTURE.replace(anchor, replacement, 1)


# --- RED：schema／validator fail-loud（negative fields）---


def test_catalog_rejects_duplicate_identity_id():
    text = mutated_catalog("", "", append='\n[[model_identity]]\nid = "glm-5.3"\n')
    with pytest.raises(AssertionError, match="duplicate model_identity id"):
        sync.parse_catalog(text)


def test_catalog_rejects_duplicate_binding_id():
    text = mutated_catalog(
        "",
        "",
        append=(
            "\n[[dispatch_binding]]\n"
            'id = "cc-opus"\n'
            'model_identity = "claude-opus"\n'
            'carrier = "claude-code"\n'
            'surface = "agent-definition"\n'
            'token = "haiku"\n'
            'token_kind = "harness_alias"\n'
            'effort_encoding = "param"\n'
            'effort_values = ["low", "high"]\n'
        ),
    )
    with pytest.raises(AssertionError, match="duplicate dispatch_binding id"):
        sync.parse_catalog(text)


def test_catalog_rejects_duplicate_binding_token_scope():
    text = mutated_catalog(
        'id = "zcode-glm-5.3"\nmodel_identity = "glm-5.3"\ncarrier = "zcode"',
        'id = "zcode-glm-5.3-clone"\nmodel_identity = "glm-5.3"\ncarrier = "zcode"',
    )
    text += (
        "\n[[dispatch_binding]]\n"
        'id = "zcode-glm-5.3"\n'
        'model_identity = "glm-5.3"\n'
        'carrier = "zcode"\n'
        'surface = "agent-definition"\n'
        'token = "glm-5.3"\n'
        'token_kind = "provider_native"\n'
        'effort_encoding = "field"\n'
        'effort_values = ["low", "high", "max"]\n'
    )
    with pytest.raises(AssertionError, match="duplicate token scope"):
        sync.parse_catalog(text)


def test_catalog_rejects_unknown_token_kind():
    text = mutated_catalog(
        'token = "opus"\ntoken_kind = "harness_alias"',
        'token = "opus"\ntoken_kind = "hybrid_alias"',
    )
    with pytest.raises(AssertionError, match="unknown token_kind"):
        sync.parse_catalog(text)


def test_catalog_rejects_availability_in_status_or_evidence():
    """availability 禁入 status／evidence_source 任一欄（volatile → snapshot）。"""
    text = mutated_catalog('status = "conditional"', 'status = "available"')
    with pytest.raises(AssertionError, match=r"status 'available'"):
        sync.parse_catalog(text)
    text = mutated_catalog(
        'workload = "ep_synthesis"\nmodel_identity = "glm-5.3"\n'
        'status = "qualified"\nevidence_source = "user_observed"',
        'workload = "ep_synthesis"\nmodel_identity = "glm-5.3"\n'
        'status = "qualified"\nevidence_source = "available_now"',
    )
    with pytest.raises(AssertionError, match=r"evidence_source 'available_now'"):
        sync.parse_catalog(text)


@pytest.mark.parametrize(
    "anchor,replacement",
    [
        # carrier_slug 誤標 provider_native（native id 不含 '/'）
        (
            'token = "chatgpt-web/high"\ntoken_kind = "carrier_slug"',
            'token = "chatgpt-web/high"\ntoken_kind = "provider_native"',
        ),
        # harness alias 誤標 carrier_slug（slug 須含 '/'）
        (
            'token = "opus"\ntoken_kind = "harness_alias"',
            'token = "opus"\ntoken_kind = "carrier_slug"',
        ),
        # provider native 誤標 harness_alias（native id 不在 alias 詞彙）
        (
            'token = "glm-5.3"\ntoken_kind = "provider_native"',
            'token = "glm-5.3"\ntoken_kind = "harness_alias"',
        ),
    ],
)
def test_catalog_rejects_mixed_token_kind_grammar(anchor: str, replacement: str):
    """native／alias／slug 分欄——混型（token 形態與 token_kind 不符）fail loud。"""
    with pytest.raises(AssertionError, match="混型"):
        sync.parse_catalog(mutated_catalog(anchor, replacement))


def test_catalog_rejects_qualification_without_evidence():
    text = mutated_catalog(
        'status = "qualified"\nevidence_source = "user_observed"\n'
        'binding_scope = ["zcode-glm-5.3-flash"]',
        'status = "qualified"\nbinding_scope = ["zcode-glm-5.3-flash"]',
    )
    with pytest.raises(AssertionError, match="缺必要鍵 'evidence_source'"):
        sync.parse_catalog(text)


def test_catalog_rejects_qualified_with_unconfirmable_effort():
    """qualified＋minimum effort 但 scope 內 binding 全無法確認 effective effort
    ——此形態只能 conditional（不滿足 decision hard gate），載入即擋。"""
    text = mutated_catalog(
        "",
        "",
        append=(
            "\n[[qualification]]\n"
            'workload = "adjudication"\n'
            'model_identity = "glm-5.3"\n'
            'status = "qualified"\n'
            'evidence_source = "user_observed"\n'
            'binding_scope = ["bridge-glm-5.3"]\n'
            'minimum_effective_effort = "high"\n'
        ),
    )
    with pytest.raises(AssertionError, match="只能 conditional"):
        sync.parse_catalog(text)


@pytest.mark.parametrize(
    "volatile_key",
    ["quota", "reset", "account", "available", "available_now"],
)
def test_catalog_rejects_volatile_fields(volatile_key: str):
    """quota／reset／account／available-now 類欄位＝volatile state，禁住 catalog。"""
    text = mutated_catalog("", "", append=f"\n{volatile_key} = 5\n")
    with pytest.raises(AssertionError, match=volatile_key):
        sync.parse_catalog(text)


@pytest.mark.parametrize(
    "demand_key",
    ["role", "work_unit", "authority", "registry_slug"],
)
def test_catalog_rejects_demand_and_deployment_fields(demand_key: str):
    """Role／work_unit／authority／registry slug 屬 demand／deployment owner，禁住 catalog。"""
    text = mutated_catalog("", "", append=f'\n{demand_key} = "x"\n')
    with pytest.raises(AssertionError, match=demand_key):
        sync.parse_catalog(text)


def test_catalog_rejects_unknown_keys():
    text = mutated_catalog("", "", append='\nspice_level = "extra"\n')
    with pytest.raises(AssertionError, match="超出白名單"):
        sync.parse_catalog(text)


def test_catalog_rejects_capability_without_evidence_and_unknown_name():
    with pytest.raises(AssertionError, match="capability name"):
        sync.parse_catalog(
            mutated_catalog('name = "native_vision"', 'name = "multimodal"')
        )
    with pytest.raises(AssertionError, match="缺必要鍵 'evidence'"):
        sync.parse_catalog(
            mutated_catalog(
                'name = "native_vision"\nevidence = "repo_observed"',
                'name = "native_vision"',
            )
        )


def test_catalog_rejects_broken_foreign_keys():
    # binding → 不存在的 model_identity
    with pytest.raises(AssertionError, match="未定義"):
        sync.parse_catalog(
            mutated_catalog(
                'id = "cc-opus"\nmodel_identity = "claude-opus"',
                'id = "cc-opus"\nmodel_identity = "claude-ghost"',
            )
        )
    # qualification scope → 不存在的 binding
    with pytest.raises(AssertionError, match="不存在的 binding"):
        sync.parse_catalog(
            mutated_catalog(
                'binding_scope = ["bridge-muse-spark"]',
                'binding_scope = ["ghost-binding"]',
            )
        )
    # qualification scope → 存在但屬另一 model_identity 的 binding
    with pytest.raises(AssertionError, match="屬 model_identity"):
        sync.parse_catalog(
            mutated_catalog(
                'binding_scope = ["bridge-muse-spark"]',
                'binding_scope = ["zcode-glm-5.3"]',
            )
        )


def test_catalog_rejects_overlapping_qualification_scope():
    text = mutated_catalog(
        "",
        "",
        append=(
            "\n[[qualification]]\n"
            'workload = "ep_synthesis"\n'
            'model_identity = "glm-5.3"\n'
            'status = "conditional"\n'
            'evidence_source = "repo_observed"\n'
            'binding_scope = ["bridge-glm-5.3"]\n'
        ),
    )
    with pytest.raises(AssertionError, match="重疊"):
        sync.parse_catalog(text)


def test_catalog_rejects_effort_encoding_shape_mismatch():
    # slug_fixed 缺 fixed_effort
    with pytest.raises(AssertionError, match="形態不符"):
        sync.parse_catalog(
            mutated_catalog(
                'effort_encoding = "slug_fixed"\nfixed_effort = "high"',
                'effort_encoding = "slug_fixed"',
            )
        )
    # field 缺 effort_values
    with pytest.raises(AssertionError, match="形態不符"):
        sync.parse_catalog(
            mutated_catalog(
                'effort_encoding = "field"\neffort_values = ["low", "high", "max"]',
                'effort_encoding = "field"',
            )
        )
    # unsupported 帶 effort_values
    with pytest.raises(AssertionError, match="形態不符"):
        sync.parse_catalog(
            mutated_catalog(
                'token = "GLM-5.3"\ntoken_kind = "provider_native"\n'
                'effort_encoding = "unsupported"',
                'token = "GLM-5.3"\ntoken_kind = "provider_native"\n'
                'effort_encoding = "unsupported"\neffort_values = ["low"]',
            )
        )


def test_catalog_rejects_unknown_effort_token():
    text = mutated_catalog(
        'effort_values = ["minimal", "low", "medium", "high", "xhigh"]',
        'effort_values = ["minimal", "low", "medium", "high", "xhigh", "turbo"]',
    )
    with pytest.raises(AssertionError, match="turbo"):
        sync.parse_catalog(text)


def test_catalog_effort_parity_error_names_binding_and_value():
    """AIR-96 殘項①：catalog effort 值域 ⊆ _EFFORT_ORDINAL 機械對帳。

    未知值須 fail loud 且訊息帶 binding id 與非法值（可定位修復）；
    effort_values 與 slug_fixed 的 fixed_effort 兩路徑都要擋。
    """
    # effort_values 帶未知值 → 訊息含 binding id＋非法值
    text = mutated_catalog(
        'effort_values = ["minimal", "low", "medium", "high", "xhigh"]',
        'effort_values = ["minimal", "low", "medium", "high", "xhigh", "turbo"]',
    )
    with pytest.raises(AssertionError, match=r"bridge-codex-sol.*turbo"):
        sync.parse_catalog(text)
    # fixed_effort（slug_fixed）帶未知值 → 同樣帶 binding id＋非法值
    text = mutated_catalog('fixed_effort = "high"', 'fixed_effort = "turbo"')
    with pytest.raises(AssertionError, match=r"bridge-codex-web-high.*turbo"):
        sync.parse_catalog(text)


def test_catalog_rejects_unknown_workload():
    text = mutated_catalog(
        'workload = "visual_observation"', 'workload = "vision_review"'
    )
    with pytest.raises(AssertionError, match=r"workload 'vision_review'"):
        sync.parse_catalog(text)


def test_catalog_rejects_wrong_schema_version():
    text = mutated_catalog("schema_version = 1", "schema_version = 2")
    with pytest.raises(AssertionError, match="schema_version"):
        sync.parse_catalog(text)


# --- GREEN：六形態可表達（GLM native／Claude alias／web slug／Muse 最低 effort／
# --- Sol effort 區間／Flash visual binding）＋真 catalog 初始記錄 ---


def test_catalog_fixture_loads():
    cat = load_fixture_catalog()
    assert set(cat.identities) == {
        "glm-5.3",
        "glm-5.3-flash",
        "claude-opus",
        "chatgpt-web-high",
        "gpt-5.6-sol",
        "muse-spark-1.3",
    }
    assert len(cat.bindings) == 8
    assert len(cat.qualifications) == 6


def test_wire_token_kinds_in_separate_columns():
    cat = load_fixture_catalog()
    native_tokens = {
        b.token for b in cat.bindings.values() if b.token_kind == "provider_native"
    }
    assert {"glm-5.3", "GLM-5.3", "glm-5.3-flash", "muse-spark-1.3"} <= native_tokens
    alias = [b for b in cat.bindings.values() if b.token_kind == "harness_alias"]
    assert [(b.token, b.carrier) for b in alias] == [("opus", "claude-code")]
    slug = [b for b in cat.bindings.values() if b.token_kind == "carrier_slug"]
    assert [(b.token, b.carrier) for b in slug] == [("chatgpt-web/high", "bridge")]


def test_web_carrier_slug_fixes_effective_effort():
    cat = load_fixture_catalog()
    b = cat.bindings["bridge-codex-web-high"]
    assert b.token_kind == "carrier_slug" and "/" in b.token
    assert b.effort_encoding == "slug_fixed"
    assert sync.effective_effort(b, None) == "high"
    assert sync.effective_effort(b, "low") == "high"  # effort 旗標不換 browser model


def test_muse_conditional_binding_scoped_minimum_effort():
    cat = load_fixture_catalog()
    b = cat.bindings["bridge-muse-spark"]
    rec = sync.qualification_for(cat, "ep_synthesis", b)
    assert rec is not None
    assert (rec.status, rec.evidence_source, rec.minimum_effective_effort) == (
        "conditional",
        "user_observed",
        "xhigh",
    )
    assert tuple(rec.binding_scope) == ("bridge-muse-spark",)
    # conditional 不過 decision hard gate（effort 已達 minimum 亦然）
    assert not sync.passes_decision_hard_gate(cat, "ep_synthesis", b, "xhigh")
    assert not sync.passes_decision_hard_gate(cat, "ep_synthesis", b, "high")


def test_sol_effort_range_requestable():
    cat = load_fixture_catalog()
    b = cat.bindings["bridge-codex-sol"]
    assert set(b.effort_values) >= {"medium", "high", "xhigh"}
    assert sync.effective_effort(b, "medium") == "medium"
    assert sync.effective_effort(b, "xhigh") == "xhigh"
    assert sync.effective_effort(b, "ultra") is None  # 非 binding 詞彙＝無法確認


def test_flash_direct_visual_eligibility_via_intersection():
    cat = load_fixture_catalog()
    assert sync.direct_visual_eligible(cat, cat.bindings["zcode-glm-5.3-flash"])
    assert not sync.direct_visual_eligible(cat, cat.bindings["zcode-glm-5.3"])


def test_real_catalog_loads():
    cat = sync.load_catalog(REPO_ROOT)
    assert {
        "glm-5.3",
        "glm-5.3-flash",
        "claude-opus",
        "chatgpt-web-high",
        "gpt-5.6-sol",
        "gpt-6-astra",
        "fabel",
        "muse-spark-1.3",
    } <= set(cat.identities)


def test_real_catalog_initial_qualification_records():
    cat = sync.load_catalog(REPO_ROOT)
    decision_qualified = {
        rec.model_identity
        for rec in cat.qualifications
        if rec.workload in {"ep_synthesis", "adjudication"}
        and rec.status == "qualified"
        and rec.evidence_source == "user_observed"
    }
    assert decision_qualified == {
        "glm-5.3",
        "chatgpt-web-high",
        "gpt-5.6-sol",
        "gpt-6-astra",
        "claude-opus",
        "fabel",
    }
    for workload in ("ep_synthesis", "adjudication"):
        muse = [
            rec
            for rec in cat.qualifications
            if rec.model_identity == "muse-spark-1.3" and rec.workload == workload
        ]
        assert len(muse) == 1
        assert muse[0].status == "conditional"
        assert muse[0].evidence_source == "user_observed"
        assert muse[0].minimum_effective_effort == "xhigh"
    flash_visual = [
        rec
        for rec in cat.qualifications
        if rec.model_identity == "glm-5.3-flash"
        and rec.workload == "visual_observation"
    ]
    assert len(flash_visual) == 1
    assert flash_visual[0].status == "qualified"
    assert flash_visual[0].evidence_source == "user_observed"


# --- 選擇層 table fixtures（executable spec——demand 表在測試側；
# --- runtime failure injection 留 S3）---


def _status_of(cat, workload: str, binding) -> str:
    rec = sync.qualification_for(cat, workload, binding)
    return rec.status if rec is not None else "unqualified"  # 無記錄＝fail-closed


def _hard_filter(cat, workload: str, requested, *, judgment_floor: str, visual: bool):
    picked = []
    for b in sorted(cat.bindings.values(), key=lambda x: x.id):
        if judgment_floor == "decision":
            if not sync.passes_decision_hard_gate(cat, workload, b, requested):
                continue
        elif _status_of(cat, workload, b) == "unqualified":
            continue
        if visual and not sync.direct_visual_eligible(cat, b):
            continue
        picked.append(b.id)
    return picked


def test_direct_visual_requires_capability_intersection():
    """EP RED case：native_vision model 的 no-image binding 不可為 direct candidate
    ——direct eligibility＝ModelIdentity.native_vision ∩ binding.image_transport。"""
    cat = load_fixture_catalog()
    bridge_flash = cat.bindings["bridge-glm-5.3-flash"]
    assert not sync.direct_visual_eligible(cat, bridge_flash)
    assert sync.direct_visual_eligible(cat, cat.bindings["zcode-glm-5.3-flash"])
    # decomposed 兩段式：observer＝direct-eligible visual binding；
    # Arbiter＝decision-qualified 且不需 visual（observations artifact 消費者）
    arbiter = cat.bindings["cc-opus"]
    assert sync.passes_decision_hard_gate(cat, "adjudication", arbiter, "high")
    assert not sync.direct_visual_eligible(cat, arbiter)


def test_effort_unconfirmable_paths_fail_decision_hard_gate():
    cat = load_fixture_catalog()
    bridge_glm = cat.bindings["bridge-glm-5.3"]
    assert sync.effective_effort(bridge_glm, "high") is None  # unsupported＝無法確認
    # 記錄不要求 effort（無 minimum）→ effort 軸不阻擋（user_observed 已成立）
    assert sync.passes_decision_hard_gate(cat, "ep_synthesis", bridge_glm, None)
    # 記錄要求 effort 時：qualified＋無法確認的組合被 loader 擋於載入（見上方
    # rejects_qualified_with_unconfirmable_effort），唯一合法載入形態＝conditional
    # ——而 conditional 不過 decision hard gate
    muse = cat.bindings["bridge-muse-spark"]
    assert sync.effective_effort(muse, "xhigh") == "xhigh"
    assert not sync.passes_decision_hard_gate(cat, "ep_synthesis", muse, "xhigh")


def test_decision_hard_gate_enforces_minimum_effective_effort():
    cat = load_fixture_catalog()
    sol = cat.bindings["bridge-codex-sol"]
    assert not sync.passes_decision_hard_gate(cat, "ep_synthesis", sol, "medium")
    assert sync.passes_decision_hard_gate(cat, "ep_synthesis", sol, "high")
    assert sync.passes_decision_hard_gate(cat, "ep_synthesis", sol, "xhigh")
    assert not sync.passes_decision_hard_gate(cat, "ep_synthesis", sol, None)
    assert not sync.passes_decision_hard_gate(cat, "ep_synthesis", sol, "ultra")


def test_hard_filter_decision_and_execution_floors():
    cat = load_fixture_catalog()
    # decision floor：qualified＋effort 滿足（無記錄／conditional 均排除）
    assert _hard_filter(
        cat, "ep_synthesis", "high", judgment_floor="decision", visual=False
    ) == [
        "bridge-codex-sol",
        "bridge-codex-web-high",
        "bridge-glm-5.3",
        "zcode-glm-5.3",
    ]
    # execution floor：非 unqualified 即可（conditional muse 可派——顯性 degradation 記錄面）
    assert _hard_filter(
        cat, "ep_synthesis", None, judgment_floor="execution", visual=False
    ) == [
        "bridge-codex-sol",
        "bridge-codex-web-high",
        "bridge-glm-5.3",
        "bridge-muse-spark",
        "zcode-glm-5.3",
    ]


def test_hard_filter_visual_and_decomposed_paths():
    cat = load_fixture_catalog()
    # 一般視覺觀察：visual_observation qualification＋direct eligibility 交集
    assert _hard_filter(
        cat, "visual_observation", None, judgment_floor="execution", visual=True
    ) == ["zcode-glm-5.3-flash"]
    # 高推理視覺裁決（decision＋visual 同時要求）無單一 candidate
    # → 正式 decomposition：observer 腿＋Arbiter 腿（arbiter_viewed_source=false）
    assert (
        _hard_filter(
            cat, "adjudication", "high", judgment_floor="decision", visual=True
        )
        == []
    )


def test_availability_tristate_stale_unknown_not_available():
    """AvailabilitySnapshot tri-state：stale／unknown 不得當 available。"""
    cat = load_fixture_catalog()
    snapshot = {  # volatile 輸入——不進 catalog（見 schema negative tests）
        "zcode-glm-5.3-flash": ("available", "fresh"),
        "bridge-codex-sol": ("unknown", "stale"),
        "cc-opus": ("unavailable", "fresh"),
    }
    assert set(snapshot) <= set(cat.bindings)  # snapshot 鍵＝binding id（對照 catalog）

    def dispatchable(bid: str) -> bool:
        state, freshness = snapshot.get(bid, ("unknown", "stale"))
        return state == "available" and freshness == "fresh"

    assert dispatchable("zcode-glm-5.3-flash")
    assert not dispatchable(
        "bridge-codex-sol"
    )  # unknown+stale → probe 或顯性 no-candidate
    assert not dispatchable("cc-opus")
    assert not dispatchable("bridge-muse-spark")  # 缺觀測＝unknown，非 available


def test_override_constrains_ranking_not_hard_filters():
    """ArcOverride 只約束合格候選的排序；指向不合格 candidate＝零 dispatch＋顯性失敗。"""

    def rank(cat, workload: str, requested: str, *, override: str) -> list[str]:
        eligible = [
            b.id
            for b in sorted(cat.bindings.values(), key=lambda x: x.id)
            if sync.passes_decision_hard_gate(cat, workload, b, requested)
        ]
        if override not in eligible:
            return []  # incompatible override——禁靜默換人
        return [override] + [bid for bid in eligible if bid != override]

    cat = load_fixture_catalog()
    assert rank(cat, "ep_synthesis", "high", override="bridge-codex-sol")[0] == (
        "bridge-codex-sol"
    )
    # user 指定 conditional candidate 跑 decision 工作＝零 dispatch（不暗換）
    assert rank(cat, "ep_synthesis", "xhigh", override="bridge-muse-spark") == []


# --- main() 整合：catalog 驗證接線（compute-then-apply——任何寫入前 fail）---


def test_main_fails_loud_on_invalid_catalog_without_write(repo: Path):
    catalog = repo / "skills" / "model-routing" / "catalog.toml"
    catalog.write_text("schema_version = 99\n", encoding="utf-8")
    before = _snapshot_tree(repo)
    assert run(repo, "check") == 2
    assert _snapshot_tree(repo) == before  # fail 於任何寫入前


def test_main_fails_loud_on_missing_presets_without_write(repo: Path):
    """presets 是 source of record——缺席＝fatal 2（compute-then-apply，零寫入）。"""
    assert run(repo, "sync") == 0
    (repo / "agents" / "presets.toml").unlink()
    before = _snapshot_tree(repo)
    assert run(repo, "check") == 2
    assert _snapshot_tree(repo) == before


# --- doctrine guards：S2 等價 gate 後——legacy tier 表已移除＋pointer 在場＋
# --- rule 不材料化 model 值 ---


def test_skill_legacy_tier_tables_removed_and_pointers_present():
    """AIR-91 S2 等價 gate 通過後：MIGRATION 標記的三張 legacy 表（tier×provider
    權威表／pins 填法表／role→requirement 分配表）移除；catalog／presets
    pointer 與 doctrine（resolver protocol）在場。"""
    text = (REPO_ROOT / "skills" / "model-routing" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    # legacy 表與 MIGRATION 標記不再在場
    assert "## tier → (model, effort)" not in text
    assert "## role → requirement（tier）分配表" not in text
    assert "### harness 部署填法" not in text
    assert "MIGRATION: legacy" not in text
    # 單一源 pointer 在場：catalog（供給）＋presets（部署）
    assert "catalog.toml" in text
    assert "agents/presets.toml" in text
    # 新 doctrine 在場：resolver protocol＋judge Q2 註記
    assert "resolver precedence" in text
    assert "WorkUnitContract" in text
    assert "minimum_effective_effort" in text


def test_rule_model_routing_no_materialized_model_values():
    """rules 端只留 precedence＋hard invariants——不材料化任何 model 值。"""
    text = (REPO_ROOT / "rules" / "model-routing.md").read_text(encoding="utf-8")
    lowered = text.lower()
    for token in (
        "glm-5.3",
        "glm-5.3-flash",
        "muse-spark",
        "gpt-5",
        "gpt-6",
        "opus",
        "sonnet",
        "haiku",
        "fabel",
        "astra",
        "chatgpt-web",
    ):
        assert token not in lowered, f"rule 材料化了 model 值：{token}"
    assert "catalog.toml" in text
    assert "no-silent-downgrade" in text
    assert "precedence" in text


# --- AIR-91 S2：deployment presets——loader／validator／projection 切換／
# --- legacy⇄new 全量等價矩陣 ---
#
# 行為契約：presets 是 deployment adapter（registry slug→membership／read-write／
# sandbox／background／default binding FK）；供給事實在 catalog、demand 在
# workflow（S3）——本段 loader fail loud 拒絕 demand／volatile 欄位侵入。
# LEGACY_* golden＝AIR-91 前 tier→pin 解析的凍結快照（值可由 git 歷史復原）；
# 等價矩陣證新解析（presets+catalog）與凍結 legacy 逐 role 逐 harness 等價。


LEGACY_ROLE_REQUIREMENTS = {
    "code-reviewer": "lite",
    "code-reviewer-primed": "lite",
    "cr-research": "full",
    "cross-verify-investigator": "lite",
    "impl-lite": "lite",
    "lite-verify": "lite",
    "mem-distill": "lite",
    "spec-miner": "lite",
    "vision-review": "vision",
}
LEGACY_ZCODE_PINS = {
    "full": ("glm-5.3", "high"),
    "lite": ("glm-5.3-flash", "high"),
    "vision": ("glm-5.3-flash", "high"),
}
LEGACY_CLAUDE_PINS = {"full": "opus"}


def _legacy_render(
    role_name: str, role_body: str, target: str, requirement: str
) -> str:
    """凍結的 legacy 渲染邏輯（AIR-91 前 sync_agents 行為）——只在測試側重現，
    等價矩陣的對照組；prod 端 legacy dict 已隨 S2 切換移除。"""
    frontmatter, body = sync.split_frontmatter(role_name, role_body)
    frontmatter = sync.project_tools(frontmatter, target)
    target_fields = ""
    if target == "zcode" and requirement in LEGACY_ZCODE_PINS:
        model, thought_level = LEGACY_ZCODE_PINS[requirement]
        target_fields = f"\nmodel: {model}\nthoughtLevel: {thought_level}"
    elif target == "claude" and requirement in LEGACY_CLAUDE_PINS:
        target_fields = f"\nmodel: {LEGACY_CLAUDE_PINS[requirement]}"
    return f"---\n{frontmatter}{target_fields}\n---\n{sync.OWNERSHIP_MARKER}\n{body}"


def mutated_presets(anchor: str, replacement: str, *, append: str = "") -> str:
    """presets fixture 定點變異（錨點在場由斷言保證——防 fixture 漂移後假綠）。"""
    if append:
        assert not anchor and not replacement
        return PRESETS_FIXTURE + append
    assert anchor in PRESETS_FIXTURE, f"mutation anchor missing: {anchor!r}"
    return PRESETS_FIXTURE.replace(anchor, replacement, 1)


# --- RED：presets loader fail-loud（negative fields／FK／相容性）---


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "role",
        "authority",
        "qualification",
        "workload",
        "judgment_floor",
        "available",
        "availability",
        "quota",
        "reset",
        "account",
    ],
)
def test_presets_rejects_demand_and_volatile_fields(forbidden_key: str):
    """Role／authority／qualification／availability（與 volatile state）禁入 presets。"""
    text = mutated_presets("", "", append=f'\n{forbidden_key} = "x"\n')
    with pytest.raises(AssertionError, match=forbidden_key):
        sync.parse_presets(text)


def test_presets_rejects_unknown_keys():
    text = mutated_presets('sandbox = "default"', 'spice = "hot"')
    with pytest.raises(AssertionError, match="超出白名單"):
        sync.parse_presets(text)


def test_presets_rejects_duplicate_slug():
    text = mutated_presets(
        "",
        "",
        append=(
            "\n[[preset]]\n"
            'slug = "t-lite"\n'
            'requirement = "lite"\n'
            'harness = ["zcode"]\n'
            'read_write = "read-only"\n'
            'sandbox = "default"\n'
            "background = true\n"
        ),
    )
    with pytest.raises(AssertionError, match="duplicate"):
        sync.parse_presets(text)


def test_presets_rejects_unknown_harness_value():
    text = mutated_presets(
        'harness = ["zcode", "claude"]', 'harness = ["zcode", "grok"]'
    )
    with pytest.raises(AssertionError, match="grok"):
        sync.parse_presets(text)


def test_presets_rejects_empty_harness():
    text = mutated_presets('harness = ["zcode", "claude"]', "harness = []")
    with pytest.raises(AssertionError, match="非空"):
        sync.parse_presets(text)


def test_presets_rejects_unknown_requirement_token():
    text = mutated_presets('requirement = "lite"', 'requirement = "medium"')
    with pytest.raises(AssertionError, match="requirement"):
        sync.parse_presets(text)


def test_presets_rejects_unknown_read_write_and_sandbox():
    with pytest.raises(AssertionError, match="read_write"):
        sync.parse_presets(
            mutated_presets('read_write = "read-only"', 'read_write = "rw"')
        )
    with pytest.raises(AssertionError, match="sandbox"):
        sync.parse_presets(mutated_presets('sandbox = "default"', 'sandbox = "strict"'))


def test_presets_rejects_non_bool_background():
    text = mutated_presets("background = true", 'background = "yes"')
    with pytest.raises(AssertionError, match="background"):
        sync.parse_presets(text)


def test_presets_rejects_binding_for_non_member_harness():
    """default_binding 宣告的 harness 必在 membership 清單——兩處需一致。"""
    text = mutated_presets(
        "",
        "",
        append=(
            "\n[[preset]]\n"
            'slug = "t-loner"\n'
            'requirement = "lite"\n'
            'harness = ["zcode"]\n'
            'read_write = "read-only"\n'
            'sandbox = "default"\n'
            "background = true\n"
            "\n[preset.default_binding.claude]\n"
            'ref = "cc-opus"\n'
        ),
    )
    with pytest.raises(AssertionError, match="membership"):
        sync.parse_presets(text)


def test_presets_rejects_unknown_binding_ref():
    cat = load_fixture_catalog()
    text = mutated_presets('ref = "zcode-glm-5.3-flash"', 'ref = "zcode-glm-ghost"')
    with pytest.raises(AssertionError, match="不存在的 binding"):
        sync.resolve_deployment(cat, sync.parse_presets(text))


def test_presets_rejects_binding_carrier_harness_mismatch():
    """zcode preset 掛 claude-code binding＝binding/harness 不相容，fail loud。"""
    cat = load_fixture_catalog()
    text = mutated_presets('ref = "zcode-glm-5.3-flash"', 'ref = "cc-opus"')
    with pytest.raises(AssertionError, match="不相容"):
        sync.resolve_deployment(cat, sync.parse_presets(text))


def test_presets_rejects_effort_not_in_binding_values():
    """capability mismatch：部署 effort 不在 binding effort_values（ultra 是跨家族
    詞彙但非該 binding 可表達檔位）——resolve 層 fail loud。"""
    cat = load_fixture_catalog()
    text = mutated_presets(
        'ref = "zcode-glm-5.3-flash"\neffort = "high"',
        'ref = "zcode-glm-5.3-flash"\neffort = "ultra"',
    )
    with pytest.raises(AssertionError, match="capability mismatch"):
        sync.resolve_deployment(cat, sync.parse_presets(text))


def test_presets_rejects_effort_on_param_binding_and_missing_on_field():
    cat = load_fixture_catalog()
    # param（CC spawn-time enum）：registry frontmatter 不帶 effort
    text = mutated_presets(
        '[preset.default_binding.claude]\nref = "cc-opus"',
        '[preset.default_binding.claude]\nref = "cc-opus"\neffort = "high"',
    )
    with pytest.raises(AssertionError, match="spawn-time"):
        sync.resolve_deployment(cat, sync.parse_presets(text))
    # field（zcode thoughtLevel）：部署 effort 必填
    text = mutated_presets(
        'ref = "zcode-glm-5.3-flash"\neffort = "high"',
        'ref = "zcode-glm-5.3-flash"',
    )
    with pytest.raises(AssertionError, match="需部署 effort"):
        sync.resolve_deployment(cat, sync.parse_presets(text))


def test_background_parity_mismatch_fails_loud(repo: Path):
    """preset.background 與 roles frontmatter 宣告需同步——drift＝fail loud。"""
    text = PRESETS_FIXTURE.replace(
        'slug = "t-vision"\nrequirement = "vision"\nharness = ["zcode", "claude"]\n'
        'read_write = "read-only"\nsandbox = "default"\nbackground = false',
        'slug = "t-vision"\nrequirement = "vision"\nharness = ["zcode", "claude"]\n'
        'read_write = "read-only"\nsandbox = "default"\nbackground = true',
    )
    (repo / "agents" / "presets.toml").write_text(text, encoding="utf-8")
    with pytest.raises(AssertionError, match="background"):
        expected(repo)


# --- GREEN：presets fixture 可載入＋等價矩陣（legacy⇄new 全量）---


def test_presets_fixture_loads():
    presets = sync.parse_presets(PRESETS_FIXTURE)
    assert set(presets) == {"t-lite", "t-vision", "t-full"}
    lite = presets["t-lite"]
    assert (lite.requirement, lite.harness, lite.read_write, lite.background) == (
        "lite",
        ("zcode", "claude"),
        "read-only",
        True,
    )
    assert lite.default_binding == {"zcode": ("zcode-glm-5.3-flash", "high")}


def test_real_presets_cover_exactly_nine_roles():
    presets = sync.load_presets(REPO_ROOT)
    assert set(presets) == set(LEGACY_ROLE_REQUIREMENTS)
    assert len(presets) == 9


def test_legacy_new_equivalence_matrix_all_nine_roles():
    """S2 等價 gate：新解析（presets+catalog）與凍結 legacy（tier→pin dict）對
    全 9 role × 2 harness 逐項比 model token／effort／輸出 bytes——全部相等。
    未來任何 presets／catalog 編輯破壞等價（legacy/new map mismatch）＝此測試 RED。"""
    catalog = sync.load_catalog(REPO_ROOT)
    presets = sync.load_presets(REPO_ROOT)
    resolved = sync.resolve_deployment(catalog, presets)
    roles = sync.load_role_specs(REPO_ROOT)
    assert roles.keys() == presets.keys() == LEGACY_ROLE_REQUIREMENTS.keys()
    for role in sorted(roles):
        requirement = LEGACY_ROLE_REQUIREMENTS[role]
        assert presets[role].requirement == requirement
        # zcode：model token＋effort 逐項等價
        zbinding, zeffort = resolved[role]["zcode"]
        legacy_model, legacy_effort = LEGACY_ZCODE_PINS[requirement]
        assert zbinding is not None and zbinding.token == legacy_model, role
        assert zeffort == legacy_effort, role
        # claude：full→別名釘選；lite/vision→inherit（無 model 欄位）
        cbinding, ceffort = resolved[role]["claude"]
        if requirement in LEGACY_CLAUDE_PINS:
            assert cbinding is not None, role
            assert cbinding.token == LEGACY_CLAUDE_PINS[requirement], role
            assert ceffort is None, role
        else:
            assert cbinding is None and ceffort is None, role
        # 輸出 bytes：新舊渲染器對同一 role 源逐 byte 相等
        for target in ("zcode", "claude"):
            binding, effort = resolved[role][target]
            new_bytes = sync.render_registry(role, roles[role], target, binding, effort)
            legacy_bytes = _legacy_render(role, roles[role], target, requirement)
            assert new_bytes == legacy_bytes, f"{role}/{target} bytes diverge"


def test_equivalence_pins_spot_checks():
    """pins 行為等價錨點：vision-review 仍 GLM Flash（影像 pin 禁降）；
    cr-research 仍 full pin（zcode glm-5.3＋claude opus 別名）。"""
    catalog = sync.load_catalog(REPO_ROOT)
    presets = sync.load_presets(REPO_ROOT)
    resolved = sync.resolve_deployment(catalog, presets)
    vision_binding, _ = resolved["vision-review"]["zcode"]
    assert vision_binding.token == "glm-5.3-flash"
    assert "image_transport" in vision_binding.transport
    cr_z, _ = resolved["cr-research"]["zcode"]
    cr_c, _ = resolved["cr-research"]["claude"]
    assert cr_z.token == "glm-5.3"
    assert cr_c.token == "opus"
    assert presets["cr-research"].requirement == "full"


def test_effort_ordinal_collapsed_apex():
    """judge 附帶觀察 Q3：_EFFORT_ORDINAL 頂檔 collapsed 形態——跨家族頂檔
    （muse ultra／codex xhigh／zcode max）同為 5，互譯時不意外分出高下。"""
    assert (
        sync._EFFORT_ORDINAL["ultra"]
        == sync._EFFORT_ORDINAL["xhigh"]
        == sync._EFFORT_ORDINAL["max"]
        == 5
    )
    assert max(sync._EFFORT_ORDINAL.values()) == 5
