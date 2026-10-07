"""session_discovery seam 契約測試（AIR-254.1；AIR-277 換源 harness-native）.

驗證式（lite 寫的測試＝規格陳述，驗收證據由 full 複驗）：
- 單一 choke point：`_collect_raw` 是唯一源存取點——harness-native scan
  （ZCode session store `session` 表唯讀直查；fixture＝tmp_path fake
  store，排序以 `time_updated` 欄控制）；失敗 raise typed DiscoveryError
  （CLI 層轉 exit 3 統一 envelope）。源缺席＝`source_unavailable`、開檔
  後結構／內容損壞＝`source_malformed`。
- 正規化 rows 八欄形狀（session_id 全碼／harness／workspace_root／label
  ／liveness／status／last_seen_iso／age_min）；label 合併＝sidecar 優先、
  無 sidecar 用 store title、皆無＝null。liveness／status 由 `time_archived`
  推導（未封存＝live／active、已封存＝ended／ended——handoff
  `status != "ended"` 過濾語義保留）。
- 覆蓋邊界（如實聲明）：harness 恆 "zcode"、coverage="zcode-only"；
  `task_type='subagent_child'` 不列；find 對非 zcode harness＝no-match
  typed＋覆蓋註記。
- `--live` 過濾＝liveness=="live" 且 `sess_` 前綴（inflight 現行雜訊
  排除語義保留；status 不參與過濾）。
- find：同 harness＋workspace_root 取 time_updated（缺則 time_created）
  最新一列；0 或 >1 候選同分＝typed failure 禁猜。
- runner 遺留槽：collect_rows／find_session 首位置參數接受 callable 且
  值被忽略（inflight_snapshot 呼叫相容——消費端零改動契約）。
- label sidecar：形 `{"sid": {"label", "updated_at"}}`、atomic 寫（無
  .tmp 殘留）、檔 0600／目錄 0700；set 冪等覆寫；get 無＝fail；驗證
  1-64 字元非純空白；絕不寫源 store（連線唯讀）。
- whoami：cwd→workspace 對照（realpath 精確匹配、time_updated 最新）；
  無匹配／源缺席＝whoami_unavailable、源損壞＝whoami_malformed。
- CLI：失敗統一 `{"schemaVersion":1,"ok":false,"error":{code,message}}`
  到 stderr、stdout 空、exit 3。

oracle＝I 級（impl 衍生——契約單一源即 scripts/session_discovery.py
docstring；真機 store L4 實跑由 full 複驗）。
"""

import json
import sqlite3
import stat
import time
from datetime import datetime
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/session_discovery.py")

WS = "/Users/ctai/Github/ai-guide"
_MS = 1_700_000_000_000  # ms epoch（store 單位）
_UNSET = object()  # 區分「未提供」與「明確傳 NULL」


def _srow(
    sid: str = "sess_aaa-0001",
    *,
    ws: str | None = WS,
    title: str | None = None,
    created: object = _UNSET,
    updated: object = _UNSET,
    archived: int | None = None,
    task_type: str | None = "interactive",
) -> tuple:
    """store 列 tuple（ms 時間戳；預設 created=_MS、updated＝created＋90s；
    明確傳 None＝NULL 值）。"""
    return (
        sid,
        ws,
        title,
        _MS if created is _UNSET else created,
        (_MS + 90_000) if updated is _UNSET else updated,
        archived,
        task_type,
    )


