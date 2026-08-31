#!/usr/bin/env bash
# Catalog: C3 — PR body draft missing sections required by the repo's PR template
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Pull the raw frontmatter line for pr_template_required_sections (a YAML array)
RAW=$(/usr/bin/awk '
  /^---$/ { fm = !fm ? 1 : 2; next }
  fm == 1 && /^pr_template_required_sections:/ {
    sub(/^pr_template_required_sections:[[:space:]]*/, "")
    print
    exit
  }
' "$GATE_DOSSIER_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$RAW" || "$RAW" == "[]" ]]; then
  gate_skip "no pr_template_required_sections in dossier"
fi

# Strip surrounding [ ], split on commas, strip quotes/whitespace per item
INNER=$(/usr/bin/printf '%s' "$RAW" | /usr/bin/sed -E 's/^\[//; s/\]$//')
if [[ -z "$INNER" ]]; then
  gate_skip "pr_template_required_sections is empty"
fi

# Build array of section names
declare -a SECTIONS=()
IFS=',' read -ra RAW_PARTS <<< "$INNER"
for part in "${RAW_PARTS[@]}"; do
  clean=$(/usr/bin/printf '%s' "$part" | /usr/bin/sed -E 's/^[[:space:]]*"?//; s/"?[[:space:]]*$//')
  [[ -n "$clean" ]] && SECTIONS+=("$clean")
done

if (( ${#SECTIONS[@]} == 0 )); then
  gate_skip "no parseable section names in pr_template_required_sections"
fi

# Extract candidate's `## PR body` section
PR_BODY=$(/usr/bin/awk '/^## PR body/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")
if [[ -z "$PR_BODY" ]]; then
  gate_skip "no '## PR body' section in candidate yet"
fi

# Check each required section name appears as a markdown header (## or ###), case-insensitive
declare -a MISSING=()
for name in "${SECTIONS[@]}"; do
  if ! /usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -qiE "^#{2,3}[[:space:]]+${name}[[:space:]]*$"; then
    MISSING+=("$name")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  joined=$(IFS=', '; /usr/bin/printf '%s' "${MISSING[*]}")
  gate_block "PR body missing required sections: $joined" "add the section headers (## $joined) to your PR body draft"
fi

gate_pass "all required PR body sections present"
