#!/usr/bin/env python3
"""availability_snapshot——dispatch 讀端 evaluator（AIR-123 段 3 最小切片）。

spine 現值（~/.agents/memory-spine/reference_model-runtime-entitlements.md）
＋catalog.toml 供給事實 → per-family tri-state availability evaluation。

evaluator-not-router（卡①）：輸出只有 family tri-state＋binding 計數＋
spine note 逐字——禁任何揀選／排序／代換建議欄位；判斷腿（eligibility、
override、failover）仍走 model-routing skill instruction protocol（卡⑦）。

fail-closed exit 契約（卡②——三處歷史不一致以此版為準）：
  0 = fresh 產出（as-of 在閾值內且「可用」行解析成功）
  1 = 無法判定，fail-closed（spine as-of 缺席或未來日期／「可用」行缺席或
      解析出零 family）
  2 = 輸入缺席或不合法（spine／catalog 檔不存在、--spine/--catalog/
      --stale-days 帶 flag 無值、catalog loader 驗證失敗、--stale-days
      參數不合法）
  3 = stale（as-of 距今超過閾值 → 全 family unknown）

family join（卡③）：catalog [[dispatch_binding]] 顯式 family 欄（閉集 enum
住 allow_lists.families，loader fail-loud 驗證）——POC 的 surface regex
family 推斷已退役（surface=agent-definition 面 family 資訊不存在於 surface
字串，heuristic 會漂）。

stale 邊界：age 恰等於 --stale-days＝fresh（> 才 stale）；--stale-days
預設 3；age 計算時區基準＝UTC（as-of date 與 now UTC date 的日級差），
as-of 未來（age<0）＝不合法 exit 1。spine 為給 LLM 讀的 md（非 schema
檔）——行級解析，歧義即 WARN、可用行解析失敗即 fail-closed，禁猜。
"""

import importlib.util
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPINE = (
    Path.home() / ".agents/memory-spine/reference_model-runtime-entitlements.md"
)
DEFAULT_CATALOG = REPO_ROOT / "skills" / "model-routing" / "catalog.toml"
STALE_DAYS_DEFAULT = 3

AS_OF_RE = re.compile(r"as-of\s+(\d{4}-\d{2}-\d{2})")
# spine 條目行（bullet＋bold 標籤＋全形/半形冒號）——head 可為複合（Anthropic／xai）
ENTRY_RE = re.compile(r"^-\s+\*\*(?P<head>[^*]+)\*\*\s*[：:]\s*(?P<body>.+)$")
AVAILABLE_PREFIX = "- **可用**"
EVENT_KEYWORDS = ("額度事件", "禁派")
# 衝突配對限制詞（F1）：family 名與限制詞「同行共現」才算衝突；僅 family 名
# 命中（非限制語義，如「能力序裁定」形態行）→ 中性並列複核。keyword 掃描
# 非窮舉、非語義歸因——判讀仍須讀 spine 原文（SKILL 指針同此句）
RESTRICTION_KEYWORDS = ("禁派", "耗盡", "reset", "1308", "429")


def _load_sync_module():
    """載入 scripts/sync_agents.py 的 parse_catalog（loader 驗證單一源——
    availability 讀端禁自刻第二個 catalog parser）。"""
    path = REPO_ROOT / "scripts" / "sync_agents.py"
    spec = importlib.util.spec_from_file_location("sync_agents", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@dataclass
class SpineState:
    as_of: str | None = None
    available_line_found: bool = False
    available_line_raw: str = ""
    available: frozenset[str] = frozenset()
    notes: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)


