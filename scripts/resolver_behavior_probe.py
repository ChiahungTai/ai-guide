#!/usr/bin/env python3
"""resolver_behavior_probe——resolver instruction behavior lane（AIR-245）。

鏈形（codex §C 設計權威）：LLM dry-run → structured proposed decision →
deterministic hard-invariant checker → verdict。本工具是鏈的**後半
（deterministic 半）**：對 corpus 每案讀 `responses/rep-<n>.json`
（fresh-agent dry-run 捕獲的 structured decision artifact）→ 餵
resolver_decision_check（單一源 import，禁自刻第二份 invariant 實作）→
per-sample verdict。

dry-run 前半（fresh-agent 演練）依 consumer-dryrun-corpus 協議執行
（skills/_common/consumer-dryrun-corpus.md——fresh agent、prompt 只描述
consumer goal），產出落 corpus case 的 responses/。

INCONCLUSIVE 契約：provider/runtime failure（explicit marker artifact）、
rep 缺席、malformed、proposed decision 結構不合法——皆記 INCONCLUSIVE
如實上報，**禁 retry-to-green**（本工具無任何重試路徑；補跑＝新的
dry-run capture，屬演練側，非本工具職責）。違規判定唯一源＝checker：
結構不合法是「無法判讀」（INCONCLUSIVE），不是 violation。

corpus 形態：
  <corpus>/case-*/case.json              # 情境 brief（dry-run prompt provenance）
  <corpus>/case-*/responses/rep-N.json   # N=1..reps；structured decision
                                         # 或 {"status":"inconclusive","reason":...}

exit 契約：0＝完成樣本 ≥1 且全 admissible（INCONCLUSIVE 如實列出）；
1＝≥1 完成樣本違反 hard invariant（behavior finding）；2＝corpus 或參數
不合法（dir 缺、case.json 缺/malformed、reps<1、全 corpus 零 artifact）；
3＝有 artifact 但零完成 admissible 樣本（全 INCONCLUSIVE）——不可宣稱
pass（F1，R1 修復批）。
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    """importlib 載入 scripts/resolver_decision_check.py（invariant 判定
    單一源——probe 禁第二份實作）。"""
    path = REPO_ROOT / "scripts" / "resolver_decision_check.py"
    spec = importlib.util.spec_from_file_location("resolver_decision_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_checker = _load_checker()


# ---- sample 分類（唯一出口＝_classify_decision，測試直接消費）----


def _classify_decision(data: object) -> tuple[str, str]:
    """已載入的 rep 內容 → (cls, detail)；cls ∈ {admissible, violation,
    inconclusive}。違規判定唯一源＝resolver_decision_check。"""
    if not isinstance(data, dict):
        return "inconclusive", f"rep 非 JSON object（{type(data).__name__}）——無法判讀"
    if data.get("status") == "inconclusive":
        reason = data.get("reason")
        if not isinstance(reason, str) or not reason:
            reason = "reason 缺席"
        return "inconclusive", reason
    input_errors, violations = _checker.validate_decision(data)
    if input_errors:
        return (
            "inconclusive",
            "proposed decision 結構不合法（" + "; ".join(input_errors) + "）——無法判讀",
        )
    if violations:
        return "violation", "; ".join(violations)
    return "admissible", ""


def _classify_rep(path: Path | None) -> tuple[str, str]:
    if path is None or not path.is_file():
        return "inconclusive", "rep artifact 缺席——無完成樣本"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "inconclusive", f"rep artifact malformed（{exc}）——無法判讀"
    return _classify_decision(data)


# ---- corpus 掃描 ----


def _scan_corpus(
    corpus: Path, reps: int
) -> tuple[int, dict[str, int], int, list[str]]:
    """回 (artifact 總數, 分類計數, case 數, 輸出行)。corpus 不合法→
    RuntimeError。"""
    cases = sorted(p for p in corpus.iterdir() if p.is_dir() and p.name.startswith("case-"))
    if not cases:
        raise RuntimeError(f"corpus 內零 case-* 目錄：{corpus}")
    counts = {"admissible": 0, "violation": 0, "inconclusive": 0}
    lines: list[str] = []
    artifacts = 0
    for case in cases:
        case_json = case / "case.json"
        if not case_json.is_file():
            raise RuntimeError(f"case.json 缺席：{case}")
        try:
            brief = json.loads(case_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"case.json malformed：{case_json}（{exc}）") from exc
        if not isinstance(brief, dict):
            raise TypeError(f"case.json 須為 object：{case_json}")
        lines.append(f"[{case.name}] {brief.get('case_id', case.name)}")
        rollup = {"admissible": 0, "violation": 0, "inconclusive": 0}
        resp_dir = case / "responses"
        for n in range(1, reps + 1):
            path = resp_dir / f"rep-{n}.json"
            if path.is_file():
                artifacts += 1
            cls, detail = _classify_rep(path)
            rollup[cls] += 1
            counts[cls] += 1
            line = f"[{case.name}] rep-{n} {cls.upper()}"
            if detail:
                line += f"（{detail}）"
            lines.append(line)
        lines.append(
            f"[{case.name}] rollup: admissible={rollup['admissible']} "
            f"violation={rollup['violation']} inconclusive={rollup['inconclusive']}"
        )
    return artifacts, counts, len(cases), lines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="resolver_behavior_probe",
        description=(
            "AIR-245 resolver behavior lane：corpus 每案 dry-run 捕獲的 "
            "structured decision → hard-invariant checker → verdict；"
            "provider/runtime failure 記 INCONCLUSIVE，禁 retry-to-green"
        ),
    )
    p.add_argument("--corpus", required=True, help="corpus 目錄（case-*/）")
    p.add_argument("--reps", type=int, default=5, help="每案 rep 數（預設 5）")

    args = p.parse_args(argv)
    corpus = Path(args.corpus)
    if args.reps < 1:
        print(f"[resolver-behavior-probe] ERROR: --reps 須 ≥ 1，got {args.reps}", file=sys.stderr)
        return 2
    if not corpus.is_dir():
        print(f"[resolver-behavior-probe] ERROR: corpus 目錄不存在：{corpus}", file=sys.stderr)
        return 2
    try:
        artifacts, counts, case_count, lines = _scan_corpus(corpus, args.reps)
    except (RuntimeError, TypeError) as exc:
        print(f"[resolver-behavior-probe] ERROR: {exc}", file=sys.stderr)
        return 2
    if artifacts == 0:
        print(
            "[resolver-behavior-probe] ERROR: corpus 零 rep artifact"
            "——無任何 dry-run capture（fail-loud）",
            file=sys.stderr,
        )
        return 2
    print(
        f"[resolver-behavior-probe] corpus={corpus} reps={args.reps} "
        f"cases={case_count}"
    )
    for line in lines:
        print(line)
    print(
        f"[resolver-behavior-probe] summary: "
        f"completed_admissible={counts['admissible']} "
        f"violation={counts['violation']} inconclusive={counts['inconclusive']}"
        f"（INCONCLUSIVE 如實——禁 retry-to-green）"
    )
    if counts["violation"]:
        return 1
    if counts["admissible"] == 0:
        # F1（R1）：有 artifact 但零完成 admissible 樣本——全 INCONCLUSIVE
        # 不可宣稱 pass（顯性非零 exit，禁 silent green）
        print(
            "[resolver-behavior-probe] NO-COMPLETED-SAMPLE: 零完成 admissible "
            "樣本（全 INCONCLUSIVE）——不可宣稱 pass",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
