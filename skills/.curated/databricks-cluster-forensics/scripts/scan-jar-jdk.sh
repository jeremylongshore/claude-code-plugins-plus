#!/usr/bin/env bash
# scan-jar-jdk.sh — detect the JDK bytecode target of cluster JARs so you can find
# the ones that risk breaking on DBR 15.1+ (bead w6qf / pain D04).
#
# DBR 15.1 removed JDK 11 and moved the runtime to JDK 17. JDK 17 can RUN older
# bytecode, but its strong module encapsulation (JPMS) and removed internal APIs
# break libraries built against JDK 8/11 internals (the classic
# InaccessibleObjectException / NoClassDefFoundError at runtime). Bytecode target
# is the cheap, deterministic SIGNAL: a JAR whose classes target JDK 8 (major 52)
# or 11 (major 55) predates JDK 17 and should be reviewed / rebuilt before the
# upgrade. This script reads each JAR's class-file major version — via `javap`
# when present, else by reading the class-file bytes directly — and flags the
# pre-17 ones.
#
# Class-file major version -> JDK:  52=8  53=9  54=10  55=11  56=12 ... 61=17  65=21
#
# Usage:  scan-jar-jdk.sh [--json] [--target-jdk N] FILE_OR_DIR [FILE_OR_DIR ...]
#   Recurses directories for *.jar. --target-jdk defaults to 17 (the DBR 15.1 floor):
#   any JAR whose max class targets < that is flagged REVIEW.
# Exit: 0 ok (findings are data) · 2 bad usage · 3 required tool (unzip) missing.
set -euo pipefail

JSON=0
TARGET_JDK=17
declare -a INPUTS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --json) JSON=1; shift ;;
    --target-jdk) TARGET_JDK="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    -*) echo "unknown arg: $1" >&2; exit 2 ;;
    *) INPUTS+=("$1"); shift ;;
  esac
done

[ "${#INPUTS[@]}" -gt 0 ] || { echo "error: pass at least one .jar file or directory" >&2; exit 2; }
command -v unzip >/dev/null 2>&1 || { echo "error: 'unzip' is required" >&2; exit 3; }

HAVE_JAVAP=0
command -v javap >/dev/null 2>&1 && HAVE_JAVAP=1

# Map a class-file major version to a human JDK label.
jdk_for_major() {
  case "$1" in
    52) echo "8" ;;  53) echo "9" ;;   54) echo "10" ;; 55) echo "11" ;;
    56) echo "12" ;; 57) echo "13" ;;  58) echo "14" ;; 59) echo "15" ;;
    60) echo "16" ;; 61) echo "17" ;;  62) echo "18" ;; 63) echo "19" ;;
    64) echo "20" ;; 65) echo "21" ;;  *) echo "?" ;;
  esac
}

# Read the class-file major version (byte 7, 0-indexed 6) from bytes on stdin.
major_from_bytes() {
  # bytes: CA FE BA BE <minor hi> <minor lo> <major hi> <major lo>
  od -An -tu1 -N8 | awk '{print $8}'
}

# Return the MAX class-file major version across a sample of classes in a JAR.
max_major_in_jar() {
  local jar="$1" max=0 maj classes cls
  # Sample up to 40 .class files (skip module-info / multi-release stubs first).
  classes="$(unzip -Z1 "$jar" 2>/dev/null | grep '\.class$' | grep -v 'module-info\.class$' | head -40 || true)"
  [ -n "$classes" ] || return 0
  while IFS= read -r cls; do
    [ -n "$cls" ] || continue
    if [ "$HAVE_JAVAP" -eq 1 ]; then
      maj="$(unzip -p "$jar" "$cls" 2>/dev/null | javap -v - 2>/dev/null | awk -F': ' '/major version/{print $2; exit}')"
    fi
    if [ -z "${maj:-}" ]; then
      maj="$(unzip -p "$jar" "$cls" 2>/dev/null | major_from_bytes || true)"
    fi
    if [ -n "${maj:-}" ] && [ "$maj" -gt "$max" ] 2>/dev/null; then max="$maj"; fi
    maj=""
  done <<EOF
$classes
EOF
  echo "$max"
}

# Collect jar paths from the inputs.
declare -a JARS=()
for in in "${INPUTS[@]}"; do
  if [ -d "$in" ]; then
    while IFS= read -r j; do JARS+=("$j"); done < <(find "$in" -type f -name '*.jar')
  elif [ -f "$in" ]; then
    JARS+=("$in")
  else
    echo "note: skipping non-existent path: $in" >&2
  fi
done

# The class-file major version that corresponds to the target JDK floor.
target_major=$((TARGET_JDK + 44))

n_review=0 n_ok=0 first=1
[ "$JSON" -eq 1 ] && printf '['
for jar in "${JARS[@]}"; do
  major="$(max_major_in_jar "$jar" || echo 0)"
  major="${major:-0}"
  if [ "$major" -eq 0 ] 2>/dev/null; then
    jdk="?"; verdict="UNKNOWN"
  else
    jdk="$(jdk_for_major "$major")"
    if [ "$major" -lt "$target_major" ] 2>/dev/null; then verdict="REVIEW"; n_review=$((n_review+1)); else verdict="OK"; n_ok=$((n_ok+1)); fi
  fi
  if [ "$JSON" -eq 1 ]; then
    [ "$first" -eq 0 ] && printf ','
    first=0
    printf '{"jar":"%s","major":%s,"jdk":"%s","verdict":"%s"}' "$jar" "${major:-0}" "$jdk" "$verdict"
  else
    printf '  %-8s JDK %-3s (major %s)  %s\n' "$verdict" "$jdk" "$major" "$jar"
  fi
done
if [ "$JSON" -eq 1 ]; then
  printf ']\n'
else
  echo "scanned ${#JARS[@]} jar(s): $n_review to REVIEW for JDK ${TARGET_JDK} (built for an older JDK), $n_ok OK"
fi
