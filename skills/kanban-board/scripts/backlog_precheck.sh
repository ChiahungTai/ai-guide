#!/usr/bin/env bash
# backlog-precheck — 歸檔/清場/清板前的機械檢查（kanban-board skill「清理前跨線掃描」的腳本載體）
# 用法: backlog_precheck.sh [card-id ...]   # 無參數 = 掃全部 To Do 卡
# Exit: 0 = 全部可清；1 = 存在不可清項（停手先協調）；2 = runtime/依賴錯誤（git/掃描失敗——非 policy 判定，禁當可清或不可清）
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

ids=("$@")
if [ ${#ids[@]} -eq 0 ]; then
  for f in backlog/tasks/*.md; do
    [ -e "$f" ] || continue
    s=$(rg -o -m1 '^status: (.+)$' -r '$1' "$f" 2>/dev/null || true)
    [ "$s" = "To Do" ] && ids+=("$(rg -o -m1 '^id: (.+)$' -r '$1' "$f" 2>/dev/null || true)")
  done
fi
[ ${#ids[@]} -eq 0 ] && { echo "[可清] 無 To Do 卡"; exit 0; }

find_card() {
  local want="$1" f cid
  for f in backlog/tasks/*.md; do
    [ -e "$f" ] || continue
    cid=$(rg -o -m1 '^id: (.+)$' -r '$1' "$f" 2>/dev/null || true)
    [ "$cid" = "$want" ] && { echo "$f"; return; }
  done
  return 0
}

blocked=0
for id in "${ids[@]}"; do
  f=$(find_card "$id")
  if [ -z "$f" ]; then
    echo "[不可清] $id — backlog/tasks/ 找不到此 id 的卡檔"; blocked=1; continue
  fi
  s=$(rg -o -m1 '^status: (.+)$' -r '$1' "$f" 2>/dev/null || true)
  if [ "$s" = "In Progress" ]; then
    echo "[不可清] $id — status=In Progress（進行中卡永不清）"; blocked=1; continue
  fi
  # --all --not HEAD = 有 commit 提及此卡、但當前 branch 不包含 = 真平行線訊號
  # （裸 --all --grep 會命中本線建卡 commit，永遠誤報；比對為子串匹配，多擋不少放——安全側）
  # -i：卡 id 大寫（AIR-46）、實作 commit subject 小寫 scope（(air-46)）——區分大小寫會整組漏抓
  # -E＋邊界：id 尾接數字會前綴互撞（AIR-108 命中 AIR-1080）——id 後須非數字或行尾
  # fail-closed：git log operational 失敗（repo/object/permission）禁吞成空 hits 假「可清」——exit 2 交 caller F2 分流
  if ! hits=$(git log --all --not HEAD -i -E --grep "${id}([^0-9]|$)" --oneline 2>&1); then
    echo "[ERROR] $id — git log 失敗（runtime，非 policy）：$hits" >&2; exit 2
  fi
  if [ -n "$hits" ]; then
    echo "[不可清] $id — 跨線訊號（其他 branch commit 提及）："; echo "$hits" | sed 's/^/    /'; blocked=1
  fi
  # 反向檢查（AIR-108）：本線已有實作 commit、卡面未翻（To Do）＝做完未收卡。
  # 只對 To Do 生效——翻 Done 即視為裁決完成（結案序列＝先翻卡再 precheck，Done 卡自動跳過）；
  # 過濾 bookkeeping（chore(backlog) 建卡/開工/結案 metadata），其餘 subject 命中即訊號。
  impl_hit=""
  if [ "$s" = "To Do" ]; then
    if ! own=$(git log HEAD -i -E --grep "${id}([^0-9]|$)" --oneline 2>&1); then
      echo "[ERROR] $id — git log 失敗（runtime，非 policy）：$own" >&2; exit 2
    fi
    impl=$(printf '%s\n' "$own" | grep -v 'chore(backlog)' || true)
    if [ -n "$impl" ]; then
      echo "[需裁決] $id — 本線已有實作 commit、卡面未翻（To Do）：收 Done（結案兩步）或記錄阻擋理由："
      echo "$impl" | sed 's/^/    /'
      impl_hit=1
      blocked=1
    fi
  fi
  if [ -z "$hits" ] && [ -z "$impl_hit" ]; then
    echo "[可清] $id (status=$s)"
  fi
done
exit $blocked
