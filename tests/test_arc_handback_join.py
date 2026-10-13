"""arc_handback_join 契約測試（AIR-234 manifest×handback 機械 join）。

釘住的 invariant（工單 §5.2 已決策勿重辯）：
- join 只驗結構齊全：schema 值、card_id/unit_id 一致、每 manifest predicate
  恰一 verdict、無未知 ac_id、verdict ∈ {PASS, FAIL, NOT-DONE}、evidence
  非空字串——違反 stdout 逐行缺項＋exit 2。
- 語義分離：verdict 為 FAIL/NOT-DONE 仍 exit 0——語義裁決歸 collection，
  不歸 join（本檔專項斷言，防 join 越權變 semantic gate）。
"""

import contextlib
import copy
import hashlib
import io
import json
import subprocess
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

hb = load_module("scripts/arc_handback_join.py")
am = load_module("scripts/arc_manifest.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "air-234"
MANIFEST = FIXTURES / "manifests" / "impl-a.json"
HANDBACK_PASS = FIXTURES / "handback-pass.json"
HANDBACK_MISSING = FIXTURES / "handback-missing.json"
# S: dispatch expectation independently frozen from EP encoding, not read at collection.
ASSIGNED_DIGEST = "961b585ef468a5a3861a04800d4a9ee7da1d63c6151d3cd3f8b7e3699d66b5f1"


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
        rc = hb.main(
            [
                "--manifest",
                str(manifest),
                "--handback",
                str(handback),
                "--expected-digest",
                ASSIGNED_DIGEST,
            ]
        )
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _handback_with(tmp_path: Path, **overrides: object) -> Path:
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
        rc, out, _ = _run(manifest=_write_json(tmp_path / "m2.json", m), handback=path)
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
        rc, out, _ = _run(manifest=_write_json(tmp_path / "m.json", m))
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
        assert (
            am.main(
                [
                    str(FIXTURES / "contract.json"),
                    "--units",
                    str(FIXTURES / "units.json"),
                    "--out-dir",
                    str(out_dir),
                ]
            )
            == 0
        )
        handback = _handback_with(tmp_path)  # verdicts 對 ac 1/2/3
        rc, out, _ = _run(manifest=out_dir / "impl-a.json", handback=handback)
        assert rc == 0
        assert "join OK: 3 predicates" in out


# Oracle provenance: S — accepted AIR-327 EP S1 oracle1–11, frozen before GREEN.
# JSON identity below is computed independently from the EP encoding contract.
def _oracle_digest(manifest: dict) -> str:
    body = {k: v for k, v in manifest.items() if k != "assigned_manifest_digest"}
    return hashlib.sha256(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _identity_pair() -> tuple[dict, dict, str]:
    manifest = _load(MANIFEST)
    manifest["schema"] = "arc-manifest/2"
    digest = _oracle_digest(manifest)
    manifest["assigned_manifest_digest"] = digest
    handback = _load(HANDBACK_PASS)
    handback.update(schema="arc-handback/2", assigned_manifest_digest=digest)
    return manifest, handback, digest


def _identity_run(
    tmp_path: Path, manifest: dict, handback: dict, expected: str
) -> tuple[int, str]:
    m = _write_json(tmp_path / "assigned.json", manifest)
    h = _write_json(tmp_path / "returned.json", handback)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = hb.main(
            ["--manifest", str(m), "--handback", str(h), "--expected-digest", expected]
        )
    return rc, out.getvalue()


class TestAssignedIdentity:
    def test_expected_only_oracle11(self, tmp_path: Path) -> None:
        """Only dispatch expectation differs; all artifact fields remain valid."""
        m, h, digest = _identity_pair()
        assert _identity_run(tmp_path, m, h, digest)[0] == 0
        rc, out = _identity_run(tmp_path, m, h, "0" * 64)
        assert rc == 2
        assert "identity" in out and "expected" in out

    def test_formatting_and_retry_preserve_identity(self, tmp_path: Path) -> None:
        m, h, digest = _identity_pair()
        reordered = dict(reversed(list(m.items())))
        rc, _ = _identity_run(tmp_path, reordered, h, digest)
        assert rc == 0
        assert hb.join(m, h, digest) == []
        assert hb.join(m, copy.deepcopy(h), digest) == []

    @pytest.mark.parametrize(
        "field", ["contract_hash", "verifier", "expected", "predicates"]
    )
    @pytest.mark.parametrize("recompute", [False, True])
    def test_changed_dispatch_rejects_old_handback(
        self, tmp_path: Path, field: str, recompute: bool
    ) -> None:
        m, h, digest = _identity_pair()
        if field == "contract_hash":
            m[field] = "f" * 64
        elif field == "predicates":
            m[field] = m[field][:2]
        else:
            m["predicates"][0][field] += " changed"
        if recompute:
            m["assigned_manifest_digest"] = _oracle_digest(m)
        rc, out = _identity_run(tmp_path, m, h, digest)
        assert rc == 2
        assert "identity" in out

    @pytest.mark.parametrize("value", [None, 42, [], "wrong", "0" * 64])
    def test_handback_digest_invalid(self, tmp_path: Path, value: object) -> None:
        m, h, digest = _identity_pair()
        if value is None:
            h.pop("assigned_manifest_digest")
        else:
            h["assigned_manifest_digest"] = value
        rc, out = _identity_run(tmp_path, m, h, digest)
        assert rc == 2
        assert "identity" in out

    @pytest.mark.parametrize("owner", ["manifest", "handback"])
    def test_legacy_schema_rejected(self, tmp_path: Path, owner: str) -> None:
        m, h, digest = _identity_pair()
        if owner == "manifest":
            m["schema"] = "arc-manifest/1"
            digest = _oracle_digest(m)
            m["assigned_manifest_digest"] = h["assigned_manifest_digest"] = digest
        else:
            h["schema"] = "arc-handback/1"
        rc, out = _identity_run(tmp_path, m, h, digest)
        assert rc == 2 and "schema" in out

    @pytest.mark.parametrize(
        "fault,diagnostic",
        [
            ("missing", "missing: ac_id=3"),
            ("duplicate", "duplicate verdict"),
            ("unknown", "未知 ac_id"),
            ("empty", "evidence"),
        ],
    )
    def test_identity_does_not_replace_structure(
        self, tmp_path: Path, fault: str, diagnostic: str
    ) -> None:
        m, h, digest = _identity_pair()
        if fault == "missing":
            h["verdicts"].pop()
        elif fault == "duplicate":
            h["verdicts"].append(h["verdicts"][0])
        elif fault == "unknown":
            h["verdicts"].append({"ac_id": "99", "verdict": "PASS", "evidence": "x"})
        else:
            h["verdicts"][0]["evidence"] = ""
        rc, out = _identity_run(tmp_path, m, h, digest)
        assert rc == 2 and diagnostic in out
        assert "identity" not in out

    @pytest.mark.parametrize("verdict", ["FAIL", "NOT-DONE"])
    def test_valid_identity_is_not_semantic_acceptance(
        self, tmp_path: Path, verdict: str
    ) -> None:
        m, h, digest = _identity_pair()
        h["verdicts"][0]["verdict"] = verdict
        assert _identity_run(tmp_path, m, h, digest)[0] == 0

    @pytest.mark.parametrize("owner", ["manifest", "handback"])
    @pytest.mark.parametrize("nonfinite", [float("nan"), float("inf"), float("-inf")])
    def test_nonfinite_cli_exit2(
        self, tmp_path: Path, owner: str, nonfinite: float
    ) -> None:
        m, h, digest = _identity_pair()
        (m if owner == "manifest" else h)["extra"] = nonfinite
        rc, out = _identity_run(tmp_path, m, h, digest)
        assert rc == 2 and "finite" in out

    def test_real_cli_producer_join_and_required_expected(self, tmp_path: Path) -> None:
        """Drive script entry points in real subprocesses (no monkeypatched IO)."""
        out_dir = tmp_path / "dispatch"
        producer = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "scripts/arc_manifest.py",
                str(FIXTURES / "contract.json"),
                "--units",
                str(FIXTURES / "units.json"),
                "--out-dir",
                str(out_dir),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert producer.returncode == 0, producer.stderr
        m = _load(out_dir / "impl-a.json")
        digest = _oracle_digest(m)
        assert m["assigned_manifest_digest"] == digest
        h = _load(HANDBACK_PASS)
        h.update(schema="arc-handback/2", assigned_manifest_digest=digest)
        h_path = _write_json(tmp_path / "h.json", h)
        cmd = [
            "uv",
            "run",
            "python",
            "scripts/arc_handback_join.py",
            "--manifest",
            str(out_dir / "impl-a.json"),
            "--handback",
            str(h_path),
        ]
        for expected, rc in [(digest, 0), ("0" * 64, 2)]:
            result = subprocess.run(
                cmd + ["--expected-digest", expected],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == rc, result.stdout + result.stderr
            if rc == 2:
                assert "identity" in result.stdout and "expected" in result.stdout
        missing = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        assert missing.returncode == 2 and "--expected-digest" in missing.stderr


# Oracle provenance: H — Marshal CLI repros in air327-adjudication-repro.json;
# target exit2/typed diagnostics adopted before repair implementation.
class TestMalformedInputRepair:
    def test_lone_surrogate_manifest_is_identity_diagnostic(
        self, tmp_path: Path
    ) -> None:
        manifest, handback, digest = _identity_pair()
        manifest["surrogate"] = "\ud800"
        m_path = tmp_path / "surrogate.json"
        # ASCII JSON escape reaches the actual consumer UTF-8 digest boundary.
        m_path.write_text(json.dumps(manifest, ensure_ascii=True), encoding="utf-8")
        h_path = _write_json(tmp_path / "handback.json", handback)
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "scripts/arc_handback_join.py",
                "--manifest",
                str(m_path),
                "--handback",
                str(h_path),
                "--expected-digest",
                digest,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2, result.stdout + result.stderr
        assert "invalid: identity" in result.stdout
        assert "UTF-8" in result.stdout
        assert "Traceback" not in result.stderr

    @pytest.mark.parametrize("ac_id", [["3"], {"id": "3"}])
    def test_unhashable_handback_ac_is_diagnosed_before_grouping(
        self, tmp_path: Path, ac_id: object
    ) -> None:
        manifest, handback, digest = _identity_pair()
        handback["verdicts"][2]["ac_id"] = ac_id
        rc, out = _identity_run(tmp_path, manifest, handback, digest)
        assert rc == 2
        assert "invalid: verdicts[2]" in out and "ac_id" in out
        assert "missing: ac_id=3" in out
        assert "identity" not in out
