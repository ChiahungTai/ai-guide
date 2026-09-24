#!/usr/bin/env bash
#
# wt-open.sh — 為已存在 card 建立 persistent card worktree（AIR-72 ①⑥）
#
# 用法：
#   wt-open.sh <card-id> --base <owning 線 ref> [--wt-root <path>]
#   wt-open.sh --ephemeral <name> --base <owning 線 ref> [--wt-root <path>]   # 免卡小修 fast-path
#
# 設計決策（audit 用）：
# - lock＝mkdir 原子鎖（非 flock）：macOS 無 /usr/bin/flock（BSD base 系統缺）；鎖放
#   共享 .git/wt-open.lock——所有 worktree 共享同一 .git，控制面互斥天然全域。
#   衝突時印持有者資訊後 exit 2，不自動搶鎖；人工復原＝確認無活進程後 rm -rf 該目錄。
# - base 顯式（核心正確性）：base 為必填參數（**無預設值**——多線 repo 忘傳即靜默立錯線，
#   缺席＝usage 錯誤 fail-loud），只接受命名 ref（owning 線）經 rev-parse 解析，
#   **絕不使用呼叫端 WT 的當前 HEAD**——多 WT 下以 caller HEAD 為 base 會把卡 branch
#   綁到平行線的歷史上。解析後的 base commit hash 落進 identity contract。
# - identity contract 落 <wt>/.agent-tmp/wt-identity.json：.agent-tmp/ 已 gitignored
#   （不污染 git status）、worker 在 WT 內可直接讀（路徑契約三閘的驗證材料）、
#   生命週期與 WT 同滅；開中 WT 的枚舉靠 git worktree list，不靠此檔。
# - muse hooks：已於 09-14 退役（.muse/hooks.json 移除、plugin muse-memory-governance
#   單閘）——本腳本零 hooks 步驟，不建死代碼。
# - 卡 metadata 零寫入：卡 status/ref 只有 board-control 可寫（board single-writer 條款，
#   見 skills/kanban-board/SKILL.md）——腳本只印起手式提醒，不代寫 In Progress/refs。
# - 池拓撲分流（AIR-71 形態①）：.agents/memory 與 .agents/memory-inbox 以 symlink 指向
#   primary canonical 主體（兩者皆 gitignored）——池內容不隨 branch 收斂；涉及池的交付
#   拆「資產源隨 branch＋池副本 marshal 合併後套」，close 端只提醒不自動執行。
#   池缺席＝WARN-skip 不 die（AIR-177）——無池 repo 不得建 worktree 到一半才失敗。
# - stale-state 檢查位：.code-reality index／bridge ledger（.delegate-bridge）／backlog
#   卡檔對時——三者皆 machine-local 或未 commit 面，開 WT 時逐項回報。
#
# 依賴：git、bash 3.2+（macOS 相容）。退出碼：0 成功／2 鎖衝突／3 驗證失敗。

set -euo pipefail

prog="$(basename "$0")"
die() { printf 'ERROR[%s]: %s\n' "$prog" "$*" >&2; exit 3; }
info() { printf '[wt-open] %s\n' "$*"; }
warn() { printf '[wt-open] WARN: %s\n' "$*" >&2; }

MODE="card"
CARD_ID=""
EPH_NAME=""
BASE_REF=""
WT_ROOT_ARG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --ephemeral) MODE="ephemeral"; EPH_NAME="${2:?--ephemeral 需 name}"; shift 2 ;;
    --base) BASE_REF="${2:?--base 需 ref}"; shift 2 ;;
    --wt-root) WT_ROOT_ARG="${2:?--wt-root 需 path}"; shift 2 ;;
    -h|--help) sed -n '2,31p' "$0"; exit 0 ;;
    *) if [ "$MODE" = "card" ] && [ -z "$CARD_ID" ]; then CARD_ID="$1"; shift;
       else die "未知參數：$1"; fi ;;
  esac
done
[ -n "$BASE_REF" ] || die "usage：--base <owning 線 ref> 必填（無預設值——多線 repo 忘傳即靜默立錯線）"

# ── repo 定位（從呼叫端 cwd 解析；共享 .git 為控制面錨點）──────────────────
GIT_COMMON="$(git rev-parse --path-format=absolute --git-common-dir)" || die "不在 git repo 內"
PRIMARY="$(dirname "$GIT_COMMON")"

