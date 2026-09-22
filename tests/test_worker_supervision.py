"""Worker supervision contract 錨點測試（AIR-160 AC#1／#2／#3／#6）.

EP 驗證式＝rg 可查的收緊條文與凍結契約錨點，本檔固化為機械檢查：
- AC#1 agent-workflow 收緊：背景＋有限工 dispatch⇒register 義務；互動短腿
  豁免已刪（字串缺席）；前景 <30s probe 與已登記 daemon 豁免明文
- AC#2 supervision contract 凍結節：三出口＋UNKNOWN fail-loud 升級（禁列
  結案態）＋偵測/處置分離＋heartbeat 缺席合法＋偽造禁令
- AC#3 兩 role pointer（不含具體路徑/taskId/timebox）＋cr-research read-only
  側通道豁免
- AC#6 harness_waiter frozen spec 主體錨點零變（狀態機表＋exit 常數）
"""

from conftest import REPO_ROOT, load_module

SKILL = REPO_ROOT / "skills" / "agent-workflow" / "SKILL.md"
IMPL_LITE = REPO_ROOT / "agents" / "roles" / "impl-lite.md"
CR_RESEARCH = REPO_ROOT / "agents" / "roles" / "cr-research.md"
CONTRACT_HEADING = "Worker supervision contract"


def _skill_text() -> str:
    return SKILL.read_text()


# ---------------------------------------------------------------------------
# AC#1：agent-workflow 收緊條文
# ---------------------------------------------------------------------------


def test_register_duty_wording_present():
    text = _skill_text()
    assert "背景＋有限工 dispatch ⇒ register 義務" in text
    assert "dispatch 尚未完成" in text
    assert "collection owner" in text


def test_interactive_shortleg_exemption_removed():
    text = _skill_text()
    assert "互動短腿可豁免" not in text, "互動短腿豁免已刪（AIR-160 事故破口）"


def test_foreground_probe_and_registered_daemon_exemptions_explicit():
    text = _skill_text()
    # 豁免僅兩項：前景 <30s probe＋已登記 ownership handle 的 daemon
    assert "前景 <30s probe" in text
    assert "--surviving-handle" in text
    assert "已登記 ownership handle" in text


# ---------------------------------------------------------------------------
# AC#2：supervision contract 凍結節
# ---------------------------------------------------------------------------


def test_contract_section_present():
    text = _skill_text()
    assert CONTRACT_HEADING in text


def test_three_exits_and_unknown_escalation():
    text = _skill_text()
    for anchor in ("TERMINAL", "HARD_DEATH_EVIDENCE", "TIMEBOX_EXPIRED"):
        assert anchor in text, f"缺三出口錨點：{anchor}"
    assert "UNKNOWN" in text
    assert "fail-loud" in text
    assert "禁列結案態" in text
    assert "禁逾時宣稱死亡" in text  # silence 可觀測、death 不可


def test_detection_disposal_separation_and_parent_ownership():
    text = _skill_text()
    assert "偵測與處置分離" in text
    assert "ownership 歸 parent" in text
    assert "parent 專屬" in text


def test_heartbeat_protocol_branches_and_absence_legal():
    text = _skill_text()
    assert "STALE_ADVISORY" in text
    assert "heartbeat_missing" in text
    assert "缺席合法" in text  # heartbeat 缺席永不失敗
    assert "2×週期" in text
    assert "scripts/child_heartbeat.py" in text
    assert "spawn prompt 注入" in text  # role 檔不硬編——參數由 spawn prompt 給


def test_forgery_bans_and_ledger_separation():
    text = _skill_text()
    assert "fresh 不延 timebox" in text
    assert "stale 不判死" in text
    assert "禁自報 collected" in text
    assert "reconciliation trigger 非 detector" in text
    # SendMessage ping contract 未凍結＝留空分支
    assert "SendMessage ping" in text
    assert "未凍結" in text


