"""S1 檢索腿：中性陳述 → 各臂約定檢索路徑 → 命中判定（findability，不測主動觸發）。"""

import re
import subprocess
from pathlib import Path

D = Path(__file__).resolve().parent

# （陳述，不含條目名/觸發詞原文；期望＝目標條目檔名 stem；池外期望＝路由出池）
PROBES = [
    ("自主模式做完事可以直接提交代碼嗎", "commit-consent-in-autonomous-mode", "pool"),
    ("多人同 repo 工作，提交前要先看什麼", "feedback_verify-wt-before-commit", "pool"),
    (
        "沒進版本控制的設定檔要改，流程是什麼",
        "feedback_backup-unversioned-live-configs",
        "pool",
    ),
    (
        "看到別的會話的交接訊息，第一步該做什麼",
        "feedback_relay-claims-verify-current-state",
        "pool",
    ),
    (
        "整個技能文件要重寫，手上有舊內容",
        "feedback_full-read-base-not-context-copy",
        "pool",
    ),
    ("只改了兩行，還要走完整檢查流程嗎", "feedback_review-even-on-quick-fix", "pool"),
    (
        "評論別人剛改過的文件要注意什麼",
        "feedback_read-current-file-before-reviewing",
        "pool",
    ),
    (
        "照以前習慣派工之前應該先做什麼",
        "feedback_dispatch-reread-governing-docs",
        "pool",
    ),
    (
        "外部工具連不上，怎麼定位問題",
        "feedback_diagnose-installed-vs-source-first",
        "pool",
    ),
    ("記憶體快滿了想刪舊東西", "feedback_inflow-needs-outflow", "pool"),
    ("額度不夠時怎麼切換模型", "feedback_quota-failover-policy", "pool"),
    ("改 backlog 卡狀態前要確認什麼", "feedback_backlog-card-edit-precheck", "pool"),
]

ARMS = {
    # arm: [(stage, file)]，按序搜；命中即停，記命中階段
    "A": [("index", "armA-index.md")],
    "B": [("resident", "armB-index.md"), ("inventory", "_inventory.md")],
    "C": [("map+resident", "armC-index.md"), ("inventory", "_inventory.md")],
}


def rg_hit(pattern_terms, path):
    """任一詞命中即 1（findability 寬判定；嚴用全詞見 out 註）。"""
    for t in pattern_terms:
        r = subprocess.run(
            ["rg", "-l", "--", t, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return True
    return False


def main():
    print("probe_no | arm | stage_hit | target")
    totals = {}
    for arm, stages in ARMS.items():
        hit = 0
        for i, (stmt, target, _scope) in enumerate(PROBES, 1):
            terms = [c for c in re.findall(r"[\u4e00-\u9fff]{2,}", stmt)]
            stage_hit = "-"
            for stage, fname in stages:
                if rg_hit(terms, D / fname) or rg_hit([target], D / fname):
                    stage_hit = stage
                    break
            if stage_hit != "-":
                hit += 1
            print(f"{i:02d} | {arm} | {stage_hit} | {target}")
        totals[arm] = hit
    print("TOTALS:", " ".join(f"{a}={v}/{len(PROBES)}" for a, v in totals.items()))


if __name__ == "__main__":
    main()
