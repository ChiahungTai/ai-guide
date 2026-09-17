"""availability_snapshot 契約測試（AIR-123——dispatch 讀端最小切片）。

 evaluator-not-router：輸出只有 per-family tri-state（available／unavailable／
unknown）＋binding 計數＋spine note 逐字——禁 selected／rank／fallback 欄位。

exit 契約（卡已決策②，三處歷史不一致以此為準）：
  0 = fresh 產出／1 = 無法判定 fail-closed（as-of 缺席、可用行解析失敗）／
  2 = 輸入缺席或不合法／3 = stale → 全 family unknown。

family join＝catalog [[dispatch_binding]] 顯式 family 欄（閉集 enum 住
allow_lists.families——loader fail-loud；POC 的 surface regex 已退役）。

fixtures＝自真 spine（2026-09-16 版）摘錄改編：as-of 新（fresh）／舊
（stale 4d）／邊界（恰 3d）／缺席三態＋可用行完整／缺席／malformed＋
codex 兩池事件／GLM 衝突事件。歷史態不可重放（spine 不版控）——fixture
是形態契約非現值證據。
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

snap = load_module("skills/model-routing/scripts/availability_snapshot.py")
sync = load_module("scripts/sync_agents.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures"
REAL_CATALOG = REPO_ROOT / "skills" / "model-routing" / "catalog.toml"

# 測試錨定 now——fixture as-of（2026-09-13/14/16）相對本值形成 4d/3d/1d
NOW = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)

FRESH = FIXTURES / "availability_spine_fresh.md"
EDGE_3D = FIXTURES / "availability_spine_edge_3d.md"
STALE_4D = FIXTURES / "availability_spine_stale_4d.md"
NO_ASOF = FIXTURES / "availability_spine_no_asof.md"
NO_AVAILABLE = FIXTURES / "availability_spine_no_available.md"
MALFORMED = FIXTURES / "availability_spine_malformed_available.md"

FAMILY_STATE_RE = re.compile(
    r"^  (\S+) = (available|unavailable|unknown)", re.MULTILINE
)
BINDINGS_RE = re.compile(
    r"^    bindings family=(\S+) count=(\d+): (\S.*)$", re.MULTILINE
)
NO_BINDING_MARK = "no bindings in catalog"


def run_main(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    rc = snap.main(argv, now=NOW)
    return rc, capsys.readouterr().out


def family_states(out: str) -> dict[str, str]:
    return dict(FAMILY_STATE_RE.findall(out))


def real_catalog_families() -> frozenset[str]:
    return sync.load_catalog(REPO_ROOT).families


# ---- AC①：catalog family 欄＋loader fail-loud ----


def test_loader_rejects_binding_without_family() -> None:
    """catalog 新 binding 未標 family → loader fail（必要欄缺席）。"""
    text = REAL_CATALOG.read_text(encoding="utf-8")
    anchor = 'id = "bridge-glm-5.3"'
    assert anchor in text  # 防 catalog 漂移後假綠
    # 移除一條 binding 的 family 欄（其餘仍在）→ 缺必要鍵 fail-loud
    stripped = text.replace('family = "glm"\n', "", 1)
    with pytest.raises(AssertionError, match="family"):
        sync.parse_catalog(stripped)
    # 對照組：現 catalog family 欄齊備可載
    cat = sync.load_catalog(REPO_ROOT)
    assert all(b.family for b in cat.bindings.values())


def test_loader_rejects_unknown_family_value() -> None:
    """未知 family 值（不在 allow_lists.families 閉集）→ fail-loud 帶 binding id。"""
    text = REAL_CATALOG.read_text(encoding="utf-8")
    anchor = 'id = "bridge-muse-spark-1.3"'
    assert anchor in text
    mutated = text.replace('family = "muse"', 'family = "openai"', 1)
    with pytest.raises(AssertionError, match=r"bridge-muse-spark-1.3.*unknown family"):
        sync.parse_catalog(mutated)


def test_real_catalog_family_assignment() -> None:
    """9 條 binding 的 family 歸屬（air-123 實查舉證的凍結表）。"""
    cat = sync.load_catalog(REPO_ROOT)
    got = {bid: b.family for bid, b in cat.bindings.items()}
    assert got == {
        "zcode-registry-glm-5.3": "glm",
        "zcode-registry-glm-5.3-flash": "glm",
        "cc-registry-opus": "anthropic",
        "bridge-glm-5.3": "glm",
        "bridge-glm-5.3-flash": "glm",
        "bridge-codex-web-high": "codex",
        "bridge-codex-sol": "codex",
        "bridge-codex-astra": "codex",
        "bridge-muse-spark-1.3": "muse",
    }
    assert cat.families == frozenset({"glm", "muse", "codex", "anthropic", "xai"})


# ---- AC②：四態 exit（2 輸入缺席／1 無法判定／0 fresh／3 stale）----


def test_exit_2_when_spine_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc, out = run_main(
        ["--spine", str(tmp_path / "absent.md"), "--catalog", str(REAL_CATALOG)],
        capsys,
    )
    assert rc == 2
    assert "缺席" in out


def test_exit_2_when_catalog_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc, _ = run_main(
        ["--spine", str(FRESH), "--catalog", str(tmp_path / "absent.toml")], capsys
    )
    assert rc == 2


def test_exit_2_on_invalid_stale_days(capsys: pytest.CaptureFixture[str]) -> None:
    rc, _ = run_main(
        ["--spine", str(FRESH), "--catalog", str(REAL_CATALOG), "--stale-days", "x"],
        capsys,
    )
    assert rc == 2


def test_exit_1_when_asof_missing(capsys: pytest.CaptureFixture[str]) -> None:
    rc, out = run_main(
        ["--spine", str(NO_ASOF), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert rc == 1
    assert "as-of" in out


def test_exit_1_when_available_line_absent(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc, out = run_main(
        ["--spine", str(NO_AVAILABLE), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert rc == 1
    assert "可用行" in out


def test_exit_0_fresh_tri_state_per_family(capsys: pytest.CaptureFixture[str]) -> None:
    rc, out = run_main(["--spine", str(FRESH), "--catalog", str(REAL_CATALOG)], capsys)
    assert rc == 0
    states = family_states(out)
    assert states == {
        "glm": "available",
        "muse": "available",
        "codex": "available",
        "anthropic": "unavailable",
        "xai": "unavailable",
    }


def test_stale_boundary_exactly_3_days_is_fresh(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """age 恰等於 --stale-days（3）→ 非 stale（> 才 stale）；4 天 → stale。"""
    rc, out = run_main(
        ["--spine", str(EDGE_3D), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert rc == 0
    assert "stale=False" in out


def test_stale_at_4_days_exit_3_all_unknown(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc, out = run_main(
        ["--spine", str(STALE_4D), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert rc == 3
    states = family_states(out)
    families = real_catalog_families()
    assert set(states) == families
    assert set(states.values()) == {"unknown"}


def test_malformed_available_line_warns_not_crash(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """可用行在場但零 family 可解析 → WARN＋exit 1（禁 traceback／禁猜 family）。"""
    rc, out = run_main(
        ["--spine", str(MALFORMED), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert rc == 1
    assert "[WARN]" in out
    assert "Traceback" not in out
    # malformed 原文顯性入輸出（人工複核線索）
    assert "（對帳中）" in out


# ---- AC③：family 覆蓋（每 family ≥1 binding 或顯式 no-binding 行，禁靜默）----


@pytest.mark.parametrize("spine_path", [FRESH, STALE_4D], ids=["fresh", "stale"])
def test_family_coverage_bindings_or_explicit_no_binding(
    spine_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc, out = run_main(
        ["--spine", str(spine_path), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert rc in (0, 3)
    states = family_states(out)
    families = real_catalog_families()
    assert set(states) == families, "閉集內每 family 都必須有狀態行（禁靜默省略）"
    # xai 在現 catalog＝零 binding → 顯式 no-binding 行（非靜默缺席）
    assert NO_BINDING_MARK in out
    # 有 binding 的 family：bindings 行計數 ≥1 且與 catalog 事實一致
    counts = {m[0]: int(m[1]) for m in BINDINGS_RE.findall(out)}  # family→count
    expected_counts: dict[str, int] = {}
    cat = sync.load_catalog(REPO_ROOT)
    for binding in cat.bindings.values():
        expected_counts[binding.family] = expected_counts.get(binding.family, 0) + 1
    for fam in families:
        n = expected_counts.get(fam, 0)
        if n:
            assert counts.get(fam) == n
        else:
            assert re.search(
                rf"^  {fam} = .*\n    {re.escape(NO_BINDING_MARK)}", out, re.MULTILINE
            ), f"{fam} 零 binding 需顯式 no-binding 行"


# ---- 卡⑥ 輸出不變量：unknown 永不與可派並存 ----


def test_unknown_never_coexists_with_dispatchable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """fresh（exit 0）輸出禁任何 unknown；stale（exit 3）輸出禁任何 available。"""
    _, fresh_out = run_main(
        ["--spine", str(FRESH), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert "unknown" not in family_states(fresh_out).values()
    assert set(family_states(fresh_out).values()) <= {"available", "unavailable"}
    _, stale_out = run_main(
        ["--spine", str(STALE_4D), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert "available" not in family_states(stale_out).values()


# ---- 卡① evaluator-not-router：禁 selected/rank/fallback 欄位 ----


@pytest.mark.parametrize(
    "spine_path",
    [FRESH, STALE_4D, NO_ASOF, MALFORMED],
    ids=["fresh", "stale", "no-asof", "malformed"],
)
def test_output_has_no_router_fields(
    spine_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, out = run_main(
        ["--spine", str(spine_path), "--catalog", str(REAL_CATALOG)], capsys
    )
    for forbidden in ("selected", "rank", "fallback", "下一個派"):
        assert forbidden not in out


def test_module_source_has_no_router_surface() -> None:
    """模組源碼禁 ranking/fallback 邏輯詞彙（evaluator-not-router 結構反向斷言）。

    注意：family 顯示序的字母排序（display determinism）非 ranking——
    排序對象限 family 名稱字串，禁對 candidate/binding 依能力或狀態排序。
    """
    src = (
        REPO_ROOT / "skills" / "model-routing" / "scripts" / "availability_snapshot.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("fallback", "rank", "priority", "prefer", "下一個派"):
        assert forbidden not in src, f"evaluator 不得出現 router 語彙：{forbidden}"
    # 排序面僅允許 family 名稱（display determinism），禁排序 binding/candidate
    for sort_call in re.findall(r"sorted\(([^)]*)\)", src):
        assert "famil" in sort_call, f"僅 family 名稱可排序：sorted({sort_call})"


# ---- 卡⑤ codex 兩池＋note 逐字保留（禁壓縮）＋可用行 vs 禁派事件衝突態 ----


def test_codex_two_pool_note_preserved_verbatim(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """spine family 條目 note 逐字保留（POC 120 字截斷已退役）＋兩池語義在場。"""
    _, out = run_main(["--spine", str(FRESH), "--catalog", str(REAL_CATALOG)], capsys)
    fixture_text = FRESH.read_text(encoding="utf-8")
    m = re.search(r"^- \*\*codex\*\*：(.+)$", fixture_text, re.MULTILINE)
    assert m is not None
    assert m.group(1) in out, "codex note 需全文逐字入輸出（禁截斷）"
    # 兩池回歸 AC：native usage-limit ≠ web 池耗盡——語義經 note 逐字帶出
    assert "不代表 web 池耗盡" in out


def test_available_vs_forbidden_event_conflict_surfaced(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """可用行列 GLM＋歷史事件行「禁派 GLM 系」→ 衝突顯性並列（WARN＋事件原文）。"""
    rc, out = run_main(["--spine", str(FRESH), "--catalog", str(REAL_CATALOG)], capsys)
    assert rc == 0  # 衝突≠crash——基準＝as-of 可用行，判斷歸 LLM（卡⑦）
    assert family_states(out)["glm"] == "available"
    assert "衝突" in out
    assert "禁派 GLM 系" in out


def test_events_listed_for_human_review_when_stale(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, out = run_main(
        ["--spine", str(STALE_4D), "--catalog", str(REAL_CATALOG)], capsys
    )
    assert "額度事件" in out


# ---- SKILL 指針（AC⑤）----


def test_skill_has_executor_pointer() -> None:
    text = (REPO_ROOT / "skills" / "model-routing" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    section = text.split("### AvailabilitySnapshot", 1)[1].split("###", 1)[0]
    assert "availability_snapshot.py" in section
    assert "uv run python" in section
