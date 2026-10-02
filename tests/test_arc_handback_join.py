"""arc_handback_join 契約測試（AIR-234 manifest×handback 機械 join）。

釘住的 invariant（工單 §5.2 已決策勿重辯）：
- join 只驗結構齊全：schema 值、card_id/unit_id 一致、每 manifest predicate
  恰一 verdict、無未知 ac_id、verdict ∈ {PASS, FAIL, NOT-DONE}、evidence
  非空字串——違反 stdout 逐行缺項＋exit 2。
- 語義分離：verdict 為 FAIL/NOT-DONE 仍 exit 0——語義裁決歸 collection，
  不歸 join（本檔專項斷言，防 join 越權變 semantic gate）。
"""

import contextlib
import io
import json
from pathlib import Path

from conftest import REPO_ROOT, load_module

hb = load_module("scripts/arc_handback_join.py")
am = load_module("scripts/arc_manifest.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "air-234"
MANIFEST = FIXTURES / "manifests" / "impl-a.json"
HANDBACK_PASS = FIXTURES / "handback-pass.json"
HANDBACK_MISSING = FIXTURES / "handback-missing.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _run(
    manifest: Path = MANIFEST,
    handback: Path = HANDBACK_PASS,
) -> tuple[int, str, str]:
    """跑 CLI 並回 (rc, stdout, stderr)——join 違約行按工單走 stdout。"""
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        rc = hb.main(["--manifest", str(manifest), "--handback", str(handback)])
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _handback_with(tmp_path: Path, **overrides: dict) -> Path:
    doc = _load(HANDBACK_PASS)
    doc.update(overrides)
    return _write_json(tmp_path / "handback.json", doc)


# ---------------------------------------------------------------------------
# pass path＋語義分離（FAIL/NOT-DONE 仍 exit 0——join 非 semantic gate）
# ---------------------------------------------------------------------------


class TestJoinPass:
    def test_fixture_pass_exit_zero(self, tmp_path: Path) -> None:
        rc, out, _ = _run()
        assert rc == 0
        assert out.strip() == "join OK: 3 predicates"

    def test_fail_verdict_still_exit_zero(self, tmp_path: Path) -> None:
        """FAIL 是語義裁決——join 只驗結構，照樣 exit 0。"""
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "FAIL", "evidence": "pytest 3 failed"},
                {"ac_id": "2", "verdict": "PASS", "evidence": "exit 2 如預期"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "全綠"},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 0
        assert "join OK" in out

    def test_not_done_verdict_still_exit_zero(self, tmp_path: Path) -> None:
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "PASS", "evidence": "exit 0"},
                {"ac_id": "2", "verdict": "NOT-DONE", "evidence": "未及實作"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "全綠"},
            ],
        )
        rc, _, _ = _run(handback=path)
        assert rc == 0


# ---------------------------------------------------------------------------
# 結構缺項（exit 2＋stdout 逐行）
# ---------------------------------------------------------------------------


