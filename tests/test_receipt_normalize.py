"""receipt_normalize 契約測試（AIR-135.1 S2——跨家族回執正規化）。

釘住的 invariant（卡面 Plan＋S1 延伸勿重辯）：
- D7：canonical 目標形＝S1 receipt schema（slice-receipt/1）；正規化產物須過
  arc_spec.validate("receipt")（terminal≠complete——completed 配 not-assessed 即紅）。
- D1：normalize＝純函式轉換，無引擎／無台帳寫入。
- D8：family/model/ledger 語義實填（family 進 canonical；model/ledger/usage 為 extras）。
- fail-loud（codex 文案形）：未知 family 列可用值、缺欄一次列全部、雙 authoritative
  （family/job id/delivery/status）即錯、歧義帳本狀態拒收待 status_override。

fixture 誠實聲明：四家族案例全為今晚真實回執（job id 可對帳兩本 jobs.json；
CollectionReceipt 條目逐字取自 waiter stdout log）——僅對 normalize 非消費面的大
欄（promptPreview／modelRequests 56 筆／finishReasons／eventTypes_seen 等）做機械
trim，消費面欄位全數保留原值。
"""

import pytest
from conftest import load_module

_mod = load_module("scripts/receipt_normalize.py")
_arc = load_module("scripts/arc_spec.py")

PLAN_HASH = "b" * 64  # 合法形 hex64；真實密封值（brief sha256）由 seal 腳本機算

LEDGER_MAIN = "/Users/ctai/Github/ai-guide/.delegate-bridge/jobs.json"
LEDGER_WT = "/Users/ctai/Github/ai-guide-air-135.1/.delegate-bridge/jobs.json"


# ---------------------------------------------------------------------------
# 今晚真實回執 fixtures（消費面欄位原值；非消費面機械 trim）
# ---------------------------------------------------------------------------


def _slice_ref(slice_id: str) -> dict:
    return {
        "slice_id": slice_id,
        "card_id": "AIR-135.1",
        "unit_id": "AIR-135.1#S1",
        "plan_version": 1,
        "plan_hash": PLAN_HASH,
    }


def _glm_s1_flash_ledger() -> dict:
    """job-muflra3f-dd7ea4（card WT 帳本；S1 flash implement）。"""
    return {
        "id": "job-muflra3f-dd7ea4",
        "sessionId": "sess_6617d75a-6709-4ac4-98b2-c5d9cb32fa7e",
        "status": "completed",
        "steps": None,
        "effort": None,
        "model": "GLM-5.3-Flash",
        "summary": (
            "S1 工作單完成（至本 session 能力邊界）。五項 DONE-WHEN： "
            "1. **#1 四物 schema＋每欄標注 — PASS**：`scripts/arc_spec.py` ARTIFACTS "
            "registry 63 欄全標 machine-invariant／llm-guidance（D5/D8 resolver 欄標 dispatch-stage）；`schema` 子命令輸出"
        ),
        "exitCode": 0,
        "timestamp": "2026-09-24T14:34:16.444Z",
        "family": "glm",
        "callerHarness": "zcode",
        "callerSession": "sess_81adb354-9860-428b-a5f6-bf50c3236d8c",
        "callerPid": 78727,
        "effectiveModel": "GLM-5.3-Flash",
        "skippedUnparsable": 1,
        "skippedUnknown": 0,
        "jsonlPath": ".delegate-bridge/jobs/job-muflra3f-dd7ea4.jsonl",
        "assembledChars": 1220,
        "carrierExit": 0,
        "mode": "edit",
        "resultUsage": {
            "cacheReadTokens": 7140160,
            "cacheWriteTokens": 0,
            "inputTokens": 7330192,
            "modelRequestCount": 56,
            "outputTokens": 76398,
            "reasoningTokens": 0,
            "source": "provider",
            "totalTokens": 7406590,
            "webFetchRequests": 0,
            "webSearchRequests": 0,
        },
        "toolCounts": {"Agent": 2, "Edit": 5, "Read": 21, "Write": 9},
        "truncationCount": 0,
        "wtPath": "/Users/ctai/Github/ai-guide-air-135.1",
    }


