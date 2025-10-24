#!/bin/bash
#
# Migrate Agent Skills from non-compliant to compliant structure
# FROM: skills/skill-adapter/SKILL.md
# TO:   skills/{descriptive-name}/SKILL.md
#
# Per Anthropic's specification, SKILL.md must be at the root of the skill directory,
# not nested in a subdirectory like "skill-adapter".
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DRY_RUN=${DRY_RUN:-true}  # Default to dry-run mode

echo -e "${BLUE}=== Agent Skills Structure Migration ===${NC}"
echo -e "${BLUE}FROM: skills/skill-adapter/SKILL.md${NC}"
echo -e "${BLUE}TO:   skills/{skill-name}/SKILL.md${NC}"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}⚠️  DRY RUN MODE - No actual changes will be made${NC}"
    echo -e "${YELLOW}   Set DRY_RUN=false to execute migration${NC}"
    echo ""
fi

# Counter
total=0
success=0
skipped=0
errors=0

# Find all plugins with skills/skill-adapter/SKILL.md
while IFS= read -r -d '' skill_file; do
    ((total++))

    # Extract plugin path
    plugin_dir=$(dirname "$(dirname "$(dirname "$skill_file")")")  # Go up 3 levels
    plugin_name=$(basename "$plugin_dir")

    # Extract category path (e.g., "testing", "ai-ml", "devops")
    category_path=$(dirname "$skill_file" | sed 's|plugins/||' | sed 's|/skills/skill-adapter||')

    # Determine new skill directory name
    # Use the last part of the plugin path as skill name
    skill_name=$(basename "$category_path")

    # Skip if it's already in correct structure
    current_dir=$(dirname "$skill_file")
    current_dirname=$(basename "$current_dir")
    if [ "$current_dirname" != "skill-adapter" ]; then
        echo -e "${YELLOW}[$total] SKIP: $category_path (already migrated)${NC}"
        ((skipped++))
        continue
    fi

    # Define paths
    old_dir="$plugin_dir/skills/skill-adapter"
    new_dir="$plugin_dir/skills/$skill_name"

    echo -e "${BLUE}[$total] $category_path${NC}"
    echo "    Old: skills/skill-adapter/"
    echo "    New: skills/$skill_name/"

    if [ "$DRY_RUN" = "false" ]; then
        # Perform actual migration
        if [ -d "$old_dir" ]; then
            # Create parent directory if needed
            mkdir -p "$(dirname "$new_dir")"

            # Move the directory
            if mv "$old_dir" "$new_dir"; then
                echo -e "    ${GREEN}✅ Migrated${NC}"
                ((success++))
            else
                echo -e "    ${RED}❌ Failed to migrate${NC}"
                ((errors++))
            fi
        else
            echo -e "    ${RED}❌ Old directory not found${NC}"
            ((errors++))
        fi
    else
        echo -e "    ${GREEN}✅ Would migrate${NC}"
        ((success++))
    fi

done < <(find plugins -type f -path "*/skills/skill-adapter/SKILL.md" -print0)

# Summary
echo ""
echo -e "${BLUE}=== Migration Summary ===${NC}"
echo "Total plugins found: $total"
echo -e "${GREEN}Successfully migrated: $success${NC}"
echo -e "${YELLOW}Skipped (already migrated): $skipped${NC}"
echo -e "${RED}Errors: $errors${NC}"

if [ "$DRY_RUN" = "true" ]; then
    echo ""
    echo -e "${YELLOW}This was a DRY RUN. To execute migration, run:${NC}"
    echo -e "${YELLOW}DRY_RUN=false ./scripts/migrate-skill-structure.sh${NC}"
fi

exit 0
