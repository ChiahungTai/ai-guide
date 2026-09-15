#!/usr/bin/env bash
# muse tool-governance hook: bash-write-guard (AIR-97 S1)
# 判斷契約移植自 ai-guide hooks/block-python-file-write.py（is_violation L29-40）：
# 攔截 bash 工具內「python heredoc + heredoc 標記之後出現檔案寫入 API」的繞道形態
# （mosaic 兩週遙測 319 次）。改檔一律走 Edit/Write 工具；heredoc 僅用於純計算/查詢。
#
# stdin 契約（AIR-97 S3 live 實測）：
#   {"hook_event_name":"PreToolUse","tool_name":"bash","tool_input":{"command":...},"cwd":...}
#   — tool_name 值＝"bash"（全小寫）；命令字串住 tool_input.command。
# deny 形：hookSpecificOutput permissionDecision="deny" + exit 0（muse 契約）；allow＝靜默 exit 0。
#
# fail-closed 契約（AIR-97 已決策③）：
#   muse 對 hook crash／非零退出＝fail-open（S3 hook test 實證：exit-1 → should_block:false），
#   故「crash→deny」不可能靠退出碼達成——所有異常路徑必須 in-script 顯式 deny（本檔每步 || deny）。
#   兩段式：① 非 bash 工具＝不進防護範圍，allow（不可分類不擋，防 brick session）；
#           ② 已判定 bash 後，命令不可判讀／jq 不可用／解析失敗→deny（漏攔成本＞誤攔）。
#   已知限制（沿襲移植源）：open() 第一參數含巢狀括號（open(Path(d).name,'w')）不攔——寧漏抓不誤傷。
set -uo pipefail   # 故意不用 -e：-e 觸發的非零退出＝muse fail-open 靜默漏攔

deny() {
  # jq-free deny 輸出（沿襲 memory-governance R1/C-C2）：控制字元先轉義再剝除，防 schema 破壞
  local reason=${1//\\/\\\\}
  reason=${reason//\"/\\\"}
  reason=${reason//$'\n'/\\n}
  reason=${reason//$'\r'/\\r}
  reason=${reason//$'\t'/\\t}
  STRIPPED=$(printf '%s' "$reason" | tr -d '\000-\037' 2>/dev/null) && reason=$STRIPPED
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
  exit 0
}

DENY_NOTE="誤攔或緊急逃生：muse plugins disable muse-tool-governance"

IN=$(cat) || deny "bash-write-guard: stdin 讀取失敗，工具呼叫無法判定（fail-closed）。$DENY_NOTE"
[ -n "$IN" ] || exit 0   # 空 stdin：無從判定＝無防護責任，靜默放行

# ① 工具身份分類——只有 bash 進入防護範圍
command -v jq >/dev/null 2>&1 || deny "bash-write-guard: jq 不可用，bash 命令可否安全執行無法判定（fail-closed）。安裝 jq（brew install jq）後重試；或 $DENY_NOTE"
TOOL=$(printf '%s' "$IN" | jq -r '.tool_name // empty' 2>/dev/null) \
  || deny "bash-write-guard: stdin JSON 解析失敗，工具身份無法判定（fail-closed）。$DENY_NOTE"
case "$TOOL" in
  bash) : ;;
  *) exit 0 ;;   # 非 bash（含 muse 內部工具與未知工具）：allow，不 brick session
esac

# ② 已入 shell 防護範圍——命令不可判讀即 deny
CMD=$(printf '%s' "$IN" | jq -r '.tool_input.command // empty' 2>/dev/null) \
  || deny "bash-write-guard: tool_input.command 解析失敗（fail-closed）。$DENY_NOTE"
[ -n "$CMD" ] || deny "bash-write-guard: bash 命令為空或缺失，無法判定安全性（fail-closed）。$DENY_NOTE"

# 判斷契約（三條件同時成立才攔；移植源 L29-40）：
#   (a) 命令含 heredoc 標記   (b) 含 python 字樣   (c) 標記之後出現寫檔 API
if printf '%s\n' "$CMD" | grep -nE "<<-?[[:space:]]*['\"]?[A-Za-z_][A-Za-z0-9_]*" >/dev/null 2>&1; then
  LINE=$(printf '%s\n' "$CMD" | grep -nE "<<-?[[:space:]]*['\"]?[A-Za-z_][A-Za-z0-9_]*" | head -1 | cut -d: -f1)
  AFTER=$(printf '%s\n' "$CMD" | tail -n +"$LINE" | sed -E "1s/.*<<-?[[:space:]]*['\"]?[A-Za-z_][A-Za-z0-9_]*//")
  if printf '%s' "$CMD" | grep -qE "(^|[^A-Za-z0-9_])python3?($|[^A-Za-z0-9_])" 2>/dev/null \
    && printf '%s' "$AFTER" | grep -qE "\.write_(text|bytes)[[:space:]]*\(|open[[:space:]]*\([^)]*['\"][wax][+b]*['\"]" 2>/dev/null; then
    deny "bash-write-guard: python heredoc 內含檔案寫入呼叫——這是繞過 Edit 工具與 sed 禁令的形態（遙測實測 319 次），不可追溯、無 read-state 保護。修正：改檔一律用 Edit/Write 工具；heredoc 僅用於純計算/查詢。$DENY_NOTE"
  fi
fi

exit 0

# AIR-97 walkthrough marker