def parse_spine(text: str, families: Iterable[str]) -> SpineState:
    """行級解析 spine（給 LLM 讀的 md——形態契約非 schema）。

    - as-of：全文首個 `as-of YYYY-MM-DD` 命中
    - 可用行：bullet `- **可用**：` 開頭的條目行（事件行內文含「可用」不誤判）
    - family 條目：`- **<family 或複合>**：<note>`——note 逐字保留（禁壓縮）
    - 事件行：含「額度事件」或「禁派」的行（人工複核線索）
    """
    state = SpineState()
    family_list = list(families)
    for ln in text.splitlines():
        stripped = ln.strip()
        if state.as_of is None:
            m = AS_OF_RE.search(ln)
            if m:
                state.as_of = m.group(1)
        if stripped.startswith(AVAILABLE_PREFIX):
            state.available_line_found = True
            state.available_line_raw = stripped
            state.available = frozenset(
                fam
                for fam in family_list
                if re.search(rf"\b{re.escape(fam)}\b", stripped, re.IGNORECASE)
            )
        m = ENTRY_RE.match(stripped)
        if m:
            heads = {t.strip().lower() for t in re.split(r"[／/、]", m["head"])}
            for fam in family_list:
                if fam in heads:
                    state.notes[fam] = m["body"]
        if any(kw in stripped for kw in EVENT_KEYWORDS):
            state.events.append(stripped)
    return state


def _family_bindings(catalog) -> dict[str, list]:
    joined = {fam: [] for fam in catalog.families}
    for binding in catalog.bindings.values():
        joined.setdefault(binding.family, []).append(binding)
    return joined


def _print_family_blocks(
    catalog, families_display, spine_state: SpineState, state_of
) -> None:
    """family 覆蓋行（卡③）：每 family 必輸出狀態＋bindings 或顯式 no-binding。"""
    joined = _family_bindings(catalog)
    notes = spine_state.notes
    for fam in families_display:
        # 顯示序僅 family 名稱字母序（display determinism——非候選排序）
        print(f"  {fam} = {state_of(fam)}")
        bindings = joined.get(fam, [])
        if bindings:
            ids = "、".join(f"{b.id}({b.token})" for b in bindings)
            print(f"    bindings family={fam} count={len(bindings)}: {ids}")
        else:
            print(
                f"    no bindings in catalog family={fam}"
                f"——閉集內零 binding（零 candidate，fail-closed；顯式標記禁靜默省略）"
            )
        if fam in notes:
            print(f"    spine note (verbatim): {notes[fam]}")