def _glm_judge_ledger() -> dict:
    """job-mufna554-a7unmg（主 repo 帳本；S1 judge GLM-5.3）。"""
    return {
        "id": "job-mufna554-a7unmg",
        "sessionId": "sess_6795b817-e463-4b5b-9a3f-45b3e5136e58",
        "status": "completed",
        "steps": None,
        "effort": None,
        "model": "GLM-5.3",
        "summary": (
            "材料完備，判讀已收斂。我已親讀全部受審產物（`scripts/arc_spec.py` 861 行、"
            "`tests/test_arc_spec.py` 575 行全文、四樣本、seal 腳本二檔）、雙腿 findings、"
            "worker receipt 與卡面，並以兩樹檔面盤點完成 diff 範圍核對"
        ),
        "exitCode": 0,
        "timestamp": "2026-09-24T14:52:16.182Z",
        "family": "glm",
        "callerHarness": None,
        "callerPid": 97451,
        "effectiveModel": "GLM-5.3",
        "skippedUnparsable": 1,
        "skippedUnknown": 0,
        "jsonlPath": ".delegate-bridge/jobs/job-mufna554-a7unmg.jsonl",
        "assembledChars": 263,
        "carrierExit": 0,
        "mode": "plan",
        "resultUsage": {
            "cacheReadTokens": 786112,
            "cacheWriteTokens": 0,
            "inputTokens": 891076,
            "modelRequestCount": 10,
            "outputTokens": 20059,
            "reasoningTokens": 0,
            "source": "provider",
            "totalTokens": 911135,
            "webFetchRequests": 0,
            "webSearchRequests": 0,
        },
        "toolCounts": {"Agent": 1, "ExitPlanMode": 1, "Glob": 5, "Read": 34},
        "truncationCount": 0,
    }


def _codex_ledger() -> dict:
    """job-mufn1cui-x7lfwh（主 repo 帳本；S1 post-build codex 腿）——逐字全欄。"""
    return {
        "id": "job-mufn1cui-x7lfwh",
        "sessionId": "01a0d3db-6b4f-7911-ba6f-9f2756004762",
        "status": "completed",
        "steps": None,
        "effort": "high",
        "model": "chatgpt-web/high",
        "summary": (
            "POSTBUILD-VERDICT: PASS-WITH-FIXES blocking: 0 "
            "findings: /Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/postbuild-codex.md"
        ),
        "exitCode": 0,
        "timestamp": "2026-09-24T14:40:28.265Z",
        "family": "codex",
        "callerHarness": None,
        "callerPid": 47126,
        "skippedUnparsable": 0,
        "skippedUnknown": 0,
        "jsonlPath": ".delegate-bridge/jobs/job-mufn1cui-x7lfwh.jsonl",
        "carrierExit": 0,
        "carrierUsage": {
            "cache_write_input_tokens": 0,
            "cached_input_tokens": 0,
            "input_tokens": 296428,
            "output_tokens": 1358,
            "reasoning_output_tokens": 0,
        },
        "codexCliVersion": "codex-cli 0.155.0-alpha.16",
        "itemTypeCounts": {"agent_message": 1, "command_execution": 2, "file_change": 1},
        "provenanceRename": "ok",
        "transport": "web",
    }