# ---------------------------------------------------------------------------
# AIR-160 修復輪：cadence 定義＋dispatch 範例補旗標＋接線四環閉環
# ---------------------------------------------------------------------------


def test_cadence_default_and_stale_threshold_defined():
    # muse Important：cadence 未定義——契約明寫週期預設與 stale 門檻
    text = _skill_text()
    assert "heartbeat 週期預設 60s" in text
    assert "2×週期" in text
    assert "--interval-secs" in text  # child CLI 週期旗標
    assert "intervalSecs" in text  # 週期寫進 sidecar row 供對帳


def test_register_example_enables_heartbeat_pilot():
    # muse Important：dispatch 範例行補 heartbeat 旗標——照抄範例即啟用 pilot
    text = _skill_text()
    assert "--expected-heartbeat --heartbeat-file" in text


def test_wiring_loop_four_links_documented():
    # codex important：spawn prompt 注入→child 寫 sidecar→register→sweep 讀
    # 四環一次讀完能照做
    text = _skill_text()
    assert "接線四環" in text
    assert "scripts/child_heartbeat.py --file" in text
    assert "--state working" in text
    assert "--state done" in text


def test_role_pointers_include_cadence_default():
    # spawn prompt 注入清單加週期項（兩 role pointer）
    for role_path in (IMPL_LITE, CR_RESEARCH):
        text = role_path.read_text()
        assert "週期（預設 60s）" in text, f"{role_path.name} 缺週期注入項"


# ---------------------------------------------------------------------------
# AC#3：role pointer（一行）＋read-only 側通道豁免
# ---------------------------------------------------------------------------


def test_impl_lite_pointer_one_line_no_hardcoded_params():
    text = IMPL_LITE.read_text()
    assert CONTRACT_HEADING in text, "impl-lite 缺 supervision contract pointer"
    assert "spawn prompt 注入" in text
    # 不含具體路徑/taskId/timebox——那些由 spawn prompt 注入
    assert "liveness-registry" not in text
    assert "--silence-budget-min" not in text
    assert "20m" not in text


def test_cr_research_pointer_and_readonly_sidechannel_exemption():
    text = CR_RESEARCH.read_text()
    assert CONTRACT_HEADING in text, "cr-research 缺 supervision contract pointer"
    assert "spawn prompt 注入" in text
    assert "liveness-registry" not in text
    # read-only 側通道豁免明文：監督遙測寫 .agent-tmp 非產物寫入
    assert "read-only" in text
    assert "監督遙測" in text
    assert ".agent-tmp" in text


# ---------------------------------------------------------------------------
# AC#6：harness_waiter frozen spec 主體錨點零變
# ---------------------------------------------------------------------------


def test_frozen_exit_constants_unchanged():
    mod = load_module("scripts/harness_waiter.py")
    assert (
        mod.EXIT_OK,
        mod.EXIT_FAILLOUD,
        mod.EXIT_HARD_DEATH,
        mod.EXIT_FREEZE,
        mod.EXIT_VERIFY_INCOMPLETE,
    ) == (0, 1, 2, 3, 4)


def test_frozen_state_machine_and_invariants_intact():
    doc = load_module("scripts/harness_waiter.py").__doc__ or ""
    for i in range(1, 10):
        assert f"| T{i} |" in doc, f"轉移表 T{i} 缺 module docstring"
    assert "watcher 不做活/死宣稱" in doc
    assert "terminal transition＝唯一權威狀態訊號" in doc


def test_heartbeat_face_contract_anchors_in_watcher():
    doc = load_module("scripts/harness_waiter.py").__doc__ or ""
    for anchor in (
        "expectedHeartbeat",
        "heartbeatFile",
        "heartbeat-fresh",
        "heartbeat_missing",
        "stale-advisory",
        "STALE_ADVISORY",
    ):
        assert anchor in doc, f"harness_waiter 缺 heartbeat 讀面錨點：{anchor}"
