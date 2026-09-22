"""compact_checkpoint 機制件測試（AIR-155 Segment 1，AC#2/#3）。

四問可答機械判準（目標/已完成/下一步/懸掛動作）＋壞檔 fail-loud＋
restore-proven 綁 checkpoint 內容 hash＋未 proven 時 cleanup guard 擋行。
欄位對齊 skills/_common/task-recovery.md「寫入端」（唯讀消費，禁改定義源）。
"""

import json

import pytest
from conftest import load_module

ccp = load_module("scripts/compact_checkpoint.py")


def _valid_data() -> dict:
    """四問齊備的最小合法 checkpoint（欄位名映射 task-recovery 寫入端欄位）。"""
    return {
        "schema": ccp.SCHEMA,
        "session_id": "session-abc",
        "created_at": "2026-09-22T10:00:00+08:00",
        "objective": "AIR-155：compact 前交接機制化——gate 探針＋checkpoint 機制件",
        "completed": [
            "Segment 1 機制件 TDD 紅轉綠",
            "探針 fixture 落 .agent-tmp/probe/",
        ],
        "next_action": "主 session 執行機器註冊後跑 live acceptance",
        "pending": ["等待 compact 事件觀察", "未裁決：probe fixture 去留"],
    }


def _write_checkpoint(tmp_path, data: dict):
    p = tmp_path / "checkpoint.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


class TestValidateCheckpoint:
    def test_valid_data_passes_and_returns_four_answers(self):
        cp = ccp.validate_checkpoint(_valid_data())
        assert cp.objective.startswith("AIR-155")
        assert cp.completed == [
            "Segment 1 機制件 TDD 紅轉綠",
            "探針 fixture 落 .agent-tmp/probe/",
        ]
        assert cp.next_action.startswith("主 session")
        assert len(cp.pending) == 2

    @pytest.mark.parametrize(
        "key", ["objective", "completed", "next_action", "pending"]
    )
    def test_missing_any_of_four_questions_rejected(self, key):
        data = _valid_data()
        del data[key]
        with pytest.raises(ccp.CheckpointError, match=key):
            ccp.validate_checkpoint(data)

    def test_empty_objective_rejected(self):
        data = _valid_data()
        data["objective"] = "   "
        with pytest.raises(ccp.CheckpointError, match="objective"):
            ccp.validate_checkpoint(data)

    def test_empty_next_action_rejected(self):
        data = _valid_data()
        data["next_action"] = ""
        with pytest.raises(ccp.CheckpointError, match="next_action"):
            ccp.validate_checkpoint(data)

    def test_non_string_objective_rejected(self):
        data = _valid_data()
        data["objective"] = ["not", "a", "string"]
        with pytest.raises(ccp.CheckpointError, match="objective"):
            ccp.validate_checkpoint(data)

    def test_completed_as_string_rejected(self):
        data = _valid_data()
        data["completed"] = "_done 不是 list"
        with pytest.raises(ccp.CheckpointError, match="completed"):
            ccp.validate_checkpoint(data)

    def test_pending_as_string_rejected(self):
        data = _valid_data()
        data["pending"] = "pending 不是 list"
        with pytest.raises(ccp.CheckpointError, match="pending"):
            ccp.validate_checkpoint(data)

    def test_empty_lists_are_answerable(self):
        # 弧起點「尚未完成」「無懸掛」是合法回答——四問判準是可答非有進度
        data = _valid_data()
        data["completed"] = []
        data["pending"] = []
        ccp.validate_checkpoint(data)

    def test_all_violations_reported_at_once(self):
        data = _valid_data()
        del data["objective"]
        del data["pending"]
        with pytest.raises(ccp.CheckpointError) as exc:
            ccp.validate_checkpoint(data)
        assert "objective" in str(exc.value)
        assert "pending" in str(exc.value)


class TestLoadCheckpoint:
    def test_valid_file_roundtrip(self, tmp_path):
        p = _write_checkpoint(tmp_path, _valid_data())
        data = ccp.load_checkpoint(p)
        assert data["session_id"] == "session-abc"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ccp.CheckpointError, match="not found"):
            ccp.load_checkpoint(tmp_path / "nope.json")

    def test_bad_json_fails_loud(self, tmp_path):
        p = tmp_path / "checkpoint.json"
        p.write_text("{broken json", encoding="utf-8")
        with pytest.raises(ccp.CheckpointError, match="bad json"):
            ccp.load_checkpoint(p)

    def test_non_dict_json_rejected(self, tmp_path):
        p = tmp_path / "checkpoint.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(ccp.CheckpointError):
            ccp.load_checkpoint(p)

    def test_missing_schema_rejected(self, tmp_path):
        data = _valid_data()
        del data["schema"]
        p = _write_checkpoint(tmp_path, data)
        with pytest.raises(ccp.CheckpointError, match="schema"):
            ccp.load_checkpoint(p)

    def test_wrong_schema_rejected(self, tmp_path):
        data = _valid_data()
        data["schema"] = "compact-checkpoint/999"
        p = _write_checkpoint(tmp_path, data)
        with pytest.raises(ccp.CheckpointError, match="schema"):
            ccp.load_checkpoint(p)

    def test_load_then_validate_full_path(self, tmp_path):
        p = _write_checkpoint(tmp_path, _valid_data())
        cp = ccp.validate_checkpoint(ccp.load_checkpoint(p))
        assert cp.next_action


