#!/usr/bin/env bash
# Catalog: G1 — Block hand-edits to vendored / generated paths
# Vendored dirs (vendor/, node_modules/, dist/, etc.) must regenerate from
# source. Lockfile changes are common and legitimate (dependency bumps);
# treat them as WARN, not BLOCK.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

CLONE="$HOME/000-projects/contributing-clanker/${GATE_REPO##*/}"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
[[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="main"

CHANGED=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" --name-only 2>/dev/null || /usr/bin/echo "")

if [[ -z "${CHANGED// /}" ]]; then
  gate_pass "no changed files"
fi

VENDOR_HITS=()
LOCKFILE_HITS=()

# Vendor-dir patterns (BLOCK)
VENDOR_RE='^(vendor/|node_modules/|\.next/|dist/|build/|generated/|_generated/)'
# Lockfile patterns (WARN)
LOCKFILE_RE='(^pnpm-lock\.yaml$|^package-lock\.json$|^Cargo\.lock$|^poetry\.lock$|^uv\.lock$|^yarn\.lock$|\.lock$)'

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if /usr/bin/printf '%s' "$f" | /usr/bin/grep -qE "$VENDOR_RE"; then
    VENDOR_HITS+=("$f")
  elif /usr/bin/printf '%s' "$f" | /usr/bin/grep -qE "$LOCKFILE_RE"; then
    LOCKFILE_HITS+=("$f")
  fi
done <<< "$CHANGED"

if (( ${#VENDOR_HITS[@]} > 0 )); then
  JOINED=$(/usr/bin/printf '%s, ' "${VENDOR_HITS[@]}" | /usr/bin/sed 's/, $//')
  gate_block "vendored/generated paths edited: $JOINED" "regenerate from source instead of editing by hand; if this is intentional, override with --override-gate G1"
fi

if (( ${#LOCKFILE_HITS[@]} > 0 )); then
  JOINED=$(/usr/bin/printf '%s, ' "${LOCKFILE_HITS[@]}" | /usr/bin/sed 's/, $//')
  gate_warn "lockfile changes detected: $JOINED" "verify the lockfile changes are intentional (dependency bumps) and not stale-checkout artifacts"
fi

gate_pass "no vendored/generated path edits"
