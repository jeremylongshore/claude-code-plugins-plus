#!/usr/bin/env bash
# arch-check.sh — Wall 7 architecture-constraint dispatcher.
#
# Detects the primary language of the repo, invokes the appropriate
# dependency / architecture checker with the project's rule pack, and
# normalizes the exit code.
#
# Exit codes:
#   0 — all rules pass
#   1 — rule violations detected
#   2 — no tool installed / no config / unsupported language
#
# Usage:
#   bash arch-check.sh              # run from repo root
#   bash arch-check.sh --json       # emit JSON summary to stdout
#   bash arch-check.sh --help

set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
JSON_OUT=0
REPORT_DIR="${ROOT}/reports/arch"

usage() {
  sed -n '2,20p' "$0"
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUT=1 ;;
    --help|-h) usage ;;
    *) echo "arch-check: unknown flag $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$REPORT_DIR"

emit_result() {
  local tool="$1" status="$2" violations="$3" log="$4"
  if [[ "$JSON_OUT" -eq 1 ]]; then
    printf '{"tool":"%s","status":"%s","violations":%s,"log":"%s"}\n' \
      "$tool" "$status" "$violations" "$log"
  else
    echo "arch-check: tool=$tool status=$status violations=$violations"
    echo "           log=$log"
  fi
}

# 1. dependency-cruiser (JS/TS)
if [[ -f "${ROOT}/.dependency-cruiser.js" || -f "${ROOT}/.dependency-cruiser.cjs" ]]; then
  LOG="${REPORT_DIR}/dep-cruiser.log"
  if command -v npx >/dev/null 2>&1; then
    if npx --no-install dependency-cruiser --validate --output-type err "${ROOT}/src" > "$LOG" 2>&1; then
      emit_result dependency-cruiser pass 0 "$LOG"
      exit 0
    else
      VIOL=$(grep -c "error" "$LOG" || echo 0)
      emit_result dependency-cruiser fail "$VIOL" "$LOG"
      exit 1
    fi
  else
    emit_result dependency-cruiser missing-tool 0 "$LOG"
    exit 2
  fi
fi

# 2. import-linter (Python)
if [[ -f "${ROOT}/.importlinter" ]] || grep -q "^\[importlinter\]" "${ROOT}/pyproject.toml" 2>/dev/null; then
  LOG="${REPORT_DIR}/import-linter.log"
  if command -v lint-imports >/dev/null 2>&1; then
    if (cd "$ROOT" && lint-imports) > "$LOG" 2>&1; then
      emit_result import-linter pass 0 "$LOG"
      exit 0
    else
      VIOL=$(grep -c "BROKEN" "$LOG" || echo 0)
      emit_result import-linter fail "$VIOL" "$LOG"
      exit 1
    fi
  else
    emit_result import-linter missing-tool 0 "$LOG"
    exit 2
  fi
fi

# 3. deptrac (PHP)
if [[ -f "${ROOT}/deptrac.yaml" ]]; then
  LOG="${REPORT_DIR}/deptrac.log"
  if [[ -x "${ROOT}/vendor/bin/deptrac" ]]; then
    if (cd "$ROOT" && vendor/bin/deptrac analyse --no-progress) > "$LOG" 2>&1; then
      emit_result deptrac pass 0 "$LOG"
      exit 0
    else
      VIOL=$(grep -Ec "violation" "$LOG" || echo 0)
      emit_result deptrac fail "$VIOL" "$LOG"
      exit 1
    fi
  else
    emit_result deptrac missing-tool 0 "$LOG"
    exit 2
  fi
fi

# 4. arch-go
if [[ -f "${ROOT}/arch-go.yml" ]]; then
  LOG="${REPORT_DIR}/arch-go.log"
  if command -v arch-go >/dev/null 2>&1; then
    if (cd "$ROOT" && arch-go) > "$LOG" 2>&1; then
      emit_result arch-go pass 0 "$LOG"
      exit 0
    else
      VIOL=$(grep -c "Violation" "$LOG" || echo 0)
      emit_result arch-go fail "$VIOL" "$LOG"
      exit 1
    fi
  else
    emit_result arch-go missing-tool 0 "$LOG"
    exit 2
  fi
fi

# 5. ArchUnit (Java/Kotlin) — run via build tool
if [[ -f "${ROOT}/build.gradle" || -f "${ROOT}/build.gradle.kts" ]] && \
   grep -rq "com.tngtech.archunit" "${ROOT}" --include="*.gradle*" 2>/dev/null; then
  LOG="${REPORT_DIR}/archunit.log"
  if [[ -x "${ROOT}/gradlew" ]]; then
    if (cd "$ROOT" && ./gradlew test --tests '*ArchitectureTest*' --tests '*ArchTest*') > "$LOG" 2>&1; then
      emit_result archunit pass 0 "$LOG"
      exit 0
    else
      VIOL=$(grep -Ec "violated|FAILED" "$LOG" || echo 0)
      emit_result archunit fail "$VIOL" "$LOG"
      exit 1
    fi
  else
    emit_result archunit missing-tool 0 "$LOG"
    exit 2
  fi
fi

# No tool / config found
emit_result none not-configured 0 "$REPORT_DIR/none.log"
exit 2
