"""AIR-135.7 W3——w3_checkpoint_link 契約測試（compiler 產出面 → W2 台帳）.

釘住 AC#4 接線面：dispatch artifact 機器欄抽取（欄位機驗單一源＝arc_spec.validate）、
checkpoint 契約投影（sink＋accept）、JIT dispatch_id 佔位 fail-loud、W2 台帳六欄
登記＋anchor/anchors/checkpoint_contract 溯源。路徑隔離：fixture 全落 pytest
tmp_path；真實上游 artifact（mini-batch dispatch-W1.md）對接歸 seal smoke（唯讀），
測試不跨 WT 依賴。
"""

import json
from pathlib import Path

import pytest
from conftest import load_module

_w3 = load_module("scripts/w3_checkpoint_link.py")
_led = load_module("scripts/dispatch_ledger.py")

AT_ISO = "2026-09-25T03:00:00+00:00"


# ---------- fixture helpers（形錨真實 mini-batch dispatch-W1.md 機器欄） ----------


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


# ---------- is_jit_dispatch_id（JIT 佔位判準） ----------


def test_is_jit_dispatch_id_markers() -> None:
    assert _w3.is_jit_dispatch_id("JIT-AT-DISPATCH")
    assert _w3.is_jit_dispatch_id("UNRESOLVABLE_FROM_CARD——卡面未載")
    assert _w3.is_jit_dispatch_id("   ")
    assert not _w3.is_jit_dispatch_id("job-mu7px22a-b1ccwa")
    assert not _w3.is_jit_dispatch_id("sess_abc123")


# ---------- extract（唯讀抽取＋validator 單一源） ----------


def test_extract_projects_checkpoint_contract(tmp_path: Path) -> None:
    contract = _w3.extract_checkpoint(_artifact(tmp_path))
    assert contract["schema"] == "dispatch-slice/1"
    assert contract["dispatch_id"] == "JIT-AT-DISPATCH"
    assert contract["dispatch_id_jit"] is True
    assert contract["carrier"] == "zcode-agent"
    assert contract["declared_collection_mode"] == "bounded-receipt"
    assert contract["declared_ledger"] == "zcode-agent-registry"
    assert contract["sink"] == {"mode": "artifact", "path": "artifact-out.md"}
    assert contract["accept"] == {"predicate": "exists+readable+nonempty", "anchors": ["ANCHOR-ONE", "ANCHOR-TWO"]}
    assert contract["slice"]["slice_id"] == "AIR-T#W1-slice"
    assert contract["slice"]["unit_id"] == "AIR-T#W1"
    assert contract["slice"]["plan_version"] == 1
    assert contract["slice"]["plan_hash"] == "a" * 64


def test_extract_real_dispatch_id_not_jit(tmp_path: Path) -> None:
    contract = _w3.extract_checkpoint(_artifact(tmp_path, dispatch_id="job-aaa-111111"))
    assert contract["dispatch_id_jit"] is False


def test_extract_receipt_only_optional_accept(tmp_path: Path) -> None:
    contract = _w3.extract_checkpoint(_artifact(tmp_path, sink={"mode": "receipt-only"}, accept=None))
    assert contract["sink"] == {"mode": "receipt-only", "path": ""}
    assert contract["accept"] == {"predicate": "", "anchors": []}


