#!/usr/bin/env bash
# Install the reviewed marketplace response-header fragment on the Caddy VPS.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CHECK_ONLY=0
if [[ ${1:-} == "--check" ]]; then
  CHECK_ONLY=1
  shift
fi
SOURCE=${1:-"$SCRIPT_DIR/tonsofskills-security-headers.caddy"}
TARGET=${2:-/etc/caddy/tonsofskills-security-headers.caddy}
MAIN_CONFIG=${3:-/etc/caddy/Caddyfile}
SITE_LABEL=${4:-'tonsofskills.com, www.tonsofskills.com {'}
IMPORT_LINE="    import $TARGET"

if [[ $CHECK_ONLY -eq 0 && ${EUID} -ne 0 ]]; then
  echo "install-security-headers: must run as root" >&2
  exit 77
fi
for path in "$SOURCE" "$MAIN_CONFIG"; do
  [[ -f "$path" ]] || { echo "install-security-headers: missing file: $path" >&2; exit 66; }
done

TMP_DIR=$(mktemp -d)
TARGET_BACKUP="${TARGET}.bak.$(date -u +%Y%m%dT%H%M%SZ)"
MAIN_BACKUP="${MAIN_CONFIG}.bak.csp.$(date -u +%Y%m%dT%H%M%SZ)"
INSTALLED=0
TARGET_EXISTED=0
[[ -f $TARGET ]] && TARGET_EXISTED=1
cleanup() { rm -rf -- "$TMP_DIR"; }
rollback_on_error() {
  local status=$?
  set +e
  if [[ $INSTALLED -eq 1 ]]; then
    if [[ $TARGET_EXISTED -eq 1 && -f $TARGET_BACKUP ]]; then
      cp --preserve=mode,ownership,timestamps -- "$TARGET_BACKUP" "$TARGET"
    else
      rm -f -- "$TARGET"
    fi
    cp --preserve=mode,ownership,timestamps -- "$MAIN_BACKUP" "$MAIN_CONFIG"
    systemctl reload caddy
    echo "install-security-headers: rolled back" >&2
  fi
  cleanup
  exit "$status"
}
trap cleanup EXIT
trap rollback_on_error ERR

python3 - "$MAIN_CONFIG" "$TMP_DIR/Caddyfile" "$SITE_LABEL" "$IMPORT_LINE" <<'PY'
import sys
from pathlib import Path

source, output, site_label, import_line = sys.argv[1:]
lines = Path(source).read_text(encoding="utf-8").splitlines()
starts = [index for index, line in enumerate(lines) if line.strip() == site_label]
if len(starts) != 1:
    raise SystemExit(f"expected one site block, found {len(starts)}: {site_label!r}")

start = starts[0]
depth = 0
end = None
for index in range(start, len(lines)):
    code = lines[index].split("#", 1)[0]
    depth += code.count("{") - code.count("}")
    if depth == 0:
        end = index
        break
if end is None:
    raise SystemExit(f"unterminated site block: {site_label!r}")

matches = [index for index in range(start + 1, end) if lines[index].strip() == import_line.strip()]
if len(matches) > 1:
    raise SystemExit(f"duplicate CSP import in site block: {import_line!r}")
if not matches:
    anchors = [
        index
        for index in range(start + 1, end)
        if lines[index].strip() == "import security-headers"
    ]
    if len(anchors) != 1:
        raise SystemExit(
            f"expected one security-header import in site block, found {len(anchors)}"
        )
    lines.insert(anchors[0] + 1, import_line)

Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

cp -- "$SOURCE" "$TMP_DIR/fragment.caddy"
sed "s|$(printf '%s' "$TARGET" | sed 's/[&/]/\\&/g')|$TMP_DIR/fragment.caddy|" \
  "$TMP_DIR/Caddyfile" > "$TMP_DIR/Caddyfile.candidate"
caddy adapt --config "$TMP_DIR/Caddyfile.candidate" >/dev/null

if [[ $CHECK_ONLY -eq 1 ]]; then
  echo "install-security-headers: candidate valid; sha256=$(sha256sum "$SOURCE" | awk '{print $1}')"
  exit 0
fi

[[ -f $TARGET ]] && cp --preserve=mode,ownership,timestamps -- "$TARGET" "$TARGET_BACKUP"
cp --preserve=mode,ownership,timestamps -- "$MAIN_CONFIG" "$MAIN_BACKUP"
INSTALLED=1
install -o root -g root -m 0644 "$SOURCE" "$TARGET"
install -o root -g root -m 0644 "$TMP_DIR/Caddyfile" "$MAIN_CONFIG"
sudo -n -u caddy caddy validate --config "$MAIN_CONFIG" >/dev/null
systemctl reload caddy
INSTALLED=0
trap - ERR

echo "install-security-headers: installed=$(sha256sum "$TARGET" | awk '{print $1}') main-backup=$MAIN_BACKUP target-backup=$TARGET_BACKUP"
