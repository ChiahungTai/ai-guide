"""handoff scbus 直送純邏輯契約測試（AIR-156）。

釘住的 invariant（card AIR-156 已決策勿重辯）：
- completion 四段：packet-produced→queued-visible→consumed/accepted→
  ownership-restored；receipt＝queued-visible 非完成（scbus proto 無 ack／
  user-read 第三態，transport receipt ≠ semantic ACK 禁互升格）。
- target 解析：已知 session 第一路＝scbus send；未知／歧義／self／ended／
  discovery-unavailable fail-closed 降 manual paste fallback；rows 形狀＝
  session_discovery seam 正規化 rows（`label` 鍵——AIR-254.1）。
- consumer contract（AIR-273）：discovery exit 3（source_unavailable／
  whoami_unavailable）＝源缺席 → FALLBACK_MANUAL（reason=
  discovery-unavailable）、直送第一路不可達——即使 rows 內容形式上
  match 也不得走 known-direct。
- consent gate：跨 ownership envelope 直送必帶 consent.evidence（AI 發起
  逐次授權的 AUTH 指針）；bus 凍結面 body ≤8192。
- 審計錨條款：完成宣稱須 receipt（command_id）＋ACK（correlation）同時對上。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/handoff_delivery.py")


def _receipt(
    message_id: str = "mid-1",
    command_id: str = "cid-1",
    stages: list[str] | None = None,
) -> dict:
    if stages is None:
        stages = ["accepted", "visible"]
    return {
        "schema_version": 1,
        "command_id": command_id,
        "message_id": message_id,
        "from": {"session_id": "sess-me"},
        "to": {"session_id": "sess-target", "name": None},
        "stages": [{"stage": s, "at_us": 1} for s in stages],
    }


def _ack(reply_type: str, in_reply_to: str = "mid-1", **extra: str) -> dict:
    ack = {"reply_type": reply_type, "in_reply_to": in_reply_to}
    ack.update(extra)
    return ack


def _row(
    sid: str = "sess-a",
    label: str | None = None,
    status: str = "active",
    workspace_root: str = "/Users/ctai/Github/ai-guide",
) -> dict:
    """seam `session_discovery list --json` 正規化 row 形狀（AIR-254.1）。"""
    return {
        "session_id": sid,
        "harness": "zcode",
        "workspace_root": workspace_root,
        "label": label,
        "liveness": "live",
        "status": status,
        "last_seen_iso": None,
        "age_min": None,
    }


# ---------------------------------------------------------------------------
# completion 四段分類
# ---------------------------------------------------------------------------


class TestClassifyCompletion:
    def test_no_receipt_is_packet_produced(self) -> None:
        trace = _mod.classify_completion(None, consumed=False, ack=None)
        assert trace.stage == _mod.CompletionStage.PACKET_PRODUCED
        assert trace.closed is False

    def test_receipt_without_consumed_is_queued_visible_not_done(self) -> None:
        """receipt＝queued-visible 非完成——禁以 transport receipt 冒充對方收到。"""
        trace = _mod.classify_completion(_receipt(), consumed=False, ack=None)
        assert trace.stage == _mod.CompletionStage.QUEUED_VISIBLE
        assert trace.closed is False
        assert trace.blocking is None

    def test_receipt_without_transport_is_packet_produced(self) -> None:
        trace = _mod.classify_completion(None, consumed=False, ack=None)
        assert trace.stage == _mod.CompletionStage.PACKET_PRODUCED

    def test_receipt_missing_visible_stage_fails_loud(self) -> None:
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(
                _receipt(stages=["accepted"]), consumed=False, ack=None
            )

    @pytest.mark.parametrize(
        "bad_stages", [None, "accepted", [None], [{"stage": "accepted"}, 5]]
    )
    def test_malformed_stages_shape_fails_as_contract_error(
        self, bad_stages: object
    ) -> None:
        """stages 非 list／元素非 dict／null——形狀違規歸 contract error，非 traceback。"""
        receipt = _receipt()
        receipt["stages"] = bad_stages
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(receipt, consumed=False, ack=None)

    def test_transport_without_receipt_fails_loud(self) -> None:
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(None, consumed=True, ack=None)

    def test_ack_without_consumed_fails_loud(self) -> None:
        """semantic ACK 以 consume 為前置（conventions 對照表）。"""
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(_receipt(), consumed=False, ack=_ack("accept"))

    def test_consumed_without_ack_stays_queued_visible_with_note(self) -> None:
        trace = _mod.classify_completion(_receipt(), consumed=True, ack=None)
        assert trace.stage == _mod.CompletionStage.QUEUED_VISIBLE
        assert trace.consumed is True
        assert trace.note is not None

    def test_consumed_plus_accept_reaches_consumed_accepted(self) -> None:
        trace = _mod.classify_completion(_receipt(), consumed=True, ack=_ack("accept"))
        assert trace.stage == _mod.CompletionStage.CONSUMED_ACCEPTED
        assert trace.closed is False

    def test_completed_reply_restores_ownership(self) -> None:
        ack = _ack("completed", result_pointer="notes://card", evidence="hash:abc")
        trace = _mod.classify_completion(_receipt(), consumed=True, ack=ack)
        assert trace.stage == _mod.CompletionStage.OWNERSHIP_RESTORED
        assert trace.closed is True

    def test_completed_without_evidence_fails_loud(self) -> None:
        """completed 必帶 result_pointer＋evidence——禁權威斷言。"""
        ack = _ack("completed", result_pointer="notes://card")
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(_receipt(), consumed=True, ack=ack)

    def test_ack_correlation_mismatch_fails_loud(self) -> None:
        """審計錨條款——ACK in_reply_to 必須對上 receipt message_id。"""
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(
                _receipt(), consumed=True, ack=_ack("accept", in_reply_to="mid-other")
            )

    @pytest.mark.parametrize("reply_type", ["declined", "needs-info"])
    def test_rejecting_replies_block_but_do_not_close(self, reply_type: str) -> None:
        trace = _mod.classify_completion(
            _receipt(), consumed=True, ack=_ack(reply_type)
        )
        assert trace.stage == _mod.CompletionStage.QUEUED_VISIBLE
        assert trace.blocking == reply_type
        assert trace.closed is False

    def test_unknown_reply_type_fails_loud(self) -> None:
        with pytest.raises(_mod.DeliveryContractError):
            _mod.classify_completion(_receipt(), consumed=True, ack=_ack("seen"))


# ---------------------------------------------------------------------------
# target 已知/未知分流
# ---------------------------------------------------------------------------


class TestResolveTarget:
    def test_session_id_match_same_workspace_is_known_direct(self) -> None:
        r = _mod.resolve_target(
            "sess-a",
            [_row()],
            own_session_id="sess-me",
            own_workspace_root="/Users/ctai/Github/ai-guide",
        )
        assert r.disposition == _mod.TargetDisposition.KNOWN_DIRECT
        assert r.session_id == "sess-a"
        assert r.cross_ownership is False

    def test_label_match_other_workspace_is_known_direct_cross_ownership(self) -> None:
        r = _mod.resolve_target(
            "southchariot-worker",
            [
                _row(
                    sid="sess-b",
                    label="southchariot-worker",
                    workspace_root="/Users/ctai/Github/southchariot",
                )
            ],
            own_session_id="sess-me",
            own_workspace_root="/Users/ctai/Github/ai-guide",
        )
        assert r.disposition == _mod.TargetDisposition.KNOWN_DIRECT
        assert r.cross_ownership is True

    def test_scbus_name_key_no_longer_matched(self) -> None:
        """rows 鍵＝seam `label`（AIR-254.1）——舊 `name` 鍵殘留不作匹配依據。"""
        rows = [_row(sid="sess-b", label=None)]
        rows[0]["name"] = "legacy-name"  # 非 seam 形狀的殘鍵
        r = _mod.resolve_target(
            "legacy-name", rows, own_session_id="s", own_workspace_root="/w"
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "no-match"

    def test_no_match_falls_back_to_manual(self) -> None:
        r = _mod.resolve_target(
            "ghost", [], own_session_id="s", own_workspace_root="/w"
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "no-match"

    def test_only_ended_match_falls_back(self) -> None:
        r = _mod.resolve_target(
            "sess-a",
            [_row(status="ended")],
            own_session_id="s",
            own_workspace_root="/w",
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "target-ended"

    def test_ambiguous_live_rows_fail_closed_to_fallback(self) -> None:
        rows = [_row(sid="sess-1", label="dup"), _row(sid="sess-2", label="dup")]
        r = _mod.resolve_target(
            "dup", rows, own_session_id="s", own_workspace_root="/w"
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "ambiguous"

    def test_self_target_falls_back(self) -> None:
        r = _mod.resolve_target(
            "sess-me",
            [_row(sid="sess-me")],
            own_session_id="sess-me",
            own_workspace_root="/w",
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "self"

    def test_unknown_ownership_is_treated_as_cross_fail_closed(self) -> None:
        r = _mod.resolve_target(
            "sess-a",
            [_row(workspace_root=None)],
            own_session_id="s",
            own_workspace_root="/w",
        )
        assert r.disposition == _mod.TargetDisposition.KNOWN_DIRECT
        assert r.cross_ownership is True

    def test_empty_target_fails_loud(self) -> None:
        with pytest.raises(_mod.DeliveryContractError):
            _mod.resolve_target(
                "", [_row()], own_session_id="s", own_workspace_root="/w"
            )

    def test_discovery_unavailable_falls_back_no_direct_send(self) -> None:
        """consumer contract（AIR-273）：discovery exit 3（source_unavailable
        ／whoami_unavailable typed envelope）＝源缺席 → FALLBACK_MANUAL
        （reason=discovery-unavailable）、非 known-direct——直送第一路
        不可達（resolve_target 純邏輯零 I/O：分流即送信判準）。"""
        r = _mod.resolve_target(
            "sess-a",
            [],  # rows 不可得——discovery 源缺席
            own_session_id="s",
            own_workspace_root="/w",
            discovery_unavailable=True,
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "discovery-unavailable"
        assert r.session_id is None
        assert r.label is None
        assert r.cross_ownership is False

    def test_discovery_unavailable_short_circuits_before_rows_match(self) -> None:
        """flag 語義＝源缺席時 rows 不可信——形式上 live match 也不得走
        known-direct（禁 direct send 的機械面）。"""
        r = _mod.resolve_target(
            "sess-a",
            [_row()],  # 形式上 match——但 discovery 已 unavailable
            own_session_id="sess-other",
            own_workspace_root="/w",
            discovery_unavailable=True,
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "discovery-unavailable"

    def test_empty_rows_without_flag_still_no_match(self) -> None:
        """既有契約不變：空 rows 無 flag（registry 空非源缺席）→ no-match。"""
        r = _mod.resolve_target(
            "ghost", [], own_session_id="s", own_workspace_root="/w"
        )
        assert r.disposition == _mod.TargetDisposition.FALLBACK_MANUAL
        assert r.reason == "no-match"


# ---------------------------------------------------------------------------
# delivery body 組裝（conventions.md 節一 v2 結構欄對齊）
# ---------------------------------------------------------------------------


class TestBuildDeliveryBody:
    def test_minimal_body_carries_structural_fields(self) -> None:
        body = _mod.build_delivery_body(
            summary="handoff packet 見 card notes",
            source="ai-guide/air-156",
            reply_address="ai-guide-marshal",
            correlation_id="corr-1",
            want="session 承接後回 accept",
            card_ref="ai-guide/air-156",
        )
        parsed = json.loads(body)
        assert parsed["want"] == "session 承接後回 accept"
        assert parsed["card_ref"] == "ai-guide/air-156"
        assert parsed["correlation_id"] == "corr-1"
        assert parsed["reply_address"] == "ai-guide-marshal"
        assert "\n" not in body

    def test_minimal_body_carries_class_header(self) -> None:
        """AIR-283：build-body 必帶 class machine-header（值 handoff）——接收端
        triage 依 class×action 表分診，body 缺 class 鍵＝分類前提不成立落
        unknown 桶（A5 實證：完成信 class:unknown＝發送端根本未發 class）。"""
        body = _mod.build_delivery_body(
            summary="s",
            source="ai-guide/air-283",
            reply_address="ai-guide-marshal",
            correlation_id="c",
            want="accept",
        )
        assert json.loads(body)["class"] == "handoff"

    def test_cross_ownership_without_consent_is_blocked(self) -> None:
        """consent gate——跨 ownership envelope 直送無 AUTH 指針＝攔。"""
        with pytest.raises(_mod.DeliveryContractError):
            _mod.build_delivery_body(
                summary="s",
                source="ai-guide/air-156",
                reply_address="ai-guide-marshal",
                correlation_id="c",
                want="accept",
                cross_ownership=True,
            )

    def test_cross_ownership_with_consent_evidence_passes_gate(self) -> None:
        body = _mod.build_delivery_body(
            summary="s",
            source="ai-guide/air-156",
            reply_address="ai-guide-marshal",
            correlation_id="c",
            want="accept",
            cross_ownership=True,
            consent_evidence="session transcript AUTH line 2026-09-22",
        )
        consent = json.loads(body)["consent"]
        assert consent["granted_by"] == "user"
        assert "AUTH line" in consent["evidence"]

    def test_body_over_bus_frozen_face_fails_loud(self) -> None:
        with pytest.raises(_mod.DeliveryContractError):
            _mod.build_delivery_body(
                summary="x" * 9000,
                source="s",
                reply_address="r",
                correlation_id="c",
                want="accept",
            )

    @pytest.mark.parametrize(
        "field", ["summary", "source", "reply_address", "correlation_id", "want"]
    )
    def test_missing_required_field_fails_loud(self, field: str) -> None:
        kwargs: dict = {
            "summary": "s",
            "source": "src",
            "reply_address": "ai-guide-marshal",
            "correlation_id": "c",
            "want": "accept",
        }
        kwargs[field] = ""
        with pytest.raises(_mod.DeliveryContractError):
            _mod.build_delivery_body(**kwargs)


# ---------------------------------------------------------------------------
# CLI 面（exit 契約：0＝ok、非零＝fail loud；2＝contract 錯）
# ---------------------------------------------------------------------------


def _run_cli(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(Path(_mod.__file__)), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


class TestCli:
    def test_build_body_cli_happy_path(self) -> None:
        r = _run_cli(
            "build-body",
            "--summary",
            "packet",
            "--source",
            "ai-guide/air-156",
            "--reply-address",
            "ai-guide-marshal",
            "--correlation-id",
            "c1",
            "--want",
            "accept",
            "--card-ref",
            "ai-guide/air-156",
        )
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["card_ref"] == "ai-guide/air-156"

    def test_build_body_cli_reply_address_lands_in_body(self) -> None:
        """judge 案①：--reply-address 值須原樣落 body JSON reply_address 鍵
        （in-band 回信管道——send 面無 from-address，收件方靠此鍵回信）。"""
        r = _run_cli(
            "build-body",
            "--summary",
            "packet",
            "--source",
            "ai-guide/air-156",
            "--reply-address",
            "ai-guide-marshal",
            "--correlation-id",
            "c1",
            "--want",
            "accept",
        )
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["reply_address"] == "ai-guide-marshal"

    def test_build_body_cli_class_lands_in_body(self) -> None:
        """AIR-283：CLI build-body 輸出須帶 class=handoff（machine header——
        接收端 default-deny 分診的第一分類鍵）。"""
        r = _run_cli(
            "build-body",
            "--summary",
            "packet",
            "--source",
            "ai-guide/air-283",
            "--reply-address",
            "ai-guide-marshal",
            "--correlation-id",
            "c1",
            "--want",
            "accept",
        )
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["class"] == "handoff"

    def test_build_body_cli_missing_reply_address_exit_2(self) -> None:
        """judge 案②：缺 --reply-address＝exit 2 fail loud（非靜默送出
        無回信門牌的信）。"""
        r = _run_cli(
            "build-body",
            "--summary",
            "packet",
            "--source",
            "ai-guide/air-156",
            "--correlation-id",
            "c1",
            "--want",
            "accept",
        )
        assert r.returncode == 2
        assert "reply-address" in r.stderr

    def test_build_body_cli_consent_gate_exit_2(self) -> None:
        r = _run_cli(
            "build-body",
            "--summary",
            "packet",
            "--source",
            "ai-guide/air-156",
            "--reply-address",
            "ai-guide-marshal",
            "--correlation-id",
            "c1",
            "--want",
            "accept",
            "--cross-ownership",
        )
        assert r.returncode == 2
        assert "consent" in r.stderr.lower()

    def test_classify_completion_cli(self, tmp_path: Path) -> None:
        receipt_path = tmp_path / "receipt.json"
        receipt_path.write_text(json.dumps(_receipt()))
        r = _run_cli("classify-completion", "--receipt-file", str(receipt_path))
        assert r.returncode == 0, r.stderr
        trace = json.loads(r.stdout)
        assert trace["stage"] == "queued-visible"
        assert trace["closed"] is False

    def test_resolve_target_cli(self, tmp_path: Path) -> None:
        rows_path = tmp_path / "rows.json"
        rows_path.write_text(json.dumps([_row(label="tagged")]))
        r = _run_cli(
            "resolve-target",
            "--target",
            "sess-a",
            "--rows-file",
            str(rows_path),
            "--own-session-id",
            "sess-me",
            "--own-workspace-root",
            "/Users/ctai/Github/ai-guide",
        )
        assert r.returncode == 0, r.stderr
        parsed = json.loads(r.stdout)
        assert parsed["disposition"] == "known-direct"
        assert parsed["label"] == "tagged"  # 輸出鍵隨 seam 形狀（name→label）

    def test_resolve_target_cli_accepts_session_discovery_list_json(
        self, tmp_path: Path
    ) -> None:
        """seam `list --json` 輸出（rows 物件）直接餵檔即用——文檔命令逐字可跑。"""
        rows_path = tmp_path / "rows.json"
        rows_path.write_text(
            json.dumps(
                {
                    "generated_at": "2026-10-05T00:00:00+00:00",
                    "rows": [_row()],
                    "count": 1,
                    "registry_total": 1,
                }
            )
        )
        r = _run_cli(
            "resolve-target",
            "--target",
            "sess-a",
            "--rows-file",
            str(rows_path),
            "--own-session-id",
            "sess-me",
            "--own-workspace-root",
            "/Users/ctai/Github/ai-guide",
        )
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["disposition"] == "known-direct"

    def test_resolve_target_cli_rejects_bad_rows_shape(self, tmp_path: Path) -> None:
        rows_path = tmp_path / "rows.json"
        rows_path.write_text(json.dumps({"unexpected": True}))
        r = _run_cli(
            "resolve-target",
            "--target",
            "sess-a",
            "--rows-file",
            str(rows_path),
            "--own-session-id",
            "sess-me",
            "--own-workspace-root",
            "/w",
        )
        assert r.returncode == 2

    def test_resolve_target_cli_discovery_unavailable(self) -> None:
        """consumer contract CLI 面（AIR-273）：--discovery-unavailable →
        fallback-manual（reason=discovery-unavailable）——無 rows-file 也
        可跑（源缺席場景的降級入口）。"""
        r = _run_cli(
            "resolve-target",
            "--target",
            "sess-a",
            "--discovery-unavailable",
            "--own-session-id",
            "sess-me",
            "--own-workspace-root",
            "/w",
        )
        assert r.returncode == 0, r.stderr
        parsed = json.loads(r.stdout)
        assert parsed["disposition"] == "fallback-manual"
        assert parsed["reason"] == "discovery-unavailable"

    def test_resolve_target_cli_without_rows_file_fails_loud(self) -> None:
        """--rows-file 缺席且無 --discovery-unavailable＝contract 錯（exit 2）——
        非靜默當空 registry。"""
        r = _run_cli(
            "resolve-target",
            "--target",
            "sess-a",
            "--own-session-id",
            "sess-me",
            "--own-workspace-root",
            "/w",
        )
        assert r.returncode == 2
        assert "rows-file" in r.stderr