# ── lock（mkdir 原子鎖；理由見檔頭）─────────────────────────────────────
LOCK="$GIT_COMMON/wt-open.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  OWNER="$(cat "$LOCK/owner" 2>/dev/null || echo '未知持有者')"
  printf 'ERROR[%s]: 鎖被佔（%s）。\n復原：確認 pid 無活進程後 rm -rf %s\n' "$prog" "$OWNER" "$LOCK" >&2
  exit 2
fi
printf '%s %s %s\n' "$$" "$(date +%s)" "${USER:-?}" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT

# ── base 顯式解析（永不取 caller HEAD）──────────────────────────────────
case "$BASE_REF" in
  HEAD|-*) die "base 禁用 HEAD／呼叫端狀態——必須是命名 ref（owning 線）" ;;
esac
BASE_HASH="$(git rev-parse --verify "${BASE_REF}^{commit}")" || die "base ref 無法解析：$BASE_REF"
info "base：$BASE_REF @ $BASE_HASH"

# ── 任務 identity───────────────────────────────────────────────────────
TASK=""
BRANCH=""
CARD_FILE=""
if [ "$MODE" = "ephemeral" ]; then
  case "$EPH_NAME" in ''|*[!A-Za-z0-9._-]*) die "ephemeral name 限 [A-Za-z0-9._-]：$EPH_NAME" ;; esac
  BRANCH="ephemeral/$EPH_NAME"
  TASK="(ephemeral) $EPH_NAME"
else
  CARD_ID="$(printf '%s' "$CARD_ID" | tr 'A-Z' 'a-z')"
  # 點號允許（子卡 air-135.3 形態常態；git branch 中段點號合法；開頭/連續兩點由 git 自身拒）——SC finding #1（sess_d6e3e495 結算信）採納
  case "$CARD_ID" in ''|*[!A-Za-z0-9.-]*) die "card id 形態異常：$CARD_ID" ;; esac
  BRANCH="$CARD_ID"
  TASK="$CARD_ID"
  # 只認 committed card（workflow.md：未提交 working-copy 狀態不視為 baseline）
  # core.quotePath=false：CJK 卡檔名被 quote 會破壞前綴比對
  CARD_FILE="$(git -c core.quotePath=false ls-tree --name-only "$BASE_REF" -- "backlog/tasks/" | grep -E "^backlog/tasks/${CARD_ID} - " | head -n 1 || true)"
  if [ -z "$CARD_FILE" ]; then
    # working copy 有但未 commit → 指路，不代建
    if ls "$PRIMARY"/backlog/tasks/"${CARD_ID}"* >/dev/null 2>&1; then
      die "卡 $CARD_ID 存在於 working copy 但未進 base ref $BASE_REF ——先依『建卡即 commit』落 owning 線再 wt-open"
    fi
    die "卡不存在（backlog/tasks/ 無 ${CARD_ID} - *.md @ $BASE_REF ）：$CARD_ID —— wt-open 不代建卡、不 allocate id"
  fi
  info "card：$CARD_FILE"
fi

# ── branch／WT reuse 判定───────────────────────────────────────────────
DEFAULT_WT="$(dirname "$PRIMARY")/$(basename "$PRIMARY")-${BRANCH#ephemeral/}"
WT_PATH="${WT_ROOT_ARG:-$DEFAULT_WT}"
REUSE_BRANCH=0
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  REUSE_BRANCH=1
  if [ "$MODE" = "ephemeral" ]; then
    if [ -n "$(git log --oneline "${BASE_REF}..${BRANCH}")" ]; then
      die "branch $BRANCH 已存在且含 commits——ephemeral 重用需人工確認：git log ${BASE_REF}..${BRANCH}"
    fi
  else
    # reuse guard：branch 上 base 之後的 commits，subject 須帶本卡 id（大小寫不拘）——非本卡殘留不續用
    FOREIGN="$(git log --format='%h %s' "${BASE_REF}..${BRANCH}" | grep -ivE "${CARD_ID}([^0-9.]|$)" || true)"
    if [ -n "$FOREIGN" ]; then
      die "branch $BRANCH 已存在且含非本卡 commits（禁直接重用，先人工判定）：$(printf '%s；' $FOREIGN)"
    fi
  fi
  # 池 symlink 污染檢查（歷史 branch 可能已收進 symlink entry——禁重用，先清）
  POLLUTED="$(git ls-tree -r "$BRANCH" -- .agents 2>/dev/null | grep 120000 || true)"
  [ -z "$POLLUTED" ] || die "branch $BRANCH 含被追蹤的池 symlink（收斂會污染 trunk）——先清除：git --work-tree=$WT_PATH rm -r --cached .agents 後重跑"
  info "branch 已存在，驗通過續用：$BRANCH"
