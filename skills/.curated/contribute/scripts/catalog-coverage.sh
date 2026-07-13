#!/usr/bin/env bash
# catalog-coverage.sh — report which catalog modes have gate implementations.
#
# Closes contributing-clanker-p5q.3.
#
# The 62-failure-mode catalog lives at:
#   <repo>/000-docs/007-DR-CATG-failure-mode-catalog.md
# Each row maps a mode ID (e.g. A1, B12, C5) to a "Gate" column with either:
#   - a real gate filename (e.g. "a01-already-assigned")
#   - "(planned)" for unimplemented modes
#   - "(see ...)" for modes covered by a different gate via reference
#
# Coverage = real-gate count / total catalog count.
# Output: per-phase table + overall %.

set -uo pipefail

CATALOG="${1:-${HOME}/000-projects/contributing-clanker/000-docs/007-DR-CATG-failure-mode-catalog.md}"
GATES_DIR="${HOME}/.claude/skills/contribute/scripts/gates"

if [[ ! -f "$CATALOG" ]]; then
  /usr/bin/printf 'catalog not found: %s\n' "$CATALOG" >&2
  /usr/bin/printf 'usage: %s [path-to-catalog.md]\n' "$0" >&2
  exit 2
fi

if [[ ! -d "$GATES_DIR" ]]; then
  /usr/bin/printf 'gates dir not found: %s\n' "$GATES_DIR" >&2
  exit 2
fi

# Extract catalog rows. Format: | A1 | description | trigger | gate-name |
# We only care about rows where col 1 is a single-letter+digit ID and col 4
# (last col) is the gate ref.
#
# Each markdown table row: | id | failure | trigger | gate |
# We want id (col 2 after leading |) and gate (col 5 after leading |).
parse_catalog() {
  /usr/bin/awk -F'|' '
    /^\| *[A-G][0-9]+ *\|/ {
      gsub(/^[ \t]+|[ \t]+$/, "", $2)   # mode id
      gsub(/^[ \t]+|[ \t]+$/, "", $5)   # gate ref
      print $2 "\t" $5
    }
  ' "$CATALOG"
}

# Aggregate per phase (A,B,C,D,E,F,G)
declare -A phase_total phase_planned phase_implemented
total=0
implemented=0
planned=0

while IFS=$'\t' read -r id gate; do
  phase="${id:0:1}"
  phase_total[$phase]=$(( ${phase_total[$phase]:-0} + 1 ))
  total=$(( total + 1 ))
  case "$gate" in
    *planned*)
      phase_planned[$phase]=$(( ${phase_planned[$phase]:-0} + 1 ))
      planned=$(( planned + 1 ))
      ;;
    *)
      # Real gate ref. Confirm a script file actually exists for it.
      # Gate refs in the catalog look like "a01-already-assigned" — match by
      # prefix lower-case + leading digits.
      gate_id_normalized=$(/usr/bin/printf '%s' "$gate" | /usr/bin/tr '[:upper:]' '[:lower:]' | /usr/bin/sed 's/[^a-z0-9].*//')
      if /usr/bin/find "$GATES_DIR" -maxdepth 1 -name "${gate_id_normalized}*.sh" -print -quit 2>/dev/null | /usr/bin/grep -q .; then
        phase_implemented[$phase]=$(( ${phase_implemented[$phase]:-0} + 1 ))
        implemented=$(( implemented + 1 ))
      else
        phase_planned[$phase]=$(( ${phase_planned[$phase]:-0} + 1 ))
        planned=$(( planned + 1 ))
      fi
      ;;
  esac
done < <(parse_catalog)

# Render
/usr/bin/printf '\nCatalog → Gate coverage\n'
/usr/bin/printf '═════════════════════════════════════════\n'
/usr/bin/printf '%-8s %10s %12s %10s\n' "PHASE" "TOTAL" "IMPLEMENTED" "COVERAGE"
/usr/bin/printf '─────────────────────────────────────────\n'
for phase in A B C D E F G; do
  t=${phase_total[$phase]:-0}
  i=${phase_implemented[$phase]:-0}
  if [[ $t -gt 0 ]]; then
    pct=$(( i * 100 / t ))
    /usr/bin/printf '%-8s %10s %12s %9s%%\n' "$phase" "$t" "$i" "$pct"
  fi
done
/usr/bin/printf '─────────────────────────────────────────\n'
overall_pct=$(( implemented * 100 / total ))
/usr/bin/printf '%-8s %10s %12s %9s%%\n' "TOTAL" "$total" "$implemented" "$overall_pct"
/usr/bin/printf '═════════════════════════════════════════\n\n'

if [[ $planned -gt 0 ]]; then
  /usr/bin/printf '  %d catalog mode(s) still planned (no gate file).\n\n' "$planned"
fi
