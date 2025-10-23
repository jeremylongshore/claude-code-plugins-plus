# ANTHROPIC CALIBER QUALITY TEMPLATE

**Purpose:** Standard template for all Claude Code plugin commands, agents, and hooks
**Target:** 95%+ success rate when executed by Claude
**Minimum Word Count:** Commands: 400+, Agents: 800+

---

## 📝 COMMAND TEMPLATE

```markdown
---
description: [One clear line describing what this command does]
category: [git|database|api|testing|deployment|security|etc]
difficulty: [beginner|intermediate|advanced]
estimated_time: [e.g., "30 seconds", "2-5 minutes"]
author: [your-github-username]
version: 1.0.0
---

<!-- DESIGN DECISIONS (Hidden comments for maintainers) -->
<!-- Why this command exists and what problem it solves -->
<!-- Alternative approaches considered and why rejected -->
<!-- Known limitations and future improvements -->

# [Command Name]

[2-3 sentences that explain WHAT this command does, WHY it's valuable, and WHEN to use it. Be specific about the value proposition.]

## When to Use

Use this command when:
- [Specific scenario 1 with concrete example]
- [Specific scenario 2 with concrete example]
- [Specific scenario 3 with concrete example]
- [Additional scenarios as needed]

Do NOT use this command for:
- [Inappropriate use case 1 with explanation]
- [Inappropriate use case 2 with explanation]
- [Suggest alternative command if applicable]

## Prerequisites

Before running this command, ensure:
- [ ] [Required condition 1, e.g., "Git repository initialized"]
- [ ] [Required condition 2, e.g., "Files staged for commit"]
- [ ] [Required permission or access]
- [ ] [Any required tools installed]

## Process

### Step 1: [Clear Action Verb + Specific Task]
[Detailed explanation of what happens in this step]
[Include any decision points or variations]
[Mention what to look for or verify]

### Step 2: [Clear Action Verb + Specific Task]
[Detailed explanation of what happens in this step]
[Explain WHY this step is important]
[Note any common pitfalls to avoid]

### Step 3: [Clear Action Verb + Specific Task]
[Detailed explanation of what happens in this step]
[Describe expected outcomes]
[Include validation or confirmation steps]

### Step 4: [Additional steps as needed]
[Continue numbered steps until process is complete]

## Output Format

The command will produce output in this format:

```
[Exact template showing the structure]
[Use placeholder variables in square brackets]
[Show all possible sections]
[Include any conditional elements]
```

**Output Fields Explained:**
- `[field1]`: [What this field contains and why it's important]
- `[field2]`: [What this field contains and constraints]
- `[field3]`: [What this field contains and format]

## Examples

### Example 1: [Common/Simple Use Case]

**Scenario:** [1-2 sentences describing the situation]

**User Input:**
```
/[command-name] [any parameters]
```

**Context:**
- Working directory: `[path]`
- Current state: [relevant context]
- Goal: [what user wants to achieve]

**Command Execution:**
```bash
# Step 1: [What Claude does]
[actual command or action]

# Step 2: [What Claude does]
[actual command or action]
```

**Output:**
```
[Complete actual output that would be produced]
[Show real values, not placeholders]
[Include any formatting or styling]
```

**Result:** [1-2 sentences explaining what was accomplished]

---

### Example 2: [Edge Case or Advanced Usage]

**Scenario:** [1-2 sentences describing complex situation]

**User Input:**
```
/[command-name] [parameters] --flag
```

**Context:**
- Special condition: [what makes this case unique]
- Challenge: [what problem needs solving]

**Command Execution:**
[Detailed steps as above]

**Output:**
[Complete actual output]

**Result:** [What was accomplished and why it matters]

---

### Example 3: [Error Case That's Handled Gracefully]

**Scenario:** [Situation where something goes wrong]

**User Input:**
```
/[command-name] [invalid or problematic input]
```

**What Happens:**
[Explain how the error is detected]
[Show the helpful error message]
[Demonstrate recovery or suggestions]

**Output:**
```
⚠️ [Error Type]: [Clear error message]

