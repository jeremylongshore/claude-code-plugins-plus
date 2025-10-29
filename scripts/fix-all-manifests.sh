#!/bin/bash

# Fix all plugin.json manifests by removing invalid fields
# Valid fields: name, version, description, author, homepage, repository, license, keywords, commands, agents, hooks, mcpServers

set -e

echo "🔧 Fixing all plugin.json manifests..."
echo ""

# Counter for files fixed
FIXED=0
TOTAL=0

# Find all plugin.json files
find plugins -name "plugin.json" -type f | while read -r file; do
    TOTAL=$((TOTAL + 1))

    # Check if file has invalid keys
    if grep -q '"capabilities"\|"categories"\|"plugins"\|"documentation"\|"requirements"\|"pricing"\|"features"\|"components"' "$file"; then
        echo "Fixing: $file"

        # Create temp file with only valid fields
        jq 'del(.capabilities, .categories, .plugins, .documentation, .requirements, .pricing, .features, .components)' "$file" > "$file.tmp"

        # Replace original with cleaned version
        mv "$file.tmp" "$file"

        FIXED=$((FIXED + 1))
    fi
done

echo ""
echo "✅ Fixed $FIXED plugin manifests"
echo ""
echo "🔍 Validating all JSON files..."

# Validate all plugin.json files
find plugins -name "plugin.json" -type f | while read -r file; do
    if ! jq empty "$file" 2>/dev/null; then
        echo "❌ Invalid JSON: $file"
        exit 1
    fi
done

echo "✅ All plugin.json files are valid JSON"
echo ""
echo "📋 Summary of required fields:"
echo "  - Required: name"
echo "  - Optional: version, description, author, homepage, repository, license, keywords"
echo "  - Components: commands, agents, hooks, mcpServers"
echo ""
echo "🚀 Run 'pnpm run sync-marketplace' to update marketplace.json"
