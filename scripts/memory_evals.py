#!/usr/bin/env python3
"""AIR-187 S2——eval grader harness（golden 逐條 classify → per-tier P/R 報告）。

定位（AC#2 驗證式「memory_evals.py --golden 全綠＋數字落檔」的機械載體）：
消費版控 golden（tests/memory_guard_golden.json；權威＝人工 adjudication），
對每條跑 scripts/memory_guard_rules.py 的 classify/classify_detail，產 stdout
報告：總計、正類（instruction-shaped）precision/recall、per-tier one-vs-rest
P/R 表、誤殺清單、漏放清單、review 例計數。

指標語義（工單「instruction-shaped 為正類；review 單列不算錯誤但計數」）
──────────────────────────────────────────────────────────────────────────
- 正類＝instruction-shaped：TP＝expect=pos∧got=pos、FP＝expect≠pos∧got=pos
  （review→pos 也計 FP——數字照實反映過旗面）、FN＝expect=pos∧got≠pos。
- per-tier 表＝三級各做 one-vs-rest P/R；review 行單列標 advisory——review
  樣本不計入正類錯誤清單（誤殺／漏放），僅在「review 例計數」段計數。
- 誤殺清單＝expect=clean 而 got≠clean（blocked_by=black 即 09-09 回測誤傷
  回歸面；blocked_by=review 為軟誤報——白例被疑訊號命中）。
- 漏放清單＝expect=instruction-shaped 而 got≠instruction-shaped。

exit 契約
─────────
- 0＝golden 全量 conform（與 tests/test_memory_guard_rules.py 的 golden 全量
  參數化斷言同一基準——本工具是該契約的 CLI 鏡像＋統計層；review 例漂移
  也是 misclassify：golden expect 即契約，review 的「不算錯誤」僅指不入
  正類錯誤清單）。
- 1＝任何 misclassify（誤殺／漏放／review 漂移任一非空）。
- 2＝fail-loud：golden 檔缺／壞 JSON／schema 違反（缺 id/expect/text/why、
  expect 超出三級契約、id 重複）／rule module 載入失敗。

邊界
────
- self-grade 禁作 oracle：本工具只報 classify 對 golden 的 conform，不對
  golden 語義再判；golden 擴充須經 marshal adjudication（池抽樣候選清單
  .agent-tmp/pool-sample-candidates.json 非 golden、非本工具輸入）。
- golden 數量下限（正反例 ≥8/8/4、總數 ≥20）歸 pytest inventory 測試管，
  本工具不重刻下限門檻。
- 純唯讀：只讀 golden 與 rule module，無寫入無網路。

用法：uv run python scripts/memory_evals.py --golden tests/memory_guard_golden.json
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
GUARD_RULES_PATH = SCRIPTS_DIR / "memory_guard_rules.py"

TIERS: tuple[str, ...] = ("instruction-shaped", "clean", "review")
POSITIVE_TIER = "instruction-shaped"

EXIT_OK = 0
EXIT_MISCLASSIFY = 1
EXIT_FAIL_LOUD = 2


def _load_guard_rules():
    """以檔案路徑載入同目錄 rule module（repo scripts 非 package，同 tests/conftest.py）。"""
    spec = importlib.util.spec_from_file_location("memory_guard_rules", GUARD_RULES_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"無法為 {GUARD_RULES_PATH} 建立 import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_golden(path: Path) -> list[dict]:
    """載入 golden 並驗 schema；任何違反 raise ValueError（caller 轉 exit 2）。"""
    if not path.is_file():
        raise ValueError(f"golden 檔不存在：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"golden 非合法 JSON（{path}）：{exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError(f"golden 頂層契約違反（{path}）：須為含 entries list 的 JSON 物件")
    seen_ids: set[str] = set()
    for idx, entry in enumerate(data["entries"]):
        where = f"entries[{idx}]"
        if not isinstance(entry, dict):
            raise ValueError(f"golden schema：{where} 須為物件")
        for key in ("id", "expect", "why"):
            val = entry.get(key)
            if not isinstance(val, str) or not val:
                raise ValueError(f"golden schema：{where} 缺 {key}（或非非空字串）")
        if not isinstance(entry.get("text"), str):
            raise ValueError(f"golden schema：{where}（{entry['id']}）缺 text（須字串，可空）")
        meta = entry.get("meta")
        if meta is not None and not isinstance(meta, dict):
            raise ValueError(f"golden schema：{where}（{entry['id']}）meta 須為物件")
        if entry["expect"] not in TIERS:
            raise ValueError(
                f"golden schema：{where}（{entry['id']}）expect {entry['expect']!r} 不在三級契約 {TIERS}"
            )
        if entry["id"] in seen_ids:
            raise ValueError(f"golden schema：id 重複：{entry['id']}")
        seen_ids.add(entry["id"])
    return data["entries"]


def _ratio(num: int, den: int) -> str:
    return f"{num / den:.4f}" if den > 0 else "n/a"


def _one_vs_rest(results: list[dict], tier: str) -> tuple[int, int, int]:
    """tier 為目標類的 one-vs-rest (tp, fp, fn)。"""
    tp = sum(1 for r in results if r["expect"] == tier and r["got"] == tier)
    fp = sum(1 for r in results if r["expect"] != tier and r["got"] == tier)
    fn = sum(1 for r in results if r["expect"] == tier and r["got"] != tier)
    return tp, fp, fn


def _mis_detail_line(r: dict, prefix: str = "") -> str:
    entry = r["entry"]
    return (
        f"  - {prefix}{entry['id']}：expect {entry['expect']}，got {r['got']}；"
        f"why={entry['why']}；命中訊號 {r['detail'] or '無'}；text={entry['text'][:60]!r}"
    )


def _blocked_by(r: dict) -> str:
    return "black" if any(h.startswith("black:") for h in r["detail"]) else "review"


def _report(results: list[dict], golden_path: Path) -> str:
    total = len(results)
    pos = [r for r in results if r["expect"] == POSITIVE_TIER]
    clean = [r for r in results if r["expect"] == "clean"]
    review = [r for r in results if r["expect"] == "review"]
    misclassified = [r for r in results if r["got"] != r["expect"]]

    lines: list[str] = [
        "[AIR-187 S2] memory_evals — golden grader",
        f"golden：{golden_path}（{total} 條：instruction-shaped {len(pos)}／clean {len(clean)}／review {len(review)}）",
        "",
        "== 總計 ==",
        f"  conform {total - len(misclassified)}/{total}；misclassify {len(misclassified)}",
        "",
        "== 正類 instruction-shaped P/R ==",
    ]
    tp, fp, fn = _one_vs_rest(results, POSITIVE_TIER)
    lines.append(f"  TP {tp}  FP {fp}  FN {fn}")
    lines.append(f"  precision {_ratio(tp, tp + fp)}  recall {_ratio(tp, tp + fn)}")
    lines.append("")
    lines.append("== per-tier P/R（one-vs-rest；review 單列——不入正類錯誤清單，僅計數）==")
    for tier in TIERS:
        t_tp, t_fp, t_fn = _one_vs_rest(results, tier)
        support = sum(1 for r in results if r["expect"] == tier)
        mark = "  (advisory)" if tier == "review" else ""
        lines.append(
            f"  {tier:<20} support {support:>3}  precision {_ratio(t_tp, t_tp + t_fp)}"
            f"  recall {_ratio(t_tp, t_tp + t_fn)}{mark}"
        )

    lines.append("")
    lines.append("== 誤殺清單（expect=clean 而 got≠clean；black＝09-09 誤傷回歸面）==")
    blocks = [r for r in results if r["expect"] == "clean" and r["got"] != "clean"]
    if not blocks:
        lines.append("  （無）")
    for r in blocks:
        lines.append(_mis_detail_line(r, prefix=f"[blocked_by={_blocked_by(r)}] "))

    lines.append("")
    lines.append("== 漏放清單（expect=instruction-shaped 而未中正類）==")
    missed = [r for r in results if r["expect"] == POSITIVE_TIER and r["got"] != POSITIVE_TIER]
    if not missed:
        lines.append("  （無）")
    for r in missed:
        lines.append(_mis_detail_line(r))

    lines.append("")
    lines.append("== review 例計數（expect=review；漂移計 misclassify 但不入誤殺/漏放清單）==")
    review_hit = sum(1 for r in review if r["got"] == "review")
    review_drift = [r for r in review if r["got"] != "review"]
    lines.append(f"  命中 review {review_hit}/{len(review)}；漂移 {len(review_drift)}")
    for r in review_drift:
        lines.append(_mis_detail_line(r))

    lines.append("")
    if misclassified:
        lines.append(f"[FAIL] golden misclassify {len(misclassified)} 條——exit {EXIT_MISCLASSIFY}")
    else:
        lines.append(f"[OK] golden 全量 conform——exit {EXIT_OK}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="memory_evals.py",
        description=(
            "AIR-187 S2 grader：golden 逐條 classify → per-tier P/R 報告"
            f"（exit {EXIT_OK} 全綠／{EXIT_MISCLASSIFY} misclassify／{EXIT_FAIL_LOUD} fail-loud）"
        ),
    )
    parser.add_argument(
        "--golden", required=True, help="golden JSON 路徑（如 tests/memory_guard_golden.json）"
    )
    args = parser.parse_args(argv)
    golden_path = Path(args.golden)

    try:
        module = _load_guard_rules()
    except Exception as exc:  # rule module 缺/語法錯——fail-loud 載入面
        print(f"[FAIL] rule module 載入失敗（{GUARD_RULES_PATH}）：{exc}", file=sys.stderr)
        return EXIT_FAIL_LOUD
    try:
        entries = _load_golden(golden_path)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return EXIT_FAIL_LOUD

    results: list[dict] = []
    for entry in entries:
        meta = entry.get("meta") or {}
        results.append(
            {
                "entry": entry,
                "expect": entry["expect"],
                "got": module.classify(entry["text"], meta),
                "detail": module.classify_detail(entry["text"], meta),
            }
        )

    print(_report(results, golden_path))
    return EXIT_MISCLASSIFY if any(r["got"] != r["expect"] for r in results) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
