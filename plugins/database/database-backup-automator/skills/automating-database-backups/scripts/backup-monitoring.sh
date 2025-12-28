#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <backup-dir> [max_age_minutes]" >&2
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

backup_dir="${1:-}"
max_age_minutes="${2:-1440}"

if [[ -z "$backup_dir" ]]; then
  usage
  exit 2
fi

if [[ ! -d "$backup_dir" ]]; then
  echo "ERROR: backup dir not found: $backup_dir" >&2
  exit 2
fi

latest="$(find "$backup_dir" -type f -maxdepth 1 -print0 | xargs -0 ls -1t 2>/dev/null | head -n 1 || true)"
if [[ -z "$latest" ]]; then
  echo "ERROR: no backup files found in: $backup_dir" >&2
  exit 1
fi

age_minutes=$(( ( $(date +%s) - $(stat -c %Y "$latest") ) / 60 ))
echo "Latest backup: $latest"
echo "Age (minutes): $age_minutes"

if (( age_minutes > max_age_minutes )); then
  echo "ERROR: latest backup is older than max_age_minutes=$max_age_minutes" >&2
  exit 1
fi

echo "OK: backup freshness within threshold."

