#!/bin/bash
# Backlog.md Done 欄清場（每日 launchd 批次）——kanban-board skill「清理批次」的自動腿
# 語義：status=Done 且 updated_date 距今 > BACKLOG_CLEANUP_AGE_DAYS（預設 30）的卡，
#       逐卡跑 backlog_precheck.sh（跨線掃描單一源）→ backlog task complete → git add backlog/ + commit
# precheck [不可清]（In Progress／跨線訊號）→ 跳過該卡記 log，不擋其他卡（有進有出）
# 授權：機械清場批次（user 2026-09-06 裁定，建卡 commit 同型態免逐次確認）
# twin: mosaic_alpha/deploy/scripts/run-backlog-cleanup.sh 同邏輯副本（絕對路徑 precheck）——修改須同步

set -uo pipefail

AGE_DAYS="${BACKLOG_CLEANUP_AGE_DAYS:-30}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKLOG_BIN="${BACKLOG_BIN:-/Users/ctai/.npm-global/bin/backlog}"
PRECHECK="$REPO_ROOT/skills/kanban-board/scripts/backlog_precheck.sh"
CLOSEOUT_CHECK="$REPO_ROOT/scripts/closeout_check.py"

# 環境預檢：工具或 precheck 缺場 → loud 失敗（靜默 no-op 與誤計 skip 都比失敗更糟）
for tool in git rg sed date bash; do command -v "$tool" >/dev/null 2>&1 || { echo "[FAIL] $tool 不在 PATH"; exit 1; }; done
command -v "$BACKLOG_BIN" >/dev/null 2>&1 || { echo "[FAIL] backlog CLI 不在場：$BACKLOG_BIN"; exit 1; }
[ -f "$PRECHECK" ] || { echo "[FAIL] precheck 不存在：$PRECHECK"; exit 1; }
[ -f "$CLOSEOUT_CHECK" ] || { echo "[FAIL] closeout_check 不存在：$CLOSEOUT_CHECK（AIR-198 前置過濾腿）"; exit 1; }

moved_total=0; skip_total=0; fail_total=0; struct_skip_total=0
now_ts=$(date +%s)

# worktree 先收陣列再迴圈（pipe 餵 while 會落 subshell，計數器帶不出來；bash 3.2 無 mapfile）
wts=()
while IFS= read -r wt; do wts+=("$wt"); done < <(git -C "$REPO_ROOT" worktree list --porcelain | sed -n 's/^worktree //p')
[ "${#wts[@]}" -gt 0 ] || { echo "[FAIL] worktree 列舉為空（git 異常？）"; exit 1; }

echo "== backlog-cleanup $REPO_ROOT $(date '+%F %T') 門檻 Done>${AGE_DAYS}d"

