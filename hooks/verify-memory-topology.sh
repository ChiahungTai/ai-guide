#!/usr/bin/env bash
# Verify the cross-harness memory topology (read-only). Used after
# fresh-machine setup and as the shrunken E2E for the migration
# acceptance gate.
#
# Checks (AIR-223 direct-anchor): pool is a real dir; the required leg is
# ZCode -> pool. The CC alias -> pool is optional compat — verified only
# when present, absence is a SKIP (not a FAIL); every present leg must
# resolve to the same inode; deployed generator --check is green.
# Muse write-gate health is plugin-plane (AIR-79 cutover; the legacy
# hooks.json / launcher checks are retired) — see
# muse-plugins/memory-governance/README.md 運維節.
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
POOL="$REPO/.agents/memory"

pass=0; failn=0
ok() { pass=$((pass + 1)); echo "OK   $1"; }
bad() { failn=$((failn + 1)); echo "FAIL $1"; }

ENCODED=$(printf '%s' "$REPO" | tr '/' '-')
HASH=$(printf '%s' "$REPO" | shasum -a 256 | cut -c1-16)
CC_MEM="$HOME/.claude/projects/$ENCODED/memory"
ZC_MEM="$HOME/.zcode/cli/memories/projects/$(basename "$REPO")-$HASH/memory"

[ -d "$POOL" ] && [ ! -L "$POOL" ] && ok "pool is a real dir" || bad "pool missing or symlink: $POOL"

if [ -L "$ZC_MEM" ] && [ "$(readlink "$ZC_MEM")" = "$POOL" ]; then
  ok "ZCode symlink -> pool"
else
  bad "ZCode link wrong: $ZC_MEM (expected -> $POOL)"
fi

CC_PRESENT=0
if [ -L "$CC_MEM" ] || [ -e "$CC_MEM" ]; then
  if [ -L "$CC_MEM" ] && [ "$(readlink "$CC_MEM")" = "$POOL" ]; then
    ok "CC alias -> pool (optional compat)"
    CC_PRESENT=1
  else
    bad "CC alias wrong: $CC_MEM (expected -> $POOL)"
  fi
else
  echo "SKIP CC alias (optional; project dir absent): $CC_MEM"
fi

if [ -f "$POOL/MEMORY.md" ] && [ -f "$ZC_MEM/MEMORY.md" ]; then
  A=$(python3 -c "import os;print(os.stat('$POOL/MEMORY.md').st_ino)")
  B=$(python3 -c "import os;print(os.stat('$ZC_MEM/MEMORY.md').st_ino)")
  if [ "$CC_PRESENT" = 1 ] && [ -f "$CC_MEM/MEMORY.md" ]; then
    C=$(python3 -c "import os;print(os.stat('$CC_MEM/MEMORY.md').st_ino)")
    [ "$A" = "$B" ] && [ "$B" = "$C" ] && ok "same inode ($A)" || bad "inode mismatch: $A $B $C"
  else
    [ "$A" = "$B" ] && ok "same inode ($A)" || bad "inode mismatch: $A $B"
  fi
else
  bad "MEMORY.md not reachable on required legs (pool + ZCode)"
fi

if [ -f "$POOL/_generate_index.py" ]; then
  GEN_LOG=$(mktemp /tmp/verify-topology-gen.XXXXXX.log)
  if python3 "$POOL/_generate_index.py" --check >"$GEN_LOG" 2>&1; then
    ok "generator --check green"
  else
    bad "generator --check failed (see $GEN_LOG)"
  fi
  rm -f "$GEN_LOG"
else
  bad "deployed generator missing: $POOL/_generate_index.py"
fi

echo "--- $pass passed, $failn failed ---"
[ "$failn" = 0 ]
