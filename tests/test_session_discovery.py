"""session_discovery seam 契約測試（AIR-254.1）.

驗證式（lite 寫的測試＝規格陳述，驗收證據由 full 複驗）：
- 單一 choke point：`_collect_raw` 是唯一 `scbus list` 呼叫點（runner
  注入 fake，不依賴真機 scbus）；失敗 raise typed DiscoveryError（CLI
  層轉 exit 3 統一 envelope）。
- 正規化 rows 八欄形狀（session_id 全碼／harness／workspace_root／label
  ／liveness／status／last_seen_iso／age_min）；label 合併＝sidecar 優先、
  無 sidecar 用 scbus name、皆無＝null。
- `--live` 過濾＝liveness=="live" 且 `sess_` 前綴（inflight 現行雜訊
  排除語義保留——UUID 與 scbus-ext-* 幽靈排除；status 不參與過濾）。
- find：同 harness＋workspace_root 取 last_seen_us（缺則 created_at_us）
  最新一列；0 或 >1 候選同分＝typed failure 禁猜。
- label sidecar：形 `{"sid": {"label", "updated_at"}}`、atomic 寫（無
  .tmp 殘留）、檔 0600／目錄 0700；set 冪等覆寫；get 無＝fail；驗證
  1-64 字元非純空白；絕不寫 scbus（介面無任何 registry 寫入路徑）。
- whoami：v1 委派 passthrough；缺席／非零 exit／壞 JSON＝typed failure。
- CLI：失敗統一 `{"schemaVersion":1,"ok":false,"error":{code,message}}`
  到 stderr、stdout 空、exit 3。

oracle＝I 級（impl 衍生——契約單一源即 scripts/session_discovery.py
docstring；真機 scbus L4 實跑由 full 複驗）。
"""

import json
import stat
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/session_discovery.py")

WS = "/Users/ctai/Github/ai-guide"


def _sess(sid: str = "sess_aaa-0001", **over: object) -> dict:
    row: dict = {
        "session_id": sid,
        "harness": "zcode",
        "workspace_root": WS,
        "name": None,
        "status": "active",
        "observed_liveness": "live",
        "created_at_us": 1_700_000_000_000_000,
        "last_seen_us": 1_700_000_090_000_000,
    }
    row.update(over)
    return row


def _payload(*sessions: dict, count: int | None = None) -> dict:
    return {
        "count": count if count is not None else len(sessions),
        "status": "ok",
        "sessions": list(sessions),
    }


def _list_runner(payload: dict):
    def run(cmd: list[str], **kwargs: object) -> str:
        assert cmd == ["scbus", "list"], f"非 choke point 命令：{cmd}"
        return json.dumps(payload)

    return run


# ---------------------------------------------------------------------------
# choke point：_collect_raw（v1 來源＝scbus registry 過渡）
# ---------------------------------------------------------------------------


class TestCollectRaw:
    def test_success_returns_parsed_payload(self) -> None:
        out = _mod._collect_raw(_list_runner(_payload(_sess())))
        assert out["count"] == 1
        assert out["sessions"][0]["session_id"] == "sess_aaa-0001"

    def test_missing_binary_raises_typed_unavailable(self) -> None:
        def run(cmd: list[str], **kwargs: object) -> str:
            raise FileNotFoundError("no scbus")

        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._collect_raw(run)
        assert ei.value.code == "source_unavailable"
        assert "scbus" in ei.value.message

    def test_nonzero_exit_raises_typed_unavailable_with_detail(self) -> None:
        def run(cmd: list[str], **kwargs: object) -> str:
            raise subprocess.CalledProcessError(1, cmd, stderr="boom\n")

        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._collect_raw(run)
        assert ei.value.code == "source_unavailable"
        assert "boom" in ei.value.message

    @pytest.mark.parametrize(
        "stdout", ["not json", '{"count": 1}', '{"sessions": "x"}', "[]"]
    )
    def test_malformed_output_raises_typed(self, stdout: str) -> None:
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._collect_raw(lambda cmd, **kw: stdout)
        assert ei.value.code == "source_malformed"


# ---------------------------------------------------------------------------
# 正規化 rows＋label 合併
# ---------------------------------------------------------------------------


