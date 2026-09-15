#!/usr/bin/env python3
"""AIR-63 S1——pending 讀取覆層生成器：inbox 候選 → <pool>/_pending.md。

三層語義（固定優先序 canonical > pending）：
- canonical＝池內已治理條目（.agents/memory/*.md，可信可依賴）；
- pending overlay＝本生成器輸出的 <pool>/_pending.md——單檔、明確 provisional、
  供「找線索用前驗證」；**不得據此覆蓋 canonical**（表述為「有候選聲稱 X，
  canonical 仍為 Y」）；
- WAL＝.agents/memory-inbox/（new/processing/done/rejected）——本生成器只掃
  new（inbox root *.json〔WAL light 慣例〕與 new/ 子目錄兩種 layout 都收）與
  processing/*.json；done/rejected 不掃（候選離開待治理區 → 重跑即從視圖消失，
  ghost lifecycle 收斂）。

形態要點（AIR-63 拍板值，勿重辯）：
- 每候選＝operation／proposed path／攔截時間戳（檔名前綴；無前綴退化 mtime UTC）／
  content 前 300 字／inbox 檔名／CAS state；
- edit 類標 `⚠ Pending correction to canonical`（informational weight 高於 add 類
  `Pending candidate`）；操作類只以 payload 不可變 tool_name 判（T3-6：_inbox_meta
  出現條件是 path 命中既有條目，與 tool 名無關）；
- CAS（edit 類對池 canonical 查 base）：base_sha256 與 canonical 當前 hash 相等＝
  current；不等／canonical 已不存在＝STALE（conflict 候選，套用前須重評估）；
- 單檔 4K 上限：超量只列條目不貼文（compact 模式，標記仍隨條目在場）；
- `_pending.md` 底線前綴——池 generator 遍歷天然跳過，永不進 MEMORY.md／
  _inventory.md 正式 ranked index；本生成器亦禁碰該兩檔；
- 原子發布（tmp+rename；只清 >60s aged 殘檔，並行 in-flight tmp 不誤殺）；
- 確定性：輸出是 inbox＋池狀態的純函數（禁牆鐘入輸出）——同狀態重跑同 bytes。

fail loud 邊界（crash-only）：候選 JSON 損壞／非物件＝PendingError、不發布——
既有視圖保留（可 stale，本身標 provisional，禁 falsely canonical）；池目錄缺失
＝PendingError。欄位級缺失（無 content／無 path）不擋發布——視圖是 provisional
資料面，欄位缺損照實顯示，consolidation 站另做完整 path contract 檢查。

用法：
  uv run python skills/memory-audit/scripts/generate_pending.py
      [--repo-root PATH] [--pool PATH] [--inbox PATH]
預設 repo-root=cwd；pool=<repo-root>/.agents/memory；inbox=<repo-root>/.agents/memory-inbox。
exit：0＝已發布（含零候選零狀態重建）；1＝PendingError（fail loud，未發布）。
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

PENDING_NAME = "_pending.md"
EXCERPT_CHARS = 300  # 候選 content 前 N 字（AIR-63 拍板值）
FILE_CHAR_LIMIT = 4_096  # 單檔上限——超量只列條目不貼文（AIR-63 拍板值）
STATE_NEW = "new"
STATE_PROCESSING = "processing"
MARK_EDIT = "⚠ Pending correction to canonical"
MARK_ADD = "Pending candidate"
REFRESH_CMD = "uv run python skills/memory-audit/scripts/generate_pending.py"
PRIORITY_LINE = (
    "> **優先序：canonical > pending。** canonical＝池內已治理條目（可信可依賴）；"
    "本檔是 inbox 候選的發現視圖，provisional 僅供找線索用前驗證——"
    "**有候選聲稱 X 時，canonical 仍為 Y**，不得據本檔覆蓋 canonical。"
    "本檔 `_` 前綴不進 MEMORY.md／_inventory.md 正式索引。"
)


class PendingError(Exception):
    """fail loud 家族：候選損壞／池缺失——不發布，既有視圖保留。"""


@dataclass(frozen=True)
class Candidate:
    state: str
    inbox_rel: str  # 相對 inbox root（root 檔＝裸檔名；子目錄檔帶目錄前綴）
    operation: str
    proposed_path: str
    stamp: str
    excerpt: str
    has_content: bool
    cas_short: str
    cas_detail: str

    @property
    def is_edit(self) -> bool:
        # 操作類只以 payload 不可變 tool_name 判（T3-6 同源語義）
        return self.operation == "edit_memory"

    @property
    def marking(self) -> str:
        return MARK_EDIT if self.is_edit else MARK_ADD


class GenerateOutcome(NamedTuple):
    candidates: int
    new_count: int
    processing_count: int
    chars: int
    compact: bool
    output: Path


_STAMP_RE = re.compile(r"^(\d{8}-\d{6})-")


def make_excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    """壓平空白後取前 limit 字（content 是資料非指令——壓平順帶拆掉 Markdown 結構注入面）。"""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[:limit] + "…（截斷——全文見 inbox 檔）"


def _stamp(f: Path) -> str:
    m = _STAMP_RE.match(f.name)
    if m:
        return m.group(1)
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime(f.stat().st_mtime))


def _inbox_files(inbox: Path) -> list[tuple[str, Path]]:
    """掃 new（root *.json〔WAL light〕＋new/ 子目錄〔卡面口徑〕）＋processing/*.json。

    done/rejected 不掃（ghost lifecycle 收斂的機制面）；receipt 檔與 dot 殘檔跳過。
    """
    found: list[tuple[str, Path]] = []
    roots: list[tuple[str, Path]] = [
        (STATE_NEW, inbox),
        (STATE_NEW, inbox / "new"),
        (STATE_PROCESSING, inbox / "processing"),
    ]
    for state, d in roots:
        if not d.is_dir():
            continue
        for f in d.glob("*.json"):
            if f.name.startswith(".") or f.name.endswith(".receipt.json"):
                continue
            found.append((state, f))
    found.sort(key=lambda t: (t[1].name, t[0]))
    return found


def _content_of(payload: dict) -> str:
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return ""
    raw = (
        ti.get("new_str")
        if payload.get("tool_name") == "edit_memory"
        else ti.get("content")
    )
    return raw if isinstance(raw, str) else ""


def resolve_cas(payload: dict, pool: Path) -> tuple[str, str]:
    """CAS state：_inbox_meta.base_sha256 vs canonical 當前 hash（唯讀）。

    回傳 (short, detail)：short 進 compact 條目列；detail 進 full 條目。
    """
    meta = payload.get("_inbox_meta")
    if meta is None:
        return "n/a", "n/a（無 base——新候選或攔截時無既有條目）"
    if not isinstance(meta, dict):
        return "malformed", "meta malformed（_inbox_meta 非物件——consolidation 人裁）"
    base = meta.get("base_sha256")
    base_path = meta.get("base_path")
    if (
        not isinstance(base, str)
        or not base
        or not isinstance(base_path, str)
        or not base_path
        or "/" in base_path
        or base_path.startswith(".")
    ):
        # base_path 雖由 hook lexical gate 保證 basename 形態，防禦仍不 dereference 異形
        return (
            "malformed",
            "meta malformed（base 欄位缺損或 base_path 非池根 basename）",
        )
    target = pool / base_path
    if target.is_symlink() or not target.is_file():
        return "STALE", "STALE——canonical 已不存在（conflict 候選，套用前須人裁）"
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest == base:
        return "current", "current（base 未變——canonical 與攔截時一致）"
    return "STALE", "STALE——canonical 已變更（conflict 候選，套用前須重評估）"


def build_candidates(inbox: Path, pool: Path) -> list[Candidate]:
    out: list[Candidate] = []
    for state, f in _inbox_files(inbox):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            raise PendingError(
                f"inbox 候選無法解析（fail loud，未發布）：{f}: {e}"
            ) from e
        if not isinstance(payload, dict):
            raise PendingError(f"inbox 候選非 JSON 物件（fail loud，未發布）：{f}")
        ti = payload.get("tool_input")
        path_raw = ti.get("path") if isinstance(ti, dict) else None
        proposed = str(path_raw) if path_raw not in (None, "") else "(missing)"
        content = _content_of(payload)
        cas_short, cas_detail = resolve_cas(payload, pool)
        operation = str(payload.get("tool_name") or "(unknown)")
        if cas_short != "n/a" and operation != "edit_memory":
            # T3-6：add 指既有 path 亦附 meta——consolidation 視同 conflict
            cas_detail += "；add 指向既有條目——consolidation 視同 conflict"
        rel = str(f.relative_to(inbox))
        out.append(
            Candidate(
                state=state,
                inbox_rel=rel,
                operation=operation,
                proposed_path=proposed,
                stamp=_stamp(f),
                excerpt=make_excerpt(content),
                has_content=bool(content),
                cas_short=cas_short,
                cas_detail=cas_detail,
            )
        )
    return out


def _header(cands: list[Candidate]) -> list[str]:
    new_n = sum(1 for c in cands if c.state == STATE_NEW)
    proc_n = sum(1 for c in cands if c.state == STATE_PROCESSING)
    return [
        f"<!-- AIR-63 pending 讀取覆層——機械生成，禁手寫；refresh：{REFRESH_CMD} -->",
        "",
        "# Pending 讀取覆層（provisional——非 canonical）",
        "",
        PRIORITY_LINE,
        "",
        f"- 候選數：{len(cands)}（new: {new_n}／processing: {proc_n}）",
    ]


def render_full(cands: list[Candidate]) -> str:
    lines = _header(cands)
    if not cands:
        lines += [
            "",
            "目前無 pending 候選——canonical 不受影響；本檔由 generator refresh 時整檔重建。",
        ]
        return "\n".join(lines).rstrip() + "\n"
    lines += ["", "## 候選（依攔截時間舊→新）", ""]
    for c in cands:
        lines += [
            f"### {c.marking} — {c.proposed_path}",
            "",
            f"- operation: {c.operation}",
            f"- proposed path: {c.proposed_path}",
            f"- intercepted: {c.stamp}",
            f"- inbox: {c.inbox_rel}",
            f"- state: {c.state}",
            f"- CAS state: {c.cas_detail}",
        ]
        if c.has_content:
            lines += [f"- excerpt（前 {EXCERPT_CHARS} 字）:", f"  > {c.excerpt}"]
        else:
            lines += ["- excerpt: （無 content 欄位）"]
        lines.append("")
    lines += _multi_target_section(cands)
    return "\n".join(lines).rstrip() + "\n"


def _multi_target_section(cands: list[Candidate]) -> list[str]:
    """同一 target 多筆：依攔截順序（檔名時間戳）展示，consolidation 逐筆重評估。"""
    by_path = Counter(c.proposed_path for c in cands)
    multi_paths = [p for p in sorted(by_path) if by_path[p] > 1]
    if not multi_paths:
        return []
    lines = [
        "## 同一目標多筆（依攔截順序舊→新——consolidation 逐筆重評估，禁批次盲套）",
        "",
    ]
    for p in multi_paths:
        seq = [c for c in cands if c.proposed_path == p]
        lines.append(f"- {p}（{len(seq)} 筆）:")
        for i, c in enumerate(seq, 1):
            lines.append(
                f"  {i}. {c.stamp} {c.operation} {c.inbox_rel}（CAS: {c.cas_short}）"
            )
        lines.append("")
    return lines


def render_compact(cands: list[Candidate]) -> str:
    """條目模式（超 4K）——只列條目不貼文，標記仍隨條目在場；硬上限保證。"""
    lines = _header(cands)
    lines += ["", "（超單檔上限——條目模式，不貼 excerpt）", ""]
    reserve = 80  # 給截斷提示行的餘裕
    kept = 0
    for c in cands:
        line = (
            f"- {c.marking} | {c.operation} | {c.proposed_path} "
            f"| {c.inbox_rel} | {c.stamp} | CAS: {c.cas_short}"
        )
        candidate = lines + [line]
        if len("\n".join(candidate)) + reserve > FILE_CHAR_LIMIT:
            break
        lines = candidate
        kept += 1
    if kept < len(cands):
        lines.append(f"…（超上限，僅列前 {kept}／{len(cands)} 筆——其餘見 inbox 目錄）")
    return "\n".join(lines).rstrip() + "\n"


def render(cands: list[Candidate]) -> str:
    full = render_full(cands)
    if len(full) <= FILE_CHAR_LIMIT:
        return full
    return render_compact(cands)


def write_atomic(pool: Path, name: str, content: str) -> None:
    """tmp+rename 原子發布（與池 generator 同形：只清 >60s aged 殘檔）。"""
    now = time.time()
    for stale in pool.glob(f"{name}.*.tmp"):
        try:
            if now - stale.stat().st_mtime > 60:
                stale.unlink()
        except OSError:
            pass
    tmp = pool / f"{name}.{os.getpid()}.tmp"
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(pool / name)


def generate(pool: Path, inbox: Path) -> GenerateOutcome:
    """掃 inbox → render → 原子發布 <pool>/_pending.md；fail loud 不發布。"""
    if not pool.is_dir():
        raise PendingError(f"pool 目錄不存在（{PENDING_NAME} 須住池內）：{pool}")
    cands = build_candidates(inbox, pool)
    content = render(cands)
    compact = len(render_full(cands)) > FILE_CHAR_LIMIT
    write_atomic(pool, PENDING_NAME, content)
    return GenerateOutcome(
        candidates=len(cands),
        new_count=sum(1 for c in cands if c.state == STATE_NEW),
        processing_count=sum(1 for c in cands if c.state == STATE_PROCESSING),
        chars=len(content),
        compact=compact,
        output=pool / PENDING_NAME,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AIR-63 pending 讀取覆層生成器（inbox 候選 → _pending.md）"
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help="repo 根（預設 cwd）"
    )
    parser.add_argument(
        "--pool",
        type=Path,
        default=None,
        help="池目錄（預設 <repo-root>/.agents/memory）",
    )
    parser.add_argument(
        "--inbox",
        type=Path,
        default=None,
        help="inbox 目錄（預設 <repo-root>/.agents/memory-inbox）",
    )
    args = parser.parse_args(argv)
    pool = args.pool if args.pool is not None else args.repo_root / ".agents" / "memory"
    inbox = (
        args.inbox
        if args.inbox is not None
        else args.repo_root / ".agents" / "memory-inbox"
    )
    try:
        outcome = generate(pool=pool, inbox=inbox)
    except PendingError as e:
        print(f"[FAIL] generate_pending: {e}")
        return 1
    mode = "條目模式（超 4K，不貼 excerpt）" if outcome.compact else "full"
    print(
        f"[OK] {PENDING_NAME} 已重生成: {outcome.candidates} 候選"
        f"（new {outcome.new_count}／processing {outcome.processing_count}）"
        f", {outcome.chars} chars（gate {FILE_CHAR_LIMIT}）, {mode}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