def _muse_ledger() -> dict:
    """job-mufn1cw6-f4fmzx（主 repo 帳本；S1 post-build muse 腿）——逐字全欄（無 usage 面）。"""
    return {
        "id": "job-mufn1cw6-f4fmzx",
        "sessionId": "01a0d3db-6b28-70e0-80e3-04086dc5d45a",
        "status": "completed",
        "steps": 200,
        "effort": "xhigh",
        "model": "muse-spark-1.3",
        "summary": (
            "POSTBUILD-VERDICT: PASS-WITH-FIXES — blocking 0 Findings: "
            "`/Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/postbuild-muse.md` "
            "(6 non-blocking + 4 notes) Independently verified: 52/52 tests green, a"
        ),
        "exitCode": 0,
        "timestamp": "2026-09-24T14:42:08.009Z",
        "family": "muse",
        "callerHarness": None,
        "callerPid": 47123,
        "skippedUnparsable": 0,
        "skippedUnknown": 85,
        "jsonlPath": ".delegate-bridge/jobs/job-mufn1cw6-f4fmzx.jsonl",
        "carrierExit": 0,
        "provenanceRename": "nonzero-exit(1)",
    }


def _glm_judge_stop_ledger() -> dict:
    """job-mufn9pd8-1zuq1i（judge 的 stop 前身——interrupted，carrierExit 143）。"""
    return {
        "id": "job-mufn9pd8-1zuq1i",
        "sessionId": None,
        "status": "interrupted",
        "steps": None,
        "effort": None,
        "model": "GLM-5.3-Flash",
        "summary": "# AIR-135.1 S1 judge 工作單（GLM-5.3 第三方評審） 你是 S1 的 judge",
        "exitCode": None,
        "timestamp": "2026-09-24T14:46:16.845Z",
        "family": "glm",
        "callerHarness": None,
        "callerPid": 96320,
        "jsonlPath": ".delegate-bridge/jobs/job-mufn9pd8-1zuq1i.jsonl",
        "carrierExit": 143,
        "mode": "plan",
    }


def _collection_codex() -> dict:
    """waiter CollectionReceipt jobs[] 條目（call_e5da7b13… log 逐字）。"""
    return {
        "jobId": "job-mufn1cui-x7lfwh",
        "status": "completed",
        "family": "codex",
        "delivery": {
            "mode": "artifact",
            "sink": "/Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/postbuild-codex.md",
            "l1_present": True,
            "l1_detail": "存在＋非空",
            "l2_anchor": True,
            "anchor_hits": ["POSTBUILD-VERDICT"],
            "verdict": "delivered",
        },
        "boundedReceiptProjection": {
            "finalTextNonEmpty": True,
            "note": "AIR-135.7 AC#2 bounded receipt 欄位集投影；語義欄判定歸 caller",
        },
    }


def _collection_muse() -> dict:
    return {
        "jobId": "job-mufn1cw6-f4fmzx",
        "status": "completed",
        "family": "muse",
        "delivery": {
            "mode": "artifact",
            "sink": "/Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/postbuild-muse.md",
            "l1_present": True,
            "l1_detail": "存在＋非空",
            "l2_anchor": True,
            "anchor_hits": ["POSTBUILD-VERDICT"],
            "verdict": "delivered",
        },
        "boundedReceiptProjection": {
            "finalTextNonEmpty": True,
            "note": "AIR-135.7 AC#2 bounded receipt 欄位集投影；語義欄判定歸 caller",
        },
    }


def _collection_s1_flash() -> dict:
    """waiter CollectionReceipt jobs[] 條目（call_6961d39a… log 逐字）。"""
    return {
        "jobId": "job-muflra3f-dd7ea4",
        "status": "completed",
        "family": "glm",
        "delivery": {
            "mode": "artifact",
            "sink": ".agent-tmp/air-135.1/s1-receipt.md",
            "l1_present": True,
            "l1_detail": "存在＋非空",
            "l2_anchor": True,
            "anchor_hits": ["S1-DONE-WHEN"],
            "verdict": "delivered",
        },
        "boundedReceiptProjection": {
            "finalTextNonEmpty": True,
            "note": "AIR-135.7 AC#2 bounded receipt 欄位集投影；語義欄判定歸 caller",
        },
    }


