"""supervisor 契約測試（AIR-287——db-99：停滯觀測→health alert→escalation
條件→人類 intervention item）。

涵蓋：
- 停滯偵測：received／processing／needs-human 且 updated_at_us 距 now
  超 DEFAULT_STALE_THRESHOLD_US（24h 具名常數）→ alert 行（address、
  envelope_id、state、年齡人類可讀）；fresh／handled／failed → 不
  alert。needs-human 在監視面（AIR-287 bi 修復——GLM F1：人類介入
  迴圈〔forward→人類結案〕停滯＝電子蹤跡；session 死於 forward 前
  不得恆靜默）；handled／failed 是已分流非停滯。
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


def test_handled_and_failed_not_stale(tmp_path):
    """handled＝終態、failed＝待消費端重試分流——非人類介入迴圈停滯
    （needs-human 已改入監視面——見 test_old_needs_human_alerts）。"""
    _seed(ADDR, "old-handled", "handled", NOW - 100 * HOUR_US, tmp_path)
    _seed(ADDR, "old-failed", "failed", NOW - 100 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert result.stale_items == []


def test_old_needs_human_alerts(tmp_path):
    """needs-human 納入監視面（AIR-287 bi 修復——GLM F1）：人類介入
    迴圈（forward→人類結案）停滯＝電子蹤跡必須在場——session 死於
    forward 前不得恆靜默。"""
    _seed(ADDR, "old-nh", "needs-human", NOW - 100 * HOUR_US, tmp_path)
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert [(i["address"], i["envelope_id"], i["state"])
            for i in result.stale_items] == [(ADDR, "old-nh", "needs-human")]
    joined = "\n".join(result.report_lines)
    assert "needs-human" in joined and "100" in joined


def test_needs_human_persistent_escalates_to_intervention(tmp_path):
    """needs-human alert 持續 > 48h→escalation→intervention-items.md
    落檔（GLM F1 驗證式：seed 舊 needs-human→supervise 不得 0 alert
    ——最貴的靜默失敗有機械防線）。"""
    _seed(ADDR, "stuck-nh", "needs-human", NOW - 100 * HOUR_US, tmp_path)
    mod.supervise(str(tmp_path), now_us=NOW)
    result = mod.supervise(str(tmp_path), now_us=NOW + 49 * HOUR_US)
    assert len(result.escalated) == 1
    assert result.escalated[0]["state"] == "needs-human"
    md = (tmp_path / "_meta" / "intervention-items.md").read_text(
        encoding="utf-8",
    )
    assert "stuck-nh" in md and "needs-human" in md


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


# ── escalation state entry 全驗（AIR-287 bi 修復——codex F3）──────────
#
# 契約：items 每筆 entry 驗完整 schema（恰七鍵）、型別、時間戳（正
# int）、key 一致性（"<address>/<envelope_id>"）；任何壞形＝
# SupervisorStateCorrupt——items.get(key) or {...} 靜默重置＝已
# escalated 項目的持續性證據被洗掉（crash-only 禁）。


def _write_esc_state(tmp_path, items):
    meta = tmp_path / "_meta"
    meta.mkdir(exist_ok=True)
    (meta / "supervisor-escalations.json").write_text(
        json.dumps({"schema_version": 1, "items": items},
                   ensure_ascii=False),
        encoding="utf-8",
    )


def _valid_entry(**overrides):
    entry = {
        "address": ADDR, "envelope_id": EID, "state": "received",
        "first_alert_at_us": NOW - 25 * HOUR_US,
        "last_alert_at_us": NOW - 1 * HOUR_US, "alert_runs": 2,
        "escalated_at_us": None,
    }
    entry.update(overrides)
    return entry


def _key(entry):
    return f"{entry['address']}/{entry['envelope_id']}"


def test_esc_state_valid_entries_still_load(tmp_path):
    """合法 entry（supervise 自身寫出形）照常載入——驗證不誤傷。"""
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    _write_esc_state(tmp_path, {_key(_valid_entry()): _valid_entry()})
    result = mod.supervise(str(tmp_path), now_us=NOW)
    assert len(result.stale_items) == 1
    state = json.loads(
        (tmp_path / "_meta" / "supervisor-escalations.json").read_text(
            encoding="utf-8",
        )
    )
    assert state["items"][f"{ADDR}/{EID}"]["alert_runs"] == 3


def test_esc_state_null_item_fails_closed(tmp_path):
    """items[key]=null 舊碼被 `or {...}` 靜默重置——現須 typed 拒用。"""
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    _write_esc_state(tmp_path, {f"{ADDR}/{EID}": None})
    with pytest.raises(mod.SupervisorStateCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


def test_esc_state_entry_missing_field_fails_closed(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    entry = _valid_entry()
    del entry["first_alert_at_us"]
    _write_esc_state(tmp_path, {f"{ADDR}/{EID}": entry})
    with pytest.raises(mod.SupervisorStateCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


def test_esc_state_entry_extra_field_fails_closed(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    entry = _valid_entry(note="junk")
    _write_esc_state(tmp_path, {f"{ADDR}/{EID}": entry})
    with pytest.raises(mod.SupervisorStateCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("first_alert_at_us", "not-a-number"),
        ("last_alert_at_us", 0),
        ("alert_runs", 0),
        ("alert_runs", True),
        ("escalated_at_us", -5),
        ("state", "bogus-state"),
        ("address", ""),
        ("envelope_id", None),
    ],
)
def test_esc_state_entry_bad_value_fails_closed(
    tmp_path, field, value,
):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    entry = _valid_entry(**{field: value})
    _write_esc_state(tmp_path, {f"{ADDR}/{EID}": entry})
    with pytest.raises(mod.SupervisorStateCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


def test_esc_state_key_mismatch_fails_closed(tmp_path):
    """items key 與 entry（address, envelope_id）不一致＝錯置記錄。"""
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    entry = _valid_entry(envelope_id="other-eid")
    _write_esc_state(tmp_path, {f"{ADDR}/{EID}": entry})
    with pytest.raises(mod.SupervisorStateCorrupt):
        mod.supervise(str(tmp_path), now_us=NOW)


def test_esc_state_top_level_extra_key_fails_closed(tmp_path):
    _seed(ADDR, EID, "received", NOW - 25 * HOUR_US, tmp_path)
    meta = tmp_path / "_meta"
    meta.mkdir()
    (meta / "supervisor-escalations.json").write_text(
        json.dumps({"schema_version": 1, "items": {}, "junk": 1},
                   ensure_ascii=False),
        encoding="utf-8",
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
