#!/usr/bin/env bash
#
# wt-close.sh — 收 card worktree：preflight → rebase/ff-only 收斂 → finalization 提醒 → WT 移除（AIR-72 ①）
#
# 用法：
#   wt-close.sh --wt <path> [--base <git-ref>] [--preflight]
#
# 設計決策（audit 用）：
# - lock＝mkdir 原子鎖（同 wt-open.sh；macOS 無 flock(1)、鎖住共享 .git/wt-open.lock）。
# - repo 定錨（P2-A）：GIT_COMMON／lock／其餘 repo 面 git 呼叫一律從 --wt 所指 WT 反推
#   （git -C "$WT_PATH" rev-parse --git-common-dir）——跨 repo 誤調用時鎖對 repo、動對 repo。
# - --preflight＝全檢查零變更（零變更＝內容面；鎖面有短暫副作用——mkdir lock 仍會開關）：
#   檢查本身只讀（identity／clean／commits scope／owning 線前進／收斂可行性），exit 0/1。
#   trunk 收斂由 marshal 收線時在 user 授權下執行（outward-action-consent「Commit 專屬
#   段」）——本腳本 full 模式即 marshal 收線工具，--preflight 供其先驗。
# - 收斂沿既有規則（repo AGENTS.md「git 慣例」＋workflow.md §wt-close）：owning 線沒前進
#   → ff-only candidate；已前進 → 先 rebase card branch onto owning 線再 ff-only 吸收；
#   ff 失敗即停。trunk 永不被 rebase、永不 force。main 未被任何 WT checkout 時（wave 形態
#   常態）用暫時 worktree 直掛 main 完成 ff merge——全程 git -C，絕不 cd 進暫時 worktree。
# - 收斂結果機械斷言（T9 事故類防護——「close rc=0 但 trunk 未收斂」的靜默假綠）：
#   ①暫時 worktree 建立後驗 HEAD symref 必掛 refs/heads/$TRUNK（HEAD 落在 detached／他支
#   時 ff 會打進非 trunk HEAD：rc=0、trunk 不動、branch -d 照樣過——pipe-test T9 實測簽跡）；
#   ②merge 後驗 $TRUNK 實際含 card branch（merge-base --is-ancestor）。任一失敗即 die 3，
#   且位於移除卡 WT／刪 branch 之前——現場保留待人工判定。
# - board finalization：卡 status/ref 只有 board-control 可寫（single-writer 條款）——腳本
#   在收斂成功後印結算提醒，不代寫卡。
# - 池副本分流（AIR-71 形態①）：池 gitignored——WT 對池的寫入隨 symlink 直落 canonical，
#   不隨 branch 收斂；close 只在 preflight 提醒「池副本 marshal 合併後套」，不自動執行。
# - receipt 落盤（AIR-112）：每次調用 append 一行機器可讀記錄至共享 .git/wt-close.log
#   （格式：timestamp|mode|wt|branch|result；mode＝preflight|full）。失敗調用也記
#   （failure receipt）；log 寫入失敗僅 stderr 警告、不改變 exit code——收線本身是主體。
#   .git 內容永不進版控（machine-local，刻意不隨 clone 同步）、存活於 WT 移除。
# - CR freshness 提醒（AIR-164）：full 收斂且 trunk 實際前進（merge 前 card branch 尚未
#   含於 trunk）→ 印「graph 可能 stale——下次 review 前 code-reality rebuild」到 stderr
#   並落 receipt（result=pass;graph-stale-reminded）。非正確性依賴、不自動 build
#   （rebuild 決策歸 marshal）。
#
# 依賴：git、bash 3.2+。退出碼：0 成功／2 鎖衝突／3 驗證失敗／4 preflight 未過。

set -euo pipefail

