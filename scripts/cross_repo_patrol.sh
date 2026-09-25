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
REPOS=(ai-guide mosaic_alpha southchariot delegate-bridge code-reality sc-router)
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
for r in "${REPOS[@]}"; do
  root="$GH/$r"
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
          if [ -n "${ts:-}" ]; then
            age=$(( ($(date +%s) - ts) / 86400 ))
            if [ "$age" -gt "$AGE_DAYS" ]; then
              aged=$((aged+1))
              aged_list="${aged_list}${aged_list:+、}$(basename "$f" | cut -c1-24)(${age}d)"
            fi
          fi
          ;;
        "In Progress") ip=$((ip+1)) ;;
      esac
    done
  fi
  # git 面
  if git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    [ -n "$(git -C "$root" status --porcelain 2>/dev/null | head -1)" ] && dirty=1
    # WT 殘留：branch 有 air-*/ephemeral/* 而 worktree 目錄已不在＝收線異常（air-68 形）
    while IFS= read -r br; do
      [ -n "$br" ] || continue
      git -C "$root" rev-parse -q --verify "refs/heads/$br" >/dev/null 2>&1 || continue
      wt_path=$(git -C "$root" worktree list --porcelain | awk -v b="refs/heads/$br" '/^branch /{seen=($0==b)} seen && /^worktree /{print $2; exit}')
      [ -z "$wt_path" ] || [ -d "$wt_path" ] || wt_left=$((wt_left+1))
    done < <(git -C "$root" for-each-ref --format='%(refname:short)' 'refs/heads/air-*' 'refs/heads/ephemeral/*' 2>/dev/null)
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
if [ "$alert_total" -gt 0 ]; then
  osascript -e "display notification \"跨 repo 巡檢：${alert_total} 項訊號——見 ~/.agents/cross-repo-patrol/latest.md\" with title \"Morning Patrol\"" 2>/dev/null || true
fi

echo "== patrol done：alerts=$alert_total report=$out"
exit 0
