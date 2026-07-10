#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PACKAGE_JSON="$ROOT/package.json"
PLUGIN_JSON="$ROOT/.claude-plugin/plugin.json"
CODEX_PLUGIN_JSON="$ROOT/.codex-plugin/plugin.json"
MARKETPLACE_JSON="$ROOT/.claude-plugin/marketplace.json"
README_MD="$ROOT/README.md"
SKILL_VERSION="$ROOT/skills/hyperflow/VERSION"

# Validate argument
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <new-version>"
  echo "Example: $0 1.2.0"
  exit 1
fi

NEW_VERSION="$1"

if [[ ! "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: version must be semver format X.Y.Z (got: $NEW_VERSION)"
  exit 1
fi

DOCS_HTML=("$ROOT/docs/index.html" "$ROOT/docs/installation.html" "$ROOT/docs/orchestration.html" "$ROOT/docs/404.html")
SITEMAP_XML="$ROOT/docs/sitemap.xml"

# Verify all files exist
for FILE in "$PACKAGE_JSON" "$PLUGIN_JSON" "$CODEX_PLUGIN_JSON" "$MARKETPLACE_JSON" "$README_MD" "${DOCS_HTML[@]}" "$SITEMAP_XML"; do
  if [[ ! -f "$FILE" ]]; then
    echo "Error: file not found: $FILE"
    exit 1
  fi
done

# Detect sed in-place flag (BSD vs GNU)
if sed --version >/dev/null 2>&1; then
  SED_INPLACE=(-i)
else
  SED_INPLACE=(-i '')
fi

# Update package.json
sed "${SED_INPLACE[@]}" 's/"version": "[^"]*"/"version": "'"$NEW_VERSION"'"/' "$PACKAGE_JSON"
echo "Updated $PACKAGE_JSON"

# Update plugin.json
sed "${SED_INPLACE[@]}" 's/"version": "[^"]*"/"version": "'"$NEW_VERSION"'"/' "$PLUGIN_JSON"
echo "Updated $PLUGIN_JSON"

# Update Codex plugin.json
sed "${SED_INPLACE[@]}" 's/"version": "[^"]*"/"version": "'"$NEW_VERSION"'"/' "$CODEX_PLUGIN_JSON"
echo "Updated $CODEX_PLUGIN_JSON"

# Update marketplace.json (both occurrences)
sed "${SED_INPLACE[@]}" 's/"version": "[^"]*"/"version": "'"$NEW_VERSION"'"/g' "$MARKETPLACE_JSON"
echo "Updated $MARKETPLACE_JSON (2 occurrences)"

# Update README.md version badge
sed "${SED_INPLACE[@]}" 's/<code>v[^<]*<\/code>/<code>v'"$NEW_VERSION"'<\/code>/' "$README_MD"
sed "${SED_INPLACE[@]}" 's|badge/version-v[^-]*-blueviolet|badge/version-v'"$NEW_VERSION"'-blueviolet|' "$README_MD"
sed "${SED_INPLACE[@]}" 's/alt="version v[^"]*"/alt="version v'"$NEW_VERSION"'"/' "$README_MD"
echo "Updated $README_MD"

# Update skill VERSION file
echo "$NEW_VERSION" > "$SKILL_VERSION"
echo "Updated $SKILL_VERSION"

# Update docs site — footer versions, index JSON-LD, sitemap lastmod
for HTML in "${DOCS_HTML[@]}"; do
  sed "${SED_INPLACE[@]}" 's/footer-version">v[0-9.]*</footer-version">v'"$NEW_VERSION"'</' "$HTML"
done
sed "${SED_INPLACE[@]}" 's/"softwareVersion": "[0-9.]*"/"softwareVersion": "'"$NEW_VERSION"'"/' "$ROOT/docs/index.html"
TODAY="$(date +%Y-%m-%d)"
sed "${SED_INPLACE[@]}" 's|<lastmod>[0-9-]*</lastmod>|<lastmod>'"$TODAY"'</lastmod>|g' "$SITEMAP_XML"
echo "Updated docs site (4 footers, JSON-LD, sitemap lastmod)"

echo "Version bumped to $NEW_VERSION (11 files)"