prog="$(basename "$0")"
die() { printf 'ERROR[%s]: %s\n' "$prog" "$*" >&2; receipt "die: $*"; exit 3; }
info() { printf '[wt-close] %s\n' "$*"; }
warn() { printf '[wt-close] WARN: %s\n' "$*" >&2; }

# ── receipt 落盤（AIR-112）：append-only 一行一筆至共享 .git/wt-close.log────────
# REC_LOG 在 repo 定錨後設值；此前失敗（usage 錯誤等）無從歸屬 repo，不記。
REC_LOG=""
receipt() {  # $1＝result 摘要（newline 攤平維持一行）
  if [ -z "$REC_LOG" ]; then return 0; fi
  local mode="full" br="-" res="${1//$'\n'/ }"
  if [ "$PREFLIGHT" = "1" ]; then mode="preflight"; fi
  if [ -n "${CUR_BR:-}" ]; then br="$CUR_BR"; fi
  if printf '%s|%s|%s|%s|%s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$mode" "$WT_PATH" "$br" "$res" 2>/dev/null >> "$REC_LOG"; then
    return 0
  fi
  warn "receipt 落盤失敗：$REC_LOG 不可寫——本次記錄遺失，收線行為不受影響"
  return 0
}

WT_PATH=""
BASE_REF=""
PREFLIGHT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --wt) WT_PATH="${2:?--wt 需 path}"; shift 2 ;;
    --base) BASE_REF="${2:?--base 需 ref}"; shift 2 ;;
    --preflight) PREFLIGHT=1; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) die "未知參數：$1" ;;
  esac
done

[ -n "$WT_PATH" ] || die "用法：wt-close.sh --wt <path> [--preflight]（--base 預設讀 identity contract 的 owning_line）"
[ -d "$WT_PATH" ] || die "WT 不存在：$WT_PATH"

# ── repo 定錨（P2-A：從 --wt 所指 WT 反推共享 .git——跨 repo 誤調用時鎖對 repo）─────
GIT_COMMON="$(git -C "$WT_PATH" rev-parse --path-format=absolute --git-common-dir)" || die "無法從 $WT_PATH 反推 git common dir（WT 非 git repo worktree？）"
PRIMARY="$(dirname "$GIT_COMMON")"
REC_LOG="$GIT_COMMON/wt-close.log"

# ── lock─────────────────────────────────────────────────────────────────
LOCK="$GIT_COMMON/wt-open.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  OWNER="$(cat "$LOCK/owner" 2>/dev/null || echo '未知持有者')"
  printf 'ERROR[%s]: 鎖被佔（%s）。復原：確認 pid 無活進程後 rm -rf %s\n' "$prog" "$OWNER" "$LOCK" >&2
  receipt "fail(lock-conflict)"
  exit 2
fi
printf '%s %s %s\n' "$$" "$(date +%s)" "${USER:-?}" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT

# ── identity contract 對讀（無檔＝拒收，防收錯 WT）─────────────────────────
IDENT="$WT_PATH/.agent-tmp/wt-identity.json"
[ -f "$IDENT" ] || die "identity contract 不存在：$IDENT （非 wt-open 開的 WT，拒收——人工判定用 git worktree remove）"
jval() { sed -nE "s/.*\"$2\"[[:space:]]*:[[:space:]]*\"([^\"]*)\".*/\1/p" "$IDENT" | head -n 1; }
ID_MODE="$(jval "$IDENT" mode)"
ID_TASK="$(jval "$IDENT" task)"
ID_OWNING="$(jval "$IDENT" owning_line)"
ID_BASE_HASH="$(jval "$IDENT" base_hash)"
ID_BRANCH="$(jval "$IDENT" branch)"
ID_WT_PATH="$(jval "$IDENT" wt_path)"
# identity 契約含 wt_path 斷言（P3-2）：contract 非本 WT（複製盜用／stale）→ 拒收
[ "$ID_WT_PATH" = "$WT_PATH" ] || die "identity wt_path 與 --wt 不符 (identity: $ID_WT_PATH vs given: $WT_PATH )——contract 非本 WT，拒收"
BASE_REF="${BASE_REF:-$ID_OWNING}"
[ -n "$BASE_REF" ] || die "owning 線未知（identity 無 owning_line 且未給 --base）"