def main(argv: list[str] | None = None, *, now: datetime | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    # F3：帶 flag 無值 → exit 2（禁靜默退回預設——--spine 無值時會 fail-open
    # 讀真 spine）
    for flag in ("--spine", "--catalog", "--stale-days"):
        if flag in args and args.index(flag) + 1 >= len(args):
            print(f"[FAIL] {flag} 帶 flag 無值——輸入不合法")
            return 2

    def opt_value(flag: str) -> str | None:
        if flag in args:
            idx = args.index(flag)
            if idx + 1 >= len(args):
                return None
            return args[idx + 1]
        return None

    stale_days = STALE_DAYS_DEFAULT
    raw_days = opt_value("--stale-days")
    if raw_days is not None:
        try:
            stale_days = int(raw_days)
        except ValueError:
            print("[FAIL] --stale-days 需一個整數參數——輸入不合法")
            return 2
        if stale_days < 0:
            print("[FAIL] --stale-days 不可為負——輸入不合法")
            return 2
    spine_path = Path(opt_value("--spine") or DEFAULT_SPINE)
    catalog_path = Path(opt_value("--catalog") or DEFAULT_CATALOG)
    now = now or datetime.now(tz=UTC)

    if not spine_path.exists() or not catalog_path.exists():
        print(
            f"[FAIL] 輸入缺席：spine={spine_path.exists()}"
            f" catalog={catalog_path.exists()}——fail-closed，禁建議（exit 2）"
        )
        return 2

    sync = _load_sync_module()
    try:
        catalog = sync.parse_catalog(catalog_path.read_text(encoding="utf-8"))
    except AssertionError as exc:
        print(f"[FAIL] catalog loader 驗證失敗（輸入不合法，exit 2）：{exc}")
        return 2

    spine = parse_spine(spine_path.read_text(encoding="utf-8"), catalog.families)

    # exit 1：as-of 缺席——連新鮮度都無法判定，先於 stale 判定
    if spine.as_of is None:
        print("[FAIL] spine as-of 缺席——無法判定新鮮度，fail-closed（exit 1）")
        return 1

    as_of_date = datetime.fromisoformat(spine.as_of).date()
    age = (now.date() - as_of_date).days
    # F4：as-of 未來（age<0，時區基準 UTC）＝不合法——未來日期非「新」，
    # 直接判 fresh 是 fail-open 漏網
    if age < 0:
        print(
            f"[FAIL] spine as-of {spine.as_of} 為未來日期（age={age}，"
            "時區基準 UTC）——不合法，fail-closed（exit 1）"
        )
        return 1
    stale = age > stale_days
    print(f"[AvailabilitySnapshot] spine={spine_path}")
    print(f"[AvailabilitySnapshot] catalog={catalog_path}")
    print(
        f"[AvailabilitySnapshot] as-of={spine.as_of} age={age}d"
        f" stale-threshold={stale_days}d stale={stale}"
    )
    families_display = sorted(catalog.families)  # 僅顯示序（display determinism）
    print(f"families: ({len(families_display)} family——閉集＝catalog allow_lists)")

    # exit 3：stale——全 family unknown（unknown 永不與可派並存——卡⑥）
    if stale:
        _print_family_blocks(
            catalog,
            families_display,
            spine,
            lambda fam: "unknown（spine stale——先探測再派，禁從歷史 instruction 推定）",
        )
        print(
            f"[WARN] spine as-of {spine.as_of} 距今 {age} 天 >{stale_days}"
            "——現值過期，全部 unknown（exit 3）"
        )
        if spine.events:
            print("[WARN] 額度事件（歷史行，人工複核——stale 下僅供考古）:")
            for e in spine.events:
                print(f"  - {e}")
        return 3

    # exit 1：fresh 但「可用」行缺席或解析出零 family——availability 無法判定
    if not spine.available_line_found or not spine.available:
        if not spine.available_line_found:
            why = "找不到「- **可用**：」條目行"
            print(f"[WARN] 可用行解析失敗（{why}）")
        else:
            print(
                f"[WARN] 可用行解析出零 family（malformed——原文："
                f"{spine.available_line_raw}）"
            )
        print("[FAIL] 可用行缺席或零 family——無法判定，fail-closed（exit 1）")
        return 1

    # exit 0：fresh evaluation——per-family tri-state
    _print_family_blocks(
        catalog,
        families_display,
        spine,
        lambda fam: (
            "available" if fam in spine.available else "unavailable（可用行未列）"
        ),
    )

    # 衝突配對（F1 收緊）：family 名＋限制詞「同行共現」才算衝突——僅 family
    # 名命中（如「能力序裁定」形態行）降為中性並列複核；衝突≠crash≠降級，
    # 基準＝as-of 可用行，判斷歸 LLM（卡⑦）
    conflicts: list[tuple[str, str]] = []
    parallels: list[tuple[str, str]] = []
    for fam in families_display:
        if fam not in spine.available:
            continue
        for e in spine.events:
            if not re.search(rf"\b{re.escape(fam)}\b", e, re.IGNORECASE):
                continue
            if any(kw in e.lower() for kw in RESTRICTION_KEYWORDS):
                conflicts.append((fam, e))
            else:
                parallels.append((fam, e))
    if conflicts:
        print(
            "[WARN] 可用行與事件衝突（family＋限制詞〔禁派/耗盡/reset/1308/"
            "429〕同行共現；基準＝as-of 可用行，事件行待人工複核——判斷腿，"
            "本 evaluator 不裁決）:"
        )
        for fam, e in conflicts:
            print(f"  {fam} × {e}")
    if parallels:
        print(
            "[WARN] 並列複核（事件行含 family 名但無限制詞共現——中性並列，"
            "判讀須讀 spine 原文）:"
        )
        for fam, e in parallels:
            print(f"  {fam} × {e}")
    if spine.events:
        print("[WARN] 額度事件（歷史行，人工複核是否已折入 as-of 基準）:")
        for e in spine.events:
            print(f"  - {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
