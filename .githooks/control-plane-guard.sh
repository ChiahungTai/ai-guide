#!/bin/bash
# 控制面 canonical 隔離閘（AIR-106）——canonical main 上禁 commit 控制面路徑。
# why：Claude 端 ~/.claude/rules/ 是 live symlink，canonical 一落即對所有 session 生效；
# F8 實證（AIR-105）commit 先於審查腿回收＝activation-before-review 洞。
# 路徑清單單一源＝本檔 CONTROL_PLANE_PATTERN（commit skill / instruction-writing
# skill / hooks/marshal_admission_guard.py 引用此處，不重刻清單）。機械判定
# （branch×path regex），無語義例外；
# 逃生口＝git commit --no-verify（同時跳過測試閘——手動補跑；須在卡 notes 記錄理由）。
#
# 兩個入口（AIR-135.10 擴）：
#   無參數                    staged-commit 模式（pre-commit 用——branch×staged 判定）
#   --match-path <repo-rel>   pure path predicate（marshal admission guard 用——
#                             exit 0 非控制面／1 命中控制面／2 用法錯誤；純路徑判定，
#                             不碰 git——沙箱與跨 checkout 呼叫皆安全）

CONTROL_PLANE_PATTERN='(^|/)(AGENTS|CLAUDE)\.md$|^(rules|skills|agents|hooks|deploy|muse-plugins|governance|\.githooks)/|^ai-development-guide\.md$|^tests/test_githooks\.py$|^scripts/(deploy_agents|sync_agents)\.py$'

if [ "$1" = "--match-path" ]; then
  [ -n "$2" ] || { echo "usage: control-plane-guard.sh --match-path <repo-relative-path>" >&2; exit 2; }
  printf '%s\n' "$2" | grep -Eq -- "$CONTROL_PLANE_PATTERN" && exit 1
  exit 0
fi

branch="$(git symbolic-ref --short -q HEAD || echo DETACHED)"
[ "$branch" = "main" ] || exit 0
# -c core.quotePath=false：預設 quotePath 會把非 ASCII 路徑 octal-escape＋引號包裹，
# 全部 alternation 分支失效＝靜默 fail-open（fresh 腿 F1 機械實證）
staged="$(git -c core.quotePath=false diff --cached --name-only)"
[ -n "$staged" ] || exit 0
hits="$(printf '%s\n' "$staged" | grep -E -- "$CONTROL_PLANE_PATTERN")"
if [ -n "$hits" ]; then
  {
    echo "[pre-commit] 控制面路徑禁落 canonical main（activation-before-review 防線，AIR-106）"
    echo "  authoring 走非 canonical WT 的卡 branch 或 persistent card WT（canonical 主樹留 main）；審查腿＋回執四欄齊後才 merge canonical。命中："
    printf '%s\n' "$hits" | sed 's/^/    /'
    echo "  逃生口：git commit --no-verify（同時跳過測試閘——手動補跑；須在卡 notes 記錄理由）"
  } >&2
  exit 1
fi
exit 0
