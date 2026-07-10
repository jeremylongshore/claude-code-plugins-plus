#!/usr/bin/env bash
# run-jrig-eval.sh — run a j-rig behavioral eval and record the verdict into
# the forge_proofs table (issue #935, the eval→forge_proofs write path).
#
# Flow:
#   1. Decrypt DEEPSEEK_API_KEY via SOPS, in-memory only (never written to
#      disk; the only disk artifacts live under /dev/shm and are removed by
#      the cleanup trap).
#   2. Run `pnpm exec j-rig eval` against a SCRATCH SQLite DB under /dev/shm.
#      j-rig writes its own run tables into whatever --db it is given, so it
#      must NEVER be pointed at the tracked freshie/inventory.sqlite — the
#      guard below refuses any scratch path containing 'freshie'.
#   3. Feed the --json result to scripts/record-jrig-proofs.mjs, which
#      upserts the tier3-jrig row into the REAL inventory DB (passed
#      separately via --inventory-db).
#
# Usage:
#   scripts/run-jrig-eval.sh --skill-dir <dir> --plugin <catalog-name> \
#     --inventory-db freshie/inventory.sqlite \
#     [--run-id <int>] [--models <csv>] [--provider <name>] [--spec <path>] \
#     [--scratch-db <path-under-/dev/shm>] [--stub]
#
# Defaults: --provider deepseek, --models deepseek-v4-flash,
#           --run-id $(date +%s), scratch DB under /dev/shm.
#
# --stub runs the j-rig stub provider (J_RIG_ALLOW_STUB=1, no API key, no
# spend) and passes --allow-stub to the recorder. Stub results are NOT ground
# truth — only use against a scratch copy of the inventory DB.
#
# Env overrides:
#   JRIG_BIN       — j-rig binary to use instead of `pnpm exec j-rig`
#   JRIG_SOPS_ENV  — SOPS dotenv file carrying DEEPSEEK_API_KEY

set -euo pipefail

die() {
  echo "[run-jrig-eval] ERROR: $*" >&2
  exit 1
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

skill_dir=""
plugin=""
inventory_db=""
run_id="$(date +%s)"
models="deepseek-v4-flash"
provider="deepseek"
spec=""
scratch_db=""
stub=0

while [ $# -gt 0 ]; do
  case "$1" in
    --skill-dir)    skill_dir="${2:?--skill-dir needs a value}"; shift 2 ;;
    --plugin)       plugin="${2:?--plugin needs a value}"; shift 2 ;;
    --inventory-db) inventory_db="${2:?--inventory-db needs a value}"; shift 2 ;;
    --run-id)       run_id="${2:?--run-id needs a value}"; shift 2 ;;
    --models)       models="${2:?--models needs a value}"; shift 2 ;;
    --provider)     provider="${2:?--provider needs a value}"; shift 2 ;;
    --spec)         spec="${2:?--spec needs a value}"; shift 2 ;;
    --scratch-db)   scratch_db="${2:?--scratch-db needs a value}"; shift 2 ;;
    --stub)         stub=1; shift ;;
    *)              die "Unknown argument: $1" ;;
  esac
done

[ -n "$skill_dir" ] || die "--skill-dir is required"
[ -n "$plugin" ] || die "--plugin is required"
[ -n "$inventory_db" ] || die "--inventory-db is required"
[ -d "$skill_dir" ] || die "--skill-dir does not exist: $skill_dir"
[ -f "$inventory_db" ] || die "--inventory-db does not exist: $inventory_db"
case "$run_id" in
  ''|*[!0-9]*) die "--run-id must be a non-negative integer (got: $run_id)" ;;
esac

# Scratch workspace: everything transient lives under /dev/shm (tmpfs — no
# plaintext or eval artifacts ever touch persistent disk) and dies with the
# trap below.
scratch_dir="$(mktemp -d /dev/shm/jrig-eval.XXXXXX)"
cleanup() {
  unset DEEPSEEK_API_KEY || true
  rm -rf "$scratch_dir"
  # sqlite WAL/SHM siblings of a user-supplied --scratch-db live next to it.
  if [ -n "$scratch_db" ]; then
    rm -f "$scratch_db" "$scratch_db-wal" "$scratch_db-shm"
  fi
}
trap cleanup EXIT INT TERM

if [ -z "$scratch_db" ]; then
  scratch_db="$scratch_dir/jrig-scratch.db"
fi

# --- GUARDS: j-rig must never write into the tracked inventory DB ----------
case "$scratch_db" in
  *freshie*) die "refusing scratch DB path containing 'freshie' ($scratch_db) — j-rig writes its own run tables and must never touch the tracked inventory DB. Use a /dev/shm scratch path." ;;
  /dev/shm/*) : ;;
  *) die "scratch DB must live under /dev/shm (got: $scratch_db)" ;;
esac
if [ "$scratch_db" = "$inventory_db" ]; then
  die "scratch DB and inventory DB must be different files"
fi
# ----------------------------------------------------------------------------

result_json="$scratch_dir/result.json"
jrig_bin="${JRIG_BIN:-}"

run_jrig() {
  if [ -n "$jrig_bin" ]; then
    "$jrig_bin" "$@"
  else
    pnpm exec j-rig "$@"
  fi
}

jrig_args=(eval "$skill_dir" --models "$models" --db "$scratch_db" --json)
if [ -n "$spec" ]; then
  jrig_args+=(--spec "$spec")
fi

if [ "$stub" -eq 1 ]; then
  echo "[run-jrig-eval] STUB MODE — no API key, no spend, results are NOT ground truth" >&2
  export J_RIG_ALLOW_STUB=1
  jrig_args+=(--provider stub)
else
  # Decrypt the DeepSeek key via SOPS into the environment only — the
  # anchored sed keeps comment/blank lines out and never writes plaintext to
  # disk (per the SOPS standard in the estate CLAUDE.md).
  sops_env="${JRIG_SOPS_ENV:-$HOME/000-projects/intent-eval-platform/intent-eval-lab/.env.sops}"
  [ -f "$sops_env" ] || die "SOPS env file not found: $sops_env"
  DEEPSEEK_API_KEY="$(sops -d --input-type dotenv --output-type dotenv "$sops_env" | sed -nE 's/^DEEPSEEK_API_KEY=(.*)$/\1/p' | head -n1)"
  [ -n "$DEEPSEEK_API_KEY" ] || die "DEEPSEEK_API_KEY not found in $sops_env"
  export DEEPSEEK_API_KEY
  jrig_args+=(--provider "$provider")
fi

echo "[run-jrig-eval] j-rig eval: skill=$skill_dir models=$models provider=$([ "$stub" -eq 1 ] && echo stub || echo "$provider") scratch=$scratch_db" >&2
run_jrig "${jrig_args[@]}" > "$result_json" || die "j-rig eval failed (see output above)"

[ -s "$result_json" ] || die "j-rig eval produced no JSON output"

record_args=(--db "$inventory_db" --plugin "$plugin" --run-id "$run_id" --result "$result_json")
if [ "$stub" -eq 1 ]; then
  record_args+=(--allow-stub)
fi

node "$repo_root/scripts/record-jrig-proofs.mjs" "${record_args[@]}"

echo "[run-jrig-eval] Done — tier3-jrig row recorded for '$plugin' (run_id=$run_id) in $inventory_db" >&2
