#!/bin/bash

# Add capabilities to agents with empty arrays
# This is a QUALITY ENHANCEMENT, not a compliance fix

echo "============================================"
echo "ADDING AGENT CAPABILITIES"
echo "============================================"
echo ""
echo "Note: Empty capabilities are compliant - this improves discoverability"
echo ""

# Track changes
updated=0

# Process each agent file
for agent_file in $(find ./plugins -path "*/agents/*.md" 2>/dev/null); do
    plugin_name=$(echo "$agent_file" | cut -d'/' -f3-4)
    agent_name=$(basename "$agent_file" .md)

    # Check frontmatter for empty capabilities
    frontmatter=$(awk '/^---$/{f++;next}f==1{print}f==2{exit}' "$agent_file")

    # Check if capabilities exist but are empty
    if echo "$frontmatter" | grep -q "capabilities:\s*\[\]" || \
       (echo "$frontmatter" | grep -q "capabilities:" && \
        ! echo "$frontmatter" | grep -q "capabilities:.*\n.*-"); then

        echo "Adding capabilities to: $plugin_name/agents/$agent_name.md"

        # Determine agent type and add appropriate capabilities
        case "$agent_name" in
            *security*|*audit*)
                capabilities='  - "Security vulnerability detection"\n  - "Code audit and analysis"\n  - "Best practices validation"'
                ;;
            *test*|*qa*)
                capabilities='  - "Test generation and execution"\n  - "Quality assurance checks"\n  - "Coverage analysis"'
                ;;
            *api*|*endpoint*)
                capabilities='  - "API design and validation"\n  - "Endpoint testing"\n  - "Integration verification"'
                ;;
            *data*|*database*)
                capabilities='  - "Data structure analysis"\n  - "Query optimization"\n  - "Schema validation"'
                ;;
            *deploy*|*devops*)
                capabilities='  - "Deployment automation"\n  - "Infrastructure management"\n  - "CI/CD pipeline optimization"'
                ;;
            *)
                # Generic capabilities based on plugin category
                category=$(echo "$agent_file" | cut -d'/' -f3)
                capabilities='  - "Specialized '"$category"' operations"\n  - "Automated task handling"\n  - "Best practices enforcement"'
                ;;
        esac

        # Create temp file with updated capabilities
        awk -v caps="$capabilities" '
            /^---$/ && !start {start=1; print; next}
            /^capabilities:/ && start && !done {
                print "capabilities:"
                print caps
                done=1
                # Skip any existing empty array or list items
                while ((getline line) > 0) {
                    if (line !~ /^  -/ && line !~ /^\[\]/ && line ~ /^[^ ]/) {
                        print line
                        break
                    }
                }
                next
            }
            /^---$/ && start {start=0}
            {print}
        ' "$agent_file" > "$agent_file.tmp"

        mv "$agent_file.tmp" "$agent_file"
        echo "  ✓ Added relevant capabilities"
        ((updated++))
    fi
done

echo ""
echo "Summary:"
echo "  Agents updated: $updated"
echo ""
echo "To revert: git checkout -- './plugins/*/agents/*.md'"