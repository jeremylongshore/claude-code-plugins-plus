#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <iac-dir> [tool]" >&2
  echo "tool: terraform|pulumi|kubernetes (default: terraform)" >&2
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

iac_dir="${1:-}"
tool="${2:-terraform}"

if [[ -z "$iac_dir" ]]; then
  usage
  exit 2
fi

if [[ ! -d "$iac_dir" ]]; then
  echo "ERROR: IaC dir not found: $iac_dir" >&2
  exit 2
fi

case "$tool" in
  terraform)
    (cd "$iac_dir" && terraform init -input=false -no-color >/dev/null)
    (cd "$iac_dir" && terraform plan -detailed-exitcode -no-color)
    ;;
  pulumi)
    (cd "$iac_dir" && pulumi preview --diff)
    ;;
  kubernetes)
    echo "Kubernetes drift checks are environment-specific; run kubectl diff against desired manifests." >&2
    exit 1
    ;;
  *)
    echo "ERROR: unknown tool: $tool" >&2
    usage
    exit 2
    ;;
esac