fi

if git show-ref --verify --quiet "refs/heads/$BRANCH" && git worktree list --porcelain | grep -qx "worktree $WT_PATH"; then
  info "persistent WT 已存在，重用：$WT_PATH"
elif [ "$REUSE_BRANCH" = "1" ]; then
  git worktree add "$WT_PATH" "$BRANCH" || die "worktree add（掛既有 branch）失敗"
else
  git worktree add -b "$BRANCH" "$WT_PATH" "$BASE_HASH" || die "worktree add -b 失敗（branch 撞號或被他 WT checkout？）"
fi

# ── 池 symlink 防污染面（.gitignore 尾斜線型態只匹配目錄——symlink 不受涵蓋，
#    git add -A 會把池 symlink 收進 commit、隨收斂污染 trunk；故以共享 .git/info/exclude
#    補無尾斜線型態。.git 內 machine-local runtime 面與 lock 同級，幂等追加）──────
EXCLUDE="$GIT_COMMON/info/exclude"
mkdir -p "$(dirname "$EXCLUDE")"
for pat in ".agents/memory" ".agents/memory-inbox"; do
  grep -qxF "$pat" "$EXCLUDE" 2>/dev/null || printf '%s\n' "$pat" >> "$EXCLUDE"
done

# ── 池／inbox symlink（primary canonical 主體 → WT 內同名路徑）────────────
# 池拓撲是 opt-in：primary 無 .agents/memory 主體的 repo 整段 WARN-skip，不 die
# （採池 repo 行為不變；真實案例：southchariot 動卡 wt-open 即死於此檢查；
# AIR-177：舊行為 .agents/ 在但 memory 主體缺席＝worktree 建到一半 exit 3——
# 池缺席不是錯誤，mid-way 死才是）
if [ ! -d "$PRIMARY/.agents/memory" ]; then
  warn "primary 記憶池缺席（$PRIMARY/.agents/memory）——WARN-skip 池 symlink（池拓撲 opt-in），WT 照常交付"
else
mkdir -p "$WT_PATH/.agents"
for d in memory memory-inbox; do
  TARGET="$PRIMARY/.agents/$d"
  if [ ! -d "$TARGET" ]; then
    if [ "$d" = "memory-inbox" ]; then mkdir -p "$TARGET"; info "primary inbox 缺，已建：$TARGET";
    else die "primary 記憶主體不存在：$TARGET"; fi
  fi
  # ln -sfn 前檢：目標位已存在且非 canonical symlink（實體目錄／斷鏈他指）→ 禁靜默覆寫
  LINK="$WT_PATH/.agents/$d"
  if [ -L "$LINK" ] || [ -e "$LINK" ]; then
    CUR_TGT="$(readlink "$LINK" 2>/dev/null || true)"
    [ "$CUR_TGT" = "$TARGET" ] || die "ln -sfn 前檢：$LINK 已存在且非 canonical symlink (got: ${CUR_TGT:-實體路徑}) —— 禁靜默覆寫，人工判定"
  fi
  ln -sfn "$TARGET" "$LINK"
done
fi

# ── identity contract 落盤（位置理由見檔頭）────────────────────────────────
IDENT_DIR="$WT_PATH/.agent-tmp"
mkdir -p "$IDENT_DIR"
OPENED_AT="$(date '+%Y-%m-%dT%H:%M:%S%z')"
cat > "$IDENT_DIR/wt-identity.json" <<EOF
{
  "v": 1,
  "mode": "$MODE",
  "task": "$TASK",
  "owning_line": "$BASE_REF",
  "base_ref": "$BASE_REF",
  "base_hash": "$BASE_HASH",
  "branch": "$BRANCH",
  "wt_path": "$WT_PATH",
  "card_file": "$CARD_FILE",
  "opened_at": "$OPENED_AT"
}
EOF

