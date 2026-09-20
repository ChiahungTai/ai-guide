"""agent-workflow liveness doctrine 錨點測試（AIR-149 S3）.

EP S3 驗證式＝`rg resumed_during_quarantine skills/agent-workflow/` 命中；
本檔把 doctrine 改寫的不可退化錨點固化為機械檢查：工具化指涉、凍結處置
協議（user 裁決條款）、RETRY_SAFE 三問、dispatch 註冊、偵測與處置分離＋
bridge advisory-only 邊界、驗屍法手工 fallback。
"""

from conftest import REPO_ROOT

SKILL = REPO_ROOT / "skills" / "agent-workflow" / "SKILL.md"


def _text() -> str:
    return SKILL.read_text()


def test_ep_s3_verification_anchor():
    # EP S3 驗證式：quarantine 恢復仍砍——禁 liveness inference 回滲
    text = _text()
    assert "resumed_during_quarantine" in text
    assert "仍照砍" in text
    assert "liveness inference" in text


def test_tool_reference_and_register_invocation():
    text = _text()
    assert "scripts/harness_waiter.py" in text
    assert "--register" in text  # dispatch 註冊一行（S2 invocation）
    assert "--surviving-handle" in text  # 未登記 daemon child 的 ownership 面


def test_freeze_disposal_protocol_chain():
    # user 裁決條款：靜默 20m→收割→喚醒→TaskStop→STOP verification
    text = _text()
    for anchor in ("TaskStop", "STOP_CONFIRMED", "STOP_INCOMPLETE", "20m"):
        assert anchor in text, f"缺凍結處置協議錨點：{anchor}"


def test_retry_safe_three_questions():
    text = _text()
    for anchor in ("surviving handles", "outward side effect", "deliverable"):
        assert anchor in text, f"缺 RETRY_SAFE 三問錨點：{anchor}"


def test_separation_and_bridge_boundary_preserved():
    text = _text()
    assert "偵測與處置分離" in text  # watcher 永不 stop／重派
    assert "advisory-only" in text  # bridge 域 AIR-146 邊界不隨工具化改


def test_manual_autopsy_kept_as_fallback():
    text = _text()
    assert "驗屍法" in text
    assert "fallback" in text  # 手工程序降位為 watcher 不可用時的 fallback
