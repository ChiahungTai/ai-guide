"""arc_settle_state 狀態機測試（AIR-135.11 值星收線機械隊列）。

釘住的 invariant（卡面狀態圖＋工單 §2 機械面＋repair-1 修復批）：
- 七態枚舉；合法轉移表＝IMPLEMENTING→REVIEWING→READY_TO_JUDGE→
  READY_TO_LAND｜NEEDS_REPAIR；NEEDS_REPAIR→IMPLEMENTING；
  READY_TO_LAND→LANDED；任態→BLOCKED。
- LANDED 語義單一化（repair-1 R2——裁決勿重辯）：LANDED 唯一合法後繼＝
  BLOCKED（任態→BLOCKED 逃逸線含 LANDED）；BLOCKED 為唯一真終態（無後繼，
  advance 一律 exit 2；show 仍可讀）。
- set＝僅限新建（既有 arc 拒收 exit 2「arc 已存在——用 advance 推進」——
  seq 單調合卡面，repair-1 R1）；advance 須合法轉移，非法 fail-loud
  逐行列「現態＋合法後繼」exit 2；seq 單調遞增（無時鐘依賴）。
- pointer 非空（空指針拒收）；寫檔原子（無 tmp 殘留）；record 欄位恰五鍵。
- queue 按 state 過濾；損壞 state 檔 fail-loud 禁靜默跳過。
"""

import json
from pathlib import Path

import pytest
from conftest import load_module

ss = load_module("scripts/arc_settle_state.py")

STATES = ss.STATES

CANON = {"sort_keys": True, "ensure_ascii": False, "separators": (",", ":")}


def _write_state(directory: Path, arc_id: str, record: dict) -> None:
    """直接落一個 state 檔（integrity 反例用——繞過 CLI 寫入面）。"""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{arc_id}.json").write_text(
        json.dumps(record, **CANON) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# 狀態枚舉與合法轉移表
# ---------------------------------------------------------------------------


class TestStateTable:
    def test_seven_states(self) -> None:
        assert set(STATES) == {
            "IMPLEMENTING",
            "REVIEWING",
            "READY_TO_JUDGE",
            "NEEDS_REPAIR",
            "READY_TO_LAND",
            "LANDED",
            "BLOCKED",
        }

    def test_table_covers_all_states(self) -> None:
        assert set(ss.TRANSITIONS) == set(STATES)

    def test_card_diagram_edges(self) -> None:
        """卡面狀態圖六條邊（不含 BLOCKED 逃逸線）逐條釘死。"""
        assert ss.TRANSITIONS["IMPLEMENTING"] == ("REVIEWING", "BLOCKED")
        assert ss.TRANSITIONS["REVIEWING"] == ("READY_TO_JUDGE", "BLOCKED")
        assert ss.TRANSITIONS["READY_TO_JUDGE"] == (
            "READY_TO_LAND",
            "NEEDS_REPAIR",
            "BLOCKED",
        )
        assert ss.TRANSITIONS["NEEDS_REPAIR"] == ("IMPLEMENTING", "BLOCKED")
        assert ss.TRANSITIONS["READY_TO_LAND"] == ("LANDED", "BLOCKED")
        assert ss.TRANSITIONS["LANDED"] == ("BLOCKED",)
        assert ss.TRANSITIONS["BLOCKED"] == ()

    def test_any_state_to_blocked(self) -> None:
        for state in STATES:
            if state == "BLOCKED":
                assert ss.TRANSITIONS[state] == ()
            else:
                assert "BLOCKED" in ss.TRANSITIONS[state]


# ---------------------------------------------------------------------------
# 全轉移表合法路徑（set→advance；seq 單調；advance 未帶 pointer 保留既有）
# ---------------------------------------------------------------------------