[Explanation of what went wrong]

To fix this:
1. [Specific action to resolve]
2. [Alternative approach]
3. [Where to get help]

Try: /[command-name] [corrected usage]
```

## Error Handling

### Error: [Common Error Condition 1]
**Symptoms:** [How to recognize this error]
**Cause:** [Why this happens]
**Solution:**
```
[Specific commands or actions to fix]
```
**Prevention:** [How to avoid this in future]

### Error: [Common Error Condition 2]
**Symptoms:** [How to recognize this error]
**Cause:** [Why this happens]
**Solution:**
```
[Specific recovery steps]
```

### Error: [Common Error Condition 3]
**Symptoms:** [How to recognize]
**Cause:** [Root cause]
**Solution:** [Fix steps]

### General Error Recovery
If the command fails unexpectedly:
1. [First diagnostic step]
2. [Second diagnostic step]
3. [How to gather debug information]
4. [Where to report issues]

## Configuration Options (if applicable)

The command behavior can be customized with:

### Option: `--[flag-name]`
- **Purpose:** [What this flag does]
- **Default:** [Default behavior without flag]
- **Example:** `/command --flag-name`

### Option: `[parameter]`
- **Purpose:** [What this parameter controls]
- **Values:** [Allowed values or format]
- **Example:** `/command parameter=value`

## Best Practices

✅ **DO:**
- [Specific good practice with reason]
- [Another good practice with benefit]
- [Performance or security tip]

❌ **DON'T:**
- [Common mistake to avoid with consequences]
- [Anti-pattern with explanation]
- [Security or performance warning]

💡 **TIPS:**
- [Pro tip for power users]
- [Time-saving shortcut]
- [Integration tip with other tools]

## Related Commands

- `/[related-command-1]` - [Brief description and when to use instead]
- `/[related-command-2]` - [Brief description and how it complements]
- `/[related-command-3]` - [Brief description and workflow connection]

## Performance Considerations

- **Typical execution time:** [e.g., "2-5 seconds for 100 files"]
- **Resource usage:** [e.g., "Minimal CPU, may use up to 100MB RAM"]
- **Scaling notes:** [How performance changes with size]
- **Optimization tips:** [How to improve performance if needed]

## Security Notes (if applicable)

⚠️ **Security Considerations:**
- [Any security implications]
- [Required permissions or access]
- [Data handling notes]
- [Audit trail information]

## Troubleshooting

### Issue: Command not recognized
**Solution:** Ensure the plugin is properly installed with `/plugin list`

### Issue: Unexpected output
**Solution:** Verify prerequisites and check context with `pwd` and `git status`

### Issue: Performance degradation
**Solution:** [Specific diagnostics and fixes]

### Getting Help
- Check examples above for similar use case
- Review error messages for specific guidance
- Report issues at: [repository issues URL]

## Version History

- **v1.0.0** - Initial implementation with core features
- **v1.1.0** - Added [feature] based on user feedback
- **v1.2.0** - Improved error handling for [case]

## Credits

- Original implementation: [@username]
- Major improvements: [@contributor]
- Based on: [any inspiration or references]

---

*Last updated: [YYYY-MM-DD]*
*Quality score: [X]/10*
*Tested with Claude: [model version]*
```

---

## 🤖 AGENT TEMPLATE

