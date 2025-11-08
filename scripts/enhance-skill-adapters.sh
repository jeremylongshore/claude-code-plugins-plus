#!/bin/bash
# Enhance skill-adapter directories with professional supporting files
# Adds useful scripts, references, and assets
# Author: Claude Code Quality Team
# Date: 2025-11-08

set -e

PLUGINS_DIR="/home/user/claude-code-plugins-plus/plugins"

echo "🔧 Skill-Adapter Enhancement - Professional Content"
echo "===================================================="
echo ""

ENHANCED=0

# Find all skill-adapter directories
while IFS= read -r ADAPTER_DIR; do
    if [ -z "$ADAPTER_DIR" ]; then
        continue
    fi

    PLUGIN_DIR=$(dirname "$(dirname "$ADAPTER_DIR")")
    PLUGIN_NAME=$(basename "$PLUGIN_DIR")

    echo "📦 Enhancing: $PLUGIN_NAME/skill-adapter"

    # Enhance scripts directory
    cat > "$ADAPTER_DIR/scripts/validation.sh" << 'SCRIPT_EOF'
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
SCRIPT_EOF

    chmod +x "$ADAPTER_DIR/scripts/validation.sh"

    # Add helper script template
    cat > "$ADAPTER_DIR/scripts/helper-template.sh" << 'SCRIPT_EOF'
#!/bin/bash
# Helper script template for skill automation
# Customize this for your skill's specific needs

set -e

function show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
}

# Parse arguments
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Your skill logic here
if [ "$VERBOSE" = true ]; then
    echo "Running skill automation..."
fi

echo "✅ Complete"
SCRIPT_EOF

    chmod +x "$ADAPTER_DIR/scripts/helper-template.sh"

    # Enhance references with examples
    cat > "$ADAPTER_DIR/references/examples.md" << 'REF_EOF'
# Skill Usage Examples

This document provides practical examples of how to use this skill effectively.

## Basic Usage

### Example 1: Simple Activation

**User Request:**
```
[Describe trigger phrase here]
```

**Skill Response:**
1. Analyzes the request
2. Performs the required action
3. Returns results

### Example 2: Complex Workflow

**User Request:**
```
[Describe complex scenario]
```

**Workflow:**
1. Step 1: Initial analysis
2. Step 2: Data processing
3. Step 3: Result generation
4. Step 4: Validation

## Advanced Patterns

### Pattern 1: Chaining Operations

Combine this skill with other tools:
```
Step 1: Use this skill for [purpose]
Step 2: Chain with [other tool]
Step 3: Finalize with [action]
```

### Pattern 2: Error Handling

If issues occur:
- Check trigger phrase matches
- Verify context is available
- Review allowed-tools permissions

## Tips & Best Practices

- ✅ Be specific with trigger phrases
- ✅ Provide necessary context
- ✅ Check tool permissions match needs
- ❌ Avoid vague requests
- ❌ Don't mix unrelated tasks

## Common Issues

**Issue:** Skill doesn't activate
**Solution:** Use exact trigger phrases from description

**Issue:** Unexpected results
**Solution:** Check input format and context

## See Also

- Main SKILL.md for full documentation
- scripts/ for automation helpers
- assets/ for configuration examples
REF_EOF

    # Add best practices reference
    cat > "$ADAPTER_DIR/references/best-practices.md" << 'REF_EOF'
# Skill Best Practices

Guidelines for optimal skill usage and development.

## For Users

### Activation Best Practices

1. **Use Clear Trigger Phrases**
   - Match phrases from skill description
   - Be specific about intent
   - Provide necessary context

2. **Provide Sufficient Context**
   - Include relevant file paths
   - Specify scope of analysis
   - Mention any constraints

3. **Understand Tool Permissions**
   - Check allowed-tools in frontmatter
   - Know what the skill can/cannot do
   - Request appropriate actions

### Workflow Optimization

- Start with simple requests
- Build up to complex workflows
- Verify each step before proceeding
- Use skill consistently for related tasks

## For Developers

### Skill Development Guidelines

1. **Clear Descriptions**
   - Include explicit trigger phrases
   - Document all capabilities
   - Specify limitations

2. **Proper Tool Permissions**
   - Use minimal necessary tools
   - Document security implications
   - Test with restricted tools

3. **Comprehensive Documentation**
   - Provide usage examples
   - Document common pitfalls
   - Include troubleshooting guide

### Maintenance

- Keep version updated
- Test after tool updates
- Monitor user feedback
- Iterate on descriptions

## Performance Tips

- Scope skills to specific domains
- Avoid overlapping trigger phrases
- Keep descriptions under 1024 chars
- Test activation reliability

## Security Considerations

- Never include secrets in skill files
- Validate all inputs
- Use read-only tools when possible
- Document security requirements
REF_EOF

    # Add configuration template to assets
    cat > "$ADAPTER_DIR/assets/config-template.json" << 'JSON_EOF'
{
  "skill": {
    "name": "skill-name",
    "version": "1.0.0",
    "enabled": true,
    "settings": {
      "verbose": false,
      "autoActivate": true,
      "toolRestrictions": true
    }
  },
  "triggers": {
    "keywords": [
      "example-trigger-1",
      "example-trigger-2"
    ],
    "patterns": []
  },
  "tools": {
    "allowed": [
      "Read",
      "Grep",
      "Bash"
    ],
    "restricted": []
  },
  "metadata": {
    "author": "Plugin Author",
    "category": "general",
    "tags": []
  }
}
JSON_EOF

    # Add schema for validation
    cat > "$ADAPTER_DIR/assets/skill-schema.json" << 'SCHEMA_EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Claude Skill Configuration",
  "type": "object",
  "required": ["name", "description"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$",
      "maxLength": 64,
      "description": "Skill identifier (lowercase, hyphens only)"
    },
    "description": {
      "type": "string",
      "maxLength": 1024,
      "description": "What the skill does and when to use it"
    },
    "allowed-tools": {
      "type": "string",
      "description": "Comma-separated list of allowed tools"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version (x.y.z)"
    }
  }
}
SCHEMA_EOF

    # Add test data example
    cat > "$ADAPTER_DIR/assets/test-data.json" << 'TEST_EOF'
{
  "testCases": [
    {
      "name": "Basic activation test",
      "input": "trigger phrase example",
      "expected": {
        "activated": true,
        "toolsUsed": ["Read", "Grep"],
        "success": true
      }
    },
    {
      "name": "Complex workflow test",
      "input": "multi-step trigger example",
      "expected": {
        "activated": true,
        "steps": 3,
        "toolsUsed": ["Read", "Write", "Bash"],
        "success": true
      }
    }
  ],
  "fixtures": {
    "sampleInput": "example data",
    "expectedOutput": "processed result"
  }
}
TEST_EOF

    ENHANCED=$((ENHANCED + 1))

done < <(find "$PLUGINS_DIR" -type d -name "skill-adapter")

echo ""
echo "===================================================="
echo "📊 Enhancement Summary:"
echo "   ✅ Enhanced: $ENHANCED skill-adapter directories"
echo ""
echo "Added to each:"
echo "   📜 scripts/validation.sh - Skill validator"
echo "   📜 scripts/helper-template.sh - Automation template"
echo "   📚 references/examples.md - Usage examples"
echo "   📚 references/best-practices.md - Guidelines"
echo "   🗂️  assets/config-template.json - Configuration"
echo "   🗂️  assets/skill-schema.json - JSON schema"
echo "   🗂️  assets/test-data.json - Test fixtures"
echo "===================================================="
echo ""
echo "✅ All skill-adapters now have professional supporting files!"
