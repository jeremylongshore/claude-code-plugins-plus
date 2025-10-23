#!/bin/bash

echo "============================================"
echo "PHASE 2: PLUGIN MANIFEST VALIDATION AUDIT"
echo "============================================"
echo ""

# Initialize counters
total_plugins=0
compliant_plugins=0
plugins_with_violations=0
plugins_with_warnings=0

# Track all issues
declare -a critical_violations
declare -a major_violations
declare -a minor_warnings

# Function to validate semver
validate_semver() {
    [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

# Function to validate kebab-case
validate_kebab_case() {
    [[ "$1" =~ ^[a-z0-9-]+$ ]]
}

# Function to validate URL
validate_url() {
    [[ "$1" =~ ^https?:// ]]
}

# Function to validate SPDX license
validate_license() {
    local valid_licenses=("MIT" "Apache-2.0" "GPL-3.0" "BSD-3-Clause" "ISC" "MPL-2.0")
    for license in "${valid_licenses[@]}"; do
        if [[ "$1" == "$license" ]]; then
            return 0
        fi
    done
    return 1
}

# Process each plugin
for plugin_json in $(find ./plugins -name "plugin.json" -path "*/.claude-plugin/*" | sort); do
    plugin_dir=$(dirname $(dirname "$plugin_json"))
    plugin_name=$(basename "$plugin_dir")

    ((total_plugins++))

    echo "---"
    echo "Plugin #$total_plugins: $plugin_name"
    echo "Location: $plugin_dir"

    has_critical=false
    has_major=false
    has_minor=false

    # Check if file is valid JSON
    if ! jq empty "$plugin_json" 2>/dev/null; then
        echo "❌ CRITICAL: Invalid JSON syntax"
        critical_violations+=("$plugin_name: Invalid JSON syntax in plugin.json")
        has_critical=true
        ((plugins_with_violations++))
        continue
    fi

    # Check REQUIRED fields

    # 1. Check name field
    name=$(jq -r '.name // empty' "$plugin_json")
    if [[ -z "$name" ]]; then
        echo "❌ CRITICAL: Missing required field 'name'"
        critical_violations+=("$plugin_name: Missing 'name' field")
        has_critical=true
    elif ! validate_kebab_case "$name"; then
        echo "❌ CRITICAL: Name '$name' not in kebab-case format"
        critical_violations+=("$plugin_name: Name '$name' not kebab-case")
        has_critical=true
    else
        echo "✓ name: $name (valid kebab-case)"
    fi

    # 2. Check version field
    version=$(jq -r '.version // empty' "$plugin_json")
    if [[ -z "$version" ]]; then
        echo "❌ CRITICAL: Missing required field 'version'"
        critical_violations+=("$plugin_name: Missing 'version' field")
        has_critical=true
    elif ! validate_semver "$version"; then
        echo "❌ CRITICAL: Version '$version' not in semantic versioning format"
        critical_violations+=("$plugin_name: Version '$version' not semver")
        has_critical=true
    else
        echo "✓ version: $version (valid semver)"
    fi

    # 3. Check description field
    description=$(jq -r '.description // empty' "$plugin_json")
    if [[ -z "$description" ]]; then
        echo "❌ CRITICAL: Missing required field 'description'"
        critical_violations+=("$plugin_name: Missing 'description' field")
        has_critical=true
    else
        desc_length=${#description}
        if [[ $desc_length -lt 10 ]]; then
            echo "⚠ WARNING: Description too short ($desc_length chars)"
            minor_warnings+=("$plugin_name: Description too short")
            has_minor=true
        else
            echo "✓ description: Present ($desc_length chars)"
        fi
    fi

    # Check OPTIONAL fields

    # Check author
    author_name=$(jq -r '.author.name // empty' "$plugin_json")
    author_email=$(jq -r '.author.email // empty' "$plugin_json")
    if [[ -n "$author_name" ]]; then
        echo "✓ author.name: $author_name"
    else
        echo "ℹ INFO: No author name specified"
    fi

    if [[ -n "$author_email" ]] && [[ "$author_email" != "null" ]]; then
        if [[ "$author_email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            echo "✓ author.email: Valid email"
        else
            echo "⚠ WARNING: Invalid email format: $author_email"
            minor_warnings+=("$plugin_name: Invalid email format")
            has_minor=true
        fi
    fi

    # Check homepage
    homepage=$(jq -r '.homepage // empty' "$plugin_json")
    if [[ -n "$homepage" ]] && [[ "$homepage" != "null" ]]; then
        if validate_url "$homepage"; then
            echo "✓ homepage: Valid URL"
        else
            echo "⚠ WARNING: Invalid homepage URL: $homepage"
            minor_warnings+=("$plugin_name: Invalid homepage URL")
            has_minor=true
        fi
    fi

    # Check repository
    repository=$(jq -r '.repository // empty' "$plugin_json")
    if [[ -n "$repository" ]] && [[ "$repository" != "null" ]]; then
        if validate_url "$repository"; then
            echo "✓ repository: Valid URL"
        else
            echo "⚠ WARNING: Invalid repository URL: $repository"
            minor_warnings+=("$plugin_name: Invalid repository URL")
            has_minor=true
        fi
    fi

    # Check license
    license=$(jq -r '.license // empty' "$plugin_json")
    if [[ -n "$license" ]] && [[ "$license" != "null" ]]; then
        if validate_license "$license"; then
            echo "✓ license: $license (valid SPDX)"
        else
            echo "⚠ WARNING: Non-standard license: $license"
            minor_warnings+=("$plugin_name: Non-standard license '$license'")
            has_minor=true
        fi
    fi

    # Check keywords
    keywords_count=$(jq '.keywords | length // 0' "$plugin_json")
    if [[ $keywords_count -gt 0 ]]; then
        echo "✓ keywords: $keywords_count keywords defined"
    fi

    # Check component paths (must be relative and start with ./)
    # Check commands path
    commands_path=$(jq -r '.commands // empty' "$plugin_json")
    if [[ -n "$commands_path" ]] && [[ "$commands_path" != "null" ]]; then
        if [[ "$commands_path" == /* ]]; then
            echo "❌ MAJOR: Commands path is absolute: $commands_path"
            major_violations+=("$plugin_name: Absolute commands path")
            has_major=true
        elif [[ "$commands_path" != ./* ]]; then
            echo "❌ MAJOR: Commands path must start with ./: $commands_path"
            major_violations+=("$plugin_name: Invalid commands path format")
            has_major=true
        else
            echo "✓ commands: $commands_path (valid relative path)"
        fi
    fi

    # Check agents path
    agents_path=$(jq -r '.agents // empty' "$plugin_json")
    if [[ -n "$agents_path" ]] && [[ "$agents_path" != "null" ]]; then
        if [[ "$agents_path" == /* ]]; then
            echo "❌ MAJOR: Agents path is absolute: $agents_path"
            major_violations+=("$plugin_name: Absolute agents path")
            has_major=true
        elif [[ "$agents_path" != ./* ]]; then
            echo "❌ MAJOR: Agents path must start with ./: $agents_path"
            major_violations+=("$plugin_name: Invalid agents path format")
            has_major=true
        else
            echo "✓ agents: $agents_path (valid relative path)"
        fi
    fi

    # Check hooks path
    hooks_value=$(jq -r '.hooks // empty' "$plugin_json")
    if [[ -n "$hooks_value" ]] && [[ "$hooks_value" != "null" ]]; then
        # Check if it's a string (path) or object (inline config)
        if jq -e '.hooks | type == "string"' "$plugin_json" > /dev/null 2>&1; then
            if [[ "$hooks_value" == /* ]]; then
                echo "❌ MAJOR: Hooks path is absolute: $hooks_value"
                major_violations+=("$plugin_name: Absolute hooks path")
                has_major=true
            elif [[ "$hooks_value" != ./* ]]; then
                echo "❌ MAJOR: Hooks path must start with ./: $hooks_value"
                major_violations+=("$plugin_name: Invalid hooks path format")
                has_major=true
            else
                echo "✓ hooks: $hooks_value (valid relative path)"
            fi
        else
            echo "✓ hooks: Inline configuration"
        fi
    fi

    # Check mcpServers path
    mcp_value=$(jq -r '.mcpServers // empty' "$plugin_json")
    if [[ -n "$mcp_value" ]] && [[ "$mcp_value" != "null" ]]; then
        # Check if it's a string (path) or object (inline config)
        if jq -e '.mcpServers | type == "string"' "$plugin_json" > /dev/null 2>&1; then
            if [[ "$mcp_value" == /* ]]; then
                echo "❌ MAJOR: MCP servers path is absolute: $mcp_value"
                major_violations+=("$plugin_name: Absolute mcpServers path")
                has_major=true
            elif [[ "$mcp_value" != ./* ]]; then
                echo "❌ MAJOR: MCP servers path must start with ./: $mcp_value"
                major_violations+=("$plugin_name: Invalid mcpServers path format")
                has_major=true
            else
                echo "✓ mcpServers: $mcp_value (valid relative path)"
            fi
        else
            echo "✓ mcpServers: Inline configuration"
        fi
    fi

    # Tally results for this plugin
    if $has_critical; then
        ((plugins_with_violations++))
        echo "STATUS: ❌ NON-COMPLIANT (Critical violations)"
    elif $has_major; then
        ((plugins_with_violations++))
        echo "STATUS: ❌ NON-COMPLIANT (Major violations)"
    elif $has_minor; then
        ((plugins_with_warnings++))
        ((compliant_plugins++))
        echo "STATUS: ⚠ COMPLIANT WITH WARNINGS"
    else
        ((compliant_plugins++))
        echo "STATUS: ✅ FULLY COMPLIANT"
    fi

    echo ""
done

# Generate summary
echo "============================================"
echo "PHASE 2 SUMMARY: PLUGIN MANIFEST VALIDATION"
echo "============================================"
echo ""
echo "Total Plugins Analyzed: $total_plugins"
echo "Fully Compliant: $compliant_plugins"
echo "With Violations: $plugins_with_violations"
echo "With Warnings Only: $plugins_with_warnings"
echo ""

if [[ ${#critical_violations[@]} -gt 0 ]]; then
    echo "CRITICAL VIOLATIONS (${#critical_violations[@]}):"
    for violation in "${critical_violations[@]}"; do
        echo "  ❌ $violation"
    done
    echo ""
fi

if [[ ${#major_violations[@]} -gt 0 ]]; then
    echo "MAJOR VIOLATIONS (${#major_violations[@]}):"
    for violation in "${major_violations[@]}"; do
        echo "  ❌ $violation"
    done
    echo ""
fi

if [[ ${#minor_warnings[@]} -gt 0 ]]; then
    echo "MINOR WARNINGS (${#minor_warnings[@]}):"
    for warning in "${minor_warnings[@]}"; do
        echo "  ⚠ $warning"
    done
fi

echo ""
echo "Compliance Rate: $(( (compliant_plugins * 100) / total_plugins ))%"