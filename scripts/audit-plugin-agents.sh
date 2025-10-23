#!/bin/bash

echo "============================================"
echo "PHASE 5: AGENTS (SUBAGENTS) VALIDATION"
echo "============================================"
echo ""

# Initialize counters
total_plugins=0
plugins_with_agents=0
total_agents=0
compliant_agents=0
non_compliant_agents=0

# Track all issues
declare -a agent_violations
declare -a agent_warnings

# Process each plugin
for plugin_dir in $(find ./plugins -name "plugin.json" -path "*/.claude-plugin/*" | xargs -I {} dirname {} | xargs -I {} dirname {} | sort); do
    plugin_name=$(basename "$plugin_dir")

    ((total_plugins++))

    # Check if plugin has agents directory
    if [[ ! -d "$plugin_dir/agents" ]]; then
        continue
    fi

    ((plugins_with_agents++))

    echo "---"
    echo "Plugin: $plugin_name"
    echo "Agents directory: $plugin_dir/agents"

    # Find all markdown files in agents directory
    agent_files=$(find "$plugin_dir/agents" -name "*.md" -type f 2>/dev/null | sort)

    if [[ -z "$agent_files" ]]; then
        echo "ℹ No agent files found in agents/ directory"
        agent_warnings+=("$plugin_name: agents/ exists but no .md files")
        continue
    fi

    # Check each agent file
    for agent_file in $agent_files; do
        agent_name=$(basename "$agent_file" .md)
        ((total_agents++))

        echo ""
        echo "  Agent: $agent_name"

        has_violation=false
        has_warning=false

        # Check for frontmatter
        if ! head -1 "$agent_file" | grep -q "^---$"; then
            echo "    ❌ Missing frontmatter delimiters"
            agent_violations+=("$plugin_name/$agent_name: Missing frontmatter")
            has_violation=true
            ((non_compliant_agents++))
            continue
        fi

        # Extract frontmatter
        frontmatter=$(awk '/^---$/{f++;next}f==1' "$agent_file")

        # Check for description field in frontmatter (REQUIRED)
        if echo "$frontmatter" | grep -q "^description:"; then
            description=$(echo "$frontmatter" | grep "^description:" | cut -d: -f2- | sed 's/^ *//;s/ *$//')
            desc_length=${#description}

            if [[ $desc_length -lt 10 ]]; then
                echo "    ⚠ Description too short ($desc_length chars): \"$description\""
                agent_warnings+=("$plugin_name/$agent_name: Description too short")
                has_warning=true
            else
                echo "    ✓ description: Present ($desc_length chars)"
            fi
        else
            echo "    ❌ Missing 'description' in frontmatter"
            agent_violations+=("$plugin_name/$agent_name: Missing description field")
            has_violation=true
        fi

        # Check for capabilities field (RECOMMENDED)
        if echo "$frontmatter" | grep -q "^capabilities:"; then
            # Count capabilities
            cap_count=$(echo "$frontmatter" | awk '/^capabilities:/,/^[^ -]/' | grep -c "^  - ")
            if [[ $cap_count -gt 0 ]]; then
                echo "    ✓ capabilities: $cap_count capabilities defined"
            else
                echo "    ⚠ capabilities field exists but no items"
                agent_warnings+=("$plugin_name/$agent_name: Empty capabilities list")
                has_warning=true
            fi
        else
            echo "    ℹ No capabilities defined (recommended but not required)"
        fi

        # Check for optional fields in frontmatter
        if echo "$frontmatter" | grep -q "^name:"; then
            echo "    ✓ name field present"
        fi

        if echo "$frontmatter" | grep -q "^model:"; then
            echo "    ✓ model field present"
        fi

        if echo "$frontmatter" | grep -q "^temperature:"; then
            echo "    ✓ temperature field present"
        fi

        # Check for heading after frontmatter
        content_after_frontmatter=$(awk '/^---$/{f++;next}f==2' "$agent_file")

        if echo "$content_after_frontmatter" | head -5 | grep -q "^# "; then
            heading=$(echo "$content_after_frontmatter" | grep "^# " | head -1)
            echo "    ✓ Has heading: $heading"
        else
            echo "    ⚠ No heading (# ) found in first 5 lines"
            agent_warnings+=("$plugin_name/$agent_name: No heading")
            has_warning=true
        fi

        # Check content length
        content_lines=$(echo "$content_after_frontmatter" | wc -l)
        if [[ $content_lines -lt 10 ]]; then
            echo "    ⚠ Minimal content ($content_lines lines)"
            agent_warnings+=("$plugin_name/$agent_name: Minimal content")
            has_warning=true
        else
            echo "    ✓ Content: $content_lines lines"
        fi

        # Check for common agent patterns
        if echo "$content_after_frontmatter" | grep -q -i "purpose\|capabilities\|when to use\|expertise\|specializ"; then
            echo "    ✓ Contains agent role description"
        else
            echo "    ℹ Consider adding clear role description"
        fi

        # Tally results for this agent
        if ! $has_violation; then
            ((compliant_agents++))
            echo "    STATUS: ✅ COMPLIANT"
        else
            ((non_compliant_agents++))
            echo "    STATUS: ❌ NON-COMPLIANT"
        fi
    done

    echo ""
done

# Generate summary
echo "============================================"
echo "PHASE 5 SUMMARY: AGENTS (SUBAGENTS)"
echo "============================================"
echo ""
echo "Total Plugins: $total_plugins"
echo "Plugins with Agents: $plugins_with_agents"
echo "Total Agent Files: $total_agents"
echo "Compliant Agents: $compliant_agents"
echo "Non-Compliant Agents: $non_compliant_agents"
echo ""

if [[ ${#agent_violations[@]} -gt 0 ]]; then
    echo "AGENT VIOLATIONS (${#agent_violations[@]}):"
    for violation in "${agent_violations[@]}"; do
        echo "  ❌ $violation"
    done
    echo ""
fi

if [[ ${#agent_warnings[@]} -gt 0 ]]; then
    echo "AGENT WARNINGS (${#agent_warnings[@]}):"
    for warning in "${agent_warnings[@]}"; do
        echo "  ⚠ $warning"
    done
fi

echo ""
if [[ $total_agents -gt 0 ]]; then
    echo "Agent Compliance Rate: $(( (compliant_agents * 100) / total_agents ))%"
else
    echo "No agents found to validate"
fi