class TestJoinViolations:
    def test_missing_verdict_line(self, tmp_path: Path) -> None:
        """fixture 即 AC#2 驗收載體——缺 ac_id=3 的 verdict。"""
        rc, out, _ = _run(handback=HANDBACK_MISSING)
        assert rc == 2
        assert "missing: ac_id=3" in out

    def test_bad_verdict_value(self, tmp_path: Path) -> None:
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "OK", "evidence": "非三值"},
                {"ac_id": "2", "verdict": "PASS", "evidence": "x"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "y"},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "invalid: ac_id=1" in out
        assert "reason=" in out

    def test_empty_evidence(self, tmp_path: Path) -> None:
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "PASS", "evidence": ""},
                {"ac_id": "2", "verdict": "PASS", "evidence": "x"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "y"},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "invalid: ac_id=1" in out
        assert "evidence" in out

    def test_whitespace_only_evidence(self, tmp_path: Path) -> None:
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "PASS", "evidence": "   \n  "},
                {"ac_id": "2", "verdict": "PASS", "evidence": "x"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "y"},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "invalid: ac_id=1" in out

    def test_unit_id_mismatch(self, tmp_path: Path) -> None:
        path = _handback_with(tmp_path, unit_id="AIR-234#impl-b")
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "unit_id" in out

    def test_card_id_mismatch(self, tmp_path: Path) -> None:
        path = _handback_with(tmp_path, card_id="AIR-OTHER")
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "card_id" in out

    def test_unknown_ac_id_in_handback(self, tmp_path: Path) -> None:
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "PASS", "evidence": "x"},
                {"ac_id": "2", "verdict": "PASS", "evidence": "y"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "z"},
                {"ac_id": "9", "verdict": "PASS", "evidence": "越權 verdict"},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "invalid: ac_id=9" in out
        assert "未知" in out

    def test_duplicate_verdict_for_same_ac(self, tmp_path: Path) -> None:
        """每 predicate 恰一個 verdict——雙 verdict 亦為結構違約。"""
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "PASS", "evidence": "x"},
                {"ac_id": "1", "verdict": "FAIL", "evidence": "y"},
                {"ac_id": "2", "verdict": "PASS", "evidence": "z"},
                {"ac_id": "3", "verdict": "PASS", "evidence": "w"},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "ac_id=1" in out

    def test_corrupt_manifest_string_entry_rejected(self, tmp_path: Path) -> None:
        """R3：manifest predicates 含字串條目＝malformed——禁縮水集合假 PASS
        （verdict 只蓋合法條目仍須 exit 2，非靜默略過）。"""
        m = _load(MANIFEST)
        m["predicates"] = [m["predicates"][0], "CORRUPT"]
        path = _handback_with(
            tmp_path,
            verdicts=[{"ac_id": "1", "verdict": "PASS", "evidence": "x"}],
        )
        rc, out, _ = _run(manifest=_write_json(tmp_path / "m.json", m), handback=path)
        assert rc == 2
        assert "invalid" in out
        assert "reason=" in out

    def test_duplicate_ac_in_manifest_rejected(self, tmp_path: Path) -> None:
        """R3：manifest predicates 同 ac_id 兩條＝重複——exit 2（禁靜默取一）。"""
        m = _load(MANIFEST)
        m["predicates"] = [
            m["predicates"][0],
            m["predicates"][0],
            m["predicates"][1],
        ]
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "PASS", "evidence": "x"},
                {"ac_id": "2", "verdict": "PASS", "evidence": "y"},
            ],
        )
        rc, out, _ = _run(
            manifest=_write_json(tmp_path / "m2.json", m), handback=path
        )
        assert rc == 2
        assert "ac_id=1" in out
        assert "重複" in out

    def test_multiple_violations_reported_per_line(self, tmp_path: Path) -> None:
        """逐行缺項——缺項與壞值同現時 stdout 多行、非僅首報。"""
        path = _handback_with(
            tmp_path,
            verdicts=[
                {"ac_id": "1", "verdict": "NOPE", "evidence": ""},
            ],
        )
        rc, out, _ = _run(handback=path)
        assert rc == 2
        lines = [ln for ln in out.strip().splitlines() if ln.strip()]
        assert len(lines) >= 3, f"未逐行回報：{lines!r}"  # 缺 2/3＋壞 1


# ---------------------------------------------------------------------------
# schema 值與檔案層錯誤
# ---------------------------------------------------------------------------


class TestSchemaAndFiles:
    def test_bad_handback_schema(self, tmp_path: Path) -> None:
        path = _handback_with(tmp_path, schema="arc-handback/9")
        rc, out, _ = _run(handback=path)
        assert rc == 2
        assert "schema" in out

    def test_bad_manifest_schema(self, tmp_path: Path) -> None:
        m = _load(MANIFEST)
        m["schema"] = "arc-manifest/9"
        rc, out, _ = _run(
            manifest=_write_json(tmp_path / "m.json", m)
        )
        assert rc == 2
        assert "schema" in out

    def test_missing_manifest_file(self, tmp_path: Path) -> None:
        rc, _, err = _run(manifest=tmp_path / "nope.json")
        assert rc == 2
        assert "not found" in err

    def test_missing_handback_file(self, tmp_path: Path) -> None:
        rc, _, err = _run(handback=tmp_path / "nope.json")
        assert rc == 2
        assert "not found" in err

    def test_malformed_json_manifest(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{broken", encoding="utf-8")
        rc, _, err = _run(manifest=bad)
        assert rc == 2
        assert "ERROR" in err

    def test_manifest_top_level_non_object_fails_clean(self, tmp_path: Path) -> None:
        """R4：合法 JSON 但 top-level 非物件（[]）——乾淨結構錯誤＋exit 2。"""
        bad = tmp_path / "m.json"
        bad.write_text("[]", encoding="utf-8")
        rc, out, _ = _run(manifest=bad)
        assert rc == 2
        assert "invalid" in out
        assert "object" in out

    def test_handback_top_level_non_object_fails_clean(self, tmp_path: Path) -> None:
        bad = tmp_path / "hb.json"
        bad.write_text("[]", encoding="utf-8")
        rc, out, _ = _run(handback=bad)
        assert rc == 2
        assert "invalid" in out
        assert "object" in out


# ---------------------------------------------------------------------------
# 與 arc_manifest 的接縫：manifest 投影→handback join 全鏈
# ---------------------------------------------------------------------------


class TestSeamWithArcManifest:
    def test_generated_manifest_joins_generated_handback(self, tmp_path: Path) -> None:
        """arc_manifest 產物可直接餵 join（介面契約釘死的接縫）——非只對
        固化 fixture 成立。"""
        out_dir = tmp_path / "manifests"
        assert am.main(
            [
                str(FIXTURES / "contract.json"),
                "--units",
                str(FIXTURES / "units.json"),
                "--out-dir",
                str(out_dir),
            ]
        ) == 0
        handback = _handback_with(tmp_path)  # verdicts 對 ac 1/2/3
        rc, out, _ = _run(
            manifest=out_dir / "impl-a.json", handback=handback
        )
        assert rc == 0
        assert "join OK: 3 predicates" in out
