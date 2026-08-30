#!/usr/bin/env bash
# Catalog: C1 — Repo prefers draft PRs first; opening non-draft is anti-pattern
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Only relevant if dossier explicitly says draft_first: true
DRAFT_FIRST=$(fm_field "$GATE_DOSSIER_PATH" "draft_first")
if [[ "$DRAFT_FIRST" != "true" ]]; then
  gate_skip "dossier does not require draft-first PRs"
fi

# Candidate's `draft:` field is set by the writer subagent (Slice 3)
DRAFT=$(fm_field "$GATE_CANDIDATE_PATH" "draft")
if [[ -z "$DRAFT" ]]; then
  gate_skip "draft preference unknown — fill in candidate's \`draft:\` field before opening"
fi

if [[ "$DRAFT" == "false" ]]; then
  gate_block "this repo prefers draft PRs first but candidate has draft: false" "this repo prefers draft PRs first; pass --draft to gh pr create OR set draft: true in the candidate"
fi

gate_pass "candidate set to open as draft (draft: true)"