def _store(tmp_path: Path, *rows: tuple) -> Path:
    """tmp fake session store（最小 `session` 表——seam SELECT 具名欄）。"""
    db = tmp_path / "store.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE session ("
        "id TEXT, directory TEXT, title TEXT, time_created INTEGER,"
        " time_updated INTEGER, time_archived INTEGER, task_type TEXT)"
    )
    con.executemany("INSERT INTO session VALUES (?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return db


# ---------------------------------------------------------------------------
# choke point：_collect_raw（harness-native scan；typed fail-closed）
# ---------------------------------------------------------------------------


class TestCollectRaw:
    def test_scan_returns_payload_newest_first(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_old", updated=_MS),
            _srow("sess_new", updated=_MS + 5_000),
        )
        out = _mod._collect_raw(db)
        assert out["count"] == 2
        assert [s["session_id"] for s in out["sessions"]] == ["sess_new", "sess_old"]

    def test_missing_store_raises_typed_unavailable(self, tmp_path: Path) -> None:
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._collect_raw(tmp_path / "nope.sqlite")
        assert ei.value.code == "source_unavailable"

    def test_corrupt_file_raises_typed_malformed(self, tmp_path: Path) -> None:
        db = tmp_path / "store.sqlite"
        db.write_bytes(b"definitely not a sqlite database file")
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._collect_raw(db)
        assert ei.value.code == "source_malformed"

    def test_missing_table_raises_typed_malformed(self, tmp_path: Path) -> None:
        db = tmp_path / "store.sqlite"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE other (x TEXT)")
        con.close()
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._collect_raw(db)
        assert ei.value.code == "source_malformed"

    def test_runner_slot_accepted_and_ignored(self, tmp_path: Path) -> None:
        """消費端呼叫相容（inflight_snapshot 位置參數傳 callable）——遺留槽
        值被忽略、源照走 store 注入。"""
        db = _store(tmp_path, _srow())

        def legacy_runner(cmd: list[str], **kwargs: object) -> str:
            raise AssertionError("harness-native 源不得經 runner 呼叫命令")

        out = _mod.collect_rows(legacy_runner, sidecar=tmp_path / "l.json", db_path=db)
        assert out["count"] == 1


# ---------------------------------------------------------------------------
# 源映射（harness 恆定／時間單位／archived 推導／subagent 排除）
# ---------------------------------------------------------------------------


class TestScanMapping:
    def test_harness_constant_and_workspace_and_title(self, tmp_path: Path) -> None:
        db = _store(tmp_path, _srow(title="my title"))
        session = _mod._collect_raw(db)["sessions"][0]
        assert session["harness"] == "zcode"
        assert session["workspace_root"] == WS
        assert session["name"] == "my title"  # title → label fallback 源

    def test_ms_to_us_conversion(self, tmp_path: Path) -> None:
        db = _store(tmp_path, _srow(created=_MS, updated=_MS + 90_000))
        session = _mod._collect_raw(db)["sessions"][0]
        assert session["created_at_us"] == _MS * 1_000
        assert session["last_seen_us"] == (_MS + 90_000) * 1_000

    def test_archived_derives_ended_liveness_and_status(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_live1"),
            _srow("sess_dead1", archived=_MS + 9_000),
        )
        sessions = {s["session_id"]: s for s in _mod._collect_raw(db)["sessions"]}
        assert sessions["sess_live1"]["observed_liveness"] == "live"
        assert sessions["sess_live1"]["status"] == "active"
        assert sessions["sess_dead1"]["observed_liveness"] == "ended"
        assert sessions["sess_dead1"]["status"] == "ended"

    def test_subagent_child_excluded(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_main"),
            _srow("sess_subagent_agent_x", task_type="subagent_child"),
            _srow("sess_forked", task_type="fork"),  # 非 subagent 照收
        )
        out = _mod._collect_raw(db)
        assert out["count"] == 2
        assert [s["session_id"] for s in out["sessions"]] == [
            "sess_forked",
            "sess_main",
        ]

    def test_null_timestamps_map_to_none(self, tmp_path: Path) -> None:
        db = _store(tmp_path, _srow("sess_nots", created=None, updated=None))
        session = _mod._collect_raw(db)["sessions"][0]
        assert session["created_at_us"] is None
        assert session["last_seen_us"] is None


# ---------------------------------------------------------------------------
# 正規化 rows＋label 合併
# ---------------------------------------------------------------------------


class TestNormalizeRows:
    def test_row_shape_eight_keys_full_session_id(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            sidecar=tmp_path / "labels.json", db_path=_store(tmp_path, _srow("sess_aaa-0001", title="t"))
        )
        assert out["count"] == 1
        assert out["registry_total"] == 1
        assert out["coverage"] == "zcode-only"
        row = out["rows"][0]
        assert set(row) == {
            "session_id",
            "harness",
            "workspace_root",
            "label",
            "liveness",
            "status",
            "last_seen_iso",
            "age_min",
        }
        assert row["session_id"] == "sess_aaa-0001"  # 全碼不截斷
        assert row["harness"] == "zcode"
        assert row["workspace_root"] == WS
        assert row["liveness"] == "live"
        assert row["status"] == "active"
        assert isinstance(row["last_seen_iso"], str)

    def test_label_merge_sidecar_wins_over_store_title(
        self, tmp_path: Path
    ) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_aaa-0001", "seam-label", sidecar=sidecar)
        out = _mod.collect_rows(
            sidecar=sidecar, db_path=_store(tmp_path, _srow(title="store-title"))
        )
        assert out["rows"][0]["label"] == "seam-label"

    def test_label_merge_falls_back_to_store_title(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            sidecar=tmp_path / "labels.json",
            db_path=_store(tmp_path, _srow(title="store-title")),
        )
        assert out["rows"][0]["label"] == "store-title"

    def test_label_null_when_neither_source(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            sidecar=tmp_path / "labels.json",
            db_path=_store(tmp_path, _srow(title=None)),
        )
        assert out["rows"][0]["label"] is None

    def test_age_from_last_seen_fallback(self, tmp_path: Path) -> None:
        recent_ms = (time.time() - 610) * 1_000
        rows = {
            r["session_id"]: r
            for r in _mod.collect_rows(
                sidecar=tmp_path / "labels.json",
                db_path=_store(
                    tmp_path,
                    _srow("sess_age-2", updated=recent_ms),
                    _srow("sess_age-3", created=None, updated=None),
                ),
            )["rows"]
        }
        assert rows["sess_age-2"]["age_min"] == 10  # 缺 age 以 last_seen 推算
        assert rows["sess_age-3"]["age_min"] is None  # 無任何時間源

    def test_last_seen_iso_none_when_missing(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            sidecar=tmp_path / "labels.json",
            db_path=_store(tmp_path, _srow(updated=None)),
        )
        assert out["rows"][0]["last_seen_iso"] is None

    def test_normalize_null_coercion_non_string_fields(self) -> None:
        row = _mod._normalize(
            {
                "session_id": "sess_x",
                "harness": 123,
                "workspace_root": None,
                "name": 7,
                "observed_liveness": 4.5,
                "status": b"raw",
                "last_seen_us": None,
            },
            {},
        )
        assert row["harness"] is None
        assert row["workspace_root"] is None
        assert row["label"] is None
        assert row["liveness"] is None
        assert row["status"] is None
        assert row["last_seen_iso"] is None

    def test_empty_sid_row_skipped_but_counted(self, tmp_path: Path) -> None:
        db = _store(tmp_path, _srow("sess_ok"), _srow(""))
        out = _mod.collect_rows(sidecar=tmp_path / "labels.json", db_path=db)
        assert out["count"] == 1
        assert out["rows"][0]["session_id"] == "sess_ok"
        assert out["registry_total"] == 2  # 掃描總數含跳過列


# ---------------------------------------------------------------------------
# --live 過濾（現行雜訊排除語義保留）
# ---------------------------------------------------------------------------


class TestLiveFilter:
    def test_live_filter_keeps_only_live_sess_prefix(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_ok-1"),
            _srow("064b2c7b-uuid-noise"),
            _srow("sess_dead-1", archived=_MS + 9_000),
            _srow("sess_sub_x", task_type="subagent_child"),
        )
        out = _mod.collect_rows(
            sidecar=tmp_path / "labels.json", live_only=True, db_path=db
        )
        assert [r["session_id"] for r in out["rows"]] == ["sess_ok-1"]
        assert out["registry_total"] == 3  # subagent_child 源頭即不列


# ---------------------------------------------------------------------------
# find（harness＋workspace_root → 最新一列；禁猜；覆蓋邊界 typed）
# ---------------------------------------------------------------------------


class TestFindSession:
    def test_unique_newest_by_time_updated(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_old", updated=_MS),
            _srow("sess_new", updated=_MS + 200_000),
            _srow("sess_other_ws", updated=_MS + 999_000, ws="/other"),
        )
        row = _mod.find_session(
            harness="zcode",
            workspace_root=WS,
            sidecar=tmp_path / "labels.json",
            db_path=db,
        )
        assert row["session_id"] == "sess_new"

    def test_fallback_time_created_when_updated_missing(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_a", created=_MS, updated=None),
            _srow("sess_b", created=_MS + 100, updated=None),
        )
        row = _mod.find_session(
            harness="zcode",
            workspace_root=WS,
            sidecar=tmp_path / "labels.json",
            db_path=db,
        )
        assert row["session_id"] == "sess_b"

    def test_no_match_raises_typed(self, tmp_path: Path) -> None:
        db = _store(tmp_path, _srow())
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.find_session(
                harness="zcode",
                workspace_root="/nope",
                sidecar=tmp_path / "labels.json",
                db_path=db,
            )
        assert ei.value.code == "no-match"
        assert "zcode-only" not in ei.value.message  # zcode 查詢不帶覆蓋註記

    def test_out_of_coverage_harness_no_match_with_coverage_note(
        self, tmp_path: Path
    ) -> None:
        """覆蓋邊界如實聲明：非 zcode harness＝no-match typed＋覆蓋註記。"""
        db = _store(tmp_path, _srow())
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.find_session(
                harness="codex",
                workspace_root=WS,
                sidecar=tmp_path / "labels.json",
                db_path=db,
            )
        assert ei.value.code == "no-match"
        assert "zcode-only" in ei.value.message

    def test_tied_candidates_raise_ambiguous(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_a", updated=_MS + 300),
            _srow("sess_b", updated=_MS + 300),
        )
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.find_session(
                harness="zcode",
                workspace_root=WS,
                sidecar=tmp_path / "labels.json",
                db_path=db,
            )
        assert ei.value.code == "ambiguous"

    def test_single_candidate_without_timestamps_is_unique(
        self, tmp_path: Path
    ) -> None:
        db = _store(tmp_path, _srow("sess_only", created=None, updated=None))
        row = _mod.find_session(
            harness="zcode",
            workspace_root=WS,
            sidecar=tmp_path / "labels.json",
            db_path=db,
        )
        assert row["session_id"] == "sess_only"

    def test_winner_label_merged_from_sidecar(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_new", "tagged", sidecar=sidecar)
        db = _store(
            tmp_path,
            _srow("sess_old", updated=_MS),
            _srow("sess_new", updated=_MS + 200),
        )
        row = _mod.find_session(
            harness="zcode",
            workspace_root=WS,
            sidecar=sidecar,
            db_path=db,
        )
        assert row["label"] == "tagged"


# ---------------------------------------------------------------------------
# label sidecar（seam 自有 display metadata；絕不寫源 store）
# ---------------------------------------------------------------------------


class TestLabelSidecar:
    def test_set_then_get_roundtrip_creates_nested_path(
        self, tmp_path: Path
    ) -> None:
        sidecar = tmp_path / "sub" / "labels.json"
        assert _mod.set_label("sess_x", "first", sidecar=sidecar) == "first"
        assert _mod.get_label("sess_x", sidecar=sidecar) == "first"

    def test_set_is_idempotent_overwrite_single_entry(
        self, tmp_path: Path
    ) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_x", "one", sidecar=sidecar)
        _mod.set_label("sess_x", "two", sidecar=sidecar)
        assert _mod.get_label("sess_x", sidecar=sidecar) == "two"
        on_disk = json.loads(sidecar.read_text(encoding="utf-8"))
        assert list(on_disk) == ["sess_x"]
        assert set(on_disk["sess_x"]) == {"label", "updated_at"}

    def test_updated_at_is_iso8601(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_x", "v", sidecar=sidecar)
        on_disk = json.loads(sidecar.read_text(encoding="utf-8"))
        datetime.fromisoformat(on_disk["sess_x"]["updated_at"])  # 不炸即 ISO

    def test_file_0600_dir_0700_owner_only(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_x", "v", sidecar=sidecar)
        assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600
        assert stat.S_IMODE(sidecar.parent.stat().st_mode) == 0o700

    def test_atomic_write_no_tmp_residue(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_x", "v1", sidecar=sidecar)
        _mod.set_label("sess_x", "v2", sidecar=sidecar)
        assert list(sidecar.parent.glob("*.tmp")) == []

    def test_get_missing_raises_typed(self, tmp_path: Path) -> None:
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.get_label("sess_ghost", sidecar=tmp_path / "labels.json")
        assert ei.value.code == "label_not_found"

    @pytest.mark.parametrize("bad", ["", "   ", "x" * 65])
    def test_invalid_label_rejected_before_write(
        self, bad: str, tmp_path: Path
    ) -> None:
        sidecar = tmp_path / "labels.json"
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.set_label("sess_x", bad, sidecar=sidecar)
        assert ei.value.code == "invalid_label"
        assert not sidecar.exists()  # 驗證先於寫入

    @pytest.mark.parametrize("ok", ["a", "x" * 64])
    def test_label_length_boundaries_accepted(
        self, ok: str, tmp_path: Path
    ) -> None:
        _mod.set_label("sess_x", ok, sidecar=tmp_path / "labels.json")
        assert _mod.get_label("sess_x", sidecar=tmp_path / "labels.json") == ok

    def test_malformed_sidecar_get_label_degrades_not_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """U8：sidecar 壞 JSON → _load_labels 降級 {}＋stderr 一行註記——
        get_label 落 label_not_found（typed exit 3），不擋發現主功能。"""
        sidecar = tmp_path / "labels.json"
        sidecar.write_text("{not json", encoding="utf-8")
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.get_label("sess_x", sidecar=sidecar)
        assert ei.value.code == "label_not_found"
        assert "label sidecar" in capsys.readouterr().err

    def test_malformed_sidecar_rows_still_out_labels_null(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """U8：display metadata 損壞不擋 address 發現（EP 原則 2 附屬性）
        ——rows 照出、label 全 null＋stderr 一行註記。"""
        sidecar = tmp_path / "labels.json"
        sidecar.write_text("{not json", encoding="utf-8")
        data = _mod.collect_rows(
            sidecar=sidecar, db_path=_store(tmp_path, _srow())
        )
        assert data["count"] == 1
        assert data["rows"][0]["session_id"] == "sess_aaa-0001"
        assert data["rows"][0]["label"] is None
        assert "label sidecar" in capsys.readouterr().err

    def test_label_set_heals_corrupt_sidecar(self, tmp_path: Path) -> None:
        """U8：CLI label set 對壞檔＝覆寫自癒（壞內容不留殘）。"""
        sidecar = tmp_path / "labels.json"
        sidecar.write_text("{not json", encoding="utf-8")
        assert _mod.set_label("sess_x", "healed", sidecar=sidecar) == "healed"
        on_disk = json.loads(sidecar.read_text(encoding="utf-8"))
        assert on_disk["sess_x"]["label"] == "healed"

    def test_env_var_overrides_default_sidecar_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        env_path = tmp_path / "env" / "labels.json"
        monkeypatch.setenv(_mod.LABELS_ENV, str(env_path))
        assert _mod._default_sidecar_path() == env_path
        _mod.set_label("sess_env", "via-env")
        assert _mod.get_label("sess_env") == "via-env"


# ---------------------------------------------------------------------------
# whoami（cwd→workspace 對照；typed fail-closed）
# ---------------------------------------------------------------------------


class TestWhoami:
    def test_cwd_workspace_match_returns_identity(self, tmp_path: Path) -> None:
        db = _store(
            tmp_path,
            _srow("sess_old", updated=_MS),
            _srow("sess_me", updated=_MS + 500),
        )
        identity = _mod._whoami_raw(db, cwd=WS)
        assert identity == {
            "session_id": "sess_me",
            "harness": "zcode",
            "workspace_root": WS,
        }

    def test_symlinked_cwd_resolved_before_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real = tmp_path / "real-ws"
        real.mkdir()
        link = tmp_path / "link-ws"
        link.symlink_to(real)
        db = _store(tmp_path, _srow("sess_in_real", ws=str(real)))
        identity = _mod._whoami_raw(db, cwd=str(link))
        assert identity["session_id"] == "sess_in_real"

    def test_no_match_raises_typed_unavailable(self, tmp_path: Path) -> None:
        db = _store(tmp_path, _srow(ws="/elsewhere"))
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._whoami_raw(db, cwd=WS)
        assert ei.value.code == "whoami_unavailable"

    def test_missing_store_raises_typed_unavailable(self, tmp_path: Path) -> None:
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._whoami_raw(tmp_path / "nope.sqlite", cwd=WS)
        assert ei.value.code == "whoami_unavailable"

    def test_corrupt_store_raises_typed_malformed(self, tmp_path: Path) -> None:
        db = tmp_path / "store.sqlite"
        db.write_bytes(b"not a db")
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._whoami_raw(db, cwd=WS)
        assert ei.value.code == "whoami_malformed"

    def test_newest_row_missing_id_raises_typed_malformed(
        self, tmp_path: Path
    ) -> None:
        db = _store(tmp_path, _srow("", updated=_MS + 999))
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._whoami_raw(db, cwd=WS)
        assert ei.value.code == "whoami_malformed"


# ---------------------------------------------------------------------------
# CLI 面（exit 0＝ok；3＝typed failure——stderr 統一 envelope、stdout 空）
# ---------------------------------------------------------------------------


class TestCli:
    def test_list_live_json_shape(self, tmp_path: Path, capsys) -> None:
        rc = _mod.main(
            ["list", "--live", "--json", "--labels-file", str(tmp_path / "labels.json")],
            db_path=_store(tmp_path, _srow()),
        )
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert set(data) == {
            "generated_at",
            "rows",
            "count",
            "registry_total",
            "coverage",
        }
        assert data["count"] == 1
        assert data["coverage"] == "zcode-only"

    def test_list_markdown_table_with_source_footer(
        self, tmp_path: Path, capsys
    ) -> None:
        rc = _mod.main(
            ["list", "--labels-file", str(tmp_path / "labels.json")],
            db_path=_store(tmp_path, _srow(title="store-title")),
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "| session_id |" in out
        assert "sess_aaa-0001" in out
        assert "store-title" in out
        assert "zcode-only" in out  # 覆蓋邊界如實聲明

    def test_find_json_ok_true_with_row(self, tmp_path: Path, capsys) -> None:
        db = _store(
            tmp_path,
            _srow("sess_old", updated=_MS),
            _srow("sess_new", updated=_MS + 200),
        )
        rc = _mod.main(
            [
                "find",
                "--harness",
                "zcode",
                "--workspace-root",
                WS,
                "--json",
                "--labels-file",
                str(tmp_path / "labels.json"),
            ],
            db_path=db,
        )
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["row"]["session_id"] == "sess_new"

    def test_find_failure_envelope_exit3_stdout_empty(
        self, tmp_path: Path, capsys
    ) -> None:
        db = _store(tmp_path, _srow())
        rc = _mod.main(
            [
                "find",
                "--harness",
                "zcode",
                "--workspace-root",
                "/nope",
                "--json",
                "--labels-file",
                str(tmp_path / "labels.json"),
            ],
            db_path=db,
        )
        assert rc == 3
        captured = capsys.readouterr()
        assert captured.out == ""
        err = json.loads(captured.err)
        assert err == {
            "schemaVersion": 1,
            "ok": False,
            "error": {"code": "no-match", "message": err["error"]["message"]},
        }

    def test_source_missing_exit3_envelope_stdout_empty(
        self, tmp_path: Path, capsys
    ) -> None:
        """源缺席 fail-closed：exit 3 typed envelope（AIR-272 契約零變）。"""
        rc = _mod.main(
            ["list", "--json"], db_path=tmp_path / "nope.sqlite"
        )
        assert rc == 3
        captured = capsys.readouterr()
        assert captured.out == ""
        err = json.loads(captured.err)
        assert err["schemaVersion"] == 1
        assert err["ok"] is False
        assert err["error"]["code"] == "source_unavailable"

    def test_whoami_cli_workspace_match(self, tmp_path: Path, capsys, monkeypatch) -> None:
        ws_dir = tmp_path / "ws"
        ws_dir.mkdir()
        db = _store(tmp_path, _srow("sess_cli_me", ws=str(ws_dir)))
        monkeypatch.chdir(ws_dir)
        rc = _mod.main(["whoami"], db_path=db)
        assert rc == 0
        identity = json.loads(capsys.readouterr().out)
        assert identity["session_id"] == "sess_cli_me"
        assert identity["harness"] == "zcode"

    def test_whoami_cli_no_match_exit3_envelope(
        self, tmp_path: Path, capsys, monkeypatch
    ) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        db = _store(tmp_path, _srow(ws="/elsewhere"))
        monkeypatch.chdir(empty)
        rc = _mod.main(["whoami"], db_path=db)
        assert rc == 3
        captured = capsys.readouterr()
        assert captured.out == ""
        assert json.loads(captured.err)["error"]["code"] == "whoami_unavailable"

    def test_label_set_get_cli_roundtrip(
        self, tmp_path: Path, capsys
    ) -> None:
        sidecar = str(tmp_path / "labels.json")
        rc = _mod.main(
            [
                "label",
                "set",
                "--session-id",
                "sess_cli",
                "--label",
                "cli-probe",
                "--labels-file",
                sidecar,
            ]
        )
        assert rc == 0
        assert "cli-probe" in capsys.readouterr().out
        rc = _mod.main(
            ["label", "get", "--session-id", "sess_cli", "--labels-file", sidecar]
        )
        assert rc == 0
        assert capsys.readouterr().out.strip() == "cli-probe"

    def test_label_get_missing_exit3_envelope(
        self, tmp_path: Path, capsys
    ) -> None:
        rc = _mod.main(
            [
                "label",
                "get",
                "--session-id",
                "sess_ghost",
                "--labels-file",
                str(tmp_path / "labels.json"),
            ]
        )
        assert rc == 3
        captured = capsys.readouterr()
        assert captured.out == ""
        assert json.loads(captured.err)["error"]["code"] == "label_not_found"

    def test_label_set_invalid_exit3_envelope(
        self, tmp_path: Path, capsys
    ) -> None:
        rc = _mod.main(
            [
                "label",
                "set",
                "--session-id",
                "sess_cli",
                "--label",
                "x" * 65,
                "--labels-file",
                str(tmp_path / "labels.json"),
            ]
        )
        assert rc == 3
        captured = capsys.readouterr()
        assert captured.out == ""
        assert json.loads(captured.err)["error"]["code"] == "invalid_label"

    def test_help_exits_zero(self, capsys) -> None:
        with pytest.raises(SystemExit) as ei:
            _mod.main(["--help"])
        assert ei.value.code == 0
        assert "session" in capsys.readouterr().out