class TestNormalizeRows:
    def test_row_shape_eight_keys_full_session_id(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            _list_runner(_payload(_sess(name="sc-name"))),
            sidecar=tmp_path / "labels.json",
        )
        assert out["count"] == 1
        assert out["registry_total"] == 1
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

    def test_label_merge_sidecar_wins_over_scbus_name(
        self, tmp_path: Path
    ) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_aaa-0001", "seam-label", sidecar=sidecar)
        out = _mod.collect_rows(
            _list_runner(_payload(_sess(name="sc-name"))), sidecar=sidecar
        )
        assert out["rows"][0]["label"] == "seam-label"

    def test_label_merge_falls_back_to_scbus_name(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            _list_runner(_payload(_sess(name="sc-name"))),
            sidecar=tmp_path / "labels.json",
        )
        assert out["rows"][0]["label"] == "sc-name"

    def test_label_null_when_neither_source(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            _list_runner(_payload(_sess(name=None))),
            sidecar=tmp_path / "labels.json",
        )
        assert out["rows"][0]["label"] is None

    def test_age_from_age_seconds_then_last_seen_fallback(
        self, tmp_path: Path
    ) -> None:
        payload = _payload(
            _sess(sid="sess_age-1", age=900),
            _sess(sid="sess_age-2", last_seen_us=(time.time() - 610) * 1_000_000),
            _sess(sid="sess_age-3", last_seen_us=None, created_at_us=None),
        )
        rows = {
            r["session_id"]: r
            for r in _mod.collect_rows(
                _list_runner(payload), sidecar=tmp_path / "labels.json"
            )["rows"]
        }
        assert rows["sess_age-1"]["age_min"] == 15  # age 秒 → 分
        assert rows["sess_age-2"]["age_min"] == 10  # 缺 age 以 last_seen 推算
        assert rows["sess_age-3"]["age_min"] is None  # 無任何時間源

    def test_last_seen_iso_none_when_missing(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            _list_runner(_payload(_sess(last_seen_us=None))),
            sidecar=tmp_path / "labels.json",
        )
        assert out["rows"][0]["last_seen_iso"] is None

    def test_null_coercion_non_string_fields(self, tmp_path: Path) -> None:
        out = _mod.collect_rows(
            _list_runner(
                _payload(
                    _sess(
                        harness=None, workspace_root=None, status=None,
                        observed_liveness=None,
                    )
                )
            ),
            sidecar=tmp_path / "labels.json",
        )
        row = out["rows"][0]
        assert row["harness"] is None
        assert row["workspace_root"] is None
        assert row["status"] is None
        assert row["liveness"] is None

    def test_non_dict_and_empty_sid_rows_skipped(self, tmp_path: Path) -> None:
        payload = _payload("noise", {"session_id": ""}, _sess(), count=4)
        out = _mod.collect_rows(
            _list_runner(payload), sidecar=tmp_path / "labels.json"
        )
        assert out["count"] == 1
        assert out["registry_total"] == 4


# ---------------------------------------------------------------------------
# --live 過濾（現行雜訊排除語義保留）
# ---------------------------------------------------------------------------


class TestLiveFilter:
    def test_live_filter_keeps_only_live_sess_prefix(
        self, tmp_path: Path
    ) -> None:
        payload = _payload(
            _sess(sid="sess_ok-1"),
            _sess(sid="064b2c7b-uuid-noise"),
            _sess(sid="scbus-ext-ghost"),
            _sess(sid="sess_dead-1", observed_liveness="ended"),
            _sess(sid="sess_live-2", status="ended", observed_liveness="live"),
            count=5,
        )
        out = _mod.collect_rows(
            _list_runner(payload), sidecar=tmp_path / "labels.json", live_only=True
        )
        # status 不參與過濾——liveness=live 的 sess_* 照收（現行語義）
        assert [r["session_id"] for r in out["rows"]] == [
            "sess_ok-1",
            "sess_live-2",
        ]
        assert out["registry_total"] == 5


# ---------------------------------------------------------------------------
# find（harness＋workspace_root → 最新一列；禁猜）
# ---------------------------------------------------------------------------


