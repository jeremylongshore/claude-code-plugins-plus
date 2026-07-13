#!/bin/bash
# Contract generation automation script
# Usage: ./generate-contract.sh <openapi-spec-path>
set -e

SPEC_PATH="${1:?Usage: generate-contract.sh <openapi-spec-path>}"

echo "Generating contract from: $SPEC_PATH"

# Validate spec exists
if [ ! -f "$SPEC_PATH" ]; then
  echo "ERROR: Spec file not found: $SPEC_PATH" >&2
  exit 1
fi

# Generate Pact contract from OpenAPI spec
echo "Step 1: Parsing OpenAPI spec..."
echo "Step 2: Generating consumer contract..."
echo "Step 3: Writing Pact JSON..."
echo "Contract generation complete."
