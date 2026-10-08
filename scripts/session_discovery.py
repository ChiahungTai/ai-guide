#!/usr/bin/env python
"""session_discovery — session 發現 seam（AIR-254.1；AIR-277 換源 harness-native）.

一句話：session 發現的單一 choke point——「現在有哪些 AI session、在哪個
repo」從此只經本檔查；消費端（inflight_snapshot 路 2、handoff resolve-
target）吃正規化 rows。來源＝harness-native scan——ZCode session store
（`~/.zcode/cli/db/db.sqlite` 的 `session` 表）**唯讀直查**（python
sqlite3 模組＋`file:...?mode=ro` URI——CLI 對此 DB 會無聲空輸出）；
`_collect_raw` 是全 repo 唯一源存取位置，未來換源只改該函式一處。

覆蓋邊界（如實聲明，禁靜默假裝全覆蓋）
----
本源只覆蓋 **zcode**——rows 的 `harness` 恆 `"zcode"`；claude／codex／
muse session 不在本源——`find` 對非 zcode harness＝`no-match` typed，
錯誤訊息帶覆蓋註記。`task_type='subagent_child'`（ephemeral 子 agent）
不列——非可定址 session。

label sidecar
----
`~/.agents/session-discovery/labels.json`（本 seam 自有；display
metadata 非 address 語義——AIR-248 successor 裁定）：形 `{"<session_id>":
{"label": str, "updated_at": iso8601}}`；atomic 寫（tmp＋os.replace）、
檔 0600／目錄 0700（owner-only）。label 絕不寫回源 store（store 連線
唯讀——seam 零 store 寫入）。路徑可經 `--labels-file` 或環境變數
`SESSION_DISCOVERY_LABELS_FILE` 注入（測試 tmp 用）。

正規化 row 形狀
----
`{"session_id": 全碼, "harness": str|null, "workspace_root": str|null,
"label": str|null, "liveness": observed_liveness, "status": str|null,
"last_seen_iso": str|null, "age_min": int|null}`——label 合併 sidecar
（store title 非空時 sidecar 優先、無 sidecar 用 title）。liveness／
status 由 store `time_archived` 推導：未封存＝`live`／`active`，已封存
＝`ended`／`ended`——handoff resolve_target 的 `status != "ended"` 過濾
語義保留。`--live` 過濾＝`liveness == "live"` 且 `session_id` 以
`sess_` 開頭——沿用 inflight_snapshot 現行雜訊排除語義；status 不參與
過濾。**`live`＝未封存，非存活觀測**——zcode store 無 session 級存活
訊號，未封存歷史 session 恆標 live；`--live` 過濾後集合含全部未封存歷
史列，下游解讀須對照 `age_min`。探勘定案（AIR-282）：`turn_usage.status`
雖有 `running` 值但全史 0 筆（事後帳非心跳）；程序面 lsof cwd 僅
workspace 級代理且非文檔契約（同 workspace 多程序、subagent 無獨立
程序）；`session_entry` 高頻 checkpoint 列屬 recency 啟發式（卡面紅
線禁提議）——`live` 語義維持「未封存」，無升級源。

CLI
----
    uv run python scripts/session_discovery.py list [--live] [--json]
    uv run python scripts/session_discovery.py find --harness H --workspace-root PATH [--json]
    uv run python scripts/session_discovery.py label set --session-id ID --label TEXT
    uv run python scripts/session_discovery.py label get --session-id ID
    uv run python scripts/session_discovery.py whoami

exit：0＝ok；3＝typed failure（stderr 統一 `{"schemaVersion": 1, "ok":
false, "error": {"code", "message"}}`、stdout 空）。`find` 無法唯一確立
（0 或 >1 候選同分）＝exit 3 禁猜；`whoami`＝harness workspace 對照
（cwd realpath 對 store `directory` 精確匹配、取 `time_updated` 最新；
無匹配／源缺席＝exit 3）。
"""

import argparse
import json
import os
import sqlite3
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LABELS_ENV = "SESSION_DISCOVERY_LABELS_FILE"
LABEL_MAX_CHARS = 64
LIVE_VALUE = "live"
SESS_PREFIX = "sess_"
SOURCE_HARNESS = "zcode"
COVERAGE = "zcode-only"
DEFAULT_DB = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"
_SUBAGENT_TASK_TYPE = "subagent_child"
_SELECT_COLS = (
    "id, directory, title, time_created, time_updated, time_archived, task_type"
)

Runner = Callable[..., str]