def _terminal_codex() -> dict:
    """codex jsonl 終端文字記錄（job-mufn1cui-x7lfwh line 9 逐字）。"""
    return {
        "type": "item.completed",
        "item": {
            "id": "item_3",
            "type": "agent_message",
            "text": (
                "POSTBUILD-VERDICT: PASS-WITH-FIXES  \nblocking: 0  \n"
                "findings: /Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/postbuild-codex.md"
            ),
        },
    }


def _terminal_muse() -> dict:
    """muse jsonl 終端記錄（job-mufn1cw6-f4fmzx line 522 逐字）。"""
    return {
        "schema_version": 1,
        "record_type": "event",
        "payload_type": "run.terminal.completed",
        "payload": {
            "kind": "run_terminal",
            "terminal": "completed",
            "text": (
                "POSTBUILD-VERDICT: PASS-WITH-FIXES — blocking 0\n\nFindings: "
                "`/Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/postbuild-muse.md` "
                "(6 non-blocking + 4 notes)\n\nIndependently verified: 52/52 tests green, "
                "all four samples VALID at correct stages, sealed plan_hash recomputes "
                "exactly, diff limited to `scripts/arc_spec.py` + `tests/test_arc_spec.py`. "
                "No D1–D8 violation."
            ),
            "reason": None,
        },
    }


def _terminal_glm_judge() -> dict:
    """glm jsonl 終端記錄（job-mufna554-a7unmg line 19924 逐字，usage 面 trim）。"""
    return {
        "eventId": "9ce61388-81df-4707-8a25-304305facde3",
        "payload": {
            "response": (
                "材料完備，判讀已收斂。我已親讀全部受審產物（`scripts/arc_spec.py` 861 行、"
                "`tests/test_arc_spec.py` 575 行全文、四樣本、seal 腳本二檔）、雙腿 findings、"
                "worker receipt 與卡面，並以兩樹檔面盤點完成 diff 範圍核對"
                "（本 judge session 無 shell 執行面——與 worker 同環境限制，以 muse stat 證詞＋"
                "兩樹 glob 同構＋pre-commit 閘三方交叉替代）。判決已定：**GO**。現提出判決書落盤計畫。"
            ),
            "tokenCount": 911135,
            "usage": {
                "inputTokens": 891076,
                "outputTokens": 20059,
                "totalTokens": 911135,
            },
            "toolCallCount": 22,
            "resultType": "success",
        },
        "seq": 15100,
        "sessionId": "sess_6795b817-e463-4b5b-9a3f-45b3e5136e58",
        "type": "turn.completed",
    }


def _delivery_judge_manual() -> dict:
    """judge 判決書的 caller 親驗 delivery——判決書由後繼 job 寫 judge-s1-transcript.md，
    錨 JUDGE-VERDICT（本 worker session 以 rg 機驗命中 line 520/546）＝manual-anchor。"""
    return {
        "mode": "artifact",
        "sink": "/Users/ctai/Github/ai-guide/.agent-tmp/air-135.1/judge-s1-transcript.md",
        "l1_present": True,
        "l2_anchor": True,
        "anchor_hits": ["JUDGE-VERDICT"],
        "verdict": "manual-anchor",
    }


# ---------------------------------------------------------------------------
# 今晚四張真實回執的 envelope 組裝
# ---------------------------------------------------------------------------


def _env_codex() -> dict:
    return {
        "ledger": _codex_ledger(),
        "ledger_path": LEDGER_MAIN,
        "slice_ref": _slice_ref("s1-postbuild-codex"),
        "collection": _collection_codex(),
        "terminal": _terminal_codex(),
    }


def _env_muse() -> dict:
    return {
        "ledger": _muse_ledger(),
        "ledger_path": LEDGER_MAIN,
        "slice_ref": _slice_ref("s1-postbuild-muse"),
        "collection": _collection_muse(),
        "terminal": _terminal_muse(),
    }


