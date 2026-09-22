"""compact-restore-inject hook 決策邏輯測試（AIR-155 segment 2，AC-D＋AC-B）。

四情境（有／無／已消費／損壞 checkpoint）＋compaction 記錄閘（誤拿防護）
＋fail-open 驗證。hook 消費 scripts/compact_checkpoint.py 的驗證/proven
機制（同一驗證，非重寫）——proven 綁定、hash 漂移重新注入等語義由本檔與
test_compact_checkpoint.py 兩端共同釘住。
"""

import datetime
import hashlib
import json
import sqlite3

from conftest import load_module

ccp = load_module("scripts/compact_checkpoint.py")
cri = load_module("hooks/compact-restore-inject.py")

SESSION = "sess_test-1234"


def _valid_data() -> dict:
    return {
        "schema": ccp.SCHEMA,
        "session_id": SESSION,
        "created_at": "2026-09-22T12:00:00+08:00",
        "objective": "segment 2：restore 注入 hook——thin pointer 決策邏輯",
        "completed": ["RED 測試就位"],
        "next_action": "GREEN：實作 hook 與路徑約定",
        "pending": ["主 session 執行機器註冊"],
    }


def _write_checkpoint(root, data=None, raw=None):
    """寫入約定路徑的 checkpoint；raw 非 None 時寫原始 bytes（損壞情境用）。"""
    cp_path, proven_path = ccp.checkpoint_paths(root, SESSION)
    cp_path.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        cp_path.write_bytes(raw)
    else:
        cp_path.write_text(
            json.dumps(data or _valid_data(), ensure_ascii=False), encoding="utf-8"
        )
    return cp_path, proven_path


def _payload(root, session_id=SESSION) -> str:
    return json.dumps(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": session_id,
            "cwd": str(root),
        }
    )


FAR_FUTURE_MS = 4_102_444_800_000  # 2100-01-01 epoch ms——遠晚於任何 receipt


def _late_compaction(db_path, session_id):
    """stub：回報遠未來的 compaction 記錄（gate 恆過）。"""
    return FAR_FUTURE_MS


def _no_compaction(db_path, session_id):
    """stub：無任何 compaction 記錄。"""
    return None  # noqa: RET501 — None 是語義值（查無 compaction part），非冗餘回傳


def _receipt_baseline_ms(proven_path) -> int:
    """測試側獨立換算 receipt verified_at → epoch ms（不經 hook 內部函式）。"""
    data = json.loads(proven_path.read_text(encoding="utf-8"))
    verified = datetime.datetime.fromisoformat(data["verified_at"])
    return int(verified.timestamp() * 1000)


class TestEvaluateFourScenarios:
    def test_no_checkpoint_is_none(self, tmp_path):
        action, _info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_no_compaction
        )
        assert action == "none"

    def test_unconsumed_checkpoint_is_inject(self, tmp_path):
        cp_path, _ = _write_checkpoint(tmp_path)
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "inject"
        assert info["checkpoint_path"] == str(cp_path)
        assert info["sha256"] == hashlib.sha256(cp_path.read_bytes()).hexdigest()

    def test_consumed_checkpoint_is_consumed(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path, verified_by="test")
        action, _info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_no_compaction
        )
        assert action == "consumed"

    def test_corrupt_checkpoint_is_corrupt(self, tmp_path):
        cp_path, _ = _write_checkpoint(tmp_path, raw=b"{broken json")
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "corrupt"
        assert info["checkpoint_path"] == str(cp_path)
        assert "checkpoint" in info["error"]

    def test_checkpoint_isolated_by_session_id(self, tmp_path):
        _write_checkpoint(tmp_path)
        action, _info = cri.evaluate(tmp_path, "sess_other-session")
        assert action == "none"


class TestProvenBindingSemantics:
    def test_corrupt_proven_receipt_still_injects(self, tmp_path):
        # proven receipt 壞＝無法判定已消費；靜默＝未消費 checkpoint 可能無聲損失
        _cp_path, proven_path = _write_checkpoint(tmp_path)
        proven_path.write_text("{corrupt", encoding="utf-8")
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "inject"
        assert "receipt_error" in info

    def test_hash_drift_after_proven_reinjects(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path)
        baseline_ms = _receipt_baseline_ms(proven_path)
        data = _valid_data()
        data["next_action"] = "proven 後又有新工作——狀態已更新"
        cp_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        def compaction_after_proven(db_path, session_id):
            return baseline_ms + 60_000  # baseline 後又有新 compaction

        action, _info = cri.evaluate(
            tmp_path, SESSION, query_compaction=compaction_after_proven
        )
        assert action == "inject"  # proven 綁舊內容 hash → 失效 → 重新注入

    def test_consumed_sha256_matches_proven_receipt_binding(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path)
        _action, info = cri.evaluate(tmp_path, SESSION, query_compaction=_no_compaction)
        proven = json.loads(proven_path.read_text(encoding="utf-8"))
        assert info["sha256"] == proven["checkpoint_sha256"]

    def test_injected_sha256_matches_proven_receipt_binding(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path)
        _action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        proven = json.loads(proven_path.read_text(encoding="utf-8"))
        assert info["sha256"] == proven["checkpoint_sha256"]


