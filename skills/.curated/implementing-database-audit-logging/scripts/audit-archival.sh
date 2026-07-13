#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <audit-log-dir> <archive-dir> [keep_count]" >&2
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

audit_log_dir="${1:-}"
archive_dir="${2:-}"
keep_count="${3:-10}"

if [[ -z "$audit_log_dir" || -z "$archive_dir" ]]; then
  usage
  exit 2
fi

if [[ ! -d "$audit_log_dir" ]]; then
  echo "ERROR: audit log dir not found: $audit_log_dir" >&2
  exit 2
fi

mkdir -p "$archive_dir"

ts="$(date -u +%Y%m%dT%H%M%SZ)"
archive_path="$archive_dir/audit-logs-$ts.tar.gz"

tar -C "$audit_log_dir" -czf "$archive_path" .
echo "Archived audit logs to: $archive_path"

ls -1t "$archive_dir"/audit-logs-*.tar.gz 2>/dev/null | tail -n +"$((keep_count + 1))" | xargs -r rm -f
echo "Retention enforced (keep_count=$keep_count)"