def _env_judge() -> dict:
    return {
        "ledger": _glm_judge_ledger(),
        "ledger_path": LEDGER_MAIN,
        "slice_ref": _slice_ref("s1-judge-glm"),
        "terminal": _terminal_glm_judge(),
        "delivery": _delivery_judge_manual(),
        "blockers": [
            "前身 job-mufn9pd8-1zuq1i interrupted（carrierExit 143）——同範圍重派；"
            "authoritative evidence＝帳本狀態＋carrier exit（supervision fence）",
        ],
    }


def _env_s1_flash() -> dict:
    return {
        "ledger": _glm_s1_flash_ledger(),
        "ledger_path": LEDGER_WT,
        "slice_ref": _slice_ref("s1-implement-flash"),
        "collection": _collection_s1_flash(),
    }


def _real_envelopes() -> list[tuple[str, dict, str]]:
    return [
        ("glm", _env_s1_flash(), "job-muflra3f-dd7ea4"),
        ("codex", _env_codex(), "job-mufn1cui-x7lfwh"),
        ("muse", _env_muse(), "job-mufn1cw6-f4fmzx"),
        ("glm", _env_judge(), "job-mufna554-a7unmg"),
    ]


# ---------------------------------------------------------------------------
# fail-loud 契約
# ---------------------------------------------------------------------------


class TestFailLoudContract:
    def test_unknown_family_lists_available(self) -> None:
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("weixin", _env_codex())
        assert "Unknown family `weixin` for receipt_normalize" in str(ei.value)
        assert "Available families: local, muse, codex, glm" in str(ei.value)

    def test_local_family_not_mapped_v0(self) -> None:
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("local", _env_codex())
        assert "no receipt mapping in receipt_normalize v0" in str(ei.value)
        assert "muse, codex, glm" in str(ei.value)

    def test_missing_envelope_keys_list_required(self) -> None:
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", {"ledger": _codex_ledger()})
        msg = str(ei.value)
        assert "`ledger_path`" in msg and "`slice_ref`" in msg
        assert "Required envelope keys: ledger, ledger_path, slice_ref" in msg

    def test_unknown_envelope_key_fails_strict(self) -> None:
        env = _env_codex()
        env["colleciton"] = _collection_codex()  # typo——禁靜默丟棄
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "Unknown envelope key(s) colleciton" in str(ei.value)

    def test_missing_ledger_fields_list_all(self) -> None:
        env = _env_codex()
        del env["ledger"]["id"]
        del env["ledger"]["summary"]
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        msg = str(ei.value)
        assert "Missing ledger field(s) id, summary" in msg
        assert "Required ledger fields: id, status, family, model, timestamp, summary" in msg

    def test_family_conflict_fails(self) -> None:
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("muse", _env_codex())  # ledger.family=codex
        assert "Conflicting family" in str(ei.value)
        assert "雙 authoritative family" in str(ei.value)

    def test_collection_delivery_dual_authority_fails(self) -> None:
        env = _env_codex()
        env["delivery"] = _delivery_judge_manual()
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "Conflicting authoritative delivery" in str(ei.value)

    def test_job_id_conflict_fails(self) -> None:
        env = _env_codex()
        env["collection"] = _collection_muse()  # jobId 屬 muse job
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "Conflicting job id" in str(ei.value)

    def test_delivery_non_dict_fails_not_silent(self) -> None:
        env = _env_judge()
        env["delivery"] = "delivered"  # 型別錯——禁靜默落 receipt-only fallback
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", env)
        assert "`delivery` must be an object" in str(ei.value)


