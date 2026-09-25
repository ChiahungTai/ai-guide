"""AIR-135.7 W4——checkpoint_obligation 契約測試（AC#5 Context Continuity 對接）.

釘住 AC#5 面：十欄投影無重抄（語義欄斷言＝卡指針非內容；枚舉外欄位禁加——
exact key-set gate）、budget 四件齊＋bounded receipt 六欄投影（單一源
dispatch_ledger，禁二刻）、semantic boundary 枚舉分類、transient/durable 分離
（packet 產出面零寫入副作用）、fail-loud 樣本。路徑隔離：fixture 全落 pytest
tmp_path；真實上游 dispatch artifact 對接歸 seal smoke（唯讀），測試不跨 WT 依賴。
"""

import json
from pathlib import Path

import pytest
from conftest import load_module

_cob = load_module("scripts/checkpoint_obligation.py")
_w3 = load_module("scripts/w3_checkpoint_link.py")

OBLIGATION_KEYS = {
    "schema",
    "goal_pointer",
    "current_stage",
    "tree_pointer",
    "delivery_and_collection",
    "next_action",
    "next_read_set",
    "durable_checkpoint",
}
BUDGET_KEYS = {
    "schema",
    "artifact_pointer",
    "bounded_receipt_fields",
    "collector_state_pointer",
    "next_read_set",
    "max_reinject_bytes",
    "reinjection_rule",
}


# ---------- fixture helpers（slice 形錨 test_w3_checkpoint_link.py——同一 arc_spec 面源） ----------


def _slice_data(**over: object) -> dict:
    data: dict = {
        "schema": "dispatch-slice/1",
        "slice_id": "AIR-T#W1-slice",
        "card_id": "AIR-T",
        "card_baseline": "abc1234",
        "plan_version": 1,
        "plan_hash": "a" * 64,
        "unit_id": "AIR-T#W1",
        "role": "implement",
        "authority": "writer",
        "capability_mode": "ReadWrite",
        "owning_wt": {"path": "/wt/ai-guide-air-t", "branch": "air-t"},
        "read_set": {"policy": "full-context", "pointers": ["backlog/tasks/x.md"]},
        "sink": {"mode": "artifact", "path": "artifact-out.md"},
        "accept": {"predicate": "exists+readable+nonempty", "anchors": ["ANCHOR-ONE", "ANCHOR-TWO"]},
        "budget_context": {"revert_remaining": 3, "slice_budget": "unlimited", "debit_events": []},
        "terminal_semantics": {
            "on_budget_exhausted": "budget-limited",
            "raise_cap": "human-action",
            "settle_gate": "human",
        },
        "carrier": "zcode-agent",
        "collection_mode": "bounded-receipt",
        "dispatch_id": "JIT-AT-DISPATCH",
        "family": "local",
        "model": "JIT-AT-DISPATCH",
        "binding": "model-routing resolver JIT",
        "ledger": "zcode-agent-registry",
        "commit_delegation": "conditional-this-repo",
    }
    data.update(over)
    return data


def _runtime_data(**over: object) -> dict:
    data: dict = {
        "dispatch_id": "job-w4x-0001",
        "sink_state": "unverified",
        "liveness_source": "bridge:jobs.json",
    }
    data.update(over)
    return data


def _write_artifact(tmp_path: Path, *blocks: str, stem: str = "dispatch-W1") -> Path:
    path = tmp_path / f"{stem}.md"
    machine = "\n".join(f"```json\n{block}\n```" for block in blocks)
    path.write_text(
        "# DispatchSlice——速讀節\n\n- sink：artifact-out.md\n\n## 機器欄\n\n" + machine + "\n",
        encoding="utf-8",
    )
    return path


def _artifact(tmp_path: Path, **over: object) -> Path:
    return _write_artifact(tmp_path, json.dumps(_slice_data(**over), ensure_ascii=False, indent=2))


