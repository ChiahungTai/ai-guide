#!/usr/bin/env python
"""arc_goal_compile——AIR-135.1.1 C5b goal compiler core：卡 AC explicit verifier → acceptance_contract 的 pure predicate compiler。

邊界（卡面已決策勿重辯——codex 裁決第 1/7 點為主軸）：
- pure compiler：無 process side effects（不 spawn、不寫卡、不觸 git）、無
  engine、不調四支週邊（intent_review／checkpoint_obligation／w3_checkpoint_link
  ／receipt_normalize 各自在既有時點獨立跑——接線契約是欄位名，不是函數調用）。
- card AC 仍是唯一 source of truth；本編譯器只把「已明文化的 verifier」變成
  predicate，禁 regex 猜自然語言（LLM 猜測包成 compiler＝silent corruption）。
- 編譯結果不是第五個 durable workflow artifact——它是 ArcPlan 新增的
  machine-invariant `acceptance_contract` 區塊（schema owner＝scripts/arc_spec.py）。
- 不合 grammar 的 AC fail-closed 為 judgment_required（reason=no-explicit-verifier），
  永不靜默丟失；集合不變式四條為核心 oracle（compile 時以輸入對照自檢）。
- 已勾 `[x]` AC 編成已滿足 predicate（帶 baseline 身份）——重編譯不丟已完成證據。

explicit verifier grammar（v1——自真實卡歸納：AIR-135.4／air-227/228/229 的 AC
段實際形狀全是 prose，無一帶 grammar 形；故 grammar 取最小無歧義形，寧可
judgment_required 也不猜）::

    AC item  := checkbox 行（`- [ ]`／`- [x]` 前綴，可帶 `#N` 顯式 id）
                ＋緊鄰續行（連續非空、非新 item、非 section 邊界的行；
                ``` 圍欄區塊整段跳過——圍欄內容不成 item 亦不作續行）
    verifier := COMMAND SP ARROW SP EXPECTED（同一行內）
    COMMAND  := `...` code span，內容 strip 後非空
    ARROW    := `→` 或 `->`
    EXPECTED := arrow 後同行剩餘文字，strip 後非空（`exit 0`、錨點詞皆可）

段邊界：AC 段掃描終止於 AC:END marker（優先）或任一 ATX heading（`^#{1,6}`＋空白）
——marker 缺席時 heading 亦終止，plan 正文不得漏進末條 AC；checkbox-like 續行
（`1. [ ]`／`- [?`／`-[]` 等不合 item grammar 的 `[` 行）＝疑似 malformed item，
fail-loud 不靜默吞併。frontmatter `id:` 只認第一個 `---` 圍欄區塊——正文 id 行
不充當 card_id。

分類三態（對每個 AC item）：
- 恰一個 verifier match → predicate（kind=command_expected，v1 唯一產出 kind；
  artifact／schema／state_transition 為保留枚舉）
- 無 match 且無 malformed 訊號 → judgment_required（reason=no-explicit-verifier）
- malformed（code span+arrow 但 command 空白或 expected 空白）或同 AC 多個
  verifier match（歧義——應拆條）→ 編譯錯 fail-loud（exit 2）

禁猜例：純文字箭頭（如「full→`--model X`」arrow 前是 prose 非 code span）不構成
verifier——該 AC 走 judgment_required；code span 存在但無 arrow（如 `.html`）同理。
第三向（v1 已知殘留誤判面——muse F3）：描述性 prose 恰好含 code span＋箭頭
（如「確認 config `A` -> `B` fallback」）會按 grammar 字面升為 predicate——語義
是敘述非機驗命令；render 人話段＋摘要行使誤編可見，wiring 弧 Plan Preview
人話複核承接，v1 不另加機制。

CLI：
- `uv run python scripts/arc_goal_compile.py CARD [--baseline SHA] [--out PATH]`
  ——預設 stdout 印人話 md（含 ```json 區塊）＋摘要行；`--out` 落檔時 stdout
  仍印摘要行。canonical JSON＝sort_keys＋緊湊分隔符＋UTF-8（同 arc_spec）。
- exit 0＝成功；exit 2＝契約/parse 錯（無 frontmatter id、無 AC 段、AC 段空、
  duplicate ac_id、malformed/歧義 verifier、續行疑似 malformed item、
  帶 `[x]` 而未給 --baseline、baseline 格式錯）——錯誤逐行 stderr，文案列
  可用值（arc_spec fail-loud 同形）。

決定性：輸出不含時鐘/process 鹽——同卡同 baseline 兩跑 byte-equal；contract
canonical JSON 可直接嵌 ArcPlan（plan hash 覆蓋）。
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ACCEPTANCE_CONTRACT_SCHEMA = "acceptance-contract/1"
# kind 枚舉（卡面：初版 command_expected 為主，其餘保留）
PREDICATE_KINDS = ("command_expected", "artifact", "schema", "state_transition")
JUDGMENT_REASONS = ("no-explicit-verifier",)

BASELINE_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
FRONTMATTER_ID_RE = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
# frontmatter 只認第一個 `---` 圍欄區塊——正文 `id:` 行不充當 card_id（R5）
FRONTMATTER_BLOCK_RE = re.compile(
    r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL
)
AC_HEADING_RE = re.compile(r"^#{1,6}\s*Acceptance Criteria\s*$")
# 任一 ATX heading 皆為 section 邊界（AC:END marker 優先；R1）
ATX_HEADING_RE = re.compile(r"^#{1,6}\s")
AC_ITEM_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s*(.*)$")
# checkbox-like 但不合 AC item grammar（`1. [ ]`／`- [?`／`-[]`）——續行偵測用
# （R3：作續行即疑似 malformed item，fail-loud 禁靜默吞併）
CHECKBOX_LIKE_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)]?)\s*\[")
AC_EXPLICIT_ID_RE = re.compile(r"^#(\d+)\s+(.*)$")
VERIFIER_RE = re.compile(r"`([^`]*)`\s*(?:→|->)\s*(\S.*?\S|\S)\s*$")
# malformed 訊號：意圖是 verifier（code span 緊鄰 arrow）但 command/expected 缺一
MALFORMED_EMPTY_COMMAND_RE = re.compile(r"`\s*`\s*(?:→|->)")
MALFORMED_EMPTY_EXPECTED_RE = re.compile(r"`[^`]+`\s*(?:→|->)\s*$")

AC_END_MARKER = "<!-- AC:END -->"


class GoalCompileError(Exception):
    """contract/parse 錯——fail-loud（exit 2），不靜默分類。"""


@dataclass(frozen=True)
class AcItem:
    """單條 AC——id／勾選態／block 行（item 行本文＋緊鄰續行）。"""

    ac_id: str
    checked: bool
    lines: tuple[str, ...]  # [0]＝checkbox 行本文；其餘＝緊鄰續行


def parse_card(card_text: str) -> tuple[str, list[AcItem]]:
    """抽 frontmatter id＋AC 段 items——無 id／無段／空段皆 fail-loud。"""
    block = FRONTMATTER_BLOCK_RE.match(card_text)
    id_match = (
        FRONTMATTER_ID_RE.search(block.group(1)) if block is not None else None
    )
    if id_match is None:
        raise GoalCompileError(
            "card frontmatter 缺 `id:` 欄——acceptance_contract 須回指卡節點身分"
            "（fail-loud；禁由檔名猜 card id；`id:` 須在第一個 `---` 圍欄區塊內，"
            "正文 id 行不充當）"
        )
    card_id = id_match.group(1)

    lines = card_text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if AC_HEADING_RE.match(ln)), None
    )
    if start is None:
        raise GoalCompileError(
            "card 無 `## Acceptance Criteria` 段——無 AC 可編譯（fail-loud；"
            "小 bug/免卡工單不應跑本編譯器）"
        )

    items: list[AcItem] = []
    current: list[str] | None = None
    current_checked = False
    in_fence = False
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue  # 圍欄行整段跳過——fenced code 不成 item 亦不作續行（R3）
        if in_fence:
            continue
        if stripped == AC_END_MARKER or ATX_HEADING_RE.match(line):
            break  # AC:END marker 優先；任一 ATX heading 皆 section 邊界（R1）
        item_match = AC_ITEM_RE.match(line)
        if item_match is not None:
            if current is not None:
                items.append(_make_item(current, current_checked, len(items)))
            current = [item_match.group(2)]
            current_checked = item_match.group(1) in ("x", "X")
            continue
        if current is None:
            continue  # heading 與首 item 間的前言／marker
        if not stripped:
            items.append(_make_item(current, current_checked, len(items)))
            current = None
            continue
        if CHECKBOX_LIKE_RE.match(line):
            raise GoalCompileError(
                f"AC 續行疑似 malformed item：`{stripped}` — checkbox-like 行"
                f"不作續行（疑漏 `- [ ]` 前綴或勾選記號非法；fail-loud 禁靜默"
                f"吞併致 AC 無聲消失）"
            )
        current.append(line)
    if current is not None:
        items.append(_make_item(current, current_checked, len(items)))

    if not items:
        raise GoalCompileError(
            "AC 段存在但零 item——空契約視同 parse 失敗（fail-loud）"
        )
    return card_id, items


def _make_item(raw_lines: list[str], checked: bool, ordinal: int) -> AcItem:
    """組 AcItem——`#N` 顯式 id 優先，否則 1-based 段內序號；重號 fail-loud 由
    compile_card 的唯一性檢查承接。"""
    first = raw_lines[0]
    explicit = AC_EXPLICIT_ID_RE.match(first)
    if explicit is not None:
        ac_id = explicit.group(1)
        lines = [explicit.group(2), *raw_lines[1:]]
    else:
        ac_id = str(ordinal + 1)
        lines = list(raw_lines)
    return AcItem(ac_id=ac_id, checked=checked, lines=tuple(lines))


def extract_verifier(item: AcItem) -> tuple[str, str] | None:
    """grammar 抽取——回 (command, expected) 或 None（judgment_required 路徑）；
    malformed／歧義 raise GoalCompileError（fail-closed，不猜）。"""
    matches = [m for line in item.lines for m in VERIFIER_RE.finditer(line)]
    good = [m for m in matches if m.group(1).strip()]
    malformed = any(
        pattern.search(line)
        for line in item.lines
        for pattern in (MALFORMED_EMPTY_COMMAND_RE, MALFORMED_EMPTY_EXPECTED_RE)
    )
    if len(good) > 1:
        raise GoalCompileError(
            f"ac #{item.ac_id} 帶 {len(good)} 個 verifier match——歧義"
            f"（fail-loud；一條 AC 一 verifier，多驗證式請拆條）"
        )
    if len(good) == 1:
        if malformed or len(matches) > 1:
            raise GoalCompileError(
                f"ac #{item.ac_id} 同時帶合法 verifier 與 malformed verifier 訊號"
                f"——意圖歧義（fail-loud；修正卡面 grammar 形後重編）"
            )
        expected_text = good[0].group(2)
        if VERIFIER_RE.search(expected_text):
            # 同行第二組 code span+arrow 被貪婪 expected 吞入——歧義，禁靜默擇一
            raise GoalCompileError(
                f"ac #{item.ac_id} 帶多個 verifier match——歧義"
                f"（fail-loud；一條 AC 一 verifier，多驗證式請拆條）"
            )
        return good[0].group(1).strip(), expected_text.strip()
    if malformed:
        empty_command = any(
            MALFORMED_EMPTY_COMMAND_RE.search(line) for line in item.lines
        )
        hint = (
            "；雙 backtick span 不支援，請用單 backtick 形" if empty_command else ""
        )
        raise GoalCompileError(
            f"ac #{item.ac_id} malformed verifier——code span 緊鄰 arrow 但 "
            f"command 空白或 expected 空白（fail-closed；grammar："
            f"`command` → expected，兩端皆須非空{hint}）"
        )
    return None


def compile_card(
    card_text: str, source_card: str, baseline: str | None = None
) -> dict:
    """卡文本 → acceptance_contract dict（純函數；集合不變式四條自檢）。

    baseline＝card tree baseline SHA（呼叫端顯式傳——純編譯器不觸 git）；卡帶
    `[x]` AC 時必填（已滿足 predicate 須帶 baseline 身份，否則 fail-loud）。
    """
    if baseline is not None and not BASELINE_RE.match(baseline):
        raise GoalCompileError(
            f"Invalid baseline `{baseline}` — 需 hex 7-40 位（card tree baseline SHA）"
        )

    card_id, items = parse_card(card_text)

    seen: dict[str, AcItem] = {}
    for item in items:
        if item.ac_id in seen:
            raise GoalCompileError(
                f"Duplicate AC id `#{item.ac_id}` — ac 身分歧義"
                f"（雙 authoritative，fail-loud）"
            )
        seen[item.ac_id] = item

    checked_ids = [i.ac_id for i in items if i.checked]
    if checked_ids and baseline is None:
        raise GoalCompileError(
            f"卡帶已勾 AC（{', '.join('#' + i for i in checked_ids)}）但未給 "
            f"--baseline——已滿足 predicate 須帶 baseline 身份（重編譯不丟已完成"
            f"證據；fail-loud）"
        )

    predicates: list[dict] = []
    judgment_required: list[dict] = []
    expected_pred_ids: list[str] = []
    expected_jud_ids: list[str] = []
    for item in items:
        verifier = extract_verifier(item)
        if verifier is not None:
            command, expected = verifier
            predicates.append(
                {
                    "ac_id": item.ac_id,
                    "kind": "command_expected",
                    "verifier": command,
                    "expected": expected,
                    "satisfied": item.checked,
                    "satisfied_at_baseline": baseline if item.checked else None,
                }
            )
            expected_pred_ids.append(item.ac_id)
        elif item.checked:
            # 已勾無 verifier——勾選即 baseline 證據；kind/verifier 不適用（null）
            predicates.append(
                {
                    "ac_id": item.ac_id,
                    "kind": None,
                    "verifier": None,
                    "expected": None,
                    "satisfied": True,
                    "satisfied_at_baseline": baseline,
                }
            )
            expected_pred_ids.append(item.ac_id)
        else:
            judgment_required.append(
                {"ac_id": item.ac_id, "reason": "no-explicit-verifier"}
            )
            expected_jud_ids.append(item.ac_id)

    contract: dict = {
        "schema": ACCEPTANCE_CONTRACT_SCHEMA,
        "card_id": card_id,
        "source_card": source_card,
        "ac_ids": [i.ac_id for i in items],
        "predicates": predicates,
        "judgment_required": judgment_required,
    }
    if baseline is not None:
        contract["card_baseline"] = baseline

    _check_set_invariants(contract, expected_pred_ids, expected_jud_ids)
    return contract


def _check_set_invariants(
    contract: dict, expected_pred_ids: list[str], expected_jud_ids: list[str]
) -> None:
    """集合不變式四條（核心 oracle——以輸入對照驗；違反＝編譯器 bug，fail-loud）：
    1. verifier-bearing/已勾 AC == exactly-once predicates
    2. no-verifier 未勾 AC == exactly-once judgment_required
    3. predicates ∪ judgment_required == 全部 AC
    4. predicates ∩ judgment_required == ∅
    """
    ac_ids = contract["ac_ids"]
    pred_ids = [p["ac_id"] for p in contract["predicates"]]
    jud_ids = [j["ac_id"] for j in contract["judgment_required"]]

    def _fail(msg: str) -> None:
        raise GoalCompileError(f"集合不變式違約（compiler 自檢）: {msg}")

    if len(set(ac_ids)) != len(ac_ids):
        _fail(f"ac_ids 含重號: {ac_ids}")
    if len(set(pred_ids)) != len(pred_ids):
        _fail(f"predicates 含重複 ac_id: {pred_ids}")
    if len(set(jud_ids)) != len(jud_ids):
        _fail(f"judgment_required 含重複 ac_id: {jud_ids}")
    if sorted(pred_ids) != sorted(expected_pred_ids):
        _fail(
            f"predicates 集合 {sorted(pred_ids)} != 輸入對照 "
            f"{sorted(expected_pred_ids)}（不變式 1）"
        )
    if sorted(jud_ids) != sorted(expected_jud_ids):
        _fail(
            f"judgment_required 集合 {sorted(jud_ids)} != 輸入對照 "
            f"{sorted(expected_jud_ids)}（不變式 2）"
        )
    union = set(pred_ids) | set(jud_ids)
    all_set = set(ac_ids)
    if union != all_set:
        lost = sorted(all_set - union)
        if lost:
            _fail(f"AC id {lost} 遺失——不變式 3（聯集=全部；靜默丟失禁）")
        extra = sorted(union - all_set)
        if extra:
            _fail(
                f"AC id {extra} 不在 ac_ids 全集——不變式 3 反向包含"
                f"（predicate/judgment 帶全集外身分；禁）"
            )
    if set(pred_ids) & set(jud_ids):
        _fail(
            f"ac_id {sorted(set(pred_ids) & set(jud_ids))} 雙重歸類——不變式 4"
            f"（交集=空）"
        )


def canonical_json(data: dict) -> str:
    """canonical JSON——sort_keys＋緊湊分隔符＋UTF-8（同 arc_spec 慣例）。"""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def summary_line(contract: dict) -> str:
    """`predicates: N／judgment-required: N（列 ac_id）` 摘要行。"""
    jud_ids = ", ".join(j["ac_id"] for j in contract["judgment_required"])
    tail = f"（{jud_ids}）" if jud_ids else "（無）"
    return (
        f"predicates: {len(contract['predicates'])}／"
        f"judgment-required: {len(contract['judgment_required'])}{tail}"
    )


def render_markdown(contract: dict) -> str:
    """人話 md 摘要＋```json 區塊（雙承載同檔；arc_spec 四物同形）。"""
    lines = [
        f"# Acceptance Contract——{contract['card_id']}",
        "",
        f"- source_card: {contract['source_card']}",
    ]
    if contract.get("card_baseline"):
        lines.append(f"- card_baseline: {contract['card_baseline']}")
    lines.append(f"- {summary_line(contract)}")
    lines.append("")

    lines.append("## Predicates")
    lines.append("")
    if contract["predicates"]:
        for p in contract["predicates"]:
            if p["satisfied"]:
                state = f"satisfied@{p['satisfied_at_baseline']}"
            else:
                state = "open"
            label = p["kind"] or "checked-baseline"
            lines.append(f"- ac #{p['ac_id']} — {label}（{state}）")
            if p["verifier"] is not None:
                lines.append(f"  - verifier: `{p['verifier']}`")
                lines.append(f"  - expected: {p['expected']}")
    else:
        lines.append("（無——本卡 AC 無一帶 explicit verifier）")
    lines.append("")

    lines.append("## Judgment Required（reason=no-explicit-verifier）")
    lines.append("")
    if contract["judgment_required"]:
        for j in contract["judgment_required"]:
            lines.append(f"- ac #{j['ac_id']}")
    else:
        lines.append("（無——全部 AC 皆編成 predicate）")
    lines.append("")
    lines.append("```json")
    lines.append(canonical_json(contract))
    lines.append("```")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arc_goal_compile",
        description=(
            "AIR-135.1.1 C5b goal compiler：卡 AC explicit verifier → "
            "acceptance_contract（pure predicate compiler；grammar 見模組 docstring）"
        ),
        epilog=(
            "grammar：`command` → expected（同行；code span 緊鄰 arrow；兩端非空）——"
            "不合 grammar 的 AC fail-closed 為 judgment_required，永不靜默丟失"
        ),
    )
    parser.add_argument("card", help="卡檔路徑（markdown；frontmatter id＋AC 段）")
    parser.add_argument(
        "--baseline",
        help="card tree baseline SHA（hex 7-40 位）；卡帶 [x] AC 時必填",
    )
    parser.add_argument(
        "--out",
        help="人話 md（含 json 區塊）落檔路徑；缺＝印 stdout（摘要行恆印 stdout）",
    )

    args = parser.parse_args(argv)
    path = Path(args.card)
    if not path.exists():
        print(f"[arc-goal] ERROR: card not found: {path}", file=sys.stderr)
        return 2
    try:
        contract = compile_card(
            path.read_text(encoding="utf-8"),
            source_card=path.as_posix(),
            baseline=args.baseline,
        )
    except GoalCompileError as e:
        print(f"[arc-goal] ERROR: {e}", file=sys.stderr)
        return 2

    rendered = render_markdown(contract)
    if args.out:
        out_path = Path(args.out)
        if out_path.parent and not out_path.parent.exists():
            out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"[arc-goal] acceptance_contract written: {out_path}")
    else:
        sys.stdout.write(rendered)
    print(summary_line(contract))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
