#!/bin/bash

echo "============================================"
echo "PHASE 4: SLASH COMMANDS VALIDATION"
echo "============================================"
echo ""

# Initialize counters
total_plugins=0
plugins_with_commands=0
total_commands=0
compliant_commands=0
non_compliant_commands=0

# Track all issues
declare -a command_violations
declare -a command_warnings

# Process each plugin
for plugin_dir in $(find ./plugins -name "plugin.json" -path "*/.claude-plugin/*" | xargs -I {} dirname {} | xargs -I {} dirname {} | sort); do
    plugin_name=$(basename "$plugin_dir")

    ((total_plugins++))

    # Check if plugin has commands directory
    if [[ ! -d "$plugin_dir/commands" ]]; then
        continue
    fi

    ((plugins_with_commands++))

    echo "---"
    echo "Plugin: $plugin_name"
    echo "Commands directory: $plugin_dir/commands"

    # Find all markdown files in commands directory
    command_files=$(find "$plugin_dir/commands" -name "*.md" -type f 2>/dev/null | sort)

    if [[ -z "$command_files" ]]; then
        echo "ℹ No command files found in commands/ directory"
        command_warnings+=("$plugin_name: commands/ exists but no .md files")
        continue
    fi

    # Check each command file
    for cmd_file in $command_files; do
        cmd_name=$(basename "$cmd_file" .md)
        ((total_commands++))

        echo ""
        echo "  Command: $cmd_name"

        has_violation=false
        has_warning=false

        # Check for frontmatter
        if ! head -1 "$cmd_file" | grep -q "^---$"; then
            echo "    ❌ Missing frontmatter delimiters"
            command_violations+=("$plugin_name/$cmd_name: Missing frontmatter")
            has_violation=true
            ((non_compliant_commands++))
            continue
        fi

        # Extract frontmatter
        frontmatter=$(awk '/^---$/{f++;next}f==1' "$cmd_file")

        # Check for description field in frontmatter
        if echo "$frontmatter" | grep -q "^description:"; then
            description=$(echo "$frontmatter" | grep "^description:" | cut -d: -f2- | sed 's/^ *//;s/ *$//')
            desc_length=${#description}

            if [[ $desc_length -lt 10 ]]; then
                echo "    ⚠ Description too short ($desc_length chars): \"$description\""
                command_warnings+=("$plugin_name/$cmd_name: Description too short")
                has_warning=true
            else
                echo "    ✓ description: Present ($desc_length chars)"
            fi
        else
            echo "    ❌ Missing 'description' in frontmatter"
            command_violations+=("$plugin_name/$cmd_name: Missing description field")
            has_violation=true
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
        content_after_frontmatter=$(awk '/^---$/{f++;next}f==2' "$cmd_file")

        if echo "$content_after_frontmatter" | head -5 | grep -q "^# "; then
            heading=$(echo "$content_after_frontmatter" | grep "^# " | head -1)
            echo "    ✓ Has heading: $heading"
        else
            echo "    ⚠ No heading (# ) found in first 5 lines"
            command_warnings+=("$plugin_name/$cmd_name: No heading")
            has_warning=true
        fi

        # Check content length
        content_lines=$(echo "$content_after_frontmatter" | wc -l)
        if [[ $content_lines -lt 5 ]]; then
            echo "    ⚠ Minimal content ($content_lines lines)"
            command_warnings+=("$plugin_name/$cmd_name: Minimal content")
            has_warning=true
        else
            echo "    ✓ Content: $content_lines lines"
        fi

        # Check for common command patterns
        if echo "$content_after_frontmatter" | grep -q -i "process\|task\|step\|instruction\|analyze\|generate\|create"; then
            echo "    ✓ Contains action instructions"
        else
            echo "    ℹ Consider adding clear action instructions"
        fi

        # Tally results for this command
        if ! $has_violation; then
            ((compliant_commands++))
            echo "    STATUS: ✅ COMPLIANT"
        else
            ((non_compliant_commands++))
            echo "    STATUS: ❌ NON-COMPLIANT"
        fi
    done

    echo ""
done

# Generate summary
echo "============================================"
echo "PHASE 4 SUMMARY: SLASH COMMANDS"
echo "============================================"
echo ""
echo "Total Plugins: $total_plugins"
echo "Plugins with Commands: $plugins_with_commands"
echo "Total Command Files: $total_commands"
echo "Compliant Commands: $compliant_commands"
echo "Non-Compliant Commands: $non_compliant_commands"
echo ""

if [[ ${#command_violations[@]} -gt 0 ]]; then
    echo "COMMAND VIOLATIONS (${#command_violations[@]}):"
    for violation in "${command_violations[@]}"; do
        echo "  ❌ $violation"
    done
    echo ""
fi

if [[ ${#command_warnings[@]} -gt 0 ]]; then
    echo "COMMAND WARNINGS (${#command_warnings[@]}):"
    for warning in "${command_warnings[@]}"; do
        echo "  ⚠ $warning"
    done
fi

echo ""
if [[ $total_commands -gt 0 ]]; then
    echo "Command Compliance Rate: $(( (compliant_commands * 100) / total_commands ))%"
else
    echo "No commands found to validate"
fi