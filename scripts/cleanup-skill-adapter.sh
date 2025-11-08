#!/bin/bash
# Clean up legacy skill-adapter directories and modernize structure
# Author: Claude Code Quality Team
# Date: 2025-11-08

set -e

PLUGINS_DIR="/home/user/claude-code-plugins-plus/plugins"
BACKUP_DIR="/home/user/claude-code-plugins-plus/backups/skill-structure-cleanup-$(date +%Y%m%d-%H%M%S)"

echo "🧹 Claude Skills Structure Modernization"
echo "========================================"
echo ""

# Create backup
echo "📦 Creating backup at $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
cp -r "$PLUGINS_DIR" "$BACKUP_DIR/"
echo "✅ Backup created"
echo ""

# Find all skill-adapter directories
ADAPTER_DIRS=$(find "$PLUGINS_DIR" -type d -name "skill-adapter")
ADAPTER_COUNT=$(echo "$ADAPTER_DIRS" | grep -c "skill-adapter" || echo "0")

echo "🔍 Found $ADAPTER_COUNT legacy skill-adapter directories"
echo ""

if [ "$ADAPTER_COUNT" -eq "0" ]; then
    echo "✅ No cleanup needed - already using modern structure!"
    exit 0
fi

# Statistics
REMOVED=0
MIGRATED=0
ERRORS=0

# Process each skill-adapter directory
while IFS= read -r ADAPTER_DIR; do
    if [ -z "$ADAPTER_DIR" ]; then
        continue
    fi

    SKILLS_DIR=$(dirname "$ADAPTER_DIR")
    PLUGIN_DIR=$(dirname "$SKILLS_DIR")

    echo "📂 Processing: $(basename "$PLUGIN_DIR")"

    # Check if there's a modern skill directory
    MODERN_SKILLS=$(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d ! -name "skill-adapter" | head -1)

    if [ -n "$MODERN_SKILLS" ]; then
        # Check if skill-adapter has any real content
        CONTENT_COUNT=$(find "$ADAPTER_DIR" -type f | wc -l)

        if [ "$CONTENT_COUNT" -eq "0" ]; then
            # Empty - safe to remove
            echo "   ✓ Removing empty skill-adapter (modern structure exists)"
            rm -rf "$ADAPTER_DIR"
            REMOVED=$((REMOVED + 1))
        else
            # Has content - needs migration
            echo "   ⚠ Has content - needs manual review: $ADAPTER_DIR"
            MIGRATED=$((MIGRATED + 1))
        fi
    else
        echo "   ⚠ No modern skill found - keeping skill-adapter"
        ERRORS=$((ERRORS + 1))
    fi
done <<< "$ADAPTER_DIRS"

echo ""
echo "========================================"
echo "📊 Summary:"
echo "   ✅ Removed: $REMOVED empty skill-adapter directories"
echo "   ⚠️  Needs review: $MIGRATED directories with content"
echo "   ❌ Errors: $ERRORS directories without modern replacement"
echo "========================================"
echo ""
echo "✅ Cleanup complete!"
echo "Backup location: $BACKUP_DIR"