class TestFindSession:
    def test_unique_newest_by_last_seen_us(self, tmp_path: Path) -> None:
        payload = _payload(
            _sess(sid="sess_old", last_seen_us=100),
            _sess(sid="sess_new", last_seen_us=200),
            _sess(sid="sess_other_ws", last_seen_us=999, workspace_root="/other"),
            _sess(sid="sess_other_h", last_seen_us=999, harness="codex"),
        )
        row = _mod.find_session(
            _list_runner(payload),
            harness="zcode",
            workspace_root=WS,
            sidecar=tmp_path / "labels.json",
        )
        assert row["session_id"] == "sess_new"

    def test_fallback_created_at_us_when_last_seen_missing(
        self, tmp_path: Path
    ) -> None:
        payload = _payload(
            _sess(sid="sess_a", last_seen_us=None, created_at_us=100),
            _sess(sid="sess_b", last_seen_us=None, created_at_us=200),
        )
        row = _mod.find_session(
            _list_runner(payload),
            harness="zcode",
            workspace_root=WS,
            sidecar=tmp_path / "labels.json",
        )
        assert row["session_id"] == "sess_b"

    def test_no_match_raises_typed(self, tmp_path: Path) -> None:
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.find_session(
                _list_runner(_payload(_sess())),
                harness="zcode",
                workspace_root="/nope",
                sidecar=tmp_path / "labels.json",
            )
        assert ei.value.code == "no-match"

    def test_tied_candidates_raise_ambiguous(self, tmp_path: Path) -> None:
        payload = _payload(
            _sess(sid="sess_a", last_seen_us=300),
            _sess(sid="sess_b", last_seen_us=300),
        )
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod.find_session(
                _list_runner(payload),
                harness="zcode",
                workspace_root=WS,
                sidecar=tmp_path / "labels.json",
            )
        assert ei.value.code == "ambiguous"

    def test_single_candidate_without_timestamps_is_unique(
        self, tmp_path: Path
    ) -> None:
        payload = _payload(
            _sess(sid="sess_only", last_seen_us=None, created_at_us=None)
        )
        row = _mod.find_session(
            _list_runner(payload),
            harness="zcode",
            workspace_root=WS,
            sidecar=tmp_path / "labels.json",
        )
        assert row["session_id"] == "sess_only"

    def test_winner_label_merged_from_sidecar(self, tmp_path: Path) -> None:
        sidecar = tmp_path / "labels.json"
        _mod.set_label("sess_new", "tagged", sidecar=sidecar)
        payload = _payload(
            _sess(sid="sess_old", last_seen_us=100),
            _sess(sid="sess_new", last_seen_us=200),
        )
        row = _mod.find_session(
            _list_runner(payload),
            harness="zcode",
            workspace_root=WS,
            sidecar=sidecar,
        )
        assert row["label"] == "tagged"


# ---------------------------------------------------------------------------
# label sidecar（seam 自有 display metadata；絕不寫 scbus）
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
            _list_runner(_payload(_sess())), sidecar=sidecar
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
# whoami（v1 委派 scbus whoami；JSON passthrough）
# ---------------------------------------------------------------------------


class TestWhoami:
    def test_passthrough_parsed_json(self) -> None:
        identity = {"session_id": "sess_me", "workspace_root": WS}

        def run(cmd: list[str], **kwargs: object) -> str:
            assert cmd == ["scbus", "whoami"]
            return json.dumps(identity)

        assert _mod._whoami_raw(run) == identity

    def test_missing_raises_typed(self) -> None:
        def run(cmd: list[str], **kwargs: object) -> str:
            raise FileNotFoundError("no scbus")

        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._whoami_raw(run)
        assert ei.value.code == "whoami_unavailable"

    def test_bad_json_raises_typed(self) -> None:
        with pytest.raises(_mod.DiscoveryError) as ei:
            _mod._whoami_raw(lambda cmd, **kw: "identity_missing: not json")
        assert ei.value.code == "whoami_malformed"


# ---------------------------------------------------------------------------
# CLI 面（exit 0＝ok；3＝typed failure——stderr 統一 envelope、stdout 空）
# ---------------------------------------------------------------------------


class TestCli:
    def test_list_live_json_shape(self, tmp_path: Path, capsys) -> None:
        rc = _mod.main(
            [
                "list",
                "--live",
                "--json",
                "--labels-file",
                str(tmp_path / "labels.json"),
            ],
            runner=_list_runner(_payload(_sess())),
        )
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert set(data) == {"generated_at", "rows", "count", "registry_total"}
        assert data["count"] == 1

    def test_list_markdown_table(self, tmp_path: Path, capsys) -> None:
        rc = _mod.main(
            ["list", "--labels-file", str(tmp_path / "labels.json")],
            runner=_list_runner(_payload(_sess(name="sc-name"))),
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "| session_id |" in out
        assert "sess_aaa-0001" in out
        assert "sc-name" in out

    def test_find_json_ok_true_with_row(self, tmp_path: Path, capsys) -> None:
        payload = _payload(
            _sess(sid="sess_old", last_seen_us=100),
            _sess(sid="sess_new", last_seen_us=200),
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
            runner=_list_runner(payload),
        )
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["row"]["session_id"] == "sess_new"

    def test_find_failure_envelope_exit3_stdout_empty(
        self, tmp_path: Path, capsys
    ) -> None:
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
            runner=_list_runner(_payload(_sess())),
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

    def test_whoami_cli_passthrough(self, capsys) -> None:
        identity = {"session_id": "sess_me", "workspace_root": WS}

        def run(cmd: list[str], **kwargs: object) -> str:
            assert cmd == ["scbus", "whoami"]
            return json.dumps(identity)

        rc = _mod.main(["whoami"], runner=run)
        assert rc == 0
        assert json.loads(capsys.readouterr().out) == identity

    def test_help_exits_zero(self, capsys) -> None:
        with pytest.raises(SystemExit) as ei:
            _mod.main(["--help"])
        assert ei.value.code == 0
        assert "session" in capsys.readouterr().out