```markdown
---
name: [agent-name]
description: [One-line description of agent's specialization]
author: [github-username]
version: 1.0.0
capabilities:
  - [Specific capability 1]
  - [Specific capability 2]
  - [Specific capability 3]
  - [4-7 total capabilities]
tools:
  - [Tool this agent uses, e.g., "file_search", "code_analysis"]
  - [Another tool]
expertise_level: [expert|specialist|assistant]
response_style: [analytical|conversational|technical|educational]
---

# [Agent Name]

[3-4 sentences introducing the agent's expertise, primary purpose, and unique value. Explain what makes this agent different from general Claude or other agents.]

## Specialization

This agent specializes in:
- **[Domain 1]:** [Specific expertise with examples]
- **[Domain 2]:** [Specific expertise with examples]
- **[Domain 3]:** [Specific expertise with examples]

## When to Invoke This Agent

### ✅ INVOKE FOR:
- [Specific task 1 with concrete example]
  - Example: "Analyze this SQL query for performance issues"
- [Specific task 2 with concrete example]
  - Example: "Design a caching strategy for this API"
- [Specific task 3 with concrete example]
  - Example: "Review this code for security vulnerabilities"

### ❌ DO NOT INVOKE FOR:
- [Task better suited for another agent or general Claude]
- [Task outside expertise area]
- [Task requiring different tools]

## Capabilities in Detail

### 1. [Capability Category]
[2-3 sentences explaining this capability]
- Can analyze: [specific things]
- Can generate: [specific outputs]
- Can optimize: [specific aspects]

### 2. [Capability Category]
[2-3 sentences explaining this capability]
- Identifies: [specific patterns or issues]
- Recommends: [specific solutions]
- Validates: [specific requirements]

### 3. [Capability Category]
[Detailed explanation of this capability]

## Analysis Process

When invoked, this agent follows this systematic approach:

### Phase 1: [Discovery/Assessment]
1. [Specific action with purpose]
2. [Specific action with purpose]
3. [Specific action with purpose]

### Phase 2: [Analysis/Processing]
1. [Detailed step with methodology]
2. [Detailed step with methodology]
3. [Detailed step with methodology]

### Phase 3: [Synthesis/Recommendations]
1. [How findings are compiled]
2. [How recommendations are prioritized]
3. [How results are presented]

## Output Format

This agent provides responses in the following structure:

```
## [Analysis/Assessment/Review] Summary

**Scope:** [What was analyzed]
**Complexity:** [Low|Medium|High]
**Risk Level:** [If applicable]
**Priority:** [If applicable]

## Key Findings

1. **[Finding Category]**
   - Observation: [What was found]
   - Impact: [Why it matters]
   - Evidence: [Specific examples]

2. **[Finding Category]**
   - Observation: [Details]
   - Impact: [Consequences]
   - Evidence: [Proof]

## Recommendations

### Priority 1: [Critical/Immediate]
- [ ] [Specific action with expected outcome]
- [ ] [Specific action with measurement]

### Priority 2: [Important/Short-term]
- [ ] [Specific improvement]

### Priority 3: [Enhancement/Long-term]
- [ ] [Optimization opportunity]

## Next Steps
1. [Immediate action]
2. [Follow-up action]
3. [Verification step]
```

## Example Interactions

### Example 1: [Common Use Case]

**User Request:** "I need help optimizing this database query that's running slowly"

**Agent Response:**
```
I'll analyze your query for performance issues using my database optimization expertise.

## Query Analysis Summary

**Query Type:** SELECT with multiple JOINs
**Complexity:** High (5 table joins, 3 subqueries)
**Estimated Impact:** 85% performance improvement possible

## Key Findings

1. **Missing Indexes**
   - Observation: No index on orders.customer_id
   - Impact: Full table scan on 1M+ rows
   - Evidence: EXPLAIN shows seq_scan

2. **Inefficient JOIN Order**
   - Observation: Largest table joined first
   - Impact: Unnecessary memory usage
   - Evidence: Query plan shows 500MB temp usage

## Recommendations

### Priority 1: Critical Performance Fixes
- [ ] Add index: CREATE INDEX idx_orders_customer ON orders(customer_id);
- [ ] Reorder JOINs: Start with smallest table (customers)