class TestRestoreProven:
    def test_write_then_proven_true(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        ccp.write_restore_proven(proven_path, cp_path, verified_by="test")
        assert ccp.is_restore_proven(proven_path, cp_path) is True

    def test_proven_binds_checkpoint_content_hash(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        ccp.write_restore_proven(proven_path, cp_path)
        # proven 後 checkpoint 內容被換 → proven 失效（綁 bytes 非綁路徑）
        data = _valid_data()
        data["next_action"] = "換掉的下一步"
        cp_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        proven, reasons = ccp.verify_restore_proven(proven_path, cp_path)
        assert proven is False
        assert "checkpoint_hash_mismatch" in reasons

    def test_write_rejects_invalid_checkpoint_and_writes_nothing(self, tmp_path):
        data = _valid_data()
        del data["next_action"]
        cp_path = _write_checkpoint(tmp_path, data)
        proven_path = tmp_path / "proven.json"
        with pytest.raises(ccp.CheckpointError, match="next_action"):
            ccp.write_restore_proven(proven_path, cp_path)
        assert not proven_path.exists()

    def test_missing_proven_file_is_unproven(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        assert ccp.is_restore_proven(tmp_path / "absent.json", cp_path) is False

    def test_checkpoint_missing_after_proven_is_unproven(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        ccp.write_restore_proven(proven_path, cp_path)
        cp_path.unlink()
        assert ccp.is_restore_proven(proven_path, cp_path) is False

    def test_corrupt_proven_json_fails_loud(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        proven_path.write_text("{corrupt", encoding="utf-8")
        with pytest.raises(ccp.CheckpointError, match="bad json"):
            ccp.is_restore_proven(proven_path, cp_path)

    def test_wrong_proven_schema_fails_loud(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        proven_path.write_text(
            json.dumps({"schema": "compact-restore-proven/999"}), encoding="utf-8"
        )
        with pytest.raises(ccp.CheckpointError, match="schema"):
            ccp.is_restore_proven(proven_path, cp_path)

    def test_different_checkpoint_path_mismatch(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        ccp.write_restore_proven(proven_path, cp_path)
        other = tmp_path / "other-checkpoint.json"  # 不同路徑（同內容）
        other.write_text(
            json.dumps(_valid_data(), ensure_ascii=False), encoding="utf-8"
        )
        proven, reasons = ccp.verify_restore_proven(proven_path, other)
        assert proven is False
        assert "checkpoint_path_mismatch" in reasons


class TestCheckpointPaths:
    """checkpoint/proven 約定落點（segment 2 restore hook 與 skill fallback 共用單一源）。"""

    def test_pair_under_agent_tmp_with_fixed_names(self, tmp_path):
        cp, proven = ccp.checkpoint_paths(tmp_path, "sess_abc")
        assert cp.parent == proven.parent  # 成對同目錄（cleanup 同擋）
        assert cp.parent == tmp_path / ".agent-tmp" / "compact-checkpoints" / "sess_abc"
        assert cp.name == "checkpoint.json"
        assert proven.name == "restore-proven.json"

    def test_normal_session_id_unchanged(self, tmp_path):
        sid = "sess_48b59be8-6c19-4761-99d0-91646b5e867a"
        cp, _ = ccp.checkpoint_paths(tmp_path, sid)
        assert cp.parent.name == sid

    def test_session_id_traversal_sanitized(self, tmp_path):
        cp, proven = ccp.checkpoint_paths(tmp_path, "../../evil")
        # sanitize 後是 checkpoints 目錄下的單一元件——無分隔符、非 .／..
        assert cp.parent.parent.parent == tmp_path / ".agent-tmp"
        name = cp.parent.name
        assert "/" not in name and name not in ("", ".", "..")
        assert proven.parent == cp.parent

    def test_dot_dot_session_becomes_placeholder(self, tmp_path):
        cp, _ = ccp.checkpoint_paths(tmp_path, "..")
        assert cp.parent.name == "_"

    def test_empty_session_becomes_placeholder(self, tmp_path):
        cp, _ = ccp.checkpoint_paths(tmp_path, "")
        assert cp.parent.name == "_"


class TestCleanupGuard:
    def test_guard_error_is_checkpoint_error(self):
        assert issubclass(ccp.CleanupBlockedError, ccp.CheckpointError)

    def test_unproven_blocks_cleanup(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        with pytest.raises(ccp.CleanupBlockedError, match="cleanup blocked"):
            ccp.assert_cleanup_allowed(cp_path, proven_path)

    def test_proven_allows_cleanup(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        ccp.write_restore_proven(proven_path, cp_path)
        ccp.assert_cleanup_allowed(cp_path, proven_path)  # 不 raise＝放行

    def test_hash_drift_after_proven_blocks_again(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        ccp.write_restore_proven(proven_path, cp_path)
        data = _valid_data()
        data["pending"] = ["proven 後又動了 checkpoint"]
        cp_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(ccp.CleanupBlockedError):
            ccp.assert_cleanup_allowed(cp_path, proven_path)

    def test_block_message_names_both_artifacts(self, tmp_path):
        cp_path = _write_checkpoint(tmp_path, _valid_data())
        proven_path = tmp_path / "proven.json"
        with pytest.raises(ccp.CleanupBlockedError) as exc:
            ccp.assert_cleanup_allowed(cp_path, proven_path)
        msg = str(exc.value)
        assert str(cp_path) in msg
        assert str(proven_path) in msg
