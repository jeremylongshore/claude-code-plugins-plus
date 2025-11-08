#!/bin/bash
# Enhance all skills with professional supporting file structure
# Adds scripts/, references/, and assets/ with useful templates
# Author: Claude Code Quality Team
# Date: 2025-11-08

set -e

PLUGINS_DIR="/home/user/claude-code-plugins-plus/plugins"

echo "🚀 Claude Skills Professional Enhancement"
echo "=========================================="
echo ""
echo "Adding supporting files to all 175 skills..."
echo ""

ENHANCED=0
SKIPPED=0

# Find all SKILL.md files in modern locations
while IFS= read -r SKILL_FILE; do
    SKILL_DIR=$(dirname "$SKILL_FILE")
    SKILL_NAME=$(basename "$SKILL_DIR")
    PLUGIN_NAME=$(basename "$(dirname "$(dirname "$SKILL_DIR")")")

    # Skip if already has supporting directories
    if [ -d "$SKILL_DIR/scripts" ] && [ -d "$SKILL_DIR/references" ] && [ -d "$SKILL_DIR/assets" ]; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "📦 Enhancing: $PLUGIN_NAME → $SKILL_NAME"

    # Create supporting directories
    mkdir -p "$SKILL_DIR/scripts"
    mkdir -p "$SKILL_DIR/references"
    mkdir -p "$SKILL_DIR/assets"

    # Add scripts README
    cat > "$SKILL_DIR/scripts/README.md" << 'EOF'
# Skill Scripts

This directory contains optional helper scripts that support this skill's functionality.

## Purpose

Scripts here can be:
- Referenced by the skill for automation
- Used as examples for users
- Executed during skill activation

## Guidelines

- All scripts should be well-documented
- Include usage examples in comments
- Make scripts executable (`chmod +x`)
- Use `#!/bin/bash` or `#!/usr/bin/env python3` shebangs

## Adding Scripts

1. Create script file (e.g., `analyze.sh`, `process.py`)
2. Add documentation header
3. Make executable: `chmod +x script-name.sh`
4. Test thoroughly before committing
EOF

    # Add references README
    cat > "$SKILL_DIR/references/README.md" << 'EOF'
# Skill References

This directory contains reference materials that enhance this skill's capabilities.

## Purpose

References can include:
- Code examples
- Style guides
- Best practices documentation
- Template files
- Configuration examples

## Guidelines

- Keep references concise and actionable
- Use markdown for documentation
- Include clear examples
- Link to external resources when appropriate

## Types of References

- **examples.md** - Usage examples
- **style-guide.md** - Coding standards
- **templates/** - Reusable templates
- **patterns.md** - Design patterns
EOF

    # Add assets README
    cat > "$SKILL_DIR/assets/README.md" << 'EOF'
# Skill Assets

This directory contains static assets used by this skill.

## Purpose

Assets can include:
- Configuration files (JSON, YAML)
- Data files
- Templates
- Schemas
- Test fixtures

## Guidelines

- Keep assets small and focused
- Document asset purpose and format
- Use standard file formats
- Include schema validation where applicable

## Common Asset Types

- **config.json** - Configuration templates
- **schema.json** - JSON schemas
- **template.yaml** - YAML templates
- **test-data.json** - Test fixtures
EOF

    ENHANCED=$((ENHANCED + 1))

done < <(find "$PLUGINS_DIR" -path "*/skills/*/SKILL.md" ! -path "*/skill-adapter/*")

echo ""
echo "=========================================="
echo "📊 Enhancement Summary:"
echo "   ✅ Enhanced: $ENHANCED skills with supporting structure"
echo "   ⏭️  Skipped: $SKIPPED skills (already had structure)"
echo "=========================================="
echo ""
echo "✅ All skills now have professional supporting file structure!"
echo ""
echo "Next: Add actual scripts/references/assets to high-value skills"
