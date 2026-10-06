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

# fm-lint:BEGIN — 卡面 frontmatter lint（AIR-264；bridge db-precheck-lint-proposal 採納）
# 掃 backlog/{tasks,completed,drafts,archive} 所有 *.md——五類卡面壞形（bridge db-80 四類＋本側 AC 雙 checkbox）：
# 首行/閉合 ---、重複 top-level key（CLI last-wins 寬容、SC ext fail-loud）、行首 tab、未閉雙引號、AC 外框包 [x] 前綴內容。
# 語義對齊 delegate-bridge tests/backlog-frontmatter.test.mjs（line-based，非 YAML parser）；零命中靜默、不擋正常路徑。
fm_lint_fail=0
for _d in tasks completed drafts archive; do
  for _f in backlog/"$_d"/*.md; do
    [ -e "$_f" ] || continue
    if ! _hits=$(awk '
      { sub(/\r$/, "") }
      NR == 1 {
        if ($0 != "---") { print "1 no-frontmatter first line is not ---"; _bad = 1; exit }
        _fm = 1; next
      }
      _fm == 1 && $0 == "---" { for (_i = 0; _i < _pi; _i++) print _pend[_i]; _pi = 0; _fm = 2; next }
      _fm == 1 {
        if ($0 ~ /^\t/) _pend[_pi++] = NR " tab-indent leading tab in frontmatter line"
        if ($0 ~ /^[A-Za-z_][A-Za-z0-9_-]*:([ \t]|$)/) {
          _k = $0; sub(/:.*/, "", _k)
          if (_k in _seen) _pend[_pi++] = NR " duplicate-key duplicated top-level key \"" _k "\" (first at L" _seen[_k] ")"
          else _seen[_k] = NR
          _v = $0; sub(/^[^:]*:[ \t]*/, "", _v)
          if ((_v ~ /^"/) != (_v ~ /"$/)) _pend[_pi++] = NR " unclosed-quote top-level value starts/ends with exactly one double quote"
        }
        next
      }
      _fm == 2 {
        if ($0 ~ /<!-- AC:BEGIN -->/) { _ac = 1; next }
        if ($0 ~ /<!-- AC:END -->/) { _ac = 0; next }
        if (_ac && $0 ~ /^[ \t]*- \[[ x]\] \[x\]([ \t]|$)/) print NR " ac-double-checkbox outer checkbox wraps [x]-prefixed content"
      }
      END {
        if (NR == 0) print "1 no-frontmatter empty card file"
        else if (!_bad && _fm == 1) print "1 unclosed-frontmatter no closing --- found"
      }
    ' "$_f"); then
      echo "[ERROR] $_f — frontmatter awk lint 失敗（runtime，非 policy）" >&2; exit 2
    fi
    if [ -n "$_hits" ]; then
      while IFS= read -r _l; do printf '[frontmatter-lint] %s:%s\n' "$_f" "$_l"; done <<< "$_hits"
      fm_lint_fail=$((fm_lint_fail + $(printf '%s\n' "$_hits" | wc -l)))
    fi
  done
done
if [ "$fm_lint_fail" -gt 0 ]; then
  echo "[不可清] frontmatter lint 命中 $fm_lint_fail 項（卡面解析壞形——SC ext Unparsed／AC 誤勾類）"
  blocked=1
fi
# fm-lint:END
exit $blocked
