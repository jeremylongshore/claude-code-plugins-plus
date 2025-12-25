#!/bin/bash
# Quick test run (assumes build is current)

set -e

cd "$(dirname "$0")/.."

echo "Quick test run (chromium desktop only)..."
npx playwright test --project=chromium-desktop --reporter=list

echo ""
echo "Screenshots available in: test-results/screenshots/"
echo "View full report: npx playwright show-report"
