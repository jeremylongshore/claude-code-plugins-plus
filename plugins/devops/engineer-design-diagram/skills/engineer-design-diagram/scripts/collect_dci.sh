#!/usr/bin/env bash
# collect_dci.sh — bounded DCI harvester for engineer-design-diagram.
# Emits a JSON document to stdout with topology signals, respecting size caps
# documented in references/dci-block.md.
#
# Usage: collect_dci.sh [repo-root]
# Default repo-root: $(pwd)
#
# Required: bash 4+, git, jq. Optional: yq, docker, terraform.

set -eu
set -o pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT" || { echo '{"error":"cannot cd to root"}' && exit 1; }

# Size-capped constants (documented in references/dci-block.md § Size Budgets)
GIT_FILES_CAP=500
COMPOSE_BYTES_CAP=40960
K8S_RESOURCE_CAP=20
TERRAFORM_BYTES_CAP=81920

emit() { jq -n --argjson v "$1" --arg k "$2" '{($k): $v}'; }

# Git file inventory (capped at 500 paths, filtered by extension)
GIT_FILES_JSON="[]"
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  GIT_FILES_JSON=$(
    git ls-files '*.ts' '*.tsx' '*.js' '*.py' '*.go' '*.rs' '*.java' '*.rb' 2>/dev/null \
      | head -n "$GIT_FILES_CAP" \
      | jq -R -s 'split("\n") | map(select(length > 0))'
  )
fi

# Docker-compose config (capped at 40 KB)
COMPOSE_JSON='null'
if command -v docker >/dev/null 2>&1 && [ -f docker-compose.yml -o -f compose.yml ]; then
  RAW=$(docker compose config 2>/dev/null | head -c "$COMPOSE_BYTES_CAP" || true)
  if [ -n "$RAW" ]; then
    COMPOSE_JSON=$(jq -Rs . <<< "$RAW")
  fi
fi

# k8s manifests (capped at 20 resources across detected dirs)
K8S_JSON="[]"
K8S_DIRS=$(find . -maxdepth 3 -type d \( -name k8s -o -name kubernetes -o -name manifests \) 2>/dev/null | head -5)
if [ -n "$K8S_DIRS" ] && command -v yq >/dev/null 2>&1; then
  K8S_RAW=$(
    for d in $K8S_DIRS; do
      find "$d" -type f \( -name '*.yaml' -o -name '*.yml' \) | head -n "$K8S_RESOURCE_CAP"
    done \
      | xargs -I {} yq -o=json '{"file": "{}", "kind": .kind, "name": .metadata.name}' {} 2>/dev/null \
      | jq -s '.' 2>/dev/null
  )
  [ -n "$K8S_RAW" ] && K8S_JSON="$K8S_RAW"
fi

# Terraform state snapshot (capped at 80 KB)
TF_JSON='null'
if command -v terraform >/dev/null 2>&1 && [ -f terraform.tfstate ]; then
  TF_RAW=$(terraform show -json 2>/dev/null | head -c "$TERRAFORM_BYTES_CAP" || true)
  if [ -n "$TF_RAW" ]; then
    TF_JSON=$(jq -Rs . <<< "$TF_RAW")
  fi
fi

# Compose final JSON document
jq -n \
  --argjson git_files "$GIT_FILES_JSON" \
  --argjson compose "$COMPOSE_JSON" \
  --argjson k8s "$K8S_JSON" \
  --argjson tf "$TF_JSON" \
  --arg root "$ROOT" \
  '{
    root: $root,
    git_files: $git_files,
    git_files_count: ($git_files | length),
    docker_compose_config: $compose,
    k8s_resources: $k8s,
    terraform_state: $tf,
    truncated: false
  }'
