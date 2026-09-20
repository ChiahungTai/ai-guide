"""bridge-dispatch／agent-workflow watcher 自動 arm doctrine 錨點測試（AIR-147）.

D1-D5 doctrine 改寫的不可退化錨點固化為機械檢查（lite 寫的測試＝規格陳述，
驗收證據由 full 複驗）：
- D1 rules/bridge-dispatch.md Dispatch⇄collection 條——waiter 主路徑、
  裸 wait 背景 shell 降 fallback、「terminal ≠ complete」句不動
- D2 skills/bridge-dispatch 完整模式段——watcher 主路徑、手動 fan-in wait
  降 fallback／重啟後手動恢復、stalled-advisory 語義（卡 AC#4）
- D3 skill desc 觸發詞（AC#2）＋ desc 值 ≤1024 chars 機驗（scan_skills_desc
  LIMIT 同源）
- D4 完整模式指針段——watcher 節指針（frozen spec、動態 T 公式、
  CollectionReceipt schema 落點＝AIR-149 EP）
- D5 agent-workflow——harness_waiter 工具化指涉保留（AIR-149 S3 防退化）
  ＋bridge_waiter auto-arm 規約一行
"""

import re

from conftest import REPO_ROOT

RULES = REPO_ROOT / "rules" / "bridge-dispatch.md"
SKILL = REPO_ROOT / "skills" / "bridge-dispatch" / "SKILL.md"
AGENT_WORKFLOW = REPO_ROOT / "skills" / "agent-workflow" / "SKILL.md"

DESC_LIMIT = 1024  # 單一源 scripts/scan_skills_desc.py LIMIT；此處防退化快照


def _rules_text() -> str:
    return RULES.read_text()


def _skill_text() -> str:
    return SKILL.read_text()


def _skill_desc() -> str:
    m = re.search(r'^description: "(.*)"$', _skill_text(), re.MULTILINE)
    assert m, "bridge-dispatch desc frontmatter 缺失或格式改變"
    return m.group(1)


def test_d1_rules_waiter_main_path():
    text = _rules_text()
    assert "scripts/bridge_waiter.py" in text  # watcher 主路徑工具指涉
    assert "fan-in 包 wait" in text  # watcher 包 wait 的形態句
    assert "CollectionReceipt" in text  # terminal 輸出 receipt
    assert "exit 3" in text  # stalled advisory wake
    assert "內部消化" in text  # 124 恆內部消化


def test_d1_rules_bare_wait_downgraded_to_fallback():
    text = _rules_text()
    assert "裸 `wait` 背景 shell 降為 fallback" in text  # 降位明示
    assert "exit 124 仍＝re-arm 非失敗、禁重派" in text  # fallback 下 124 語義保留


def test_d1_rules_terminal_not_complete_untouched():
    # D1 規格：「terminal ≠ complete」句不動——逐字防退化
    text = _rules_text()
    assert (
        "terminal ≠ complete：有 sink 登記者以 artifact 機驗（存在＋非空＋錨點）為完成，無登記者以 bounded receipt 非空為完成"
        in text
    )
    assert (
        "workflow 層配套（bounded slices／checkpoint 續寫）單一源＝AIR-135.7 契約"
        in text
    )


def test_d2_skill_full_mode_watcher_main_path():
    text = _skill_text()
    assert "scripts/bridge_waiter.py" in text  # N 顆平行主路徑＝watcher
    assert "背景 shell 跑" in text  # 一顆背景 shell 跑 watcher
    assert "watcher 內部包 fan-in" in text  # watcher 取代手動 fan-in
    assert "CollectionReceipt" in text
    assert "exit 0＝全 terminal completed 且 delivery 過" in text
    assert "exit 1＝任一 terminal 非 completed" in text


def test_d2_skill_manual_fanin_downgraded_with_recovery():
    text = _skill_text()
    assert "fallback" in text  # 手動 fan-in wait 降 fallback
    assert "重啟後手動恢復" in text  # 重啟後恢復路徑保留
    assert "re-arm 非失敗" in text  # 124 re-arm 語義不變
    assert "禁重派" in text


def test_d2_skill_stalled_advisory_disposal_sentence():
    # 卡 AC#4：stalled-advisory 處置句進 doctrine——喚醒不處置；stop 恆為主 session 判斷
    text = _skill_text()
    assert "stalled-advisory" in text
    assert "只喚醒不處置" in text
    assert "偵測與處置分離" in text
    assert "恆歸主 session" in text


def test_d3_desc_trigger_words():
    # 卡 AC#2：desc 觸發詞涵蓋新形態
    desc = _skill_desc()
    # timebox 觸發詞刻意不收——bridge 域無 timebox 概念（in-harness 域＝harness_waiter／agent-workflow D5 標注）
    for word in ("bridge_waiter", "CollectionReceipt", "stalled-advisory"):
        assert word in desc, f"desc 缺觸發詞：{word}"


def test_d3_desc_length_within_budget():
    assert len(_skill_desc()) <= DESC_LIMIT, (
        f"desc 值 {len(_skill_desc())} chars 超上限 {DESC_LIMIT}（scan_skills_desc 同源 gate）"
    )


def test_d4_skill_watcher_section_pointer():
    text = _skill_text()
    assert "watcher 節" in text  # 指針段自身
    assert "scripts/bridge_waiter.py" in text
    assert "動態 T 公式" in text  # T 公式指針
    assert "CollectionReceipt 欄位集權威" in text  # schema 權威指針（＝AIR-135.7 AC#2）
    assert (
        "AIR-149 EP" in text
    )  # 兄弟契約同源指針（EP 路徑字面刻意不落 skill——權威＝AIR-135.7 AC#2）


def test_d5_agent_workflow_harness_waiter_reference_kept():
    # AIR-149 S3 已落地的工具化指涉——本弧禁退化
    text = AGENT_WORKFLOW.read_text()
    assert "scripts/harness_waiter.py" in text
    assert "liveness 工具化條" in text


def test_d5_agent_workflow_bridge_waiter_auto_arm_line():
    text = AGENT_WORKFLOW.read_text()
    assert "scripts/bridge_waiter.py" in text  # bridge 域 auto-arm 指涉
    assert "自動 arm" in text  # 規約一行錨點
    assert "bridge-dispatch skill" in text  # 規約單一源回指
