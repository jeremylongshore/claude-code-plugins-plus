#!/bin/bash

echo "============================================"
echo "PHASE 3: DIRECTORY STRUCTURE VALIDATION"
echo "============================================"
echo ""

# Initialize counters
total_plugins=0
compliant_plugins=0
plugins_with_violations=0

# Track all issues
declare -a critical_violations
declare -a structure_warnings

# Process each plugin
for plugin_json in $(find ./plugins -name "plugin.json" -path "*/.claude-plugin/*" | sort); do
    plugin_dir=$(dirname $(dirname "$plugin_json"))
    plugin_name=$(basename "$plugin_dir")

    ((total_plugins++))

    echo "---"
    echo "Plugin #$total_plugins: $plugin_name"
    echo "Location: $plugin_dir"

    has_violations=false
    has_warnings=false

    # CRITICAL: Check .claude-plugin is at root
    claude_plugin_dir=$(dirname "$plugin_json")
    expected_location="$plugin_dir/.claude-plugin"

    if [[ "$claude_plugin_dir" != "$expected_location" ]]; then
        echo "❌ CRITICAL: .claude-plugin/ not at plugin root"
        echo "  Found: $claude_plugin_dir"
        echo "  Expected: $expected_location"
        critical_violations+=("$plugin_name: .claude-plugin/ not at plugin root")
        has_violations=true
    else
        echo "✓ .claude-plugin/ at root level"
    fi

    # Check for plugin.json in correct location
    if [[ -f "$plugin_dir/.claude-plugin/plugin.json" ]]; then
        echo "✓ plugin.json in .claude-plugin/"
    else
        echo "❌ CRITICAL: plugin.json not in .claude-plugin/"
        critical_violations+=("$plugin_name: plugin.json not in .claude-plugin/")
        has_violations=true
    fi

    # Check for prohibited structures
    # Check for plugin.json in wrong locations
    wrong_locations=()

    if [[ -f "$plugin_dir/commands/plugin.json" ]]; then
        wrong_locations+=("commands/plugin.json")
    fi

    if [[ -f "$plugin_dir/agents/plugin.json" ]]; then
        wrong_locations+=("agents/plugin.json")
    fi

    if [[ -f "$plugin_dir/plugin.json" ]]; then
        wrong_locations+=("plugin.json at root")
    fi

    if [[ ${#wrong_locations[@]} -gt 0 ]]; then
        echo "❌ VIOLATION: plugin.json found in wrong locations:"
        for loc in "${wrong_locations[@]}"; do
            echo "  - $loc"
            critical_violations+=("$plugin_name: plugin.json in wrong location: $loc")
        done
        has_violations=true
    fi

    # Check for commands inside .claude-plugin (VIOLATION)
    if [[ -d "$plugin_dir/.claude-plugin/commands" ]]; then
        echo "❌ VIOLATION: commands/ inside .claude-plugin/"
        critical_violations+=("$plugin_name: commands/ inside .claude-plugin/")
        has_violations=true
    fi

    # Check for agents inside .claude-plugin (VIOLATION)
    if [[ -d "$plugin_dir/.claude-plugin/agents" ]]; then
        echo "❌ VIOLATION: agents/ inside .claude-plugin/"
        critical_violations+=("$plugin_name: agents/ inside .claude-plugin/")
        has_violations=true
    fi

    # Check component directories
    has_component=false

    # Check commands directory
    if [[ -d "$plugin_dir/commands" ]]; then
        echo "✓ commands/ directory exists"
        has_component=true

        # Check for non-markdown files in commands
        non_md_count=$(find "$plugin_dir/commands" -type f ! -name "*.md" 2>/dev/null | wc -l)
        if [[ $non_md_count -gt 0 ]]; then
            echo "⚠ WARNING: $non_md_count non-markdown files in commands/"
            structure_warnings+=("$plugin_name: $non_md_count non-markdown files in commands/")
            has_warnings=true
        fi

        # Count command files
        cmd_count=$(find "$plugin_dir/commands" -name "*.md" -type f 2>/dev/null | wc -l)
        echo "  Found $cmd_count command files"
    fi

    # Check agents directory
    if [[ -d "$plugin_dir/agents" ]]; then
        echo "✓ agents/ directory exists"
        has_component=true

        # Check for non-markdown files in agents
        non_md_count=$(find "$plugin_dir/agents" -type f ! -name "*.md" 2>/dev/null | wc -l)
        if [[ $non_md_count -gt 0 ]]; then
            echo "⚠ WARNING: $non_md_count non-markdown files in agents/"
            structure_warnings+=("$plugin_name: $non_md_count non-markdown files in agents/")
            has_warnings=true
        fi

        # Count agent files
        agent_count=$(find "$plugin_dir/agents" -name "*.md" -type f 2>/dev/null | wc -l)
        echo "  Found $agent_count agent files"
    fi

    # Check hooks directory or inline config
    if [[ -d "$plugin_dir/hooks" ]]; then
        echo "✓ hooks/ directory exists"
        has_component=true
        if [[ -f "$plugin_dir/hooks/hooks.json" ]]; then
            echo "  ✓ hooks.json found"
        else
            echo "  ℹ No hooks.json in hooks/"
        fi
    fi

    # Check for .mcp.json
    if [[ -f "$plugin_dir/.mcp.json" ]]; then
        echo "✓ .mcp.json found at root"
        has_component=true
    fi

    # Check for mcp directory
    if [[ -d "$plugin_dir/mcp" ]]; then
        echo "✓ mcp/ directory exists"
        has_component=true
    fi

    # Check for scripts directory
    if [[ -d "$plugin_dir/scripts" ]]; then
        echo "✓ scripts/ directory exists"
        # Check for executable scripts
        exec_count=$(find "$plugin_dir/scripts" -type f -executable | wc -l)
        non_exec_count=$(find "$plugin_dir/scripts" -name "*.sh" -type f ! -executable | wc -l)

        echo "  $exec_count executable scripts"
        if [[ $non_exec_count -gt 0 ]]; then
            echo "⚠ WARNING: $non_exec_count .sh scripts not executable"
            structure_warnings+=("$plugin_name: $non_exec_count non-executable .sh scripts")
            has_warnings=true
        fi
    fi

    # Check for documentation files
    if [[ -f "$plugin_dir/README.md" ]]; then
        echo "✓ README.md exists"
    else
        echo "ℹ No README.md"
    fi

    if [[ -f "$plugin_dir/000-docs/001-BL-LICN-license.txt" ]]; then
        echo "✓ LICENSE file exists"
    else
        echo "ℹ No LICENSE file"
    fi

    # Verify plugin has at least one component
    if ! $has_component; then
        echo "⚠ WARNING: No component directories found (commands/, agents/, hooks/, mcp/, scripts/)"
        structure_warnings+=("$plugin_name: No component directories")
        has_warnings=true
    fi

    # Tally results for this plugin
    if $has_violations; then
        ((plugins_with_violations++))
        echo "STATUS: ❌ STRUCTURE VIOLATIONS"
    elif $has_warnings; then
        ((compliant_plugins++))
        echo "STATUS: ⚠ COMPLIANT WITH WARNINGS"
    else
        ((compliant_plugins++))
        echo "STATUS: ✅ STRUCTURE COMPLIANT"
    fi

    echo ""
done

# Generate summary
echo "============================================"
echo "PHASE 3 SUMMARY: DIRECTORY STRUCTURE"
echo "============================================"
echo ""
echo "Total Plugins Analyzed: $total_plugins"
echo "Structure Compliant: $compliant_plugins"
echo "With Violations: $plugins_with_violations"
echo ""

if [[ ${#critical_violations[@]} -gt 0 ]]; then
    echo "CRITICAL STRUCTURE VIOLATIONS (${#critical_violations[@]}):"
    for violation in "${critical_violations[@]}"; do
        echo "  ❌ $violation"
    done
    echo ""
fi

if [[ ${#structure_warnings[@]} -gt 0 ]]; then
    echo "STRUCTURE WARNINGS (${#structure_warnings[@]}):"
    for warning in "${structure_warnings[@]}"; do
        echo "  ⚠ $warning"
    done
fi

echo ""
echo "Structure Compliance Rate: $(( (compliant_plugins * 100) / total_plugins ))%"