def _write_runtime(tmp_path: Path, **over: object) -> Path:
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(_runtime_data(**over), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build(tmp_path: Path, artifact: Path | None = None, runtime: Path | None = None) -> int:
    return _cob.main(
        [
            "build",
            "--slice",
            str(artifact or _artifact(tmp_path)),
            "--runtime",
            str(runtime or _write_runtime(tmp_path)),
        ]
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


# ---------- is_semantic_boundary（AC#5 枚舉分類） ----------


def test_is_semantic_boundary_true_for_ac5_events() -> None:
    for transition in ("plan-recompile", "budget-exhausted", "window-crossing", "worker-terminal"):
        assert _cob.is_semantic_boundary(transition) is True


def test_is_semantic_boundary_false_otherwise() -> None:
    # 枚舉外 transition 恆非 boundary——分類謂詞禁為未知值發明語義
    for transition in ("dispatch-start", "mid-slice-progress", "heartbeat", "bogus-transition", ""):
        assert _cob.is_semantic_boundary(transition) is False


def test_boundary_enum_pinned_to_ac5() -> None:
    assert _cob.BOUNDARY_TRANSITIONS == (
        "plan-recompile",
        "budget-exhausted",
        "window-crossing",
        "worker-terminal",
    )


# ---------- build_obligation：十欄投影無重抄 ----------


def test_obligation_projects_mechanical_columns() -> None:
    obligation = _cob.build_obligation(_slice_data(), _runtime_data(sink_state="unverified"))
    assert obligation["schema"] == "checkpoint-obligation/1"
    # 十欄 1 目標指針（unit_id→卡；成功條件＝卡 AC 指針）
    assert obligation["goal_pointer"] == {
        "unit_id": "AIR-T#W1",
        "card_id": "AIR-T",
        "success_pointer": "card:AIR-T#AC",
    }
    # 十欄 2 現行階段（unit_id＋plan 回指）
    assert obligation["current_stage"] == {
        "slice_id": "AIR-T#W1-slice",
        "unit_id": "AIR-T#W1",
        "role": "implement",
        "plan_version": 1,
        "plan_hash": "a" * 64,
    }
    # 十欄 3 baseline/dirty 指針（owning_wt＋機械比對鍵；dirty 內容不產）
    assert obligation["tree_pointer"] == {
        "owning_wt": {"path": "/wt/ai-guide-air-t", "branch": "air-t"},
        "card_baseline": "abc1234",
    }
    # 十欄 7 sink/collector/收法
    dc = obligation["delivery_and_collection"]
    assert dc["sink"] == {"mode": "artifact", "path": "artifact-out.md"}
    assert dc["accept"] == {"predicate": "exists+readable+nonempty", "anchors": ["ANCHOR-ONE", "ANCHOR-TWO"]}
    assert dc["sink_state"] == "unverified"
    assert dc["dispatch"] == {
        "dispatch_id": "job-w4x-0001",
        "carrier": "zcode-agent",
        "collection_mode": "bounded-receipt",
        "liveness_source": "bridge:jobs.json",
    }
    assert "work-order §10" in dc["collection_form_pointer"]
    # 十欄 10 read-set
    assert obligation["next_read_set"] == {"policy": "full-context", "pointers": ["backlog/tasks/x.md"]}


def test_obligation_semantic_columns_are_pointers_not_content() -> None:
    obligation = _cob.build_obligation(_slice_data(), _runtime_data())
    payload = json.dumps(obligation, ensure_ascii=False)
    # 語義欄（arc_spec 機器欄也一樣）不投影進 packet——內容留在 durable owner
    for forbidden in (
        "intent_verbatim",
        "non_goals",
        "assumptions",
        "success_predicate",
        "commit_delegation",
        "prompt_material",
        "guidance",
    ):
        assert forbidden not in payload
    durable = obligation["durable_checkpoint"]
    assert durable["owner"] == "card-notes"
    assert durable["card_id"] == "AIR-T"
    assert durable["notes_anchor"] == "Implementation Notes"  # 卡 id＋note 錨
    assert "授權" in durable["rule"] and "禁重抄" in durable["rule"]


def test_obligation_exact_top_level_keys() -> None:
    # AC#5 枚舉外欄位禁加——exact key-set 是 anti-inflation gate
    obligation = _cob.build_obligation(_slice_data(), _runtime_data())
    assert set(obligation) == OBLIGATION_KEYS


def test_obligation_receipt_only_normalization() -> None:
    obligation = _cob.build_obligation(
        _slice_data(sink={"mode": "receipt-only"}, accept=None),
        _runtime_data(sink_state="verified"),
    )
    assert obligation["delivery_and_collection"]["sink"] == {"mode": "receipt-only", "path": ""}
    assert obligation["delivery_and_collection"]["accept"] == {"predicate": "", "anchors": []}


# ---------- next_action（sink_state 機械衍生，非自由敘述） ----------


@pytest.mark.parametrize(
    "state,fragment",
    [
        ("verified", "collect-and-proceed"),
        ("unverified", "machine-verify-sink"),
        ("missing", "terminal-sink-missing"),
    ],
)
def test_next_action_derivation(state: str, fragment: str) -> None:
    obligation = _cob.build_obligation(_slice_data(), _runtime_data(sink_state=state))
    assert fragment in obligation["next_action"]["action"]
    assert obligation["next_action"]["basis"] == f"runtime.sink_state={state}"


def test_next_action_missing_state_maps_to_no_redispatch() -> None:
    # terminal-sink-missing 語義錨 AC#4：縮 slice／改交付形態，禁原樣重派
    action = _cob.build_obligation(_slice_data(), _runtime_data(sink_state="missing"))["next_action"]["action"]
    assert "禁原樣重派" in action


# ---------- liveness source 解析鏈（單一源＝w3.resolve_liveness_source） ----------


def test_obligation_liveness_source_chain() -> None:
    # runtime 顯式最高
    obligation = _cob.build_obligation(_slice_data(), _runtime_data(liveness_source="custom:ledger"))
    assert obligation["delivery_and_collection"]["dispatch"]["liveness_source"] == "custom:ledger"
    # runtime 空值 → slice ledger 欄逐字
    obligation = _cob.build_obligation(_slice_data(), _runtime_data(liveness_source=""))
    assert obligation["delivery_and_collection"]["dispatch"]["liveness_source"] == "zcode-agent-registry"
    # 皆空 → bridge 預設
    obligation = _cob.build_obligation(_slice_data(ledger=""), _runtime_data(liveness_source=""))
    assert obligation["delivery_and_collection"]["dispatch"]["liveness_source"] == "bridge:jobs.json"


# ---------- runtime facts 契約（fail-loud） ----------


def test_obligation_rejects_jit_dispatch_id() -> None:
    with pytest.raises(_cob.CheckpointObligationError) as excinfo:
        _cob.build_obligation(_slice_data(), _runtime_data(dispatch_id="JIT-AT-DISPATCH"))
    assert "JIT 佔位" in str(excinfo.value)


def test_obligation_rejects_bad_sink_state() -> None:
    with pytest.raises(_cob.CheckpointObligationError) as excinfo:
        _cob.build_obligation(_slice_data(), _runtime_data(sink_state="done"))
    assert "Available sink states" in str(excinfo.value)


def test_obligation_rejects_unknown_runtime_key() -> None:
    with pytest.raises(_cob.CheckpointObligationError) as excinfo:
        _cob.build_obligation(_slice_data(), {**_runtime_data(), "extra": 1})
    assert "Recognized runtime keys" in str(excinfo.value)


def test_obligation_rejects_missing_runtime_key() -> None:
    data = _runtime_data()
    del data["sink_state"]
    with pytest.raises(_cob.CheckpointObligationError) as excinfo:
        _cob.build_obligation(_slice_data(), data)
    assert "Required runtime keys" in str(excinfo.value)


# ---------- build_delivery_budget：AC#5 括號枚舉四件＋上下界 ----------


def test_budget_four_items_and_exact_keys() -> None:
    budget = _cob.build_delivery_budget(_slice_data())
    assert set(budget) == BUDGET_KEYS
    # ① artifact pointer（slice sink 指針）
    assert budget["artifact_pointer"] == {"mode": "artifact", "path": "artifact-out.md"}
    # ② bounded receipt 欄位集
    assert "dispatch_ledger" in budget["bounded_receipt_fields"]["single_source"]
    # ③ collector state 指針（liveness source）
    assert budget["collector_state_pointer"] == "zcode-agent-registry"
    # ④ next read-set（role-dependent read-set 首讀面）
    assert budget["next_read_set"] == {"policy": "full-context", "pointers": ["backlog/tasks/x.md"]}
    # 上下界
    assert budget["max_reinject_bytes"] == 4096
    assert "只給指針" in budget["reinjection_rule"]


def test_budget_bounded_receipt_projection_real_id() -> None:
    budget = _cob.build_delivery_budget(_slice_data(dispatch_id="job-aaa-111111"))
    brf = budget["bounded_receipt_fields"]
    assert brf["declared"] == {
        "dispatch_id": "job-aaa-111111",
        "carrier": "zcode-agent",
        "sink": "artifact-out.md",
        "collection_mode": "bounded-receipt",
        "liveness_source": "zcode-agent-registry",
    }
    assert brf["jit_at_dispatch"] == ["dispatched_at", "collector_owner"]


def test_budget_bounded_receipt_projection_jit_id_moves_to_slot() -> None:
    budget = _cob.build_delivery_budget(_slice_data())  # fixture 預設 JIT 佔位
    brf = budget["bounded_receipt_fields"]
    assert "dispatch_id" not in brf["declared"]
    assert brf["jit_at_dispatch"] == ["dispatch_id", "dispatched_at", "collector_owner"]


def test_budget_receipt_only() -> None:
    budget = _cob.build_delivery_budget(_slice_data(sink={"mode": "receipt-only"}, accept=None))
    assert budget["artifact_pointer"] == {"mode": "receipt-only", "path": ""}
    assert budget["bounded_receipt_fields"]["declared"]["sink"] == "receipt-only"
    assert budget["collector_state_pointer"] == "zcode-agent-registry"


def test_budget_next_read_set_role_dependent() -> None:
    budget = _cob.build_delivery_budget(
        _slice_data(role="review", read_set={"policy": "problem-contract-only", "pointers": ["backlog/tasks/x.md"]})
    )
    assert budget["next_read_set"] == {"policy": "problem-contract-only", "pointers": ["backlog/tasks/x.md"]}
    # S1 顯式決策：pointers 缺席合法——投影為空列表、policy 留存
    budget = _cob.build_delivery_budget(_slice_data(read_set={"policy": "full-context"}))
    assert budget["next_read_set"] == {"policy": "full-context", "pointers": []}


def test_budget_collector_state_pointer_fallback() -> None:
    assert _cob.build_delivery_budget(_slice_data(ledger=""))["collector_state_pointer"] == "bridge:jobs.json"


# ---------- transient/durable 分離：packet 產出面零寫入副作用 ----------


def test_no_write_side_effects(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    runtime = _write_runtime(tmp_path, dispatch_id="job-w4x-0020")
    before = _snapshot(tmp_path)
    slice_data = _w3.parse_dispatch_slice(artifact.read_text(encoding="utf-8"), str(artifact))
    _cob.build_obligation(slice_data, _runtime_data(dispatch_id="job-w4x-0020"))
    _cob.build_delivery_budget(slice_data)
    assert _cob.main(["build", "--slice", str(artifact), "--runtime", str(runtime)]) == 0
    assert _snapshot(tmp_path) == before  # 檔案面逐位元組不變——禁寫卡禁寫檔機械證據


# ---------- CLI build（stdout packet；fail-loud exit 2） ----------


def test_cli_build_outputs_packet(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _build(tmp_path) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["obligation"]["schema"] == "checkpoint-obligation/1"
    assert payload["obligation"]["goal_pointer"]["unit_id"] == "AIR-T#W1"
    assert payload["obligation"]["next_action"]["basis"] == "runtime.sink_state=unverified"
    assert payload["delivery_budget"]["schema"] == "context-delivery-budget/1"
    assert payload["delivery_budget"]["max_reinject_bytes"] == 4096
    assert payload["delivery_budget"]["collector_state_pointer"] == "zcode-agent-registry"


def test_cli_missing_slice_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _cob.main(
        ["build", "--slice", str(tmp_path / "absent.md"), "--runtime", str(_write_runtime(tmp_path))]
    ) == 2
    assert "無法讀取" in capsys.readouterr().err


def test_cli_wrong_schema_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _write_artifact(tmp_path, json.dumps({"schema": "arc-plan/1"}))
    assert _cob.main(["build", "--slice", str(path), "--runtime", str(_write_runtime(tmp_path))]) == 2
    err = capsys.readouterr().err
    assert "dispatch-slice/1" in err  # 可用值
    assert "arc-plan/1" in err  # 實際找到


def test_cli_validator_failure_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # artifact 模式拔 accept——欄位機驗單一源 arc_spec 逐條報錯，本工具不重刻
    path = _artifact(tmp_path, accept=None)
    assert _cob.main(["build", "--slice", str(path), "--runtime", str(_write_runtime(tmp_path))]) == 2
    assert "validator 未過" in capsys.readouterr().err


def test_cli_missing_runtime_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _cob.main(
        ["build", "--slice", str(_artifact(tmp_path)), "--runtime", str(tmp_path / "absent.json")]
    ) == 2
    assert "無法讀取" in capsys.readouterr().err


def test_cli_bad_runtime_json_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "runtime.json"
    path.write_text("{ not json", encoding="utf-8")
    assert _cob.main(["build", "--slice", str(_artifact(tmp_path)), "--runtime", str(path)]) == 2
    assert "無法解析" in capsys.readouterr().err


def test_cli_runtime_non_object_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "runtime.json"
    path.write_text("[1, 2]", encoding="utf-8")
    assert _cob.main(["build", "--slice", str(_artifact(tmp_path)), "--runtime", str(path)]) == 2
    assert "JSON object" in capsys.readouterr().err


def test_cli_jit_dispatch_id_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    runtime = _write_runtime(tmp_path, dispatch_id="JIT-AT-DISPATCH")
    assert _build(tmp_path, runtime=runtime) == 2
    assert "JIT 佔位" in capsys.readouterr().err
