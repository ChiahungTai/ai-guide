#!/usr/bin/env bash
# muse memory governance hook (AIR-79 S1; divert semantics origin AIR-54).
# Shared core for the muse-memory-governance plugin: PreToolUse gate for
# add_memory/edit_memory with per-repo marker three-state opt-in.
#
# Contract (09-09 experiments, AIR-54; unchanged):
# - stdin: {"tool_name": "...", "tool_input": {scope, path, content}}
# - deny via CC-style hookSpecificOutput; allow = silent exit 0.
# - Deny emission is jq-free (printf template + minimal escaping) so a
#   degraded jq still yields a legal deny schema (EP review C3).
#
# Origins (EP S1 要點2/3):
# - plugin origin (no governance env): resolve repo per call
#   (GOVERNANCE_REPO > stdin cwd field [order frozen — see resolver
#   comment; workspace/host_workspace kept as fallbacks] > git $PWD
#   upward), marker three-state, inbox containment check, fail-closed
#   divert.
# - registered origin (thin launcher sets GOVERNANCE_ORIGIN=registered +
#   GOVERNANCE_REPO=<repo root>): skips repo resolution / marker — the
#   registered gate diverts unconditionally, gate semantics identical to
#   the pre-refactor launcher hook (migration-window contract: pre-marker
#   repos must not silently lose the gate, EP review C1).
#
# Decision order (EP pseudo code skeleton; each step exits early):
#   empty stdin -> crude self-filter -> jq availability -> precise
#   tool_name filter -> repo resolve -> marker three-state (plugin
#   origin) -> inbox symlink containment (all origins) -> divert
#   (atomic, CAS lexical gates, fail-closed) -> deny with inbox path.
#
# 2026-09-14 security closure (AIR-79, codex advisory): the hooks.json
# owner-yield branch was removed — the launcher era is retired, so a
# repo-controllable hooks.json is untrusted input and honoring a claimed
# owner let a repo no-op the only gate (bypass surface). This plugin is
# the sole write gate; no yield path exists (removal record: plugin
# README Gate 語義節).
set -euo pipefail
umask 077

deny() {
  # jq-free deny emission; JSON-string-safe escaping (review R1/C-C2): raw
  # control bytes in the reason would break the schema -> muse fail-open on a
  # path that is supposed to be fail-closed. Map \n \r \t to JSON escapes,
  # then strip any remaining control chars (<0x20).
  local reason=${1//\\/\\\\}
  reason=${reason//\"/\\\"}
  reason=${reason//$'\n'/\\n}
  reason=${reason//$'\r'/\\r}
  reason=${reason//$'\t'/\\t}
  # Strip remaining control chars (<0x20) only when tr exists — the newline/
  # CR/tab mappings above are pure bash and always apply; an absent tr must
  # not empty the reason (degraded PATH environments run this code path).
  STRIPPED=$(printf '%s' "$reason" | tr -d '\000-\037' 2>/dev/null) && reason=$STRIPPED
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
  exit 0
}

deny_degraded() {
  deny "memory-governance tooling degraded: jq unavailable or unusable, cannot evaluate the repo governance state; conservatively denying the memory write (fail-closed). Install jq (e.g. 'brew install jq') and retry."
}

IN=$(cat) || deny "memory-governance: stdin unreadable (fail-closed)"
[ -n "$IN" ] || exit 0   # SM-13 empty stdin: nothing to divert

# Self-filter, fast path: crude bash string match on memory-tool features
# (superset — plugin hooks have no matcher; the precise check below needs jq).
case "$IN" in
  *add_memory*|*edit_memory*) : ;;
  *) exit 0 ;;
esac

# jq availability: without jq we cannot parse tool_name or the marker, so
# the opt-out state is unevaluable -> conservative deny (EP ⑦ taxonomy).
command -v jq >/dev/null 2>&1 || deny_degraded

# Precise self-filter: a crude hit may be innocent text mentioning the tool
# names; only actual memory tools are gated (EP ①: tool_name not in
# {add_memory, edit_memory} -> exit 0). jq failing here is the same
# "cannot parse tool_name" degraded family as above.
TOOL=$(printf '%s' "$IN" | jq -r '.tool_name // empty' 2>/dev/null) || deny_degraded
case "$TOOL" in
  add_memory|edit_memory) : ;;
  *) exit 0 ;;
esac

# Repo resolution: env (launcher/fallback injection) > stdin repo fields
# (order .cwd // .workspace // .host_workspace — frozen, live 2026-09-14;
# absence tolerated) > git rev-parse upward from $PWD.
REPO=""
if [ -n "${GOVERNANCE_REPO:-}" ]; then
  REPO=$GOVERNANCE_REPO
else
  # P-WS frozen (live 2026-09-14): muse live stdin carries `cwd` (workspace
  # root); no `workspace`/`host_workspace` field exists. Alternates kept as
  # backward-compat fallbacks.
  REPO=$(printf '%s' "$IN" | jq -r '.cwd // .workspace // .host_workspace // empty' 2>/dev/null || true)
  if [ -n "$REPO" ]; then
    # Seam hardening (P-WS frozen order): a stdin-derived repo is
    # untrusted input — only trust it when it is itself a git root; otherwise
    # fall back to $PWD-based resolution (harness cwd-in-repo semantics).
    SEAM_OK=$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null || true)
    [ "$SEAM_OK" = "$REPO" ] || REPO=""
  fi