class TestStatusMapping:
    def _minimal_ledger(self, status: str, **extra: object) -> dict:
        base = {
            "id": "job-x",
            "status": status,
            "family": "glm",
            "model": "GLM-5.3",
            "timestamp": "2026-09-24T00:00:00Z",
            "summary": "s",
        }
        base.update(extra)
        return base

    def _base_env(self, ledger: dict) -> dict:
        return {
            "ledger": ledger,
            "ledger_path": LEDGER_MAIN,
            "slice_ref": _slice_ref("s1-x"),
        }

    def test_completed_maps(self) -> None:
        out = _mod.normalize("glm", self._base_env(self._minimal_ledger("completed")))
        assert out["status"] == "completed"

    def test_interrupted_maps_to_failed_with_blocker_note(self) -> None:
        env = self._base_env(
            self._minimal_ledger("interrupted", carrierExit=143)
        )
        out = _mod.normalize("glm", env)
        assert out["status"] == "failed"
        assert any("interrupted" in b and "carrierExit=143" in b for b in out["blockers"])

    def test_running_rejected_non_terminal(self) -> None:
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", self._base_env(self._minimal_ledger("running")))
        msg = str(ei.value)
        assert "Non-terminal ledger status `running`" in msg
        assert "Mappable ledger statuses: completed, interrupted" in msg

    def test_failed_or_capped_rejected_without_override(self) -> None:
        """今晚實證：job-muflp5n2-8604w2（glm prepare 階段 provisioning 失敗）——歧義禁靜默映射。"""
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", self._base_env(self._minimal_ledger("failed-or-capped")))
        msg = str(ei.value)
        assert "Ambiguous ledger status `failed-or-capped`" in msg
        assert "status_override" in msg

    def test_override_failed_accepted(self) -> None:
        env = self._base_env(self._minimal_ledger("failed-or-capped"))
        env["status_override"] = "failed"
        out = _mod.normalize("glm", env)
        assert out["status"] == "failed"

    def test_override_unknown_terminal_lists_available(self) -> None:
        env = self._base_env(self._minimal_ledger("failed-or-capped"))
        env["status_override"] = "done"
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", env)
        assert "Unknown status_override `done`" in str(ei.value)
        assert "budget-limited" in str(ei.value)

    def test_override_on_unambiguous_status_conflicts(self) -> None:
        env = self._base_env(self._minimal_ledger("completed"))
        env["status_override"] = "failed"
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", env)
        assert "Conflicting status authority" in str(ei.value)


class TestSliceRef:
    def test_missing_subkeys_list_all(self) -> None:
        env = _env_codex()
        env["slice_ref"] = {"slice_id": "x"}
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        msg = str(ei.value)
        assert "Missing slice_ref key(s)" in msg
        for key in ("card_id", "unit_id", "plan_version", "plan_hash"):
            assert key in msg

    def test_bad_plan_hash_fails(self) -> None:
        env = _env_codex()
        env["slice_ref"]["plan_hash"] = "abc123"
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "需 hex 64 位" in str(ei.value)

    def test_plan_version_zero_fails(self) -> None:
        env = _env_codex()
        env["slice_ref"]["plan_version"] = 0
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "需正整數" in str(ei.value)

    def test_blank_slice_ref_value_fails(self) -> None:
        """muse NB-3 回歸釘：空白 slice_ref 值＝碼面有閘、測試面補釘。"""
        env = _env_codex()
        env["slice_ref"]["slice_id"] = "   "
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "Blank slice_ref key(s)" in str(ei.value)
        assert "slice_id" in str(ei.value)


class TestPassThroughTypeGate:
    """muse NB-1 回歸釘：pass-through 欄非 list 即 fail-loud（禁字元沙拉）。"""

    def test_blockers_string_input_fails(self) -> None:
        env = _env_judge()
        env["blockers"] = "oops-string"
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", env)
        assert "`blockers` must be a list" in str(ei.value)
        assert "str" in str(ei.value)

    def test_top_findings_dict_input_fails(self) -> None:
        env = _env_codex()
        env["top_findings"] = {"a": 1}
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "`top_findings` must be a list" in str(ei.value)


class TestGlmUsageUnmappedKeys:
    """muse NB-2 回歸釘：glm usage 未映射鍵原樣保留＋unverified 註記（禁靜默丟棄）。"""

    def test_unmapped_key_preserved_and_annotated(self) -> None:
        env = _env_judge()
        env["ledger"]["resultUsage"]["cacheWriteTokens"] = 5000
        out = _mod.normalize("glm", env)
        assert out["usage"]["cacheWriteTokens"] == 5000
        assert any(
            "cacheWriteTokens" in u and "未映射鍵原樣保留" in u for u in out["unverified"]
        )


