"""arc_manifest 契約測試（AIR-234 per-unit assigned-predicate manifest 投影器）。

釘住的 invariant（工單 §5.1 已決策勿重辯）：
- set 不變式三條為核心 oracle：units ac_ids 聯集 == contract ac_ids
  （少＝漏分派、多＝未知 ac_id）、units 兩兩不相交（重疊＝雙頭分派）、
  unit_id 無重複——違反任一逐行 stderr＋exit 2，永不靜默投影。
- contract_hash＝sha256(canonical_json(contract))——canonical 形同 arc_spec
  （sort_keys＋緊湊分隔符＋UTF-8）；hash 值以 dispatcher assigned manifest
  的實際值為獨立錨（非工具自證）。
- happy path：每 unit 一檔 `<unit_id「#」後綴>.json`，predicates 帶
  ac_id/kind/verifier/expected 四鍵且非空；輸出與固化 fixture byte-equal。
"""

import json
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

am = load_module("scripts/arc_manifest.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "air-234"
CONTRACT = FIXTURES / "contract.json"
UNITS = FIXTURES / "units.json"
EXPECTED_MANIFEST = FIXTURES / "manifests" / "impl-a.json"
# 獨立錨：dispatcher assigned manifest（.agent-tmp/air-234/manifests/impl-a.json）
# 的 contract_hash 實際值——canonical_json 形正確性的外部 oracle。
CONTRACT_HASH = "150a9879818a348cd3af2b3c8bab4eeaa3c620425b8102f9b0cf6ded81eb37c5"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _run(
    tmp_path: Path, contract: Path = CONTRACT, units: Path = UNITS
) -> tuple[int, Path]:
    out_dir = tmp_path / "out"
    rc = am.main([str(contract), "--units", str(units), "--out-dir", str(out_dir)])
    return rc, out_dir


# ---------------------------------------------------------------------------
# happy path：三 unit 各一檔、predicates 非空、hash 外部錨、fixture byte-equal
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_three_unit_files_written(self, tmp_path: Path) -> None:
        rc, out_dir = _run(tmp_path)
        assert rc == 0
        for name in ("impl-a.json", "impl-b.json", "settle.json"):
            m = _load(out_dir / name)
            assert m["schema"] == "arc-manifest/1"
            assert m["card_id"] == "AIR-234"
            assert len(m["predicates"]) > 0, f"{name} predicates 空"

    def test_impl_a_predicates_projection(self, tmp_path: Path) -> None:
        _, out_dir = _run(tmp_path)
        m = _load(out_dir / "impl-a.json")
        assert m["unit_id"] == "AIR-234#impl-a"
        assert [p["ac_id"] for p in m["predicates"]] == ["1", "2", "3"]
        for p in m["predicates"]:
            assert set(p) == {"ac_id", "kind", "verifier", "expected"}
            assert p["kind"] == "command_expected"
            assert p["verifier"]
            assert p["expected"]
        assert m["predicates"][0]["verifier"].startswith(
            "uv run python scripts/arc_manifest.py"
        )

    def test_contract_hash_matches_external_anchor(self, tmp_path: Path) -> None:
        """hash 錨點取自 dispatcher assigned manifest 實際值（非工具自證）。"""
        _, out_dir = _run(tmp_path)
        assert _load(out_dir / "impl-a.json")["contract_hash"] == CONTRACT_HASH

    def test_output_byte_equal_to_frozen_fixture(self, tmp_path: Path) -> None:
        rc, out_dir = _run(tmp_path)
        assert rc == 0
        generated = (out_dir / "impl-a.json").read_text(encoding="utf-8")
        frozen = EXPECTED_MANIFEST.read_text(encoding="utf-8")
        assert generated == frozen, "工具輸出與固化 fixture 不一致（drift）"

    def test_settle_unit_single_predicate(self, tmp_path: Path) -> None:
        _, out_dir = _run(tmp_path)
        m = _load(out_dir / "settle.json")
        assert m["unit_id"] == "AIR-234#settle"
        assert [p["ac_id"] for p in m["predicates"]] == ["7"]


# ---------------------------------------------------------------------------
# set 不變式三條（核心 oracle——違反逐行 stderr＋exit 2）
# ---------------------------------------------------------------------------


class TestSetInvariants:
    def _units_with(self, tmp_path: Path, units: list[dict]) -> Path:
        doc = {"schema": "arc-units/1", "card_id": "AIR-234", "units": units}
        return _write_json(tmp_path / "units.json", doc)

    def test_union_missing_ac_fails(self, tmp_path: Path) -> None:
        """聯集少於 contract ac_ids＝漏分派——exit 2 逐行指名缺的 ac_id。"""
        units = self._units_with(
            tmp_path,
            [
                {"unit_id": "AIR-234#impl-a", "ac_ids": ["1", "2", "3"]},
                {"unit_id": "AIR-234#impl-b", "ac_ids": ["4"]},
            ],
        )
        rc, _ = _run(tmp_path, units=units)
        assert rc == 2

    def test_union_extra_unknown_ac_fails(self, tmp_path: Path) -> None:
        """聯集多出 contract 外的 ac_id＝未知 ac_id——exit 2。"""
        units = self._units_with(
            tmp_path,
            [
                {"unit_id": "AIR-234#impl-a", "ac_ids": ["1", "2", "3", "99"]},
                {"unit_id": "AIR-234#impl-b", "ac_ids": ["4", "5", "6"]},
                {"unit_id": "AIR-234#settle", "ac_ids": ["7"]},
            ],
        )
        rc, _ = _run(tmp_path, units=units)
        assert rc == 2

    def test_overlap_fails(self, tmp_path: Path) -> None:
        """兩 unit 重疊同一 ac_id＝雙頭分派——exit 2。"""
        units = self._units_with(
            tmp_path,
            [
                {"unit_id": "AIR-234#impl-a", "ac_ids": ["1", "2", "3"]},
                {"unit_id": "AIR-234#impl-b", "ac_ids": ["3", "4", "5", "6"]},
                {"unit_id": "AIR-234#settle", "ac_ids": ["7"]},
            ],
        )
        rc, _ = _run(tmp_path, units=units)
        assert rc == 2

    def test_duplicate_unit_id_fails(self, tmp_path: Path) -> None:
        units = self._units_with(
            tmp_path,
            [
                {"unit_id": "AIR-234#impl-a", "ac_ids": ["1", "2"]},
                {"unit_id": "AIR-234#impl-a", "ac_ids": ["3"]},
                {"unit_id": "AIR-234#settle", "ac_ids": ["4", "5", "6", "7"]},
            ],
        )
        rc, _ = _run(tmp_path, units=units)
        assert rc == 2

    def test_invariant_errors_are_line_per_error_on_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """違反須逐行錯誤（非僅首報）——漏分派＋重疊同現時 stderr 多行。"""
        units = self._units_with(
            tmp_path,
            [
                {"unit_id": "AIR-234#impl-a", "ac_ids": ["1", "2"]},
                {"unit_id": "AIR-234#impl-b", "ac_ids": ["2"]},
            ],
        )
        rc = am.main(
            [str(CONTRACT), "--units", str(units), "--out-dir", str(tmp_path / "o")]
        )
        assert rc == 2
        err = capsys.readouterr().err
        assert len(err.strip().splitlines()) >= 2, "錯誤未逐行（静默合併）"
        assert "漏分派" in err
        assert "重疊" in err

    def test_judgment_required_ac_projection_fails_loud(
        self, tmp_path: Path
    ) -> None:
        """unit 分派到 judgment-required ac（無 predicate 可投影）——fail-loud
        禁產生 predicates 空的 manifest。"""
        contract = {
            "schema": "acceptance-contract/1",
            "card_id": "AIR-234",
            "source_card": "inline",
            "ac_ids": ["1"],
            "predicates": [],
            "judgment_required": [{"ac_id": "1", "reason": "no-explicit-verifier"}],
        }
        cpath = _write_json(tmp_path / "contract.json", contract)
        units = self._units_with(
            tmp_path, [{"unit_id": "AIR-234#u", "ac_ids": ["1"]}]
        )
        rc = am.main(
            [str(cpath), "--units", str(units), "--out-dir", str(tmp_path / "o")]
        )
        assert rc == 2


# ---------------------------------------------------------------------------
# 結構邊界：schema 值、card_id 一致、unit_id 檔名衍生
# ---------------------------------------------------------------------------


class TestStructuralBoundaries:
    def test_bad_contract_schema_fails(self, tmp_path: Path) -> None:
        contract = _load(CONTRACT)
        contract["schema"] = "acceptance-contract/9"
        rc, _ = _run(tmp_path, contract=_write_json(tmp_path / "c.json", contract))
        assert rc == 2

    def test_bad_units_schema_fails(self, tmp_path: Path) -> None:
        doc = _load(UNITS)
        doc["schema"] = "arc-units/9"
        rc, _ = _run(tmp_path, units=_write_json(tmp_path / "u.json", doc))
        assert rc == 2

    def test_card_id_mismatch_fails(self, tmp_path: Path) -> None:
        doc = _load(UNITS)
        doc["card_id"] = "AIR-OTHER"
        rc, _ = _run(tmp_path, units=_write_json(tmp_path / "u.json", doc))
        assert rc == 2

    def test_unit_id_without_hash_suffix_fails(self, tmp_path: Path) -> None:
        """無「#」後綴無法衍生檔名——fail-loud 禁靜默改用全名。"""
        doc = _load(UNITS)
        doc["units"] = [{"unit_id": "no-hash", "ac_ids": ["1", "2", "3", "4", "5", "6", "7"]}]
        rc, _ = _run(tmp_path, units=_write_json(tmp_path / "u.json", doc))
        assert rc == 2

    def test_unit_id_path_escape_fails(self, tmp_path: Path) -> None:
        """「#」後綴帶路徑字元——fail-loud 禁目錄逃逸。"""
        doc = _load(UNITS)
        doc["units"] = [
            {"unit_id": "AIR-234#../escape", "ac_ids": ["1", "2", "3", "4", "5", "6", "7"]}
        ]
        rc, _ = _run(tmp_path, units=_write_json(tmp_path / "u.json", doc))
        assert rc == 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    def test_exit_0_and_summary_on_stdout(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = am.main(
            [str(CONTRACT), "--units", str(UNITS), "--out-dir", str(tmp_path / "o")]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "3" in out  # units 數
        assert "7" in out  # predicates 總數

    def test_exit_2_missing_contract_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = am.main(
            ["no-such-contract.json", "--units", str(UNITS), "--out-dir", "/x"]
        )
        assert rc == 2
        assert "not found" in capsys.readouterr().err

    def test_exit_2_missing_units_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = am.main(
            [str(CONTRACT), "--units", "no-such-units.json", "--out-dir", "/x"]
        )
        assert rc == 2
        assert "not found" in capsys.readouterr().err

    def test_exit_2_malformed_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        rc = am.main([str(bad), "--units", str(UNITS), "--out-dir", str(tmp_path / "o")])
        assert rc == 2
        assert "ERROR" in capsys.readouterr().err

    def test_creates_out_dir(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "nested" / "out"
        rc = am.main(
            [str(CONTRACT), "--units", str(UNITS), "--out-dir", str(out_dir)]
        )
        assert rc == 0
        assert (out_dir / "impl-a.json").exists()