class DiscoveryError(Exception):
    """session 發現失敗（來源缺席／損壞／無法唯一確立）——CLI 轉 exit 3 typed failure。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _now_iso() -> str:
    return datetime.now(tz=UTC).astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# 來源（choke point）——換源只改本節
# ---------------------------------------------------------------------------


def _ms_to_us(value: Any) -> int | float | None:
    """store 時間戳（ms epoch）→ seam 內部單位（us）；非數值＝None。"""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value * 1_000
    return None


def _query_store(
    db_path: Path, workspace: str | None = None
) -> list[dict[str, Any]]:
    """唯讀直查 ZCode session store（`session` 表；URI `mode=ro`——seam
    零 store 寫入）。

    匹配語義：`directory` 為精確字串匹配、未正規化——尾斜線等歷史變體
    不匹配（落 typed unavailable/no-match，fail-closed）。

    源缺席（檔案不存在）＝`source_unavailable`；已開檔但結構／內容損壞
    （非 DB 檔、缺表缺欄、鎖死逾時）＝`source_malformed`——typed
    fail-closed，CLI 層轉 exit 3 統一 envelope。`subagent_child` 不列。
    """
    if not db_path.exists():
        raise DiscoveryError("source_unavailable", f"session store 缺席：{db_path}")
    sql = "SELECT " + _SELECT_COLS + " FROM session WHERE (task_type IS NULL OR task_type != ?)"
    params: list[Any] = [_SUBAGENT_TASK_TYPE]
    if workspace is not None:
        sql += " AND directory = ?"
        params.append(workspace)
    sql += " ORDER BY time_updated DESC, rowid DESC"
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
        try:
            con.row_factory = sqlite3.Row
            rows = con.execute(sql, params).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise DiscoveryError(
            "source_malformed", f"session store 查詢失敗：{exc}"
        ) from exc
    return [dict(row) for row in rows]


def _to_session(row: dict[str, Any]) -> dict[str, Any]:
    """store 列 → 正規化前置形（`_normalize` 消費的欄位映射）。

    liveness／status 單一推導源＝`time_archived`（未封存＝live／active、
    已封存＝ended／ended）。**`live`＝未封存，非存活觀測**——zcode
    store 無存活訊號，未封存歷史 session 恆標 live；`--live` 過濾後集合
    含全部未封存歷史列，下游解讀須對照 `age_min`。"""
    ended = row.get("time_archived") is not None
    return {
        "session_id": row.get("id"),
        "harness": SOURCE_HARNESS,
        "workspace_root": row.get("directory"),
        "name": row.get("title"),
        "status": "ended" if ended else "active",
        "observed_liveness": "ended" if ended else LIVE_VALUE,
        "created_at_us": _ms_to_us(row.get("time_created")),
        "last_seen_us": _ms_to_us(row.get("time_updated")),
    }


def _collect_raw(db_path: Path | None = None) -> dict[str, Any]:
    """唯一源存取點——harness-native scan（ZCode session store 唯讀直查）。

    回 `{"count", "sessions": [...]}`（正規化前置形，欄位映射見
    `_to_session`）；失敗 raise typed DiscoveryError（CLI 層轉 exit 3
    統一 envelope）。"""
    path = db_path if db_path is not None else DEFAULT_DB
    rows = _query_store(path)
    return {"count": len(rows), "sessions": [_to_session(r) for r in rows]}


def _whoami_raw(
    db_path: Path | None = None, *, cwd: str | None = None
) -> dict[str, Any]:
    """harness workspace 對照——cwd realpath 對 store `directory` 精確
    匹配，取 `time_updated` 最新一列。

    身份語義（正式定案，非過渡；探勘證據＝AIR-282）：本命令回 workspace
    `time_updated` 最新列＝**活躍度代理，非呼叫者身份**。ZCode runtime
    對 CLI 子程序無身份注入面——env 無 session id、`zcode` CLI 無
    session 查詢命令、`~/.zcode/cli/` 無 current-session 指針檔；唯一
    權威身份源＝hook stdin payload 的 `session_id`（hooks/duty_receive.py
    已消費、值與 store `session.id` 同形），但僅 hook 程序內可達——接線
    須新增 hook＋指針寫入機制（staleness 語義另決），非本 seam 小改。
    同 workspace 多 session 並行時可能回他者；同分由 rowid 決定（與
    `find` 的 ambiguous 禁猜語義不同——workspace 對照設計即取最新）。

    無匹配／源缺席＝`whoami_unavailable`；源損壞／最新列缺 id＝
    `whoami_malformed`（typed，CLI 轉 exit 3）。"""
    path = db_path if db_path is not None else DEFAULT_DB
    here = os.path.realpath(cwd) if cwd else os.path.realpath(os.getcwd())
    try:
        rows = _query_store(path, workspace=here)
    except DiscoveryError as exc:
        code = (
            "whoami_malformed" if exc.code == "source_malformed" else "whoami_unavailable"
        )
        raise DiscoveryError(code, f"whoami 源不可用：{exc.message}") from exc
    if not rows:
        raise DiscoveryError(
            "whoami_unavailable", f"cwd 無對應 session 工作區：{here}"
        )
    best = _to_session(rows[0])  # SQL 已 ORDER BY time_updated DESC
    sid = best.get("session_id")
    if not isinstance(sid, str) or not sid:
        raise DiscoveryError("whoami_malformed", "whoami 最新列缺 session_id")
    return {
        "session_id": sid,
        "harness": SOURCE_HARNESS,
        "workspace_root": best.get("workspace_root"),
    }


# ---------------------------------------------------------------------------
# label sidecar（seam 自有 display metadata；絕不寫源 store）
# ---------------------------------------------------------------------------


def _default_sidecar_path() -> Path:
    env = os.environ.get(LABELS_ENV)
    if env:
        return Path(env)
    return Path.home() / ".agents" / "session-discovery" / "labels.json"


def _load_labels(sidecar: Path | None = None) -> dict[str, dict[str, str]]:
    """載入 label sidecar → mapping；**附屬性降級（U8）**：display metadata
    損壞不擋 address 發現主功能——壞 JSON／OSError／非物件 → stderr 一行
    註記＋回 {}（rows 照出、label 全 null）。CLI `label set` 對壞檔＝
    覆寫自癒（load 得 {} 後整檔重寫）。"""
    path = sidecar if sidecar is not None else _default_sidecar_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"[session-discovery] label sidecar 損壞——label 降級 null 續行"
            f"（{path}：{exc}）",
            file=sys.stderr,
        )
        return {}
    if not isinstance(data, dict):
        print(
            f"[session-discovery] label sidecar 形狀非物件——label 降級"
            f" null 續行（{path}）",
            file=sys.stderr,
        )
        return {}
    return data


def _save_labels(
    labels: dict[str, dict[str, str]], sidecar: Path | None = None
) -> None:
    """atomic 寫（pid 後綴 tmp＋os.replace——並行 writer 不互踩 tmp 檔，
    與 duty_receive.save_state 慣例一致）；目錄 0700／檔 0600（owner-only）。"""
    path = sidecar if sidecar is not None else _default_sidecar_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)  # mkdir mode 受 umask 影響——顯式 chmod 保證
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(
        json.dumps(labels, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _validate_label(label: str) -> str:
    if not isinstance(label, str) or not label.strip():
        raise DiscoveryError(
            "invalid_label", f"label 必填且非純空白（1-{LABEL_MAX_CHARS} 字元）"
        )
    if not 1 <= len(label) <= LABEL_MAX_CHARS:
        raise DiscoveryError(
            "invalid_label",
            f"label 長度須 1-{LABEL_MAX_CHARS} 字元（現 {len(label)}）",
        )
    return label


def set_label(session_id: str, label: str, *, sidecar: Path | None = None) -> str:
    """冪等覆寫 label（display metadata；絕不寫源 store）。回寫入值。"""
    if not isinstance(session_id, str) or not session_id:
        raise DiscoveryError("invalid_session_id", "session-id 必填")
    _validate_label(label)
    labels = _load_labels(sidecar)
    labels[session_id] = {"label": label, "updated_at": _now_iso()}
    _save_labels(labels, sidecar)
    return label


def get_label(session_id: str, *, sidecar: Path | None = None) -> str:
    labels = _load_labels(sidecar)
    entry = labels.get(session_id)
    if not isinstance(entry, dict) or not isinstance(entry.get("label"), str):
        raise DiscoveryError(
            "label_not_found", f"session {session_id} 無 label（sidecar 未挂）"
        )
    return entry["label"]


# ---------------------------------------------------------------------------
# 正規化（消費端唯一入口形狀）
# ---------------------------------------------------------------------------


def _last_seen_iso(session: dict[str, Any]) -> str | None:
    us = session.get("last_seen_us")
    if not isinstance(us, (int, float)):
        return None
    return (
        datetime.fromtimestamp(us / 1_000_000, tz=UTC)
        .astimezone()
        .isoformat(timespec="seconds")
    )


def _age_min(session: dict[str, Any]) -> int | None:
    """age（秒）→ 分；缺 age 以 last_seen_us 對 now 推算；無時間源＝None。"""
    age = session.get("age")
    if not isinstance(age, (int, float)):
        last_seen = session.get("last_seen_us")
        if not isinstance(last_seen, (int, float)):
            return None
        age = datetime.now(tz=UTC).timestamp() - last_seen / 1_000_000
    if age < 0:
        return None
    return round(age / 60)


def _normalize(session: dict[str, Any], labels: dict[str, dict[str, str]]) -> dict[str, Any]:
    sid = session.get("session_id")
    sid = sid if isinstance(sid, str) and sid else None
    name = session.get("name")
    store_name = name if isinstance(name, str) and name else None
    entry = labels.get(sid) if sid else None
    sidecar_label = entry.get("label") if isinstance(entry, dict) else None
    if not isinstance(sidecar_label, str):
        sidecar_label = None

    def _str(key: str) -> str | None:
        value = session.get(key)
        return value if isinstance(value, str) else None

    return {
        "session_id": sid,
        "harness": _str("harness"),
        "workspace_root": _str("workspace_root"),
        "label": sidecar_label or store_name,  # sidecar 優先、無 sidecar 用 store title
        "liveness": _str("observed_liveness"),
        "status": _str("status"),
        "last_seen_iso": _last_seen_iso(session),
        "age_min": _age_min(session),
    }


def collect_rows(
    runner: Runner | None = None,
    *,
    sidecar: Path | None = None,
    live_only: bool = False,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """store 正規化 rows（label 合併 sidecar）＋`--live` 雜訊排除語義。

    `runner` 參數＝v1 transport 遺留槽——harness-native 源（AIR-277）直讀
    store、不經 runner；參數僅為既有消費端呼叫相容保留（inflight_snapshot
    以位置參數傳入、**值被忽略**），禁新依賴。測試／工具注入面＝
    `db_path`（tmp fake store）。
    """
    payload = _collect_raw(db_path)
    labels = _load_labels(sidecar)
    rows: list[dict[str, Any]] = []
    for session in payload["sessions"]:
        if not isinstance(session, dict):
            continue
        row = _normalize(session, labels)
        if row["session_id"] is None:
            continue
        if live_only and not (
            row["liveness"] == LIVE_VALUE and row["session_id"].startswith(SESS_PREFIX)
        ):
            continue
        rows.append(row)
    return {
        "generated_at": _now_iso(),
        "rows": rows,
        "count": len(rows),
        "registry_total": payload.get("count", len(payload["sessions"])),
        "coverage": COVERAGE,
    }


def _sort_ts(session: dict[str, Any]) -> int | float | None:
    """排序時間戳：last_seen_us 缺則 created_at_us；皆無＝None。"""
    for key in ("last_seen_us", "created_at_us"):
        value = session.get(key)
        if isinstance(value, (int, float)):
            return value
    return None


def find_session(
    runner: Runner | None = None,
    *,
    harness: str,
    workspace_root: str,
    sidecar: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """同 harness＋workspace_root 取最新註冊列（回正規化 row）。

    無法唯一確立（0 候選或 >1 同分）＝raise typed——禁猜（CLI 轉 exit 3）。
    覆蓋邊界：源僅 zcode——harness != "zcode" 恆 no-match，訊息帶覆蓋註記。
    `runner` 參數同 `collect_rows`（遺留槽，值被忽略；注入面＝`db_path`）。
    """
    payload = _collect_raw(db_path)
    labels = _load_labels(sidecar)
    candidates = [
        s
        for s in payload["sessions"]
        if isinstance(s, dict)
        and s.get("harness") == harness
        and s.get("workspace_root") == workspace_root
    ]
    if not candidates:
        note = (
            ""
            if harness == SOURCE_HARNESS
            else f"（源覆蓋={COVERAGE}——非 zcode harness 不在本源）"
        )
        raise DiscoveryError(
            "no-match",
            f"harness={harness} workspace_root={workspace_root} 無註冊列{note}",
        )
    stamps = [_sort_ts(s) for s in candidates]
    best = max((s for s in stamps if s is not None), default=None)
    winners = [s for s, ts in zip(candidates, stamps, strict=True) if ts == best]
    if len(winners) > 1:
        raise DiscoveryError(
            "ambiguous",
            f"harness={harness} workspace_root={workspace_root}"
            f" 有 {len(winners)} 列同分——無法唯一確立",
        )
    row = _normalize(winners[0], labels)
    if row["session_id"] is None:
        raise DiscoveryError(
            "no-match",
            f"harness={harness} workspace_root={workspace_root} 唯一候選缺 session_id",
        )
    return row


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _render_list_markdown(data: dict[str, Any], *, live_only: bool) -> str:
    scope = "live（liveness=live 且 sess_*）" if live_only else "all rows"
    lines = [
        f"# session discovery（{scope}）— {data['generated_at']}",
        "",
        "| session_id | label | harness | workspace_root | liveness | status | age_min |",
        "|" + "---|" * 7,
    ]
    for row in data["rows"]:
        lines.append(
            f"| {row['session_id']} | {row['label'] or '-'} |"
            f" {row['harness'] or '-'} | {row['workspace_root'] or '-'} |"
            f" {row['liveness'] or '-'} | {row['status'] or '-'} |"
            f" {row['age_min']} |"
        )
    lines += [
        "",
        f"- rows {data['count']}（registry_total {data['registry_total']}）"
        f"；source=zcode session store（coverage={data['coverage']}）",
    ]
    return "\n".join(lines) + "\n"


def _fail_envelope(exc: DiscoveryError) -> None:
    json.dump(
        {"schemaVersion": 1, "ok": False, "error": {"code": exc.code, "message": exc.message}},
        sys.stderr,
        ensure_ascii=False,
    )
    sys.stderr.write("\n")


def main(
    argv: list[str] | None = None,
    *,
    db_path: Path | None = None,
    sidecar: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "session 發現 seam（AIR-254.1）——來源 zcode session store 直讀，"
            "換源只改 _collect_raw"
        )
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="正規化 session rows（--live＝live＋sess_*）")
    p_list.add_argument("--live", action="store_true")
    p_list.add_argument("--json", action="store_true", help="輸出 {generated_at, rows, count, registry_total, coverage}")
    p_list.add_argument("--labels-file", default=None, help="label sidecar 路徑覆寫")

    p_find = sub.add_parser("find", help="harness＋workspace_root → 最新一列（無法唯一確立＝exit 3）")
    p_find.add_argument("--harness", required=True)
    p_find.add_argument("--workspace-root", required=True)
    p_find.add_argument("--json", action="store_true")
    p_find.add_argument("--labels-file", default=None, help="label sidecar 路徑覆寫")

    p_label = sub.add_parser("label", help="seam 自有顯示標籤（display metadata；絕不寫源 store）")
    label_sub = p_label.add_subparsers(dest="label_cmd", required=True)
    p_set = label_sub.add_parser("set", help="挂／覆寫 label（冪等）")
    p_set.add_argument("--session-id", required=True)
    p_set.add_argument("--label", required=True)
    p_set.add_argument("--labels-file", default=None, help="label sidecar 路徑覆寫")
    p_get = label_sub.add_parser("get", help="讀 label（無＝exit 3）")
    p_get.add_argument("--session-id", required=True)
    p_get.add_argument("--labels-file", default=None, help="label sidecar 路徑覆寫")

    sub.add_parser("whoami", help="本側 identity（cwd→store workspace 對照；JSON）")

    args = parser.parse_args(argv)
    labels_file = Path(args.labels_file) if getattr(args, "labels_file", None) else sidecar
    try:
        if args.cmd == "list":
            data = collect_rows(sidecar=labels_file, live_only=args.live, db_path=db_path)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(_render_list_markdown(data, live_only=args.live), end="")
        elif args.cmd == "find":
            row = find_session(
                harness=args.harness,
                workspace_root=args.workspace_root,
                sidecar=labels_file,
                db_path=db_path,
            )
            if args.json:
                print(json.dumps({"ok": True, "row": row}, ensure_ascii=False))
            else:
                print(
                    f"{row['session_id']}  {row['harness'] or '-'}  {row['label'] or '-'}  "
                    f"{row['workspace_root'] or '-'}  status={row['status']}  age_min={row['age_min']}"
                )
        elif args.cmd == "label":
            if args.label_cmd == "set":
                set_label(args.session_id, args.label, sidecar=labels_file)
                print(f"label set: {args.session_id} → {args.label}")
            else:
                print(get_label(args.session_id, sidecar=labels_file))
        else:
            print(json.dumps(_whoami_raw(db_path), ensure_ascii=False))
    except DiscoveryError as exc:
        _fail_envelope(exc)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