# ---------------------------------------------------------------------------
# 三家族真實案例——canonical 語義
# ---------------------------------------------------------------------------


class TestRealReceiptsCanonical:
    def test_glm_s1_flash_real(self) -> None:
        out = _mod.normalize("glm", _env_s1_flash())
        assert out["schema"] == "slice-receipt/1"
        assert out["job_id"] == "job-muflra3f-dd7ea4"
        assert out["family"] == "glm"
        assert out["status"] == "completed"
        assert out["model"] == "GLM-5.3-Flash"
        assert out["slice_id"] == "s1-implement-flash"
        assert out["delivery"]["verdict"] == "delivered"
        assert out["delivery"]["anchor_hits"] == ["S1-DONE-WHEN"]
        assert out["bounded_receipt_projection"]["final_text_non_empty"] is True
        # waiter camelCase → canonical snake
        assert "finalTextNonEmpty" not in out["bounded_receipt_projection"]
        assert out["usage"]["input_tokens"] == 7330192
        assert out["usage"]["output_tokens"] == 76398
        assert out["usage"]["model_request_count"] == 56
        # 無 terminal——final_text 判定源必須自我申報為帳本摘要
        assert "final_text_excerpt" not in out
        assert any("帳本 summary" in u for u in out["unverified"])

    def test_glm_judge_real_manual_anchor(self) -> None:
        out = _mod.normalize("glm", _env_judge())
        assert out["job_id"] == "job-mufna554-a7unmg"
        assert out["status"] == "completed"
        assert out["delivery"]["verdict"] == "manual-anchor"
        assert out["delivery"]["anchor_hits"] == ["JUDGE-VERDICT"]
        assert "GO" in out["final_text_excerpt"]
        assert out["usage"]["input_tokens"] == 891076
        assert out["usage"]["output_tokens"] == 20059
        assert out["usage"]["total_tokens"] == 911135
        # stop 前身 pass-through（supervision fence 證詞）
        assert any("job-mufn9pd8-1zuq1i" in b for b in out["blockers"])

    def test_codex_real(self) -> None:
        out = _mod.normalize("codex", _env_codex())
        assert out["job_id"] == "job-mufn1cui-x7lfwh"
        assert out["model"] == "chatgpt-web/high"
        assert out["usage"]["input_tokens"] == 296428
        assert out["usage"]["output_tokens"] == 1358
        assert out["delivery"]["sink"].endswith("postbuild-codex.md")
        assert out["delivery"]["verdict"] == "delivered"
        assert "POSTBUILD-VERDICT" in out["final_text_excerpt"]
        assert out["ledger"]["jsonl"].endswith("job-mufn1cui-x7lfwh.jsonl")

    def test_muse_real_no_usage_face(self) -> None:
        out = _mod.normalize("muse", _env_muse())
        assert out["job_id"] == "job-mufn1cw6-f4fmzx"
        assert out["model"] == "muse-spark-1.3"
        assert "usage" not in out  # 缺席非 0
        assert any("muse 帳本無 usage 欄" in u for u in out["unverified"])
        assert out["delivery"]["verdict"] == "delivered"
        assert out["bounded_receipt_projection"]["final_text_non_empty"] is True
        assert "52/52 tests green" in out["final_text_excerpt"]

    def test_unverified_plan_hash_disclaimer_always_present(self) -> None:
        for family, env, _ in _real_envelopes():
            out = _mod.normalize(family, env)
            assert any("plan_hash 回指面由 caller 提供" in u for u in out["unverified"])


# ---------------------------------------------------------------------------
# 家族終端記錄形（三家族三形）
# ---------------------------------------------------------------------------