fi
if [ -z "$REPO" ]; then
  # git-binary-missing vs explicit not-a-repo vs git execution fault are
  # distinct branches (EP ⑦ taxonomy, review C-C3): binary missing and
  # explicit non-repo allow native (repo/marker unobservable or absent);
  # any other rev-parse failure denies — the workspace governance state
  # cannot be determined (fail-closed).
  if ! command -v git >/dev/null 2>&1; then
    exit 0   # git binary missing: repo unresolvable, marker unobservable
  fi
  if ! GIT_OUT=$(git rev-parse --show-toplevel 2>&1); then
    case "$GIT_OUT" in
      *"not a git repository"*) exit 0 ;;   # SM-11 determined non-repo
      *) deny "memory-governance: git rev-parse failed (workspace governance state undeterminable, fail-closed): $GIT_OUT" ;;
    esac
  fi
  REPO=$GIT_OUT
fi

# Marker three-state (plugin origin; registered origin diverts
# unconditionally per the migration-window contract, EP S1 要點3).
# jq numeric equality reads 1.0 as 1 — JSON has a single number type.
if [ "${GOVERNANCE_ORIGIN:-}" != registered ]; then
  MARKER=$REPO/.agents/memory-governance.json
  if [ ! -e "$MARKER" ] && [ ! -L "$MARKER" ]; then
    exit 0   # SM-2 absent: allow native (determined non-governed)
  fi
  # Contract (review C-C4/R5 ruling): a JSON *number* equal to 1 is the only
  # valid protocol — jq numeric equality accepts lexical 1.0/1e0 as the same
  # number, which is accepted by design (semantic number equality, not
  # lexical form). Everything else (parse failure, missing field, 0, -1, "1",
  # null, true, false, numbers != 1) denies without landing — a declared
  # governance state must not fail open (SM-3/SM-4).
  if ! jq -e '.protocol == 1' "$MARKER" >/dev/null 2>&1; then
    deny "memory-governance marker malformed/unsupported: $MARKER (protocol must be the number 1)"
  fi
fi

# Inbox containment (all origins, A7): lstat each path segment — any
# existing symlink component denies without landing (SM-12); ENOENT
# segments are safe (the hook creates them below).
for SEG in "$REPO" "$REPO/.agents" "$REPO/.agents/memory-inbox"; do
  if [ -L "$SEG" ]; then
    deny "memory-governance: inbox path fails symlink/containment check: $SEG"
  fi
done

# Divert — AIR-54 semantics: atomic tmp+rename,
# filename = timestamp + pid + content hash (no model-supplied basename),
# CAS enrichment behind the T3-1/T4-2 lexical gates. Every internal
# failure denies (fail-closed, EP ⑦ — muse itself is fail-open).
TS=$(date +%Y%m%d-%H%M%S) || deny "memory-governance: divert failed (governed repo fail-closed): timestamp unavailable"
INBOX=$REPO/.agents/memory-inbox
SUM=$(printf '%s' "$IN" | shasum -a 256 | cut -c1-12) || deny "memory-governance: divert failed (governed repo fail-closed): checksum unavailable"
OUT=$INBOX/${TS}-$$-${SUM}.json
TMP=$INBOX/.tmp-${TS}-$$-${SUM}
mkdir -p "$INBOX" || deny "memory-governance: divert failed (governed repo fail-closed): cannot create $INBOX"

PAYLOAD=$IN
# jq parse failure must NOT kill the script (set -e) — P falls back to
# empty -> no-enrichment path -> deny+land still happens (AIR-54 review F1).
P=$(printf '%s' "$IN" | jq -r '.tool_input.path // empty' 2>/dev/null || true)
# T3-1 lexical gate: P is unverified model input — never dereference it
# before this gate. T4-2: consolidation only takes pool-root basenames,
# so any P with a slash (absolute or nested) skips enrichment; trailing
# symlink targets are excluded by the [ ! -L ] check below.
SAFE_P=""
case "$P" in
  *.md)
    case "$P" in /*|*/*) : ;; *) SAFE_P=$P ;; esac
    ;;
esac
if [ -n "$SAFE_P" ] \
  && [ -f "$REPO/.agents/memory/$SAFE_P" ] \
  && [ ! -L "$REPO/.agents/memory/$SAFE_P" ]; then
  H=$(shasum -a 256 "$REPO/.agents/memory/$SAFE_P" 2>/dev/null | cut -d' ' -f1) || H=""
  if [ -n "$H" ]; then
    PAYLOAD=$(jq -c --arg p "$SAFE_P" --arg h "$H" \
      '. + {_inbox_meta:{base_path:$p, base_sha256:$h}}' <<<"$IN" 2>/dev/null) || PAYLOAD=$IN
  fi
fi

if ! printf '%s' "$PAYLOAD" > "$TMP" 2>/dev/null; then
  rm -f "$TMP" 2>/dev/null || true
  deny "memory-governance: divert failed (governed repo fail-closed): cannot write $TMP"
fi
if ! mv -f "$TMP" "$OUT" 2>/dev/null; then
  rm -f "$TMP" 2>/dev/null || true
  deny "memory-governance: divert failed (governed repo fail-closed): cannot finalize $OUT"
fi

deny "已代存 inbox: ${OUT}（consolidation 站將處理入池）"