# ── preflight 檢查（全唯讀）──────────────────────────────────────────────
FAIL=0
TOP="$(git -C "$WT_PATH" rev-parse --show-toplevel)"
CUR_BR="$(git -C "$WT_PATH" branch --show-current)"

chk() { if [ "$2" = "1" ]; then info "PASS $1"; else warn "FAIL $1 — $3"; FAIL=1; fi }

if [ "$TOP" = "$WT_PATH" ] && [ "$CUR_BR" = "$ID_BRANCH" ]; then
  chk "P1 identity 對時（mode=$ID_MODE task=$ID_TASK branch=$ID_BRANCH toplevel OK）" 1
else
  chk "P1 identity 對時" 0 "toplevel=$TOP branch=$CUR_BR 但 identity 宣稱 wt=$WT_PATH branch=$ID_BRANCH"
fi

DIRTY="$(git -C "$WT_PATH" status --porcelain)"
if [ -z "$DIRTY" ]; then chk "P2 working tree clean" 1
else chk "P2 working tree clean" 0 "$DIRTY"; fi

# 池 symlink 污染檢查（branch 若收進 symlink entry，收斂會污染 trunk——preflight 攔下）
POLLUTED="$(git -C "$WT_PATH" ls-tree -r "$CUR_BR" -- .agents 2>/dev/null | grep 120000 || true)"
if [ -z "$POLLUTED" ]; then chk "P2.5 無被追蹤的池 symlink" 1
else chk "P2.5 無被追蹤的池 symlink" 0 "$POLLUTED——先 git rm --cached 清除再收"; fi

COMMITS="$(git -C "$WT_PATH" log --format='%h %s' "${BASE_REF}..${CUR_BR}")"
N_COMMITS="$(printf '%s' "$COMMITS" | grep -c . || true)"
if [ "$ID_MODE" = "card" ]; then
  TAG="$(printf '%s' "$ID_TASK" | tr 'A-Z' 'a-z')"
  FOREIGN="$(printf '%s\n' "$COMMITS" | grep -ivE "${TAG}([^0-9.]|$)" || true)"
  if [ -z "$FOREIGN" ]; then chk "P3 commits scope（$N_COMMITS 顆全屬 $TAG ）" 1
  else chk "P3 commits scope" 0 "含非本卡 subject：$FOREIGN"; fi
else
  chk "P3 commits scope（ephemeral $N_COMMITS 顆，僅點名）" 1
fi

OWNING_TIP="$(git -C "$WT_PATH" rev-parse --verify "${BASE_REF}^{commit}")" || die "owning ref 解析失敗：$BASE_REF"
if [ "$OWNING_TIP" = "$ID_BASE_HASH" ]; then
  chk "P4 owning 線未前進（ff-only candidate）" 1
  NEED_REBASE=0
else
  ADVANCED="$(git -C "$WT_PATH" log --oneline -5 "${ID_BASE_HASH}..${OWNING_TIP}")"
  warn "P4 owning 線已前進（baseline／relay 假設需對照）：$ADVANCED"
  NEED_REBASE=1
fi

# 收斂可行性：main（trunk）由誰 checkout？
TRUNK="${BASE_REF}"
TRUNK_WT=""
PREV=""
while IFS= read -r line; do
  case "$line" in
    worktree\ *) PREV="${line#worktree }" ;;
    branch\ refs/heads/"$TRUNK") TRUNK_WT="$PREV" ;;
  esac
done <<EOF
$(git -C "$WT_PATH" worktree list --porcelain)
EOF
TRUNK_WT_CLEAN=1
if [ -n "$TRUNK_WT" ]; then
  [ -z "$(git -C "$TRUNK_WT" status --porcelain)" ] || TRUNK_WT_CLEAN=0