def test_extract_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _w3.main(["extract", "--artifact", str(_artifact(tmp_path)), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["slice"]["unit_id"] == "AIR-T#W1"
    assert payload["accept"]["anchors"] == ["ANCHOR-ONE", "ANCHOR-TWO"]


def test_extract_missing_file_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _w3.main(["extract", "--artifact", str(tmp_path / "absent.md")]) == 2
    assert "無法讀取" in capsys.readouterr().err


def test_extract_no_json_block_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "plain.md"
    path.write_text("# 只有散文，無 fenced block\n", encoding="utf-8")
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "fenced block" in capsys.readouterr().err


def test_extract_corrupt_json_block_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _write_artifact(tmp_path, "{ not json")
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "無法解析" in capsys.readouterr().err


def test_extract_non_object_block_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _write_artifact(tmp_path, "[1, 2]")
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "非 JSON object" in capsys.readouterr().err


def test_extract_wrong_schema_lists_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _write_artifact(tmp_path, json.dumps({"schema": "arc-plan/1"}))
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    err = capsys.readouterr().err
    assert "dispatch-slice/1" in err  # 可用值
    assert "arc-plan/1" in err  # 實際找到


def test_extract_multiple_slices_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    other = json.dumps(_slice_data(slice_id="AIR-T#W2-slice", unit_id="AIR-T#W2"), ensure_ascii=False)
    path = _write_artifact(tmp_path, json.dumps(_slice_data(), ensure_ascii=False), other)
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "多個 dispatch-slice" in capsys.readouterr().err


def test_extract_validator_failure_surfaces_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # artifact 模式拔 accept——欄位機驗單一源 arc_spec 應逐條報錯，本工具不重刻
    path = _artifact(tmp_path, accept=None)
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "validator 未過" in capsys.readouterr().err


def test_extract_artifact_mode_empty_accept_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # validator 對 accept 內鍵「有鍵才驗」——accept={} 過欄位驗證；映射面須擋空 predicate
    path = _artifact(tmp_path, accept={})
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "accept.predicate 空" in capsys.readouterr().err


def test_extract_artifact_mode_missing_anchors_fails_loud(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _artifact(tmp_path, accept={"predicate": "exists+readable+nonempty"})
    assert _w3.main(["extract", "--artifact", str(path)]) == 2
    assert "accept.anchors 空" in capsys.readouterr().err


# ---------- register（餵 W2 台帳） ----------


def _register(tmp_path: Path, artifact: Path, *extra: str) -> int:
    return _w3.main(
        [
            "register",
            "--artifact",
            str(artifact),
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--at",
            AT_ISO,
            *extra,
        ]
    )


def test_register_jit_without_id_fails_and_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ledger = tmp_path / "ledger.json"
    assert _register(tmp_path, _artifact(tmp_path)) == 2
    assert "--dispatch-id" in capsys.readouterr().err
    assert not ledger.exists()  # 佔位串禁寫進台帳


def test_register_jit_with_placeholder_override_also_fails(tmp_path: Path) -> None:
    assert _register(tmp_path, _artifact(tmp_path), "--dispatch-id", "UNRESOLVABLE_FROM_CARD x") == 2
    assert not (tmp_path / "ledger.json").exists()


def test_register_jit_with_explicit_id_writes_full_entry(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    assert _register(tmp_path, _artifact(tmp_path), "--dispatch-id", "sess-w3x-0001") == 0
    entry = json.loads(ledger.read_text(encoding="utf-8"))["expectations"]["sess-w3x-0001"]
    # liveness 六欄（AC#3）
    assert entry["dispatch_id"] == "sess-w3x-0001"
    assert entry["carrier"] == "zcode-agent"
    assert entry["dispatched_at"] == AT_ISO
    assert entry["sink"] == "artifact-out.md"
    assert entry["collection_mode"] == "detached"
    assert entry["collector_owner"] == "marshal"
    assert entry["liveness_source"] == "zcode-agent-registry"
    # checkpoint predicate：單錨供 W2 三步機驗、全錨點供 collector
    assert entry["anchor"] == "ANCHOR-ONE"
    assert entry["anchors"] == ["ANCHOR-ONE", "ANCHOR-TWO"]
    # compiler 產出面溯源塊（AC#4 接線可審計）
    cc = entry["checkpoint_contract"]
    assert cc["source_artifact"].endswith("dispatch-W1.md")
    assert cc["compiled_schema"] == "dispatch-slice/1"
    assert cc["slice_id"] == "AIR-T#W1-slice"
    assert cc["unit_id"] == "AIR-T#W1"
    assert cc["plan_version"] == 1
    assert cc["plan_hash"] == "a" * 64
    assert cc["accept_predicate"] == "exists+readable+nonempty"
    assert cc["declared_collection_mode"] == "bounded-receipt"


def test_register_real_id_needs_no_flag(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    assert _register(tmp_path, _artifact(tmp_path, dispatch_id="job-aaa-111111")) == 0
    doc = json.loads(ledger.read_text(encoding="utf-8"))
    assert "job-aaa-111111" in doc["expectations"]


def test_resolve_liveness_source_fallback_chain(tmp_path: Path) -> None:
    contract = _w3.extract_checkpoint(_artifact(tmp_path))
    # slice ledger 欄逐字優先 → 明示覆寫最高
    assert _w3.resolve_liveness_source(None, contract) == "zcode-agent-registry"
    assert _w3.resolve_liveness_source("bridge:jobs.json", contract) == "bridge:jobs.json"
    # validator 放寬 ledger 欄時的防線（台帳六欄不可空）
    assert _w3.resolve_liveness_source(None, {**contract, "declared_ledger": ""}) == "bridge:jobs.json"


def test_register_receipt_only_entry(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    artifact = _artifact(tmp_path, sink={"mode": "receipt-only"}, accept=None)
    assert _register(tmp_path, artifact, "--dispatch-id", "sess-w3x-0003") == 0
    entry = json.loads(ledger.read_text(encoding="utf-8"))["expectations"]["sess-w3x-0003"]
    assert entry["sink"] == "receipt-only"
    assert "anchor" not in entry  # receipt-only 不設單錨（驗收歸 collector）
    assert "anchors" not in entry
    assert entry["checkpoint_contract"]["unit_id"] == "AIR-T#W1"


def test_register_upserts_same_id(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    assert _register(tmp_path, artifact, "--dispatch-id", "sess-w3x-0004") == 0
    assert _register(tmp_path, artifact, "--dispatch-id", "sess-w3x-0004", "--collector-owner", "reviewer") == 0
    doc = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert len(doc["expectations"]) == 1
    assert doc["expectations"]["sess-w3x-0004"]["collector_owner"] == "reviewer"


def test_register_corrupt_ledger_fails_no_repair(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text("{ not json", encoding="utf-8")
    before = ledger.read_bytes()
    assert _register(tmp_path, _artifact(tmp_path), "--dispatch-id", "sess-w3x-0005") == 2
    assert ledger.read_bytes() == before


def test_register_bad_collection_mode_is_argparse_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _w3.main(
            [
                "register",
                "--artifact",
                str(_artifact(tmp_path)),
                "--dispatch-id",
                "sess-w3x-0006",
                "--collection-mode",
                "bogus",
            ]
        )
    assert excinfo.value.code == 2


def test_register_bad_at_fails_loud(tmp_path: Path) -> None:
    assert _register(tmp_path, _artifact(tmp_path), "--dispatch-id", "sess-w3x-0007", "--at", "not-a-date") == 2


def test_register_missing_artifact_fails_loud(tmp_path: Path) -> None:
    assert _register(tmp_path, tmp_path / "absent.md", "--dispatch-id", "sess-w3x-0008") == 2
    assert not (tmp_path / "ledger.json").exists()


# ---------- 接縫驗證：登記的 anchor 真的驅動 W2 sink 三步機驗 ----------


def test_registered_anchor_drives_w2_sink_verdict(tmp_path: Path) -> None:
    contract = _w3.extract_checkpoint(_artifact(tmp_path))
    entry = _w3.build_entry(contract, "sess-w3x-0009", "detached", "marshal", "zcode-agent-registry", AT_ISO)
    row = _led.ActualRow("sess-w3x-0009", tmp_path, "completed")
    sink = tmp_path / "artifact-out.md"
    sink.write_text("增量落盤內容……ANCHOR-ONE 命中\n", encoding="utf-8")
    status, note = _led.status_of(entry, row, "", tmp_path)
    assert status == "matched" and "三步過" in note
    sink.write_text("非空但無錨點\n", encoding="utf-8")
    status, note = _led.status_of(entry, row, "", tmp_path)
    assert status == "sink-missing" and "錨點" in note  # terminal≠complete


def test_receipt_only_entry_matches_on_row_presence(tmp_path: Path) -> None:
    contract = _w3.extract_checkpoint(_artifact(tmp_path, sink={"mode": "receipt-only"}, accept=None))
    entry = _w3.build_entry(contract, "sess-w3x-0010", "detached", "marshal", "zcode-agent-registry", AT_ISO)
    row = _led.ActualRow("sess-w3x-0010", tmp_path, "completed")
    status, note = _led.status_of(entry, row, "", tmp_path)
    assert status == "matched" and "collector" in note
