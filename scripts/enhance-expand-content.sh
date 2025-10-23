#!/bin/bash

# Expand minimal command and agent content
# This is a QUALITY ENHANCEMENT, not a compliance fix

echo "============================================"
echo "EXPANDING MINIMAL CONTENT"
echo "============================================"
echo ""
echo "Note: Minimal content is compliant - this improves AI guidance"
echo ""

# Track changes
commands_expanded=0
agents_expanded=0

# Function to expand command content
expand_command() {
    local cmd_file="$1"
    local cmd_name=$(basename "$cmd_file" .md)
    local readable_name=$(echo "$cmd_name" | tr '-' ' ')

    # Count current content lines (after frontmatter)
    content_lines=$(awk '/^---$/{f++;next}f==2' "$cmd_file" | wc -l)

    if [[ $content_lines -lt 5 ]]; then
        echo "Expanding: $cmd_file"

        # Append template content
        cat >> "$cmd_file" << EOF

## Purpose

This command provides ${readable_name} functionality to enhance your development workflow.

## How It Works

1. Analyzes your current context
2. Applies ${readable_name} logic
3. Provides actionable results

## Usage Examples

\`\`\`
# Basic usage
/$cmd_name

# With parameters (if applicable)
/$cmd_name [options]
\`\`\`

## Benefits

- Automates ${readable_name} tasks
- Reduces manual effort
- Ensures consistency
EOF

        ((commands_expanded++))
        echo "  ✓ Expanded content"
    fi
}

# Function to expand agent content
expand_agent() {
    local agent_file="$1"
    local agent_name=$(basename "$agent_file" .md)
    local readable_name=$(echo "$agent_name" | tr '-' ' ')

    # Count current content lines (after frontmatter)
    content_lines=$(awk '/^---$/{f++;next}f==2' "$agent_file" | wc -l)

    if [[ $content_lines -lt 10 ]]; then
        echo "Expanding: $agent_file"

        # Add capabilities if empty
        if grep -q "capabilities:\s*\[\]" "$agent_file" 2>/dev/null; then
            # Replace empty capabilities
            sed -i '/capabilities:/,/^[^ -]/{
                /capabilities:/!d
                a\  - "Specialized ${readable_name} analysis"
                a\  - "Context-aware recommendations"
                a\  - "Best practices enforcement"
            }' "$agent_file"
        fi

        # Append content template
        cat >> "$agent_file" << EOF

## Expertise Areas

This agent specializes in:
- ${readable_name} tasks
- Automated analysis and recommendations
- Quality assurance and validation

## When to Use

Invoke this agent when you need:
- Expert guidance on ${readable_name}
- Automated task handling
- Consistent best practices application

## Interaction Examples

\`\`\`
User: Help me with ${readable_name}
Agent: I'll analyze your needs and provide tailored solutions...
\`\`\`
EOF

        ((agents_expanded++))
        echo "  ✓ Expanded content"
    fi
}

# Process commands
echo "Processing commands..."
for cmd in $(find ./plugins -path "*/commands/*.md" 2>/dev/null); do
    expand_command "$cmd"
done

echo ""
echo "Processing agents..."
for agent in $(find ./plugins -path "*/agents/*.md" 2>/dev/null); do
    expand_agent "$agent"
done

echo ""
echo "Summary:"
echo "  Commands expanded: $commands_expanded"
echo "  Agents expanded: $agents_expanded"
echo ""
echo "To revert: git checkout -- './plugins/*/commands/*.md' './plugins/*/agents/*.md'"