fi
if [ "$NEED_REBASE" = "1" ]; then
  if git -C "$WT_PATH" merge-base --is-ancestor "$OWNING_TIP" "$CUR_BR"; then
    chk "P5 收斂可行性（owning 已含於 branch——免 rebase）" 1
  else
    chk "P5 收斂可行性（將 rebase $CUR_BR onto $TRUNK ）" 1
  fi
  # trunk clean 檢查對 rebase 路徑同樣適用（ff-only merge 在 full 模式需要；
  # 漏檢＝preflight PASS 但 full 晚死——0922 AIR-153 實證，codex 152 複審指認）
  chk "P5b trunk clean（${TRUNK_WT} clean=${TRUNK_WT_CLEAN}）" "$([ "${TRUNK_WT_CLEAN}" = "1" ] && echo 1 || echo 0)" "${TRUNK_WT} working tree 不 clean——先處理再收（含他弧 runtime 檔：確認 gitignored 或歸屬）"
else
  chk "P5 收斂可行性（$TRUNK @ ${TRUNK_WT:-暫時 worktree}${TRUNK_WT:+，clean=$TRUNK_WT_CLEAN}）" "$([ "$TRUNK_WT_CLEAN" = "1" ] && echo 1 || echo 0)" "$TRUNK_WT working tree 不 clean——先處理再收"
fi

# 池副本分流提醒（不自動執行）
info "池副本提醒：池 gitignored——WT 池寫入已隨 symlink 直落 primary canonical；若有池結構副本需重放，由 marshal 合併後套（本腳本不自動執行）"

if [ "$PREFLIGHT" = "1" ]; then
  rm -rf "$LOCK"; trap - EXIT
  if [ "$FAIL" = "1" ]; then
    receipt "fail(preflight-checks)"
    printf '[wt-close] preflight 未過（零變更）\n' >&2; exit 4
  fi
  receipt "pass"
  info "✅ preflight 全過（零變更＝內容面；鎖面有短暫副作用）——收斂由 marshal 收線時在 user 授權下執行"
  exit 0
fi
[ "$FAIL" = "0" ] || { receipt "fail(preflight-checks)"; printf '[wt-close] preflight 未過，停止（零變更）——先處理 FAIL 項或改跑 --preflight 檢視\n' >&2; exit 4; }

# ── 收斂：rebase → ff-only 吸收（trunk 永不被 rebase、永不 force）──────────
if [ "$NEED_REBASE" = "1" ]; then
  if git -C "$WT_PATH" merge-base --is-ancestor "$OWNING_TIP" "$CUR_BR"; then
    info "owning 已含於 branch，跳過 rebase"
  else
    info "rebase $CUR_BR onto $TRUNK ..."
    git -C "$WT_PATH" rebase "$TRUNK" || {
      git -C "$WT_PATH" rebase --abort 2>/dev/null || true
      die "rebase 衝突——已 abort 留現場，人工依 /rebase owning 線處理"
    }
  fi
fi

MERGE_TARGET_BRANCH="$CUR_BR"
# CR freshness（AIR-164）：merge 前先捕捉 trunk 是否已含 card branch——未含＝本次收斂
# 將實際前進 trunk（供收尾條件式提醒；非正確性依賴）
TRUNK_ADVANCED=0
git -C "$PRIMARY" merge-base --is-ancestor "$MERGE_TARGET_BRANCH" "$TRUNK" || TRUNK_ADVANCED=1
cleanup_tmp() { [ -n "${TMP_WT:-}" ] && git -C "$PRIMARY" worktree remove --force "$TMP_WT" 2>/dev/null || true; }
MERGE_WT=""
if [ -n "$TRUNK_WT" ]; then
  [ "$TRUNK_WT_CLEAN" = "1" ] || die "trunk checkout WT 不 clean：$TRUNK_WT"
  MERGE_WT="$TRUNK_WT"
  warn "將推動 $TRUNK_WT 的 HEAD（$TRUNK fast-forward）——收線前確認該 session 已協調"
  git -C "$TRUNK_WT" merge --ff-only "$MERGE_TARGET_BRANCH" || die "ff-only 被拒——trunk 已前進且非 ancestor？停下查原因（禁 force）"
  info "ff-only 吸收進 $TRUNK @ $TRUNK_WT"
