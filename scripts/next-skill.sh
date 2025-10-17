#!/bin/bash
# Find the next plugin that needs an Agent Skill added

set -euo pipefail

MARKETPLACE=.claude-plugin/marketplace.json

# Find first plugin without agent-skills in high-priority categories
NEXT=$(jq -r '.plugins[] |
  select((.keywords[]? == "agent-skills") | not) |
  select(.category == "devops" or .category == "security" or .category == "testing" or .category == "ai-ml") |
  {name, category, description, source} |
  @json' "$MARKETPLACE" | head -n 1)

if [ -z "$NEXT" ]; then
  echo "✅ No high-priority plugins left! All devops/security/testing/ai-ml plugins have skills."
  echo ""
  echo "Remaining categories:"
  jq -r '.plugins[] |
    select((.keywords[]? == "agent-skills") | not) |
    .category' "$MARKETPLACE" | sort | uniq -c | sort -rn
  exit 0
fi

# Parse and display
NAME=$(echo "$NEXT" | jq -r '.name')
CAT=$(echo "$NEXT" | jq -r '.category')
DESC=$(echo "$NEXT" | jq -r '.description')
PATH=$(echo "$NEXT" | jq -r '.source')

echo "🎯 Next Plugin to Add Agent Skill:"
echo ""
echo "  Name:        $NAME"
echo "  Category:    $CAT"
echo "  Path:        $PATH"
echo "  Description: $DESC"
echo ""
echo "📝 To add skill manually:"
echo ""
echo "  1. Create skill folder:"
echo "     mkdir -p $PATH/skills/skill-adapter"
echo ""
echo "  2. Create SKILL.md with YAML frontmatter"
echo ""
echo "  3. Update keywords:"
echo "     - $PATH/.claude-plugin/plugin.json"
echo "     - .claude-plugin/marketplace.extended.json"
echo ""
echo "  4. Sync and commit:"
echo "     node scripts/sync-marketplace.cjs"
echo "     git add . && git commit -m 'feat(skills): add Agent Skill to $NAME'"
echo ""
echo "🤖 Or wait for tomorrow's automated GitHub issue at 10 AM UTC"
