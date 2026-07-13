#!/bin/bash
# CI-ready schema validation script
# Usage: ./validate-schema.sh <schema-path> [--strict]
set -e

SCHEMA_PATH="${1:?Usage: validate-schema.sh <schema-path> [--strict]}"
STRICT="${2:-}"

echo "Validating schema: $SCHEMA_PATH"

if [ ! -f "$SCHEMA_PATH" ]; then
  echo "ERROR: Schema file not found: $SCHEMA_PATH" >&2
  exit 1
fi

# Run Spectral linting if available
if command -v spectral &>/dev/null; then
  echo "Running Spectral linting..."
  spectral lint "$SCHEMA_PATH" ${STRICT:+--fail-severity=warn}
else
  echo "WARN: Spectral not installed. Install: npm install -g @stoplight/spectral-cli"
fi

echo "Schema validation complete."