else
  TMP_WT="$GIT_COMMON/wt-close-tmp.$$"
  git -C "$PRIMARY" worktree add "$TMP_WT" "$TRUNK" || die "暫時 trunk worktree 建立失敗"
  trap 'cleanup_tmp; rm -rf "$LOCK"' EXIT
  TMP_HEAD="$(git -C "$TMP_WT" symbolic-ref HEAD 2>/dev/null || true)"
  [ "$TMP_HEAD" = "refs/heads/$TRUNK" ] || \
    die "暫時 trunk worktree HEAD 未掛 refs/heads/$TRUNK (got: ${TMP_HEAD:-detached}) -- ff 將落在非 trunk HEAD (rc=0 假收斂)，停下"
  MERGE_WT="$TMP_WT"
  git -C "$TMP_WT" merge --ff-only "$MERGE_TARGET_BRANCH" || die "ff-only 被拒——停下查原因（禁 force）"
  info "ff-only 吸收進 $TRUNK @ 暫時 worktree"
fi
# 收斂結果斷言：merge rc=0 不等於 trunk 真的吸收——ref 未前進即靜默假綠（T9 事故類），大聲失敗
git -C "$PRIMARY" merge-base --is-ancestor "$MERGE_TARGET_BRANCH" "$TRUNK" || \
  die "收斂驗證失敗：$TRUNK 未含 $MERGE_TARGET_BRANCH (merge rc=0 但 ref 未前進) -- 現場保留，人工依 git log/reflog 判定"

# ── finalization 提醒（board 單寫者＝board-control；腳本不代寫）─────────────
info "board finalization 提醒：git 收斂已完成——結案兩步（status Done＋final summary／done refs）與 metadata commit 由 board-control（marshal／主 session）依 kanban-board skill 執行"

# ── 移除卡 WT → 刪 branch → 暫時 WT 收掉＋釋鎖─────────────────────────────
# 順序依據：ff merge 已保證吸收；git 拒刪「被任何 WT checkout」的 branch——必須先移除
# 卡 WT 才能刪 branch；branch -d 在 trunk checkout 處執行（-d 只認執行處 HEAD 的合併狀態）
git -C "$PRIMARY" worktree remove "$WT_PATH" || die "worktree remove 失敗（dirty？P2 應已攔）"
git -C "$MERGE_WT" branch -d "$CUR_BR" || die "branch -d 被拒（未完全合併？）——停下查原因，禁 -D"
if [ -n "${TMP_WT:-}" ]; then
  git -C "$PRIMARY" worktree remove "$TMP_WT"
  TMP_WT=""
  trap 'rm -rf "$LOCK"' EXIT
fi
info "已移除：WT $WT_PATH ＋ branch $CUR_BR （identity contract 隨 .agent-tmp 同滅）"

rm -rf "$LOCK"; trap - EXIT
if [ "$TRUNK_ADVANCED" = "1" ]; then
  warn "CR freshness 提醒：trunk 已實際前進（吸收 ${CUR_BR}）——code-reality graph 可能 stale，下次 review 前建議 code-reality rebuild（非正確性依賴，不自動 build）"
  receipt "pass;graph-stale-reminded"
else
  receipt "pass"
fi
info "✅ wt-close 完成：$TRUNK @ $(git -C "$PRIMARY" rev-parse --short "$TRUNK")"
