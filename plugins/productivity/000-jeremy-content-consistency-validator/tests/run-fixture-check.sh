#!/usr/bin/env bash
# Red/green fixture gate for the content-consistency validator (GH issue #991).
#
# GREEN (exit 0) iff the deterministic checker finds:
#   - ZERO findings on fixtures/clean/           (no invented findings), AND
#   - EXACTLY the seeded findings from fixtures/expected-findings.json on
#     fixtures/drifted/ (zero invented, zero missed).
# Anything else is RED (exit 1).
#
# Local:
#   bash plugins/productivity/000-jeremy-content-consistency-validator/tests/run-fixture-check.sh
# CI (step in .github/workflows/validate-plugins.yml):
#   run: bash plugins/productivity/000-jeremy-content-consistency-validator/tests/run-fixture-check.sh
#
# Dependency-free: bash + python3 stdlib only. No LLM, no network, no installs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

exec python3 "$SCRIPT_DIR/fixture_checker.py" gate --fixtures-dir "$PLUGIN_DIR/fixtures"
