#!/usr/bin/env python
"""segment receipt 生成器——EP 段落收斂狀態的機械欄生成＋freshness 鏈（AIR-62，AIR-60 段③併入）。

設計（archived AIR-62 已決策勿重辯）：
- 欄位分級：git／檔案系統可推導欄全部機械生成（零 LLM 手寫）——解「receipt
  最被需要時（session 末、model 最退化）寫作品質最低」的寫入者悖論。
- freshness 語義：receipt 鏈式版本（parent receipt identity）——resume 端
  `--verify` 判「世界是否已分叉」，不是還原 snapshot。freshness 鏈防
  drift／手誤，非防惡意竄改（parent＋child 同改可繞過；防惡意另案）。
- receipt 是 transcript cache 的 validity token，**不是第二真相源**——完成度
  真相仍是 Git＋EP re-derive。receipt 住 `.agent-tmp/segment-receipts/`
  （ephemeral），非第六落盤層。

機械欄：baseline_head（EP 弧＝`> **baseline**:` 解析；card-first 弧＝--baseline
caller-declared）、head、tracked_diff_hash（`git diff HEAD` content hash）、
untracked manifest（路徑＋content hash，untracked-only 變更也算內容變更——與
workflow-review-pattern header identity 同詞）。判斷欄（未驗面／下一步／review
尚需）**不住本檔**——寫 EP 進度節（card-first 弧＝卡 Plan／Notes），receipt 只
記 EP／卡指針。

pytest 欄：僅呼叫端顯式帶 scoped 測試 args 時機械捕獲（exit＋summary 行）；
缺席＝not carried——不假造測試結果。review_rounds 為 caller-declared 申報欄
（標 source，非機械推導——誠實標註勝過偽機械）。

CLI：
- 生成（EP 弧照舊）：`uv run python scripts/segment_receipt.py --repo <root> --segment <id> --ep <ep.md> [--parent <receipt>] [--pytest-cmd "uv run pytest"] [--pytest-args "-q tests/x.py"] [--out <path>]`
- 生成（card-first 弧，AIR-135.2 AC#4 模式 4）：`--baseline <sha>` 帶卡 Plan／work-order §3 的 Plan 版本 hash（hex 7-40 位，不合 exit 2）、`--card <path>` 僅作 provenance 記錄欄（receipt 記卡路徑，不讀內容）；兩者皆缺 → baseline_head＝None
- 驗證：`uv run python scripts/segment_receipt.py --verify <receipt> [--repo <root>]`（card-first receipt 的 baseline 為 declared 常數，無 world 可 re-derive——verify 只比對 head／tracked／untracked）
- exit 契約（對齊 reconcile_memory_pool 慣例）：verify 0＝FRESH、1＝DRIFTED、2＝contract/infra 錯。

跨 repo 消費：本工具住 ai-guide repo，消費端 repo 以 ai-guide checkout 絕對
路徑呼叫（先例：`scripts/reconcile_memory_pool.py`）。
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

SCHEMA = "segment-receipt/1"
EMPTY_DIFF_SENTINEL = "clean"
NONE_SENTINEL = "none"
BASELINE_RE = re.compile(r"^>\s*\*\*baseline\*\*:\s*(\S+)", re.MULTILINE)
BASELINE_FMT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
SUMMARY_RE = re.compile(r"(\d+)\s+(passed|failed|error|skipped|warning)")


class ReceiptError(Exception):
    """contract/infra 錯（缺檔、壞 JSON、缺欄）——fail loud，禁靜默。"""


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    if check and r.returncode != 0:
        raise ReceiptError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def _hash_object(repo: Path, content: str) -> str:
    r = subprocess.run(
        ["git", "hash-object", "--stdin"],
        cwd=repo, input=content, capture_output=True, text=True, check=False,
    )
    if r.returncode != 0:
        raise ReceiptError(f"git hash-object failed: {r.stderr.strip()}")
    return r.stdout.strip()


def compute_identity(repo: Path, ep: Path | None = None, baseline: str | None = None) -> dict:
    """機械欄計算——全部由 git／檔案系統推導，零外部輸入。

    baseline 來源分流（AIR-135.2 AC#4 模式 4）：顯式 baseline（card-first 弧，
    caller-declared Plan 版本 hash，hex 7-40 位）優先；否則 EP 解析（該弧原有
    EP 時照舊）；兩者皆缺 → baseline_head＝None。
    """
    if baseline is not None and not BASELINE_FMT_RE.match(baseline):
        raise ReceiptError(f"invalid baseline format（需 hex 7-40 位）: {baseline!r}")
    head = _run(repo, "rev-parse", "HEAD").stdout.strip()
    diff = _run(repo, "diff", "HEAD").stdout
    tracked = EMPTY_DIFF_SENTINEL if diff == "" else _hash_object(repo, diff)

    others = _run(repo, "ls-files", "--others", "--exclude-standard").stdout
    receipts_prefix = ".agent-tmp/segment-receipts/"
    # 自我指涉防護：receipt cache 自身的足跡不算世界內容（否則生成即分叉）；
    # 其餘 untracked（含 .agent-tmp 下 evidence 檔）仍計入 identity。
    files = sorted(
        ln for ln in others.splitlines()
        if ln and not ln.startswith(receipts_prefix)
    )
    if files:
        manifest = "".join(
            f"{f}:{_hash_object(repo, (repo / f).read_text(errors='replace'))}\n"
            for f in files
        )
        untracked = {"count": len(files), "manifest_hash": _hash_object(repo, manifest)}
    else:
        untracked = {"count": 0, "manifest_hash": NONE_SENTINEL}

    baseline_head = None
    if baseline is not None:
        baseline_head = baseline
    elif ep is not None:
        if not ep.exists():
            raise ReceiptError(f"ep not found: {ep}")
        m = BASELINE_RE.search(ep.read_text(errors="replace"))
        baseline_head = m.group(1) if m else None

    return {
        "head": head,
        "tracked_diff_hash": tracked,
        "untracked": untracked,
        "baseline_head": baseline_head,
    }


def _identity_digest(data: dict) -> str:
    """鏈式 key——baseline/head/tracked/untracked 四元組的內容雜湊。"""
    payload = "\0".join([
        data["baseline_head"] or "",
        data["head"],
        data["tracked_diff_hash"],
        data["untracked"]["manifest_hash"],
    ])
    return hashlib.sha256(payload.encode()).hexdigest()


def _parse_receipt(path: Path) -> dict:
    if not path.exists():
        raise ReceiptError(f"receipt not found: {path}")
    text = path.read_text()
    if "```json" not in text or "```" not in text.split("```json", 1)[1]:
        raise ReceiptError(f"no json block in receipt: {path}")
    block = text.split("```json", 1)[1].split("```", 1)[0]
    try:
        return json.loads(block)
    except json.JSONDecodeError as e:
        raise ReceiptError(f"bad json in receipt {path}: {e}") from e


def _capture_pytest(repo: Path, cmd: str, args: list[str]) -> dict:
    argv = [*shlex.split(cmd), *args]
    try:
        r = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=600, check=False)
    except FileNotFoundError as e:
        raise ReceiptError(f"pytest cmd not found: {cmd}") from e
    except subprocess.TimeoutExpired as e:
        raise ReceiptError(f"pytest timed out after 600s: {cmd} {' '.join(args)}") from e
    tail = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
    summary = tail[-1] if tail else ""
    pairs = SUMMARY_RE.findall(summary)
    if pairs:
        summary = ", ".join(f"{n} {w}" for n, w in pairs)
    return {"cmd": cmd, "args": args, "exit": r.returncode, "summary": summary[:200]}


def generate_receipt(
    repo: Path,
    segment: str,
    ep: Path | None = None,
    parent: Path | None = None,
    pytest_cmd: str | None = None,
    pytest_args: list[str] | None = None,
    review_rounds: int | None = None,
    out_dir: Path | None = None,
    out: Path | None = None,
    baseline: str | None = None,
    card: Path | None = None,
) -> Path:
    """生成 receipt（機械欄）；回傳寫入路徑。

    --out 須落排除前綴 `.agent-tmp/segment-receipts/` 內，否則 receipt 自身
    足跡計入 untracked manifest——生成即 DRIFTED。

    card-first 弧（AIR-135.2 AC#4 模式 4）：baseline＝caller-declared Plan
    版本 hash（hex 7-40 位）；card＝僅 provenance 記錄欄（記路徑不讀內容）。
    """
    identity = compute_identity(repo, ep, baseline)

    parent_data = None
    if parent is not None:
        pdata = _parse_receipt(parent)
        parent_data = {
            "path": str(parent),
            "identity_digest": pdata.get("identity_digest"),
        }

    pytest_data = None
    if pytest_args:
        pytest_data = _capture_pytest(repo, pytest_cmd or "uv run pytest", pytest_args)

    data = {
        "schema": SCHEMA,
        "segment": segment,
        "ep": str(ep) if ep else None,
        "card": str(card) if card else None,
        "baseline_source": (
            "card-first-declared" if baseline is not None else ("ep" if ep is not None else None)
        ),
        "baseline_head": identity["baseline_head"],
        "head": identity["head"],
        "tracked_diff_hash": identity["tracked_diff_hash"],
        "untracked": identity["untracked"],
        "pytest": pytest_data,
        "review_rounds": (
            {"declared": review_rounds, "source": "caller-declared"}
            if review_rounds is not None
            else None
        ),
        "parent": parent_data,
        "identity_digest": _identity_digest(identity),
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    body = (
        f"# Segment Receipt — {segment}\n\n"
        "> 機械欄生成（`scripts/segment_receipt.py`；git 可推導欄零 LLM 手寫）。\n"
        "> 判斷欄在 EP 進度節（card-first 弧＝卡 Plan／Notes）——本 receipt 是 "
        "validity token，不是第二真相源；\n"
        "> 完成度真相＝Git＋EP／卡 re-derive。freshness 核對："
        "`--verify <本檔>`（FRESH＝判斷欄仍有效；DRIFTED＝以實物 re-derive）。\n\n"
        f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```\n"
    )

    if out is None:
        out_dir = out_dir or (repo / ".agent-tmp" / "segment-receipts")
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^A-Za-z0-9._-]", "-", segment)
        out = out_dir / f"receipt-{safe}-{ts}.md"
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    return out


def verify_receipt(receipt: Path, repo: Path) -> tuple[bool, list[str]]:
    """核對 receipt 對當前實物是否仍 FRESH。回傳 (fresh?, drifted keys)。

    世界是否已分叉的比對鍵：baseline_head（EP 弧＝EP 可達且解析一致；
    card-first 弧的 baseline 為 caller-declared 凍結指針，無 world 可
    re-derive——不比對，內容對驗歸 PlanSource snapshot 契約）、
    tracked_diff_hash、untracked manifest（tracked 與 untracked 都是內容
    身份——untracked-only 變更也算分叉）；parent 鏈核對＝parent 檔在場且
    identity 未被換。
    """
    data = _parse_receipt(receipt)
    if data.get("schema") != SCHEMA:
        raise ReceiptError(f"unsupported schema: {data.get('schema')!r}")

    drifted: list[str] = []
    ep = Path(data["ep"]) if data.get("ep") else None
    if ep is not None and not ep.is_absolute():
        ep = repo / ep

    try:
        current = compute_identity(repo, ep)
    except ReceiptError as e:
        return False, [f"identity_unavailable({e})"]

    if ep is not None and data.get("baseline_head") != current["baseline_head"]:
        drifted.append("baseline_head")
    if data.get("head") != current["head"]:
        drifted.append("head")
    if data.get("tracked_diff_hash") != current["tracked_diff_hash"]:
        drifted.append("tracked_diff_hash")
    if data.get("untracked", {}).get("manifest_hash") != current["untracked"]["manifest_hash"]:
        drifted.append("untracked")

    parent = data.get("parent")
    if parent:
        parent_path = Path(parent["path"])
        if not parent_path.is_absolute():
            parent_path = repo / parent_path
        try:
            pdata = _parse_receipt(parent_path)
        except ReceiptError as e:
            drifted.append(f"parent({e})")
        else:
            if pdata.get("identity_digest") != parent.get("identity_digest"):
                drifted.append("parent(identity_digest)")

    return (not drifted), drifted


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--repo", default=".", help="repo root（預設 cwd）")
    p.add_argument("--segment", help="EP 段落編號（生成用）")
    p.add_argument("--ep", help="EP 檔路徑（baseline 解析來源；repo 相對或絕對；EP 弧照舊）")
    p.add_argument("--baseline", help="card-first 弧 baseline（卡 Plan／work-order §3 的 Plan 版本 hash；hex 7-40 位，不合 exit 2；顯式聲明優先於 --ep）")
    p.add_argument("--card", help="卡檔路徑（僅 provenance 記錄欄——receipt 記路徑，不讀內容）")
    p.add_argument("--parent", help="parent receipt 路徑（freshness 鏈）")
    p.add_argument("--pytest-cmd", default="uv run pytest", help="測試命令前綴（預設 uv run pytest）")
    p.add_argument("--pytest-args", default="", help="scoped 測試 args（空＝不承載測試欄）")
    p.add_argument("--review-rounds", type=int, default=None, help="caller-declared review 迴圈輪數（申報欄）")
    p.add_argument("--out", help="receipt 輸出路徑（預設 .agent-tmp/segment-receipts/；須落排除前綴 .agent-tmp/segment-receipts/ 內，否則生成即 DRIFTED）")
    p.add_argument("--verify", help="核對模式：receipt 路徑")
    args = p.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"[segment-receipt] not a git repo: {repo}", file=sys.stderr)
        return 2

    if args.baseline is not None and not BASELINE_FMT_RE.match(args.baseline):
        print(
            f"[segment-receipt] ERROR: --baseline 格式不合（需 hex 7-40 位）: {args.baseline!r}",
            file=sys.stderr,
        )
        return 2

    if args.verify:
        receipt = Path(args.verify)
        if not receipt.is_absolute():
            receipt = repo / receipt
        try:
            fresh, keys = verify_receipt(receipt, repo)
        except ReceiptError as e:
            print(f"[segment-receipt] ERROR: {e}", file=sys.stderr)
            return 2
        if fresh:
            print(f"FRESH {receipt}")
            return 0
        print(f"DRIFTED: {', '.join(keys)}")
        return 1

    if not args.segment:
        p.error("--segment required（或 --verify <receipt>）")
    ep = Path(args.ep) if args.ep else None
    if ep is not None and not ep.is_absolute():
        ep = repo / ep
    card = Path(args.card) if args.card else None
    if card is not None and not card.is_absolute():
        card = repo / card
    parent = Path(args.parent) if args.parent else None
    if parent is not None and not parent.is_absolute():
        parent = repo / parent
    pytest_args = shlex.split(args.pytest_args) if args.pytest_args else []

    try:
        path = generate_receipt(
            repo=repo, segment=args.segment, ep=ep, parent=parent,
            pytest_cmd=args.pytest_cmd, pytest_args=pytest_args,
            review_rounds=args.review_rounds,
            out=Path(args.out) if args.out else None,
            baseline=args.baseline, card=card,
        )
    except ReceiptError as e:
        print(f"[segment-receipt] ERROR: {e}", file=sys.stderr)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
