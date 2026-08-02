#!/usr/bin/env bash
# Name-leak gate — the design-reference site studied for the neobrutalist
# rebrand is intentionally anonymous in this repository. See
# 000-docs/706-AT-DECR-neobrutalist-rebrand-anonymity-preamble.md.
#
# This gate fails if any identifying string appears in tracked OR untracked
# files (scratch notes and lockfiles included). Patterns are stored
# base64-encoded so the gate file itself stays clean; runs as a step in the
# `validate` job of .github/workflows/validate-plugins.yml (already inside
# ci-required's needs, so it is blocking) and manually before commits.
#
# Ported from the sibling blog/jeremylongshore implementation rather than
# reinvented — one mechanism, one pattern list shape, one failure mode.
#
# ONE pattern from the sibling list is deliberately NOT carried here: the
# generic hyphenated term that also appears, unrelated, in six files of the
# community `skills-janitor` plugin. In a repo with 3,000+ skills that term is
# ordinary vocabulary, so including it would make this gate fail on every run —
# and a gate that always fails is a gate that gets deleted. The distinctive
# patterns below are the ones that would actually identify the reference site.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PATTERNS_B64=(
  'Y29yZXk='
  'aGFpbmVz'
  'c3dpcGV3ZWxs'
  'c3dpcGVmaWxlcw=='
  'Y29udmVyc2lvbmZhY3Rvcnk='
  'Y29udmVyc2lvbiBmYWN0b3J5'
  'bWFnaXN0ZXJtYXJrZXRpbmc='
  'dHJ1ZWxpc3QuaW8='
  'Y29kaW5nZm9ybWFya2V0ZXJz'
  'cmV0ZXh0Lmlv'
  'bWFrZXJza2lsbHM='
)

fail=0
for b64 in "${PATTERNS_B64[@]}"; do
  pattern=$(printf '%s' "$b64" | base64 -d)
  if hits=$(git grep -I -i -F -n --untracked -- "$pattern" -- ':!scripts/name-leak-gate.sh' 2>/dev/null); then
    echo "LEAK: pattern #${b64:0:6}… found:"
    echo "$hits"
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "name-leak-gate: FAILED — remove the identifying strings above." >&2
  exit 1
fi
echo "name-leak-gate: clean"