class TestTerminalShapes:
    def test_codex_malformed(self) -> None:
        env = _env_codex()
        env["terminal"] = {"type": "turn.completed"}
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("codex", env)
        assert "Malformed codex terminal record" in str(ei.value)
        assert "agent_message" in str(ei.value)

    def test_muse_malformed(self) -> None:
        env = _env_muse()
        env["terminal"] = {"payload_type": "run.output.delta"}
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("muse", env)
        assert "Malformed muse terminal record" in str(ei.value)
        assert "run.terminal.completed" in str(ei.value)

    def test_muse_unknown_terminal_value(self) -> None:
        env = _env_muse()
        env["terminal"] = {
            "payload_type": "run.terminal.completed",
            "payload": {"terminal": "cancelled", "text": "x"},
        }
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("muse", env)
        assert "Unknown muse terminal value `cancelled`" in str(ei.value)
        assert "Known muse terminal values: completed" in str(ei.value)

    def test_glm_malformed(self) -> None:
        env = _env_judge()
        env["terminal"] = {"type": "session.updated", "payload": {}}
        with pytest.raises(_mod.NormalizeError) as ei:
            _mod.normalize("glm", env)
        assert "Malformed glm terminal record" in str(ei.value)
        assert "payload.response" in str(ei.value)

    def test_excerpt_truncated_beyond_cap(self) -> None:
        out = _mod.normalize("muse", _env_muse())
        assert out["final_text_excerpt"].endswith("…（截斷 280 字元，全文見 jsonl）") or len(
            out["final_text_excerpt"]
        ) <= 280 + 30


# ---------------------------------------------------------------------------
# validator gate（DONE-WHEN #3 的測試側：正規化產物過 S1 validator）
# ---------------------------------------------------------------------------


class TestValidatorGate:
    @pytest.mark.parametrize(
        "family_env_job", _real_envelopes(), ids=[j for _, _, j in _real_envelopes()]
    )
    def test_real_receipts_pass_arc_spec_validator(
        self, family_env_job: tuple[str, dict, str]
    ) -> None:
        family, env, job_id = family_env_job
        out = _mod.normalize(family, env)
        assert out["job_id"] == job_id
        assert _mod.validate_normalized(out) == []

    def test_completed_without_verified_delivery_fails_gate(self) -> None:
        """terminal≠complete：兩收線面皆缺時 verdict=not-assessed，completed 必被 S1 validator 擋——設計行為。"""
        env = {
            "ledger": _glm_s1_flash_ledger(),
            "ledger_path": LEDGER_WT,
            "slice_ref": _slice_ref("s1-implement-flash"),
        }
        out = _mod.normalize("glm", env)
        assert out["delivery"]["verdict"] == "not-assessed"
        assert _mod.validate_normalized(out) != []


# ---------------------------------------------------------------------------
# 合成視圖
# ---------------------------------------------------------------------------


class TestMergedView:
    def test_view_covers_all_four_real_receipts(self) -> None:
        receipts = [
            _mod.normalize(family, env) for family, env, _ in _real_envelopes()
        ]
        view = _mod.render_merged_view(
            receipts,
            title="AIR-135.1 S1 夜間批量——四回執合成視圖（v0）",
            note="由 receipt_normalize 產出；帳本指針可逐筆回查。",
        )
        for _, _, job_id in _real_envelopes():
            assert job_id in view
        for token in (
            "總表",
            "誰",
            "做了什麼",
            "交付了什麼",
            "狀態",
            "帳本指針",
            "POSTBUILD-VERDICT",
            "JUDGE-VERDICT",
            "S1-DONE-WHEN",
            "manual-anchor",
            "delivered",
        ):
            assert token in view, token

    def test_view_is_markdown_table_plus_details(self) -> None:
        receipts = [_mod.normalize(f, e) for f, e, _ in _real_envelopes()]
        view = _mod.render_merged_view(receipts, title="t")
        assert view.startswith("# t\n")
        assert "| # | job |" in view
