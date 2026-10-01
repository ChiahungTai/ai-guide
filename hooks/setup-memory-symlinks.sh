#!/usr/bin/env bash
# Rebuild CC/ZCode memory symlinks for a transferred pool (multi-machine).
#
# Context: the pool (.agents/memory/) is local-only git and never clones.
# After transferring the pool to a new machine (bundle or cp -a), the
# harness-side symlinks must be rebuilt because their directory names are
# machine-derived: CC encodes the repo path (`/` -> `-`), ZCode appends
# sha256(repo path)[:16] (both rules verified empirically 2026-09-09).
#
# Layout rebuilt (AIR-223 direct-anchor; pool = single authority):
#   ZCode memories/<repo>-<hash>/memory -> <repo>/.agents/memory (real dir)
#   CC projects/<encoded>/memory        -> <repo>/.agents/memory  (optional
#     compat alias; built only when the CC project dir already exists,
#     otherwise SKIP — never a prerequisite)
#
# Safety: default is DRY-RUN (print plan only). `--apply` executes, and
# every replaced entry is first moved to <name>.bak-<timestamp> (never rm).
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
POOL="$REPO/.agents/memory"
fail() { echo "setup-memory-symlinks: FAIL: $1" >&2; exit 1; }

APPLY=0
case "${1:-}" in
  --apply) APPLY=1 ;;
  "") : ;;
  *) fail "unknown argument: $1 (usage: setup-memory-symlinks.sh [--apply])" ;;
esac

[ -d "$POOL" ] && [ ! -L "$POOL" ] || fail "pool missing or not a real dir: $POOL (transfer it first: bundle clone or cp -a, see MULTI-MACHINE.md)"

ENCODED=$(printf '%s' "$REPO" | tr '/' '-')
HASH=$(printf '%s' "$REPO" | shasum -a 256 | cut -c1-16)
CC_MEM="$HOME/.claude/projects/$ENCODED/memory"
ZC_MEM="$HOME/.zcode/cli/memories/projects/$(basename "$REPO")-$HASH/memory"

plan_entry() { # $1=label $2=link-path $3=target
  if [ -L "$2" ] && [ "$(readlink "$2")" = "$3" ]; then
    echo "OK   $1 already points at target: $2"
  elif [ -e "$2" ] || [ -L "$2" ]; then
    echo "PLAN $1 backup $2 -> $2.bak-$(date +%Y%m%d-%H%M%S), then ln -s $3 $2"
  else
    echo "PLAN $1 create parent dirs, then ln -s $3 $2"
  fi
}

do_entry() { # $1=label $2=link-path $3=target
  if [ -L "$2" ] && [ "$(readlink "$2")" = "$3" ]; then
    echo "OK   $1 already points at target: $2"
    return 0
  fi
  if [ -e "$2" ] || [ -L "$2" ]; then
    BAK="$2.bak-$(date +%Y%m%d-%H%M%S)"
    mv "$2" "$BAK"
    echo "BACKUP $1 moved to $BAK"
  fi
  mkdir -p "$(dirname "$2")"
  ln -s "$3" "$2"
  echo "LINK $1 $2 -> $3"
}

if [ "$APPLY" = 1 ]; then
  do_entry "ZCode" "$ZC_MEM" "$POOL"
  if [ -d "$(dirname "$CC_MEM")" ]; then
    do_entry "CC" "$CC_MEM" "$POOL"
  else
    echo "SKIP CC alias (optional; project dir absent): $(dirname "$CC_MEM")"
  fi
else
  echo "(dry-run; pass --apply to execute)"
  plan_entry "ZCode" "$ZC_MEM" "$POOL"
  if [ -d "$(dirname "$CC_MEM")" ]; then
    plan_entry "CC" "$CC_MEM" "$POOL"
  else
    echo "SKIP CC alias (optional; project dir absent): $(dirname "$CC_MEM")"
  fi
fi
