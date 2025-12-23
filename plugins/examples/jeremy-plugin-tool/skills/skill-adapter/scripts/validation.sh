#!/bin/bash
# Skill validation helper
# Validates skill activation and functionality

set -e

echo "🔍 Validating skill..."

# Check if SKILL.md exists
if [ ! -f "../SKILL.md" ]; then
    echo "❌ Error: SKILL.md not found"
    exit 1
fi

# Validate frontmatter
if ! grep -q "^---$" "../SKILL.md"; then
    echo "❌ Error: No frontmatter found"
    exit 1
fi

# Check required fields
if ! grep -q "^name:" "../SKILL.md"; then
    echo "❌ Error: Missing 'name' field"
    exit 1
fi

if ! grep -q "^description:" "../SKILL.md"; then
    echo "❌ Error: Missing 'description' field"
    exit 1
fi

echo "✅ Skill validation passed"
