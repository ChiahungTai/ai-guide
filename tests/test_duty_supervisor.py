"""supervisor 契約測試（AIR-287——db-99：停滯觀測→health alert→escalation
條件→人類 intervention item）。

涵蓋：
- 停滯偵測：received／processing 且 updated_at_us 距 now 超
  DEFAULT_STALE_THRESHOLD_US（24h 具名常數）→ alert 行（address、
  envelope_id、state、年齡人類可讀）；fresh／handled／needs-human／
  failed → 不 alert（needs-human／failed 是已分流狀態非停滯）。
- escalation：alert 持續（同一停滯項 first_alert_at_us 距 now ≥
  DEFAULT_ESCALATION_AFTER_US＝48h）→ escalation state 記錄＋
  intervention-items.md 落檔清單（人類可讀）；未達門檻→只 alert 不
  escalate；項目回復（handled）→ escalation state 清除＋清單重生成。
- 唯讀觀測面：scan 前後 address 目錄所有檔零變（content＋mtime）——
  supervisor 只寫 _meta/ 下自己的觀測檔。
- crash-only：address 目錄內壞 ledger 檔＝typed 錯誤整掃拒行（同
  duty_disposition 裁定——見 test_duty_disposition）；supervisor 自身
  state 檔壞＝typed 錯誤（觀測權威檔 fail-closed）。
- _meta/ 不入掃描；空 ledger＝clean report。
- CLI：--json 機讀輸出、--report 落檔、exit 0 成功／1 typed 錯誤／
  2 args 誤用。
"""

import json
import os

import pytest
from conftest import load_module

mod = load_module("scripts/duty_supervisor.py")
dd = load_module("scripts/duty_disposition.py")

ADDR = "ai-guide-marshal"
EID = "018f-aaa"
HOUR_US = 3_600 * 1_000_000
NOW = 100 * 24 * HOUR_US  # 固定 now（第 100 天）


def _seed(address, eid, state, updated_us, base_dir, session_id="s",
          correlation_id=None):
    if state == "received":
        dd.set(address, eid, "received", session_id=session_id,
               correlation_id=correlation_id, now_us=updated_us,
               base_dir=str(base_dir))
    else:
        # 直達非初始態：received 起手再轉目標態（時間戳＝updated_us）
        dd.set(address, eid, "received", session_id=session_id,
               correlation_id=correlation_id,
               now_us=updated_us - 1, base_dir=str(base_dir))
        dd.set(address, eid, state, session_id=session_id,
               now_us=updated_us, base_dir=str(base_dir))


def _snapshot(root):
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            st = os.stat(p)
            with open(p, "rb") as fh:
                out[p] = (fh.read(), st.st_mtime_ns)
    return out


# ── 停滯偵測 ─────────────────────────────────────────────────────────


def test_no_records_clean_report(tmp_path):
    (tmp_path / ADDR).mkdir()
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert result.stale_items == []
    assert result.escalated == []
    assert any("clean" in line.lower() for line in result.report_lines)


