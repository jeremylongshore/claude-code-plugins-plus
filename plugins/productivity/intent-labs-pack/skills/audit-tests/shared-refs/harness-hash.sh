#!/usr/bin/env bash
# harness-hash.sh — SHA-256 manifest for engineer-owned artifacts.
#
# Pins .feature files and architecture rule configs. Any byte change to a
# pinned file without a fresh --init is treated as HARNESS_TAMPERED and
# causes escape-scan.sh to REFUSE the AI diff.
#
# Usage:
#   bash harness-hash.sh --init      # write manifest (engineer-initiated)
#   bash harness-hash.sh --verify    # compare current hashes to manifest
#   bash harness-hash.sh --list      # show which files are pinned
#
# Exit codes:
#   0 — OK (pin matches, or init succeeded)
#   2 — HARNESS_TAMPERED (hash mismatch)
#   3 — no manifest found (--verify without --init)

set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
MANIFEST="${ROOT}/.harness-hash"

PATTERNS=(
  # Wall 1: acceptance
  "features/**/*.feature"
  "features/*.feature"
  # Wall 7: architecture rule configs
  ".dependency-cruiser.js"
  ".dependency-cruiser.cjs"
  ".importlinter"
  "deptrac.yaml"
  "arch-go.yml"
  # Java ArchUnit tests
  "src/test/java/**/*ArchTest*.java"
  "src/test/java/**/*ArchitectureTest*.java"
  # .NET ArchTests
  "test/**/*ArchTests.cs"
  "tests/**/*ArchTests.cs"
  # Coverage thresholds (edits to these are escape attempts — hash them)
  ".c8rc.json"
  "stryker.conf.json"
  "stryker.config.js"
)

collect_files() {
  local out=()
  shopt -s nullglob globstar
  for pattern in "${PATTERNS[@]}"; do
    for f in $pattern; do
      [[ -f "$f" ]] && out+=("$f")
    done
  done
  # de-dupe
  printf '%s\n' "${out[@]}" | sort -u
}

hash_files() {
  local files
  files=$(collect_files)
  if [[ -z "$files" ]]; then
    return 0
  fi
  while IFS= read -r f; do
    printf '%s  %s\n' "$(sha256sum "$f" | awk '{print $1}')" "$f"
  done <<< "$files"
}

cmd_init() {
  cd "$ROOT"
  hash_files > "$MANIFEST"
  local count
  count=$(wc -l < "$MANIFEST" | tr -d ' ')
  echo "harness-hash: pinned $count file(s) → $MANIFEST"
}

cmd_verify() {
  cd "$ROOT"
  if [[ ! -f "$MANIFEST" ]]; then
    echo "harness-hash: no manifest at $MANIFEST (run --init)" >&2
    exit 3
  fi
  local current
  current=$(hash_files)
  local expected
  expected=$(cat "$MANIFEST")

  # Compare sorted manifests so order doesn't matter
  local diff_out
  diff_out=$(diff <(echo "$expected" | sort) <(echo "$current" | sort) || true)
  if [[ -z "$diff_out" ]]; then
    echo "harness-hash: OK"
    exit 0
  fi
  echo "HARNESS_TAMPERED: pinned artifact changed" >&2
  echo "$diff_out" >&2
  exit 2
}

cmd_list() {
  cd "$ROOT"
  if [[ ! -f "$MANIFEST" ]]; then
    echo "harness-hash: no manifest (run --init)" >&2
    exit 3
  fi
  awk '{print $2}' "$MANIFEST"
}

case "${1:-}" in
  --init)   cmd_init ;;
  --verify) cmd_verify ;;
  --list)   cmd_list ;;
  --help|-h|*)
    sed -n '2,20p' "$0"
    exit 0
    ;;
esac
