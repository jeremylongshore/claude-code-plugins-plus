#!/usr/bin/env bash
# Catalog: F1 — License compatibility check for newly added dependencies
# Lists new deps and prompts manual license verification. Does NOT look up
# SPDX from registries (too heavy for a gate); informational only.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

CLONE="$HOME/000-projects/contributing-clanker/${GATE_REPO##*/}"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
if [[ -z "$DEFAULT_BRANCH" ]]; then
  gate_skip "no default_branch in dossier"
fi

REPO_LICENSE=$(fm_field "$GATE_DOSSIER_PATH" "license")
[[ -z "$REPO_LICENSE" ]] && REPO_LICENSE="unknown"

CHANGED=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" --name-only 2>/dev/null || /usr/bin/echo "")

MANIFESTS=()
while IFS= read -r f; do
  case "$f" in
    package.json|*/package.json) MANIFESTS+=("$f") ;;
    Cargo.toml|*/Cargo.toml) MANIFESTS+=("$f") ;;
    requirements.txt|*/requirements.txt) MANIFESTS+=("$f") ;;
    pyproject.toml|*/pyproject.toml) MANIFESTS+=("$f") ;;
    go.mod|*/go.mod) MANIFESTS+=("$f") ;;
    Gemfile|*/Gemfile) MANIFESTS+=("$f") ;;
  esac
done <<< "$CHANGED"

if (( ${#MANIFESTS[@]} == 0 )); then
  gate_pass "no dependency manifest changes"
fi

NEW_DEPS=()
for m in "${MANIFESTS[@]}"; do
  DIFF=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" -- "$m" 2>/dev/null || /usr/bin/echo "")
  # Best-effort regex per manifest type — extract package names from + lines
  case "$m" in
    *package.json)
      while IFS= read -r line; do
        name=$(/usr/bin/printf '%s' "$line" | /usr/bin/sed -nE 's/^\+[[:space:]]*"([^"]+)":[[:space:]]*"[^"]+".*$/\1/p')
        [[ -n "$name" ]] && NEW_DEPS+=("$name")
      done <<< "$DIFF"
      ;;
    *Cargo.toml)
      while IFS= read -r line; do
        name=$(/usr/bin/printf '%s' "$line" | /usr/bin/sed -nE 's/^\+[[:space:]]*([a-zA-Z0-9_-]+)[[:space:]]*=.*$/\1/p')
        [[ -n "$name" ]] && NEW_DEPS+=("$name")
      done <<< "$DIFF"
      ;;
    *requirements.txt)
      while IFS= read -r line; do
        name=$(/usr/bin/printf '%s' "$line" | /usr/bin/sed -nE 's/^\+[[:space:]]*([a-zA-Z0-9_.-]+)[[:space:]]*[<>=~!].*$/\1/p; s/^\+[[:space:]]*([a-zA-Z0-9_.-]+)[[:space:]]*$/\1/p')
        [[ -n "$name" ]] && NEW_DEPS+=("$name")
      done <<< "$DIFF"
      ;;
    *pyproject.toml)
      while IFS= read -r line; do
        name=$(/usr/bin/printf '%s' "$line" | /usr/bin/sed -nE 's/^\+[[:space:]]*"([a-zA-Z0-9_.-]+)[[:space:]<>=~!].*"$/\1/p; s/^\+[[:space:]]*([a-zA-Z0-9_.-]+)[[:space:]]*=[[:space:]]*".*$/\1/p')
        [[ -n "$name" ]] && NEW_DEPS+=("$name")
      done <<< "$DIFF"
      ;;
    *go.mod)
      while IFS= read -r line; do
        name=$(/usr/bin/printf '%s' "$line" | /usr/bin/sed -nE 's/^\+[[:space:]]*([a-zA-Z0-9_./-]+)[[:space:]]+v[0-9].*$/\1/p')
        [[ -n "$name" ]] && NEW_DEPS+=("$name")
      done <<< "$DIFF"
      ;;
    *Gemfile)
      while IFS= read -r line; do
        name=$(/usr/bin/printf '%s' "$line" | /usr/bin/sed -nE "s/^\+[[:space:]]*gem[[:space:]]+['\"]([^'\"]+)['\"].*$/\1/p")
        [[ -n "$name" ]] && NEW_DEPS+=("$name")
      done <<< "$DIFF"
      ;;
  esac
done

if (( ${#NEW_DEPS[@]} == 0 )); then
  gate_pass "no new dependency entries detected in changed manifests"
fi

# Dedupe
UNIQ=$(/usr/bin/printf '%s\n' "${NEW_DEPS[@]}" | /usr/bin/awk '!seen[$0]++' | /usr/bin/tr '\n' ',' | /usr/bin/sed 's/,$//')

gate_inform "new dependencies added: $UNIQ; verify license compatibility with repo's $REPO_LICENSE license manually"
