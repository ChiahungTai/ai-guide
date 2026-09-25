#!/bin/bash
# cross-repo morning patrol（AIR-199）——六 repo 晨間巡檢聚合器
# 排程：launchd 每日 08:10（sweep 08:05 之後）。輸出：~/.agents/cross-repo-patrol/latest.md
# 語義：瞬時報告（非記憶——memory spine 契約禁任務流水）；偵測與處置分離（只報告不動手）
# 巡檢面：backlog 計數（To Do/In Progress）＋超齡 To Do（>30d，可見期時鐘同 cleanup）＋
#         git 髒樹＋WT/branch 殘留；code-reality 無 backlog 面只巡 git 面
# repo 清單 user 0925 確認：ai-guide＋mosaic_alpha（非 mosaic）＋southchariot＋delegate-bridge＋code-reality＋sc-router

set -uo pipefail

AGE_DAYS=30
PATROL_DIR="$HOME/.agents/cross-repo-patrol"
# repo 卡 branch 前綴表（補審 F2：原版只掃 air-*/ephemeral/*＝六 repo 涵蓋 1/6；
# code-reality 無卡面＝空字串不掃 branch）
REPOS=(ai-guide mosaic_alpha southchariot delegate-bridge code-reality sc-router)
PREFIXES=("air-" "mos-" "sc-" "db-" "scr-" "")
GH="$HOME/Github"

for tool in git rg date bash; do command -v "$tool" >/dev/null 2>&1 || { echo "[FAIL] $tool 不在 PATH"; exit 1; }; done
mkdir -p "$PATROL_DIR"

out="$PATROL_DIR/latest.md"
{
  echo "# Cross-repo morning patrol — $(date '+%F %T')"
  echo
  echo "| repo | To Do | In Progress | 超齡 To Do | 髒樹 | WT 殘留 |"
  echo "|---|---|---|---|---|---|"
} > "$out"

alert_total=0
repo_idx=0
for r in "${REPOS[@]}"; do
  root="$GH/$r"
  prefix="${PREFIXES[$repo_idx]}"
  repo_idx=$((repo_idx+1))
  if [ ! -d "$root" ]; then
    echo "| $r | — | — | — | — | repo 缺場 |" >> "$out"
    alert_total=$((alert_total+1))
    continue
  fi
  todo=0; ip=0; aged=0; dirty=0; wt_left=0; aged_list=""
  # backlog 面（缺面＝合法，非 alert）
  if [ -d "$root/backlog/tasks" ]; then
    for f in "$root"/backlog/tasks/*.md; do
      [ -e "$f" ] || continue
      s=$(rg -o -m1 '^status: (.+)$' -r '$1' "$f" 2>/dev/null || true)
      case "$s" in
        "To Do")
          todo=$((todo+1))
          ds=$(rg -o -m1 "^updated_date: '?([^']+)'?" -r '$1' "$f" 2>/dev/null || true)
          ts=$(date -j -f '%Y-%m-%d %H:%M' "$ds" +%s 2>/dev/null || true)
          # 補審 F4：嚴格 >30d（地板除法會讓 30.5d 變 30 漏報）
          if [ -n "${ts:-}" ] && [ $(( $(date +%s) - ts )) -gt $(( AGE_DAYS * 86400 )) ]; then
            aged=$((aged+1))
            aged_list="${aged_list}${aged_list:+、}$(basename "$f" | cut -c1-24)($(( ($(date +%s) - ts) / 86400 ))d)"
          fi
          ;;
        "In Progress") ip=$((ip+1)) ;;
      esac
    done
  fi
  # git 面
  if git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    [ -n "$(git -C "$root" status --porcelain 2>/dev/null | head -1)" ] && dirty=1
    # WT 殘留偵測（補審 F1 重寫——原 awk 雙缺陷＝永久 no-op＋假綠燈）：
    # 兩段式——先建「在場 branch → worktree dir」映射，再反轉判定：
    # 候選 branch 不在映射中（branch 存在但無 worktree entry）或在映射中但目錄已消失 → 殘留
    wt_map=$(git -C "$root" worktree list --porcelain 2>/dev/null | awk '
      /^worktree /{wt=substr($0,10)}
      /^branch /{br=$2; sub("^refs/heads/","",br); print br "\t" wt}
    ')
    while IFS= read -r br; do
      [ -n "$br" ] || continue
      git -C "$root" rev-parse -q --verify "refs/heads/$br" >/dev/null 2>&1 || continue
      wt_path=$(printf '%s\n' "$wt_map" | awk -F'\t' -v b="$br" '$1==b{print $2; exit}')
      if [ -z "$wt_path" ] || [ ! -d "$wt_path" ]; then
        wt_left=$((wt_left+1))
      fi
    done < <(printf '%s\n' "$prefix" | while IFS= read -r p; do
      git -C "$root" for-each-ref --format='%(refname:short)' "refs/heads/${p}*" "refs/heads/ephemeral/*" 2>/dev/null
    done)
  else
    dirty=-1  # 非 git（異常）
  fi
  if [ "$dirty" -eq 1 ]; then ds="髒"; elif [ "$dirty" -eq 0 ]; then ds="乾淨"; else ds="非-git"; alert_total=$((alert_total+1)); fi
  echo "| $r | $todo | $ip | ${aged}${aged_list:+ <br>$aged_list} | $ds | $wt_left |" >> "$out"
  alert_total=$((alert_total + aged + wt_left))
done

{
  echo
  echo "_偵測與處置分離：本報告不動手——處置決策歸 user／晨間 marshal session。_"
} >> "$out"

# 通知面：alerts>0 才發 macOS 原生通知（零 LLM 額度；launchd 排程 user 不開 app 也跑）
# 補審 F3：通知失敗不可靜默（漏報向量）——失敗落 stderr 進 launchd err log
if [ "$alert_total" -gt 0 ]; then
  osascript -e "display notification \"跨 repo 巡檢：${alert_total} 項訊號——見 ~/.agents/cross-repo-patrol/latest.md\" with title \"Morning Patrol\"" 2>/dev/null || echo "[WARN] osascript 通知失敗——請手動查看 $out" >&2
fi

echo "== patrol done：alerts=$alert_total report=$out"
exit 0