[Complete response continues...]
```

### Example 2: [Complex Scenario]

[Similar detailed example showing agent handling complex case]

## Integration with Other Agents

This agent works well with:
- **[Agent Name]:** [How they complement each other]
- **[Agent Name]:** [Workflow integration]
- **[Agent Name]:** [Hand-off scenarios]

## Limitations and Boundaries

This agent:
- **CAN:** [List of things within scope]
- **CANNOT:** [List of things outside scope]
- **SHOULD NOT:** [Things to avoid]

## Quality Metrics

This agent aims for:
- **Accuracy:** 95%+ in identifying [specific issues]
- **Completeness:** Covers all major [aspects]
- **Actionability:** 100% of recommendations are implementable
- **Clarity:** Explains complex topics in accessible language

## Continuous Improvement

This agent improves through:
- User feedback on recommendation effectiveness
- Updates to best practices in [domain]
- Integration of new analysis techniques
- Expansion of pattern recognition library

---

*Agent training data current as of: [date]*
*Specialty validation: [date]*
*Performance metrics: [success rate]*
```

---

## 🔗 HOOK TEMPLATE

```json
{
  "description": "Clear description of what this hook configuration does and why it's valuable",
  "version": "1.0.0",
  "author": "github-username",
  "PostToolUse": {
    "match": {
      "tool": "Write|Edit|Create",
      "pattern": ".*\\.(js|ts|py)$"
    },
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/post-write.sh",
    "description": "Runs after writing code files to ensure formatting and linting"
  },
  "PreToolUse": {
    "match": {
      "tool": "Delete",
      "confirm": true
    },
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/pre-delete.sh",
    "description": "Confirms deletion and creates backup"
  }
}
```

### Associated Script Template

```bash
#!/bin/bash
# Script: [script-name.sh]
# Purpose: [Clear description of what this script does]
# Hook: [Which hook triggers this]
# Author: [github-username]
# Version: 1.0.0

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/../logs/hook-$(date +%Y%m%d).log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit "${2:-1}"
}

# Main logic
main() {
    log "Starting ${0##*/} for: $1"

    # Validate input
    [[ -z "${1:-}" ]] && error_exit "No input file provided" 2

    # Core functionality
    if [[ -f "$1" ]]; then
        # Process the file
        log "Processing: $1"

        # Add your logic here

        log "Successfully processed: $1"
    else
        error_exit "File not found: $1" 3
    fi

    log "Completed successfully"
}

# Execute main function with all arguments
main "$@"
```

---

## ✅ QUALITY CHECKLIST

Before submitting any component, verify:

### Mandatory Requirements
- [ ] Minimum word count met (Commands: 400+, Agents: 800+)
- [ ] All template sections included
- [ ] 3+ examples with input/output
- [ ] 3+ error scenarios handled
- [ ] Output format specified precisely
- [ ] "When to use" section included
- [ ] Prerequisites listed
- [ ] Process has numbered steps

### Quality Standards
- [ ] Instructions unambiguous (no "might", "could", "sometime")
- [ ] Examples cover common AND edge cases
- [ ] Error messages helpful and actionable
- [ ] Related commands referenced
- [ ] Performance implications noted
- [ ] Security considerations addressed

### Testing
- [ ] Tested with Claude 10+ times
- [ ] Success rate >95%
- [ ] All examples verified working
- [ ] Error scenarios triggered and handled
- [ ] Different contexts tested

### Documentation
- [ ] Description accurate in frontmatter
- [ ] Version number included
- [ ] Author credited
- [ ] Last updated date current
- [ ] Design decisions documented in comments

---

## 📚 RESOURCES

- **Gold Standard Example:** `/plugins/devops/git-commit-smart/commands/commit-smart.md`
- **Quality Validator:** `scripts/validate-quality.sh`
- **Testing Guide:** `docs/QUALITY_TESTING.md`
- **Style Guide:** `docs/STYLE_GUIDE.md`

---

*This template ensures Claude Code plugins meet Anthropic's quality standards for 95%+ execution success rate.*