class TestBuildContextThinPointer:
    def test_none_and_consumed_produce_no_context(self, tmp_path):
        assert cri.build_context("none", {}) == ""
        assert cri.build_context("consumed", {"checkpoint_path": "x"}) == ""

    def test_inject_pointer_has_path_hash_and_read_first(self, tmp_path):
        cp_path, _ = _write_checkpoint(tmp_path)
        _action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        context = cri.build_context("inject", info)
        assert context.startswith("<compact-restore-inject>")
        assert str(cp_path) in context
        assert info["sha256"] in context
        assert "先讀" in context  # 讀檔指令——指針非內容本體
        assert "write_restore_proven" in context  # 恢復驗證接線指針

    def test_thin_pointer_excludes_full_text(self, tmp_path):
        sentinel = "SENTINEL-FULL-TEXT" * 400  # 6800 字——全文不得進 context
        data = _valid_data()
        data["objective"] = sentinel
        _cp_path, _ = _write_checkpoint(tmp_path, data=data)
        _action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        context = cri.build_context("inject", info)
        assert sentinel not in context  # codex spill 語義同構：只帶指針

    def test_preview_bounded_for_large_file(self, tmp_path):
        data = _valid_data()
        data["completed"] = ["x" * 5000]
        _cp_path, _ = _write_checkpoint(tmp_path, data=data)
        _action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        context = cri.build_context("inject", info)
        assert len(context) < 4000  # head/tail 各 400 bytes 量級，非全文
        assert "中略" in context  # 大檔標記截斷

    def test_corrupt_context_names_path_and_error(self, tmp_path):
        cp_path, _ = _write_checkpoint(tmp_path, raw=b"{broken")
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "corrupt"
        context = cri.build_context("corrupt", info)
        assert str(cp_path) in context
        assert "損壞" in context


class TestRunFailOpen:
    """run() 契約：永不 raise、exit 恆 0、該靜默時零輸出。"""

    def test_no_checkpoint_zero_output(self, tmp_path):
        code, out = cri.run(_payload(tmp_path))
        assert code == 0 and out == ""

    def test_consumed_zero_output(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path)
        code, out = cri.run(_payload(tmp_path))
        assert code == 0 and out == ""

    def test_inject_outputs_protocol_json(self, tmp_path):
        _write_checkpoint(tmp_path)
        code, out = cri.run(_payload(tmp_path), query_compaction=_late_compaction)
        assert code == 0
        parsed = json.loads(out)
        specific = parsed["hookSpecificOutput"]
        assert specific["hookEventName"] == "UserPromptSubmit"
        assert "<compact-restore-inject>" in specific["additionalContext"]

    def test_garbage_stdin_fail_open(self):
        for raw in ["not json", "", "[]", '"str"', "null"]:
            code, out = cri.run(raw)
            assert code == 0 and out == ""

    def test_missing_fields_fail_open(self):
        code, out = cri.run(json.dumps({"session_id": ""}))
        assert code == 0 and out == ""

    def test_broken_ccp_dependency_fail_open(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cri, "CCP", object())  # 機制模組不可用
        _write_checkpoint(tmp_path)
        code, out = cri.run(_payload(tmp_path))
        assert code == 0 and out == ""

    def test_output_guard_suppresses_oversized_injection(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cri, "OUTPUT_GUARD_BYTES", 100)
        _write_checkpoint(tmp_path)
        code, out = cri.run(_payload(tmp_path), query_compaction=_late_compaction)
        assert code == 0 and out == ""