# ── {toplevel, branch, card, baseline} 驗證───────────────────────────────
TOP="$(git -C "$WT_PATH" rev-parse --show-toplevel)"
CUR_BR="$(git -C "$WT_PATH" branch --show-current)"
CUR_HEAD="$(git -C "$WT_PATH" rev-parse HEAD)"
[ "$TOP" = "$WT_PATH" ] || die "toplevel 驗證失敗：$TOP"
[ "$CUR_BR" = "$BRANCH" ] || die "branch 驗證失敗：$CUR_BR"
# baseline 驗證：新 branch 須恰好立在 base 上；重用 branch 須為 base 的後代（跨 session 接續）
if [ "$REUSE_BRANCH" = "1" ]; then
  git merge-base --is-ancestor "$BASE_HASH" "$CUR_HEAD" || \
    die "baseline 驗證失敗：branch $BRANCH 非 base $BASE_HASH 的後代（分岔歷史，禁直接接續）"
else
  [ "$CUR_HEAD" = "$BASE_HASH" ] || die "baseline 驗證失敗：$CUR_HEAD != $BASE_HASH"
fi
if [ "$MODE" = "card" ]; then
  [ -e "$WT_PATH/$CARD_FILE" ] || die "card 檔在 WT 內不可達：$CARD_FILE"
  info "card 於 WT 內可達：backlog/tasks/$(basename "$CARD_FILE")"
fi

# ── stale-state 檢查位（.code-reality index／bridge ledger／backlog 對時）──
if [ -e "$WT_PATH/.code-reality" ]; then
  warn "stale 檢查位：WT 內有 .code-reality/（舊 index 殘留——重 build 再做符號查詢）"
else
  info "stale 檢查位 .code-reality：未建（WT 內符號查詢前須先 build index）"
fi
if [ -e "$WT_PATH/.delegate-bridge" ]; then
  warn "stale 檢查位：WT 內有 .delegate-bridge/（bridge ledger 殘留）"
else
  info "stale 檢查位 bridge ledger：無殘留"
fi
if [ "$MODE" = "card" ]; then
  if ! git -C "$PRIMARY" status --porcelain -- "$CARD_FILE" | grep -q .; then
    info "stale 檢查位 backlog 對時：卡檔 primary working copy 無未 commit 變更"
  else
    warn "stale 檢查位 backlog 對時：primary 卡檔有未 commit 變更——WT 內看到的是 committed 版本，開工前先對時"
  fi
fi

# ── 池 symlink 解析驗證（斷鏈＝fatal）＋ignore 面檢查────────────────────────
# guard 與 symlink 建立段同鍵（.agents/memory 在場）——池缺席 WARN-skip 時本段空跳
if [ -d "$PRIMARY/.agents/memory" ]; then
for d in memory memory-inbox; do
  LINK="$WT_PATH/.agents/$d"
  [ -e "$LINK" ] || die "池 symlink 斷鏈：$LINK"
  git -C "$WT_PATH" check-ignore -q ".agents/$d" || \
    warn "池路徑 .agents/$d 未被 gitignore 涵蓋——repo 應補 .gitignore（.agents/memory/ 與 .agents/memory-inbox/），否則 WT 恆 dirty"
done
info "池拓撲：.agents/{memory,memory-inbox} → primary canonical（池內容不入 branch；交付分流＝資產源隨 branch、池副本 marshal 合併後套）"
fi

# ── 釋鎖＋回報───────────────────────────────────────────────────────────
rm -rf "$LOCK"; trap - EXIT
info "✅ wt-open 完成"
printf '%s\n' "  WT       : $WT_PATH"
printf '%s\n' "  branch   : $BRANCH"
printf '%s\n' "  task     : $TASK"
printf '%s\n' "  owning   : $BASE_REF @ $BASE_HASH"
printf '%s\n' "  identity : $IDENT_DIR/wt-identity.json"
printf '%s\n' "  下一步   : cd $WT_PATH 啟動 session；起手式 ①⑤（In Progress＋refs）由 board-control 依 kanban 執行；freshness：git log --oneline $BASE_HASH..$BASE_REF 應為空"
