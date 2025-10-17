#!/bin/bash

echo "Fixing plugin manifests by removing invalid fields..."

# Find all plugin.json files with invalid fields
plugins=$(find /home/jeremy/000-projects/claude-code-plugins/plugins -name "plugin.json" -exec grep -l '"category":\|"enhances":\|"requires":' {} \; 2>/dev/null)

count=0
for plugin in $plugins; do
    echo "Fixing: $plugin"
    # Remove category, enhances, and requires fields
    jq 'del(.category, .enhances, .requires)' "$plugin" > "$plugin.tmp" && mv "$plugin.tmp" "$plugin"
    count=$((count + 1))
done

echo "✅ Fixed $count plugin manifests"