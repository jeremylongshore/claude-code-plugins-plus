#!/bin/bash

# Add missing plugins to marketplace.extended.json

set -e

echo "🔍 Finding missing plugins..."

# Get list of all plugins from filesystem
all_plugins=$(find plugins -name "plugin.json" -exec jq -r '.name' {} \; | sort)

# Get list of plugins in marketplace
marketplace_plugins=$(jq -r '.plugins[].name' .claude-plugin/marketplace.extended.json | sort)

# Find missing plugins
missing=$(comm -23 <(echo "$all_plugins") <(echo "$marketplace_plugins"))

if [ -z "$missing" ]; then
    echo "✅ No missing plugins found!"
    exit 0
fi

echo "📋 Missing plugins:"
echo "$missing"
echo ""

# Add each missing plugin
for plugin_name in $missing; do
    echo "Adding: $plugin_name"

    # Find the plugin.json file
    plugin_file=$(find plugins -name "plugin.json" -exec grep -l "\"name\": \"$plugin_name\"" {} \; | head -1)

    if [ -z "$plugin_file" ]; then
        echo "  ⚠️  Could not find plugin.json for $plugin_name"
        continue
    fi

    # Get the directory containing .claude-plugin
    plugin_dir=$(dirname $(dirname "$plugin_file"))
    source_path="./$(realpath --relative-to=. "$plugin_dir" 2>/dev/null || echo "$plugin_dir")"

    # Read plugin metadata
    version=$(jq -r '.version // "1.0.0"' "$plugin_file")
    description=$(jq -r '.description // ""' "$plugin_file")
    category=$(jq -r '.category // "other"' "$plugin_file")

    # Get keywords/tags
    keywords=$(jq -r 'if .keywords then .keywords elif .tags then .tags else [] end | join(",")' "$plugin_file")

    # Get author
    author_name=$(jq -r 'if .author then (if type == "string" then . else .name end) else "Claude Code Plugins" end' "$plugin_file")
    author_email=$(jq -r 'if .author and .author.email then .author.email else "" end' "$plugin_file")

    # Create new plugin entry
    new_entry=$(cat <<EOF
{
  "name": "$plugin_name",
  "source": "$source_path",
  "description": "$description",
  "version": "$version",
  "category": "$category",
  "keywords": [$(echo "$keywords" | sed 's/,/", "/g' | sed 's/^/"/' | sed 's/$/"/')],
  "author": {
    "name": "$author_name"
    $([ -n "$author_email" ] && echo ", \"email\": \"$author_email\"" || echo "")
  }
}
EOF
)

    # Add to marketplace.extended.json
    jq --argjson entry "$new_entry" '.plugins += [$entry]' .claude-plugin/marketplace.extended.json > .claude-plugin/marketplace.extended.json.tmp
    mv .claude-plugin/marketplace.extended.json.tmp .claude-plugin/marketplace.extended.json

    echo "  ✅ Added $plugin_name"
done

echo ""
echo "✅ Added $(echo "$missing" | wc -w) plugins to marketplace.extended.json"
echo ""
echo "🔄 Run 'node scripts/sync-marketplace.cjs' to sync CLI catalog"
