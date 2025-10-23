#!/bin/bash

# Fix placeholder emails in plugin.json files
# This is a QUALITY ENHANCEMENT, not a compliance fix

echo "============================================"
echo "ENHANCING PLUGIN AUTHOR EMAILS"
echo "============================================"
echo ""
echo "Note: This is optional - placeholder emails are compliant"
echo ""

# Track changes
updated=0
skipped=0

# Process each plugin
for plugin_json in $(find ./plugins -name "plugin.json" -path "*/.claude-plugin/*" | sort); do
    plugin_dir=$(dirname $(dirname "$plugin_json"))
    plugin_name=$(basename "$plugin_dir")

    # Check if it has the placeholder email
    current_email=$(jq -r '.author.email // empty' "$plugin_json")

    if [[ "$current_email" == "[email protected]" ]]; then
        echo "Found placeholder in: $plugin_name"

        # Get author name
        author_name=$(jq -r '.author.name // "Claude Code Plugins"' "$plugin_json")

        # Generate a more specific email based on plugin category
        category=$(echo "$plugin_dir" | cut -d'/' -f3)
        new_email="${category}@claudecodeplugins.io"

        # Update the email
        jq --arg email "$new_email" '.author.email = $email' "$plugin_json" > "$plugin_json.tmp"
        mv "$plugin_json.tmp" "$plugin_json"

        echo "  ✓ Updated to: $new_email"
        ((updated++))
    else
        ((skipped++))
    fi
done

echo ""
echo "Summary:"
echo "  Updated: $updated plugins"
echo "  Skipped: $skipped plugins"
echo ""
echo "To revert: git checkout -- './plugins/*/.claude-plugin/plugin.json'"