#!/usr/bin/env python3
"""wt-sweep.py — orphan card WT TTL sweep（AIR-159；DB-21 裁決承接）。

掃描 `git worktree list` 中帶 identity contract（<wt>/.agent-tmp/wt-identity.json，
wt-open 落盤）的 card WT，三條件齊才列孤兒，預設 dry-run 只報告；
`--prune` 顯式才回收，且僅限「可證無損」子集。本腳本是 wt-open/wt-close 的
回收腿擴充入口，不改兩者既有行為；處置權歸主 session。

## 孤兒三條件（缺一即排除並記原因）

1. **contract 存在且自洽**：檔案可解析、`v` 支援、`wt_path` 與掃描路徑一致
   （防複製盜用／stale contract——與 wt-close 的拒收 guard 同源語義）。
2. **dispatcher session 死（代理判定）**：identity contract 沒有 session id
   欄位，無從對特定 session 輪詢；改以「活動面靜默」代理——在 WT 內工作的
   session 會在下列三個獨立面留下活動痕跡，任一 mtime 落在 TTL 窗口內即視為
   session 活著：
   - S1 `<wt>/.agent-tmp/**`：scratch 面（ai-guide 慣例：impl marker、
     session journal、POC 皆落此；identity 檔本身是開 WT 時的下限）。
   - S2 `<wt>/.delegate-bridge/**`：bridge ledger 面（有才掃）。
   - S3 git 活動面：WT gitdir 的 `HEAD`（checkout/reset 觸碰）＋該 WT branch
     的共享 loose ref 檔 `<common>/refs/heads/<branch>`（commit 改寫它）。
     **index mtime 刻意排除**——`git status` 會重寫 index，掃描自身會自我續命；
     **packed-refs 亦不採**——它是 repo 級面，任一 ref 打包會刷新全 repo 孤兒的
     時鐘（過度保守）；loose ref 已被打包消失＝該面無訊號，交其餘活動面承擔。
   全部活動面不可讀＝「metadata 不可達」，無法證明死亡 → 不列孤兒
   （fail-closed：reaper 只收編可證已死者）。
3. **TTL 逾**：`now - opened_at >= --ttl`（persistent card WT 合法活數天，
   太年輕的一律排除）。條件 2 與 3 共用 `--ttl` 單一旋鈕：2＝活動面靜默期、
   3＝開張年齡。

## 回收（--prune）：可證無損才動手

孤兒成立後另過一道 lossless 閘，任一不滿即跳過並記原因：
- working tree 乾淨（`git status --porcelain` 空）——未 commit 工作是唯一
  真正會滅失的東西，**--force 也不豁免此條**；
- branch 無未 merge 獨有 commit（`git log owning..branch` 空）——`--force`
  顯式可豁免此條（獨有 commit 經 wt-close 收斂路徑進 owning 線或大聲失敗）；
- 非鎖（worktree locked）、非 detached HEAD、非呼叫端自身 CWD 所在 WT、
  owning 線可解析（滅失即無從證明 merged，fail-closed）、mode 為已知值。

回收動作**複用 wt-close.sh**（subprocess 全模式——identity 拒收／清樹檢查／
收斂／branch -d／receipt log 全部沿用既有語義，不複製不重implement）；
鎖面由 wt-close 自帶的 mkdir 原子鎖守。永不 `branch -D`、永不動 main／
foreign WT、不做自動排程（單次顯式調用）。

## 判定詞彙（verdict）

orphan（三條件齊；prune 與否看 skip_reasons／prune_eligible）、fresh（③未逾）、
active（②未死）、identity-corrupt／identity-mismatch／unsupported-version
（①敗——broken alert，永不觸碰）、opened-at-unparseable／metadata-unreachable
（時間面不可判——fail-closed）、wt-dir-missing（porcelain 有登記目錄已滅——
broken alert，人工 `git worktree prune`，本腳本不代執行）、main（主工作樹，
恆排除）。

## exit 契約

- 0＝掃描完成（含零孤兒；--prune 下個別 WT 回收失敗也是報告列，不翻 rc）。
- 1＝fail-loud：root 非 git repo、git 呼叫失敗、--ttl 非正數、--prune 而
  wt-close.sh 不存在。
- argparse usage 錯誤維持其自帶 rc 2（慣例，不屬本契約面）。

用法：`uv run python scripts/wt-sweep.py [--root <repo>] [--ttl <hours>]
[--json] [--prune] [--force]`
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

TTL_DEFAULT_HOURS = 72.0
SUPPORTED_CONTRACT_VERSION = 1
KNOWN_MODES = ("card", "ephemeral")
CONTRACT_FIELDS = (
    "v",
    "mode",
    "task",
    "owning_line",
    "base_ref",
    "base_hash",
    "branch",
    "wt_path",
    "card_file",
    "opened_at",
)
CLOSE_SCRIPT = Path(__file__).resolve().parent / "wt-close.sh"


class SweepError(RuntimeError):
    """fail-loud（exit 1）：root 非 repo／git 失敗／參數錯／prune 前置缺。"""


def _git(root: Path, *args: str) -> str:
    """跑 git（check rc），失敗即 SweepError——禁吞錯續行。"""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise SweepError(f"git 呼叫失敗：{exc}") from exc
    if proc.returncode != 0:
        raise SweepError(
            f"git {' '.join(args)} 失敗（rc={proc.returncode}）：{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _git_common(root: Path) -> Path:
    """共享 .git 目錄（兼 repo 存在性驗證：非 repo＝fail-loud）。"""
    return Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))


def _parse_worktree_list(text: str) -> list[dict[str, object]]:
    """解析 `git worktree list --porcelain`（blank-line 分段；首筆＝main）。"""
    entries: list[dict[str, object]] = []
    cur: dict[str, object] | None = None
    for line in text.splitlines():
        if not line.strip():
            if cur is not None:
                entries.append(cur)
                cur = None
            continue
        key, _, rest = line.partition(" ")
        if key == "worktree":
            cur = {
                "worktree": rest,
                "branch": None,
                "bare": False,
                "detached": False,
                "locked": False,
            }
        elif cur is None:
            continue
        elif key == "branch":
            cur["branch"] = rest.removeprefix("refs/heads/")
        elif key == "bare":
            cur["bare"] = True
        elif key == "detached":
            cur["detached"] = True
        elif key == "locked":
            cur["locked"] = True
    if cur is not None:
        entries.append(cur)
    return entries


def _load_contract(wt: Path) -> tuple[dict[str, object] | None, str | None]:
    """讀 identity contract。回 (contract, None) 或 (None, 原因)。

    原因 "no-identity"＝檔案不存在（foreign WT）；其餘＝檔案在但不可用
    （broken alert 面）。
    """
    ident = wt / ".agent-tmp" / "wt-identity.json"
    if not ident.is_file():
        return None, "no-identity"
    try:
        raw: object = json.loads(ident.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"identity-corrupt：{exc}"
    if not isinstance(raw, dict):
        return None, "identity-corrupt：contract 非物件"
    missing = [f for f in CONTRACT_FIELDS if f not in raw]
    if missing:
        return None, f"identity-corrupt：缺欄位 {','.join(missing)}"
    return raw, None


def _newest_mtime(target: Path) -> float | None:
    """target（檔或目錄樹）最新 mtime；不可讀回 None。"""
    try:
        newest = os.stat(target, follow_symlinks=False).st_mtime
    except OSError:
        return None
    for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
        for name in (*dirnames, *filenames):
            try:
                m = os.stat(os.path.join(dirpath, name), follow_symlinks=False).st_mtime
            except OSError:
                continue
            newest = max(newest, m)
    return newest


def _last_activity(
    wt: Path, git_dir: Path, common_dir: Path, branch: object
) -> float | None:
    """活動面最新 mtime（S1 scratch／S2 bridge ledger／S3 git 活動）。

    全面不可讀回 None＝metadata 不可達（呼叫端 fail-closed，不列孤兒）。
    """
    candidates: list[float] = []
    newest_scratch = _newest_mtime(wt / ".agent-tmp")
    if newest_scratch is not None:
        candidates.append(newest_scratch)
    if (wt / ".delegate-bridge").exists():
        newest_ledger = _newest_mtime(wt / ".delegate-bridge")
        if newest_ledger is not None:
            candidates.append(newest_ledger)
    git_faces = [git_dir / "HEAD"]
    if isinstance(branch, str) and branch:
        git_faces.append(common_dir / "refs" / "heads" / branch)
    for face in git_faces:
        try:
            candidates.append(face.stat().st_mtime)
        except OSError:
            pass
    return max(candidates) if candidates else None


def _lossless_skips(
    wt: Path,
    entry: dict[str, object],
    contract: dict[str, object],
    root: Path,
    cwd: Path,
    force: bool,
) -> tuple[list[str], int | None]:
    """孤兒成立後的可證無損閘。回（skip 原因列, 獨有 commit 數）。"""
    skips: list[str] = []
    if contract["mode"] not in KNOWN_MODES:
        skips.append("unknown-mode")
    if _git(wt, "status", "--porcelain").strip():
        skips.append("dirty")
    if entry["locked"]:
        skips.append("locked")
    branch = entry["branch"]
    if entry["detached"] or branch is None:
        skips.append("detached-head")
        branch = None
    if cwd.is_relative_to(wt.resolve()):
        skips.append("self-cwd")
    unique: int | None = None
    if branch is not None:
        try:
            _git(root, "rev-parse", "--verify", f"{contract['owning_line']}^{{commit}}")
            listing = _git(
                root, "log", "--format=%H", f"{contract['owning_line']}..{branch}"
            )
        except SweepError:
            skips.append("owning-line-missing")
        else:
            unique = len([ln for ln in listing.splitlines() if ln.strip()])
            if unique > 0 and not force:
                skips.append("unmerged-commits")
    return skips, unique


def _evaluate(
    wt: Path,
    entry: dict[str, object],
    *,
    root: Path,
    ttl_hours: float,
    now: float,
    cwd: Path,
    force: bool,
    foreign: list[str],
) -> dict[str, object] | None:
    """評估單一非 main WT。foreign（無 contract）回 None（只計數不判定）。"""
    if not wt.exists():
        return {
            "path": str(wt),
            "verdict": "wt-dir-missing",
            "orphan": False,
            "prune_eligible": False,
            "skip_reasons": [],
            "prune_result": None,
        }
    contract, err = _load_contract(wt)
    if contract is None:
        if err == "no-identity":
            foreign.append(str(wt))
            return None
        return {
            "path": str(wt),
            "verdict": "identity-corrupt",
            "detail": err,
            "orphan": False,
            "prune_eligible": False,
            "skip_reasons": [],
            "prune_result": None,
        }
    row: dict[str, object] = {
        "path": str(wt),
        "branch": entry["branch"],
        "mode": contract["mode"],
        "task": contract["task"],
        "base_hash": contract["base_hash"],
        "opened_at": contract["opened_at"],
        "age_hours": None,
        "last_activity_hours": None,
        "orphan": False,
        "prune_eligible": False,
        "skip_reasons": [],
        "unique_commits": None,
        "prune_result": None,
    }
    if contract["v"] != SUPPORTED_CONTRACT_VERSION:
        row["verdict"] = "unsupported-version"
        return row
    if Path(str(contract["wt_path"])).resolve() != wt.resolve():
        row["verdict"] = "identity-mismatch"
        return row
    try:
        opened_ts = datetime.fromisoformat(str(contract["opened_at"])).timestamp()
    except ValueError:
        row["verdict"] = "opened-at-unparseable"
        return row
    git_dir = Path(_git(wt, "rev-parse", "--absolute-git-dir"))
    last = _last_activity(wt, git_dir, _git_common(root), entry["branch"])
    age_hours = (now - opened_ts) / 3600.0
    idle_hours = None if last is None else (now - last) / 3600.0
    row["age_hours"] = age_hours
    row["last_activity_hours"] = idle_hours
    if last is None:
        row["verdict"] = "metadata-unreachable"
        return row
    if age_hours < ttl_hours:
        row["verdict"] = "fresh"
        return row
    if idle_hours < ttl_hours:
        row["verdict"] = "active"
        return row
    row["verdict"] = "orphan"
    row["orphan"] = True
    skips, unique = _lossless_skips(wt, entry, contract, root, cwd, force)
    row["skip_reasons"] = skips
    row["unique_commits"] = unique
    row["prune_eligible"] = not skips
    return row


def _prune_row(row: dict[str, object]) -> dict[str, object]:
    """回收一列：subprocess 複用 wt-close.sh 全模式（語義單一源，禁複製）。"""
    wt = str(row["path"])
    try:
        proc = subprocess.run(
            ["bash", str(CLOSE_SCRIPT), "--wt", wt],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"status": "failed", "close_rc": -1, "detail": str(exc)}
    detail = ((proc.stderr or "") + (proc.stdout or "")).strip()[-400:]
    if proc.returncode != 0:
        return {"status": "failed", "close_rc": proc.returncode, "detail": detail}
    if Path(wt).exists():  # 防禦斷言：rc=0 但目錄仍在＝異常，大聲報
        return {
            "status": "failed",
            "close_rc": 0,
            "detail": "wt-close rc=0 但 WT 目錄仍在——人工檢查",
        }
    return {"status": "pruned", "close_rc": 0, "detail": ""}


def _summary(rows: list[dict[str, object]]) -> dict[str, int]:
    pruned = sum(
        1
        for r in rows
        if isinstance(r.get("prune_result"), dict)
        and r["prune_result"]["status"] == "pruned"
    )
    failed = sum(
        1
        for r in rows
        if isinstance(r.get("prune_result"), dict)
        and r["prune_result"]["status"] == "failed"
    )
    return {
        "scanned": len(rows),
        "identity": sum(1 for r in rows if r.get("mode") is not None),
        "orphans": sum(1 for r in rows if r.get("orphan")),
        "prune_eligible": sum(1 for r in rows if r.get("prune_eligible")),
        "pruned": pruned,
        "failed": failed,
    }


def sweep(
    root: Path,
    ttl_hours: float,
    *,
    prune: bool = False,
    force: bool = False,
    cwd: Path | None = None,
) -> dict[str, object]:
    """掃描 root repo 的 worktrees，回報告 payload（--json 同形）。

    prune=True 才動手；force=True 只放寬「獨有 commit」條，不豁免乾淨樹。
    """
    if not (ttl_hours > 0):  # 否定形比較：NaN／負數／零全擋（fail-closed）
        raise SweepError(f"--ttl 必須為正數，got：{ttl_hours}")
    cwd = Path(cwd if cwd is not None else os.getcwd()).resolve()
    _git_common(root)  # repo 存在性驗證（非 repo＝fail-loud）
    if prune and not CLOSE_SCRIPT.is_file():
        raise SweepError(
            f"回收腳本不存在：{CLOSE_SCRIPT}（--prune 需複用 wt-close.sh）"
        )
    entries = _parse_worktree_list(_git(root, "worktree", "list", "--porcelain"))
    now = time.time()
    rows: list[dict[str, object]] = []
    foreign: list[str] = []
    for idx, entry in enumerate(entries):
        if entry["bare"]:
            continue
        wt = Path(str(entry["worktree"]))
        if idx == 0:  # 主工作樹恆排除（git 保證首筆＝main worktree）
            rows.append(
                {
                    "path": str(wt),
                    "verdict": "main",
                    "orphan": False,
                    "prune_eligible": False,
                    "skip_reasons": [],
                    "prune_result": None,
                }
            )
            continue
        row = _evaluate(
            wt,
            entry,
            root=root,
            ttl_hours=ttl_hours,
            now=now,
            cwd=cwd,
            force=force,
            foreign=foreign,
        )
        if row is not None:
            rows.append(row)
    report: dict[str, object] = {
        "root": str(Path(root).resolve()),
        "ttl_hours": ttl_hours,
        "foreign": {"count": len(foreign), "paths": foreign},
        "worktrees": rows,
        "summary": _summary(rows),
    }
    if prune:
        for row in rows:
            if row["prune_eligible"]:
                row["prune_result"] = _prune_row(row)
        report["summary"] = _summary(rows)
    return report


def _render_human(report: dict[str, object]) -> str:
    """人讀報告（print＝索引通道；--json 才是機器面）。"""
    lines = [
        f"[wt-sweep] root={report['root']} ttl={report['ttl_hours']}h",
    ]
    for r in report["worktrees"]:
        if r["verdict"] == "main":
            lines.append(f"  main       {r['path']}")
            continue
        extra = f" branch={r['branch']}" if r.get("branch") else ""
        lines.append(f"  {r['verdict']!s:<22} {r['path']}{extra}")
        details: list[str] = []
        if isinstance(r.get("age_hours"), float):
            details.append(f"age={r['age_hours']:.1f}h")
        if isinstance(r.get("last_activity_hours"), float):
            details.append(f"idle={r['last_activity_hours']:.1f}h")
        if r.get("unique_commits"):
            details.append(f"unique_commits={r['unique_commits']}")
        if r.get("skip_reasons"):
            details.append("skip=" + ",".join(r["skip_reasons"]))
        if r.get("detail"):
            details.append(str(r["detail"]))
        if details:
            lines.append("      " + " ".join(details))
        pr = r.get("prune_result")
        if isinstance(pr, dict):
            lines.append(
                f"      prune: {pr['status']} rc={pr['close_rc']} {pr['detail']}".rstrip()
            )
    foreign = report["foreign"]
    if isinstance(foreign, dict) and foreign["count"]:
        lines.append(
            f"  foreign（無 identity contract，不判定不觸碰）：{foreign['count']}"
        )
        for p in foreign["paths"]:
            lines.append(f"    {p}")
    s = report["summary"]
    lines.append(
        f"  summary: scanned={s['scanned']} identity={s['identity']} "
        f"orphans={s['orphans']} prune_eligible={s['prune_eligible']} "
        f"pruned={s['pruned']} failed={s['failed']}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。exit 0＝掃描完成／1＝fail-loud（詳模組 docstring exit 契約）。"""
    parser = argparse.ArgumentParser(
        prog="wt-sweep", description="orphan card WT TTL sweep（AIR-159）"
    )
    parser.add_argument("--root", default=".", help="掃描目標 repo（預設 CWD）")
    parser.add_argument(
        "--ttl",
        default=str(TTL_DEFAULT_HOURS),
        help=f"TTL 小時（預設 {TTL_DEFAULT_HOURS}）",
    )
    parser.add_argument("--json", action="store_true", help="JSON 輸出（機器面）")
    parser.add_argument("--prune", action="store_true", help="顯式回收（預設 dry-run）")
    parser.add_argument(
        "--force", action="store_true", help="放寬「無獨有 commit」條（不豁免乾淨樹）"
    )
    args = parser.parse_args(argv)
    try:
        ttl = float(args.ttl)
    except ValueError:
        print(f"ERROR[wt-sweep]: --ttl 非數值：{args.ttl}", file=sys.stderr)
        return 1
    try:
        report = sweep(
            Path(args.root), ttl_hours=ttl, prune=args.prune, force=args.force
        )
    except SweepError as exc:
        print(f"ERROR[wt-sweep]: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(report, ensure_ascii=False, indent=2)
        if args.json
        else _render_human(report)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
