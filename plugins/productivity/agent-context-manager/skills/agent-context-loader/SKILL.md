---
name: agent-context-loader
description: |
  PROACTIVE AUTO-LOADING: Automatically detects and loads AGENTS.md files from the current working directory when starting a session or changing directories. This skill ensures agent-specific instructions are incorporated into Claude Code's context alongside CLAUDE.md, enabling specialized agent behaviors. Triggers automatically when Claude detects it's working in a directory, when starting a new session, or when explicitly requested to "load agent context" or "check for AGENTS.md file".
---

# Agent Context Auto-Loader

**⚡ This skill activates AUTOMATICALLY - no user action required!**

## Purpose

This skill makes Claude Code recognize and load `AGENTS.md` files with the same priority as `CLAUDE.md` files, enabling specialized agent-specific instructions for your projects.

## How It Works

### Automatic Trigger Conditions

This skill automatically activates when:
1. **Starting a new Claude Code session** in any directory
2. **Changing directories** during a session (via `cd` or file operations)
3. **Any other agent skill is invoked** (ensures agent context is loaded first)
4. **User explicitly requests**: "load agent context", "check for AGENTS.md", or "read agent rules"

### Execution Flow

When triggered, Claude Code will:

1. **Check for AGENTS.md**: Look for `./AGENTS.md` in the current working directory
2. **Read the file** (if it exists): Use the Read tool to load full content
3. **Incorporate into context**: Treat AGENTS.md rules as session-level instructions
4. **Announce loading**: Confirm with user: "📋 Loaded agent-specific context from AGENTS.md"
5. **Apply for session**: Follow these rules for all subsequent operations

### Priority and Conflict Resolution

- **AGENTS.md supplements CLAUDE.md**: Both are active simultaneously
- **In case of conflicts**: AGENTS.md takes precedence for agent-specific behaviors
- **Scope**: AGENTS.md applies to agent workflows; CLAUDE.md applies to general project context

## Expected Behavior

### If AGENTS.md exists:
```
📋 Loaded agent-specific context from AGENTS.md

Following specialized agent rules for this session:
- [rule 1 from AGENTS.md]
- [rule 2 from AGENTS.md]
...
```

### If AGENTS.md doesn't exist:
```
No AGENTS.md found - using standard CLAUDE.md context only
```

## User Experience

**Fully Automatic** (preferred):
- Install plugin → AGENTS.md loads automatically → Agent rules active → No user action needed

**Manual Invocation** (fallback):
```bash
# If auto-loading doesn't trigger, user can say:
"load agent context"
"check for AGENTS.md"
"read agent rules from AGENTS.md"
```

## Implementation Details

### Step 1: Check for File
```bash
# Claude executes internally:
if [ -f "./AGENTS.md" ]; then
    echo "📋 AGENTS.md detected"
fi
```

### Step 2: Read Content
```markdown
Use Read tool:
file_path: ./AGENTS.md

Load full content into session context
```

### Step 3: Apply Rules
```
Treat AGENTS.md content as:
- Session-level instructions (like CLAUDE.md)
- Agent-specific behavioral rules
- Overrides for agent workflows
```

## Example AGENTS.md Structure

```markdown
# AGENTS.md - Agent-Specific Instructions

## Agent Behavior Rules

When working with Agent Skills in this project:

1. **Always use TypeScript strict mode** for all generated code
2. **Never create files** without explicit user permission
3. **Follow naming convention**: use kebab-case for all file names
4. **Auto-commit after changes**: Create git commits automatically when tasks complete

## Specialized Workflows

### Code Generation
- Use templates from `./templates/` directory
- Run ESLint after generating any .ts/.js files
- Add comprehensive JSDoc comments

### Testing
- Generate tests alongside implementation files
- Use Jest for all test files
- Achieve 80%+ code coverage

## Priority Overrides

These rules override CLAUDE.md when agent skills are active:
- AGENTS.md → agent-specific strict rules
- CLAUDE.md → general project context
```

## Integration with Other Skills

This skill runs **before** other agent skills to ensure agent context is loaded first. When any other skill is invoked, this skill checks if AGENTS.md has been loaded for the current directory and loads it if not already present.

## Troubleshooting

**If AGENTS.md isn't loading automatically:**

1. **Manual invoke**: Say "load agent context"
2. **Check file location**: Ensure `AGENTS.md` is in current working directory (`pwd`)
3. **Check file permissions**: Ensure `AGENTS.md` is readable
4. **Use slash command**: Run `/sync-agent-context` to merge AGENTS.md into CLAUDE.md permanently

## Related Features

- **Slash Command**: `/sync-agent-context` - Permanently merges AGENTS.md into CLAUDE.md
- **Hook Script**: Runs on directory change to remind Claude to load context
- **Manual Loading**: Can always explicitly request "load AGENTS.md"

## Benefits

- **Zero configuration**: Just create `AGENTS.md` and it works
- **Project-specific rules**: Different agent behaviors per project
- **No CLAUDE.md pollution**: Keep agent-specific rules separate
- **Automatic synchronization**: Always up-to-date with current directory

---

**Status**: Proactive Auto-Loading Enabled
**Requires User Action**: No (automatic)
**Fallback**: Manual invocation if auto-loading fails