for wt in "${wts[@]}"; do
  [ -d "$wt/backlog/tasks" ] || { echo "[skip-WT] ${wt}（無 backlog/tasks）"; continue; }
  git -C "$wt" rev-parse --verify HEAD >/dev/null 2>&1 || { echo "[FAIL] ${wt}（git HEAD 不可用——operational，非 policy）"; fail_total=$((fail_total+1)); continue; }
  # rebase/merge 進行中不動（半途狀態 commit 會攪進別人的手術）
  if [ -d "$(git -C "$wt" rev-parse --git-path rebase-merge)" ] || [ -d "$(git -C "$wt" rev-parse --git-path rebase-apply)" ] || [ -f "$(git -C "$wt" rev-parse --git-path MERGE_HEAD)" ]; then
    echo "[skip-WT] ${wt}（rebase/merge 進行中）"; continue
  fi
  git -C "$wt" symbolic-ref -q HEAD >/dev/null 2>&1 || { echo "[skip-WT] ${wt}（detached HEAD——commit 無 branch 承接）"; continue; }

  # 枚舉過齡 Done 卡（updated_date 是最後編輯時間＝可見期時鐘；pair＝"id|檔名"）
  cands=()
  for f in "$wt"/backlog/tasks/*.md; do
    [ -e "$f" ] || continue
    s=$(rg -o -m1 '^status: (.+)$' -r '$1' "$f" 2>/dev/null || true)
    [ "$s" = "Done" ] || continue
    ds=$(rg -o -m1 "^updated_date: '?([^']+)'?" -r '$1' "$f" 2>/dev/null)
    ts=$(date -j -f '%Y-%m-%d %H:%M' "$ds" +%s 2>/dev/null || true)
    if [ -z "${ts:-}" ]; then echo "[skip] $(basename "$f")（updated_date 無法解析：${ds}）"; skip_total=$((skip_total+1)); continue; fi
    age=$(( (now_ts - ts) / 86400 ))
    if [ "$age" -gt "$AGE_DAYS" ]; then
      cid=$(rg -o -m1 '^id: (.+)$' -r '$1' "$f")
      [ -n "$cid" ] && cands+=("$cid|$(basename "$f")")
    fi
  done
  echo "[WT] $wt — ${#cands[@]} 張過齡候選"

  moved=0
  moved_paths=()
  # bash 3.2 + set -u：空陣列直展開報 unbound——護衛語法 ${cands[@]+"${cands[@]}"}；pair＝"id|檔名"
  for pair in ${cands[@]+"${cands[@]}"}; do
    id=${pair%%|*}; fname=${pair##*|}
    [ -n "$id" ] || continue
    # precheck exit 契約：0=可清／1=不可清（policy skip）／其他=runtime/依賴錯誤（非 policy——禁誤計為 skip）
    verdict=$(cd "$wt" && bash "$PRECHECK" "$id" 2>&1); pst=$?
    if [ "$pst" -eq 0 ]; then
      # AIR-198：結案結構 predicate 前置過濾（判定單一源＝guard，經 closeout_check 複查腿消費）——
      # FAIL 卡不進本批（批次 commit 會被 pre-commit guard 殺全批）；跳過＋計數＋待補清單，fail-closed 保持
      struct_err=$(cd "$wt" && python3 "$CLOSEOUT_CHECK" "backlog/tasks/$fname" 2>&1); cst=$?
      if [ "$cst" -ne 0 ]; then
        echo "[待補段-跳過] ${id}（closeout_check exit ${cst}——補齊後次日自動重試）：${struct_err}"; struct_skip_total=$((struct_skip_total+1)); skip_total=$((skip_total+1)); continue
      fi
      if out=$(cd "$wt" && "$BACKLOG_BIN" task complete "$id" </dev/null 2>&1); then
        echo "[moved] $id"; moved=$((moved+1)); moved_total=$((moved_total+1))
        moved_paths+=("backlog/tasks/$fname" "backlog/completed/$fname")
      else
        echo "[FAIL] ${id}：$out"; fail_total=$((fail_total+1))
      fi
    elif [ "$pst" -eq 1 ]; then
      echo "[不可清-跳過] ${id}：$verdict"; skip_total=$((skip_total+1))
    else
      echo "[FAIL] ${id} precheck 異常（exit ${pst}≠契約 0/1——runtime/依賴錯誤，非 policy skip）：$verdict"; fail_total=$((fail_total+1))
    fi
  done

  if [ "$moved" -gt 0 ]; then
    # 逐檔 pathspec：只 add/commit 本批次實際搬移的卡——不掃平行 session 在 backlog/ 的其他變更，也不吃 index 裡別人已 staged 的東西
    if git -C "$wt" add -- "${moved_paths[@]}"; then
      if git -C "$wt" diff --cached --quiet; then
        echo "[WARN] moved=${moved} 但無 staged 變更（CLI 假成功或搬移未落盤）——人工對帳 [moved] 清單"; fail_total=$((fail_total+1))
      elif git -C "$wt" commit -m "chore(backlog): cleanup — ${moved} cards → completed/ (Done >${AGE_DAYS}d)" -- "${moved_paths[@]}" >/dev/null; then
        echo "[commit] $(git -C "$wt" rev-parse --short HEAD) @ ${wt##*/} ×${moved}"
      else
        echo "[FAIL] commit 失敗 @ ${wt}（檔案已搬移但未 commit——隔日人工檢視）"; fail_total=$((fail_total+1))
      fi
    else
      echo "[FAIL] git add 失敗 @ ${wt}（index.lock 競態？）——檔案已搬移但未 staged，隔日人工檢視"; fail_total=$((fail_total+1))
    fi
  fi
done

echo "== done：moved=${moved_total} skipped=${skip_total} 結構待補=${struct_skip_total} failed=${fail_total}"
# launchd 失敗訊號：fail_total 非零必須非零退出（否則排程層永遠看到成功，清卡失敗無人知）
if [ "$fail_total" -gt 0 ]; then exit 1; fi