class TestCompactionGate:
    """AC-B compaction 記錄閘——gate_pass 才走原分流（誤拿防護）。

    gate_pass ⇔ zcode DB 存在晚於 baseline（proven verified_at epoch ms；
    無 receipt＝0）的 compaction part 記錄。gate_pass=False → 靜默：無有效
    proven 回 none、有則 consumed；DB 查詢任何異常 → 視同無記錄（fail-open
    優先於 gate）。gate 與 checkpoint 內容判定正交——gate 過後才走原分流。
    """

    def test_no_compaction_record_is_none(self, tmp_path):
        _write_checkpoint(tmp_path)  # checkpoint 存在且未 proven——舊制會 inject
        action, _info = cri.evaluate(tmp_path, SESSION, query_compaction=_no_compaction)
        assert action == "none"

    def test_late_record_unproven_is_inject(self, tmp_path):
        cp_path, _ = _write_checkpoint(tmp_path)
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "inject"
        assert info["checkpoint_path"] == str(cp_path)

    def test_late_record_corrupt_is_corrupt(self, tmp_path):
        cp_path, _ = _write_checkpoint(tmp_path, raw=b"{broken json")
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "corrupt"
        assert info["checkpoint_path"] == str(cp_path)
        assert "checkpoint" in info["error"]

    def test_record_older_than_proven_is_consumed(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path, verified_by="test")
        baseline_ms = _receipt_baseline_ms(proven_path)

        def older_than_proven(db_path, session_id):
            return baseline_ms - 60_000

        action, _info = cri.evaluate(
            tmp_path, SESSION, query_compaction=older_than_proven
        )
        assert action == "consumed"

    def test_no_record_with_valid_proven_is_consumed(self, tmp_path):
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path, verified_by="test")
        action, _info = cri.evaluate(tmp_path, SESSION, query_compaction=_no_compaction)
        assert action == "consumed"

    def test_late_record_with_valid_proven_reinjects(self, tmp_path):
        # F3（settlement）：proven 後又 compaction＝已恢復 context 被再壓 → re-restore 注入
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path, verified_by="test")
        action, info = cri.evaluate(
            tmp_path, SESSION, query_compaction=_late_compaction
        )
        assert action == "inject"
        assert info["re_restore"] == "proven predates latest compaction"
        assert info["sha256"] == ccp._checkpoint_digest(cp_path)

    def test_db_query_exception_is_none(self, tmp_path):
        _write_checkpoint(tmp_path)

        def boom(db_path, session_id):
            raise RuntimeError("db gone")

        action, _info = cri.evaluate(tmp_path, SESSION, query_compaction=boom)
        assert action == "none"

    def test_db_query_exception_with_valid_proven_is_consumed(self, tmp_path):
        # fail-open 優先於 gate——查詢異常不得把已消費誤判成待注入
        cp_path, proven_path = _write_checkpoint(tmp_path)
        ccp.write_restore_proven(proven_path, cp_path, verified_by="test")

        def boom(db_path, session_id):
            raise RuntimeError("db gone")

        action, _info = cri.evaluate(tmp_path, SESSION, query_compaction=boom)
        assert action == "consumed"

    def test_run_without_compaction_is_silent(self, tmp_path):
        _write_checkpoint(tmp_path)
        code, out = cri.run(_payload(tmp_path), query_compaction=_no_compaction)
        assert code == 0 and out == ""


class TestCompactionDbQuery:
    """_max_compaction_ms 對真實 sqlite schema（part×message JOIN＋json_extract）。"""

    @staticmethod
    def _make_db(path, parts):
        conn = sqlite3.connect(str(path))
        conn.execute(
            "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT NOT NULL,"
            " time_created INTEGER NOT NULL, data TEXT NOT NULL)"
        )
        conn.execute("INSERT INTO message VALUES ('m1', ?)", (SESSION,))
        conn.execute("INSERT INTO message VALUES ('m2', 'sess_other')")
        for ts, ptype, mid in parts:
            conn.execute(
                "INSERT INTO part VALUES (?, ?, ?, ?)",
                (f"p-{ts}-{ptype}", mid, ts, json.dumps({"type": ptype})),
            )
        conn.commit()
        conn.close()

    def test_returns_latest_compaction_time_for_session(self, tmp_path):
        db = tmp_path / "db.sqlite"
        self._make_db(
            db,
            [
                (1000, "compaction", "m1"),
                (2000, "compaction", "m1"),
                (3000, "text", "m1"),  # 非 compaction 不計
                (99999, "compaction", "m2"),  # 其他 session 不計
            ],
        )
        assert cri._max_compaction_ms(str(db), SESSION) == 2000
        assert cri._max_compaction_ms(str(db), "sess_none") is None

    def test_missing_db_returns_none_without_side_effect(self, tmp_path):
        missing = tmp_path / "absent.sqlite"
        assert cri._max_compaction_ms(str(missing), SESSION) is None
        assert not missing.exists()  # 唯讀——禁 sqlite 副作用建檔


class TestProvenBaselineMs:
    """baseline＝proven receipt verified_at 的 epoch ms；缺／壞 receipt＝0。"""

    def test_parses_verified_at_to_epoch_ms(self, tmp_path):
        _cp_path, proven_path = _write_checkpoint(tmp_path)
        receipt = {
            "schema": ccp.PROVEN_SCHEMA,
            "checkpoint_path": "x",
            "checkpoint_sha256": "x",
            "verified_at": "2026-09-22T12:00:00+08:00",
        }
        proven_path.write_text(
            json.dumps(receipt, ensure_ascii=False), encoding="utf-8"
        )
        expected = int(
            datetime.datetime.fromisoformat("2026-09-22T12:00:00+08:00").timestamp()
            * 1000
        )
        assert cri._proven_baseline_ms(proven_path) == expected

    def test_missing_or_corrupt_receipt_is_zero(self, tmp_path):
        _cp_path, proven_path = _write_checkpoint(tmp_path)
        assert cri._proven_baseline_ms(proven_path) == 0  # 缺 receipt
        proven_path.write_text("{corrupt", encoding="utf-8")
        assert cri._proven_baseline_ms(proven_path) == 0  # 壞 receipt