class TestLegalPaths:
    def test_every_legal_edge_advance_ok(self, tmp_path: Path) -> None:
        for src, successors in ss.TRANSITIONS.items():
            for dst in successors:
                d = tmp_path / f"{src.lower()}-{dst.lower()}"
                rc = ss.main(
                    [
                        "set",
                        "--arc",
                        "A",
                        "--state",
                        src,
                        "--pointer",
                        "p.md",
                        "--dir",
                        str(d),
                    ]
                )
                assert rc == 0, f"{src}->{dst}"
                rc = ss.main(
                    ["advance", "--arc", "A", "--state", dst, "--dir", str(d)]
                )
                assert rc == 0, f"{src}->{dst}"
                record = json.loads((d / "A.json").read_text(encoding="utf-8"))
                assert record["state"] == dst
                assert record["seq"] == 2
                assert record["pointer"] == "p.md"

    def test_seq_monotonic_along_repair_loop(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        path = d / "A.json"
        assert (
            ss.main(
                [
                    "set",
                    "--arc",
                    "A",
                    "--state",
                    "IMPLEMENTING",
                    "--pointer",
                    "p.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        chain = ["REVIEWING", "READY_TO_JUDGE", "NEEDS_REPAIR", "IMPLEMENTING"]
        for expected_seq, dst in enumerate(chain, start=2):
            assert (
                ss.main(["advance", "--arc", "A", "--state", dst, "--dir", str(d)])
                == 0
            )
            assert json.loads(path.read_text(encoding="utf-8"))["seq"] == expected_seq

    def test_advance_updates_pointer_when_given(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        ss.main(
            [
                "set",
                "--arc",
                "A",
                "--state",
                "IMPLEMENTING",
                "--pointer",
                "old.md",
                "--dir",
                str(d),
            ]
        )
        rc = ss.main(
            [
                "advance",
                "--arc",
                "A",
                "--state",
                "REVIEWING",
                "--pointer",
                "new.md",
                "--dir",
                str(d),
            ]
        )
        assert rc == 0
        record = json.loads((d / "A.json").read_text(encoding="utf-8"))
        assert record["pointer"] == "new.md"
        assert record["seq"] == 2

    def test_set_existing_arc_rejected(self, tmp_path: Path, capsys) -> None:
        """repair-1 R1（翻轉自 test_set_overwrite_resets_seq）：set 僅限新建——
        既有 arc 拒收 exit 2「arc 已存在——用 advance 推進」，seq 單調合卡面。"""
        d = tmp_path / "q"
        assert (
            ss.main(
                [
                    "set",
                    "--arc",
                    "A",
                    "--state",
                    "IMPLEMENTING",
                    "--pointer",
                    "p1.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        capsys.readouterr()
        rc = ss.main(
            [
                "set",
                "--arc",
                "A",
                "--state",
                "REVIEWING",
                "--pointer",
                "p2.md",
                "--dir",
                str(d),
            ]
        )
        assert rc == 2
        err = capsys.readouterr().err
        assert "arc 已存在" in err
        assert "advance" in err
        # 既有 state 檔未被覆寫
        record = json.loads((d / "A.json").read_text(encoding="utf-8"))
        assert record["state"] == "IMPLEMENTING"
        assert record["seq"] == 1
        assert record["pointer"] == "p1.md"

    def test_seq_continuity_set_advance_advance(self, tmp_path: Path) -> None:
        """repair-1 R1 補測：set→advance→advance seq 連續 1,2,3（單調由
        advance 承擔，set 無重置面）。"""
        d = tmp_path / "q"
        path = d / "A.json"
        assert (
            ss.main(
                [
                    "set",
                    "--arc",
                    "A",
                    "--state",
                    "IMPLEMENTING",
                    "--pointer",
                    "p.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        assert json.loads(path.read_text(encoding="utf-8"))["seq"] == 1
        assert (
            ss.main(["advance", "--arc", "A", "--state", "REVIEWING", "--dir", str(d)])
            == 0
        )
        assert json.loads(path.read_text(encoding="utf-8"))["seq"] == 2
        assert (
            ss.main(
                ["advance", "--arc", "A", "--state", "READY_TO_JUDGE", "--dir", str(d)]
            )
            == 0
        )
        assert json.loads(path.read_text(encoding="utf-8"))["seq"] == 3

    def test_full_chain_to_ready_to_judge(self, tmp_path: Path) -> None:
        """repair-1 R3 整鏈 sequence：impl set IMPLEMENTING → review advance
        REVIEWING → join 過 advance READY_TO_JUDGE——全鏈 exit 0。"""
        d = tmp_path / "q"
        assert (
            ss.main(
                [
                    "set",
                    "--arc",
                    "A",
                    "--state",
                    "IMPLEMENTING",
                    "--pointer",
                    "impl.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        assert (
            ss.main(
                [
                    "advance",
                    "--arc",
                    "A",
                    "--state",
                    "REVIEWING",
                    "--pointer",
                    "review.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        assert (
            ss.main(
                [
                    "advance",
                    "--arc",
                    "A",
                    "--state",
                    "READY_TO_JUDGE",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        record = json.loads((d / "A.json").read_text(encoding="utf-8"))
        assert record["state"] == "READY_TO_JUDGE"
        assert record["seq"] == 3
        assert record["pointer"] == "review.md"


# ---------------------------------------------------------------------------
# set／show／queue 基本面（AC#1/#3 形狀）
# ---------------------------------------------------------------------------


class TestCommands:
    def test_set_creates_file(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        rc = ss.main(
            [
                "set",
                "--arc",
                "AIR-X",
                "--state",
                "READY_TO_JUDGE",
                "--pointer",
                ".agent-tmp/x.md",
                "--dir",
                str(d),
            ]
        )
        assert rc == 0
        assert (d / "AIR-X.json").exists()
        record = json.loads((d / "AIR-X.json").read_text(encoding="utf-8"))
        assert record == {
            "schema": "arc-settle-state/1",
            "arc_id": "AIR-X",
            "state": "READY_TO_JUDGE",
            "pointer": ".agent-tmp/x.md",
            "seq": 1,
        }

    def test_record_on_disk_canonical_json(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        ss.main(
            [
                "set",
                "--arc",
                "AIR-X",
                "--state",
                "READY_TO_JUDGE",
                "--pointer",
                ".agent-tmp/x.md",
                "--dir",
                str(d),
            ]
        )
        raw = (d / "AIR-X.json").read_text(encoding="utf-8")
        expected = json.dumps(
            {
                "schema": "arc-settle-state/1",
                "arc_id": "AIR-X",
                "state": "READY_TO_JUDGE",
                "pointer": ".agent-tmp/x.md",
                "seq": 1,
            },
            **CANON,
        )
        assert raw == expected + "\n"

    def test_no_tmp_residue_after_set(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        ss.main(
            [
                "set",
                "--arc",
                "AIR-X",
                "--state",
                "REVIEWING",
                "--pointer",
                "p.md",
                "--dir",
                str(d),
            ]
        )
        assert sorted(p.name for p in d.iterdir()) == ["AIR-X.json"]

    def test_show_prints_state_and_pointer(self, tmp_path: Path, capsys) -> None:
        d = tmp_path / "q"
        ss.main(
            [
                "set",
                "--arc",
                "A",
                "--state",
                "READY_TO_JUDGE",
                "--pointer",
                ".agent-tmp/x.md",
                "--dir",
                str(d),
            ]
        )
        capsys.readouterr()
        assert ss.main(["show", "--arc", "A", "--dir", str(d)]) == 0
        out = capsys.readouterr().out
        assert "state: READY_TO_JUDGE" in out
        assert "pointer: .agent-tmp/x.md" in out

    def test_show_missing_arc_exit2(self, tmp_path: Path) -> None:
        assert ss.main(["show", "--arc", "GHOST", "--dir", str(tmp_path)]) == 2

    def test_queue_filters_by_state(self, tmp_path: Path, capsys) -> None:
        d = tmp_path / "q"
        for arc, state in (
            ("AIR-1", "READY_TO_JUDGE"),
            ("AIR-2", "IMPLEMENTING"),
            ("AIR-3", "READY_TO_JUDGE"),
        ):
            assert (
                ss.main(
                    [
                        "set",
                        "--arc",
                        arc,
                        "--state",
                        state,
                        "--pointer",
                        "p.md",
                        "--dir",
                        str(d),
                    ]
                )
                == 0
            )
        capsys.readouterr()
        assert ss.main(["queue", "--dir", str(d), "--state", "READY_TO_JUDGE"]) == 0
        out = capsys.readouterr().out
        assert "AIR-1" in out
        assert "AIR-3" in out
        assert "AIR-2" not in out

    def test_queue_empty_result_exit0(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        d.mkdir()
        assert ss.main(["queue", "--dir", str(d), "--state", "LANDED"]) == 0

    def test_queue_missing_dir_exit2(self, tmp_path: Path) -> None:
        rc = ss.main(["queue", "--dir", str(tmp_path / "nope"), "--state", "LANDED"])
        assert rc == 2


# ---------------------------------------------------------------------------
# fail-loud：非法轉移／空指針／非法身分與狀態／損壞檔
# ---------------------------------------------------------------------------


ILLEGAL_PAIRS = [
    ("LANDED", "IMPLEMENTING"),
    ("IMPLEMENTING", "LANDED"),
    ("IMPLEMENTING", "READY_TO_LAND"),
    ("REVIEWING", "NEEDS_REPAIR"),
    ("READY_TO_LAND", "REVIEWING"),
    ("READY_TO_JUDGE", "IMPLEMENTING"),
    ("NEEDS_REPAIR", "LANDED"),
    ("BLOCKED", "IMPLEMENTING"),
    ("BLOCKED", "REVIEWING"),
    ("BLOCKED", "BLOCKED"),
]


class TestFailLoud:
    @pytest.mark.parametrize(("src", "dst"), ILLEGAL_PAIRS)
    def test_illegal_transition_exit2_lists_successors(
        self, tmp_path: Path, capsys, src: str, dst: str
    ) -> None:
        d = tmp_path / "q"
        assert (
            ss.main(
                [
                    "set",
                    "--arc",
                    "A",
                    "--state",
                    src,
                    "--pointer",
                    "p.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        capsys.readouterr()
        rc = ss.main(["advance", "--arc", "A", "--state", dst, "--dir", str(d)])
        assert rc == 2
        err = capsys.readouterr().err
        assert f"現態={src}" in err
        assert "合法後繼" in err
        for successor in ss.TRANSITIONS[src]:
            assert successor in err
        if not ss.TRANSITIONS[src]:
            assert "（無" in err
        record = json.loads((d / "A.json").read_text(encoding="utf-8"))
        assert record["state"] == src
        assert record["seq"] == 1

    def test_blocked_no_successor_advance_always_rejected(
        self, tmp_path: Path
    ) -> None:
        d = tmp_path / "q"
        assert (
            ss.main(
                [
                    "set",
                    "--arc",
                    "A",
                    "--state",
                    "BLOCKED",
                    "--pointer",
                    "p.md",
                    "--dir",
                    str(d),
                ]
            )
            == 0
        )
        for dst in STATES:
            assert (
                ss.main(["advance", "--arc", "A", "--state", dst, "--dir", str(d)])
                == 2
            )
        assert ss.main(["show", "--arc", "A", "--dir", str(d)]) == 0

    def test_set_empty_pointer_rejected(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        rc = ss.main(
            [
                "set",
                "--arc",
                "A",
                "--state",
                "REVIEWING",
                "--pointer",
                "   ",
                "--dir",
                str(d),
            ]
        )
        assert rc == 2
        assert not (d / "A.json").exists()

    def test_advance_empty_pointer_rejected(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        ss.main(
            [
                "set",
                "--arc",
                "A",
                "--state",
                "IMPLEMENTING",
                "--pointer",
                "p.md",
                "--dir",
                str(d),
            ]
        )
        rc = ss.main(
            [
                "advance",
                "--arc",
                "A",
                "--state",
                "REVIEWING",
                "--pointer",
                "",
                "--dir",
                str(d),
            ]
        )
        assert rc == 2
        record = json.loads((d / "A.json").read_text(encoding="utf-8"))
        assert record["state"] == "IMPLEMENTING"
        assert record["pointer"] == "p.md"

    def test_advance_missing_arc_exit2(self, tmp_path: Path) -> None:
        rc = ss.main(
            ["advance", "--arc", "GHOST", "--state", "REVIEWING", "--dir", str(tmp_path)]
        )
        assert rc == 2

    @pytest.mark.parametrize("bad", ["../evil", "", "a/b", ".hidden", "a b", "x\ny"])
    def test_invalid_arc_id_rejected(self, tmp_path: Path, bad: str) -> None:
        rc = ss.main(
            ["set", "--arc", bad, "--state", "LANDED", "--pointer", "p", "--dir", str(tmp_path)]
        )
        assert rc == 2

    def test_set_invalid_state_exit2_lists_valid(self, tmp_path: Path) -> None:
        rc = ss.main(
            [
                "set",
                "--arc",
                "A",
                "--state",
                "FOO",
                "--pointer",
                "p",
                "--dir",
                str(tmp_path),
            ]
        )
        assert rc == 2
        assert not (tmp_path / "A.json").exists()

    def test_queue_invalid_state_exit2(self, tmp_path: Path) -> None:
        rc = ss.main(["queue", "--dir", str(tmp_path), "--state", "FOO"])
        assert rc == 2

    def test_corrupt_file_fails_loud_everywhere(self, tmp_path: Path) -> None:
        d = tmp_path / "q"
        d.mkdir(parents=True)
        (d / "BAD.json").write_text("{not json", encoding="utf-8")
        assert ss.main(["queue", "--dir", str(d), "--state", "LANDED"]) == 2
        assert (
            ss.main(
                ["advance", "--arc", "BAD", "--state", "LANDED", "--dir", str(d)]
            )
            == 2
        )
        assert ss.main(["show", "--arc", "BAD", "--dir", str(d)]) == 2

    def test_schema_mismatch_fails_loud(self, tmp_path: Path) -> None:
        _write_state(
            tmp_path,
            "A",
            {
                "schema": "other/9",
                "arc_id": "A",
                "state": "LANDED",
                "pointer": "p",
                "seq": 1,
            },
        )
        assert ss.main(["show", "--arc", "A", "--dir", str(tmp_path)]) == 2

    def test_arc_id_filename_mismatch_fails_loud(self, tmp_path: Path) -> None:
        _write_state(
            tmp_path,
            "A",
            {
                "schema": "arc-settle-state/1",
                "arc_id": "B",
                "state": "LANDED",
                "pointer": "p",
                "seq": 1,
            },
        )
        assert ss.main(["show", "--arc", "A", "--dir", str(tmp_path)]) == 2

    def test_unknown_state_in_file_fails_loud(self, tmp_path: Path) -> None:
        _write_state(
            tmp_path,
            "A",
            {
                "schema": "arc-settle-state/1",
                "arc_id": "A",
                "state": "FOO",
                "pointer": "p",
                "seq": 1,
            },
        )
        assert ss.main(["show", "--arc", "A", "--dir", str(tmp_path)]) == 2

    def test_bad_seq_in_file_fails_loud(self, tmp_path: Path) -> None:
        _write_state(
            tmp_path,
            "A",
            {
                "schema": "arc-settle-state/1",
                "arc_id": "A",
                "state": "LANDED",
                "pointer": "p",
                "seq": 0,
            },
        )
        assert ss.main(["show", "--arc", "A", "--dir", str(tmp_path)]) == 2