def test_old_received_alerts_with_readable_line(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert len(result.stale_items) == 1
    item = result.stale_items[0]
    assert (item["address"], item["envelope_id"], item["state"]) == (
        ADDR, EID, "received",
    )
    joined = "\n".join(result.report_lines)
    assert ADDR in joined and EID in joined
    assert "25" in joined  # 年齡小時人類可讀


def test_fresh_received_no_alert(tmp_path):
    _seed(ADDR, EID, "received", NOW - 1 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert result.stale_items == []


def test_exactly_threshold_not_stale(tmp_path):
    _seed(ADDR, EID, "received", NOW - mod.DEFAULT_STALE_THRESHOLD_US,
          tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert result.stale_items == []  # 超過才 stale（>，非 ≥）


def test_handled_and_needs_human_not_stale(tmp_path):
    _seed(ADDR, "old-handled", "handled", NOW - 100 * HOUR_US, tmp_path)
    _seed(ADDR, "old-nh", "needs-human", NOW - 100 * HOUR_US, tmp_path)
    _seed(ADDR, "old-failed", "failed", NOW - 100 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert result.stale_items == []


def test_processing_old_alerts(tmp_path):
    _seed(ADDR, EID, "processing", NOW - 30 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert [i["state"] for i in result.stale_items] == ["processing"]


def test_multi_address_scan_skips_meta(tmp_path):
    (tmp_path / "_meta").mkdir()
    (tmp_path / "_meta" / "junk.json").write_text("{bad", encoding="utf-8")
    _seed("addr-a", "e-1", "received", NOW - 30 * HOUR_US, tmp_path)
    _seed("addr-b", "e-2", "processing", NOW - 30 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert sorted(i["address"] for i in result.stale_items) == [
        "addr-a", "addr-b",
    ]


# ── escalation（alert 持續→人類 intervention item）───────────────────


def test_first_alert_no_escalation(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert result.escalated == []
    assert not (tmp_path / "_meta" / "intervention-items.md").exists()


def test_persistent_alert_escalates_after_threshold(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    mod.supervise(str(tmp_path), now_us=NOW)  # 第一次 alert（first_alert=NOW）
    later = NOW + 49 * HOUR_US  # alert 持續 49h ≥ 48h 門檻
    result = mod.supervise(str(tmp_path), now_us=later)
    assert len(result.escalated) == 1
    assert result.escalated[0]["envelope_id"] == EID
    md = (tmp_path / "_meta" / "intervention-items.md").read_text(
        encoding="utf-8",
    )
    assert EID in md and ADDR in md
    state = json.loads(
        (tmp_path / "_meta" / "supervisor-escalations.json").read_text(
            encoding="utf-8",
        )
    )
    entry = state["items"][f"{ADDR}/{EID}"]
    assert entry["escalated_at_us"] == later
    assert entry["first_alert_at_us"] == NOW


def test_alert_not_persistent_long_enough_no_escalation(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    mod.supervise(str(tmp_path), now_us=NOW)
    result = mod.supervise(str(tmp_path), now_us=NOW + 47 * HOUR_US)
    assert result.escalated == []


def test_resolved_item_cleared_from_escalation_and_list(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    mod.supervise(str(tmp_path), now_us=NOW)
    later = NOW + 49 * HOUR_US
    mod.supervise(str(tmp_path), now_us=later)  # escalated
    dd.set(ADDR, EID, "processing", session_id="human",
           now_us=later + HOUR_US, base_dir=str(tmp_path))
    result = mod.supervise(str(tmp_path), now_us=later + 2 * HOUR_US)
    assert result.escalated == []
    # 清單檔語義：存在＝有未決 intervention——resolved＝檔移除
    assert not (tmp_path / "_meta" / "intervention-items.md").exists()


# ── 唯讀觀測面＋crash-only ───────────────────────────────────────────


def test_scan_never_touches_address_dirs(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    before = _snapshot(str(tmp_path / ADDR))
    mod.supervise(str(tmp_path), now_us=NOW)
    assert _snapshot(str(tmp_path / ADDR)) == before


def test_corrupt_ledger_file_fails_closed(tmp_path):
    (tmp_path / ADDR).mkdir()
    (tmp_path / ADDR / "bad.json").write_text("{nope", encoding="utf-8")
    # 類別取 mod.dd 實例（supervisor 內部載入的 module instance——
    # except 面看後者；house 慣例同 test_duty_receive._hook_err）。
    with pytest.raises(mod.dd.LedgerCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


def test_corrupt_supervisor_state_fails_closed(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    meta = tmp_path / "_meta"
    meta.mkdir()
    (meta / "supervisor-escalations.json").write_text(
        "not-json", encoding="utf-8",
    )
    with pytest.raises(mod.SupervisorStateCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


# ── CLI 面 ───────────────────────────────────────────────────────────


def test_cli_json_and_report_file(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    report = tmp_path / "report.txt"
    rc = mod.main([
        "scan", "--base-dir", str(tmp_path), "--now-us", str(NOW),
        "--json", "--report", str(report),
    ])
    assert rc == 0
    assert report.exists()


def test_cli_typed_error_exit_1(tmp_path):
    (tmp_path / ADDR).mkdir()
    (tmp_path / ADDR / "bad.json").write_text("{nope", encoding="utf-8")
    rc = mod.main([
        "scan", "--base-dir", str(tmp_path), "--now-us", str(NOW),
    ])
    assert rc == 1


def test_cli_missing_arg_exit_2():
    with pytest.raises(SystemExit) as exc:
        mod.main([])
    assert exc.value.code == 2
