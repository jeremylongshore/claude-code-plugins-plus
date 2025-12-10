---
name: memory
version: 1.0.0
description: |
  Access and use project memories from previous sessions for context-aware assistance.
  Use when recalling past decisions, checking project conventions, or understanding user preferences.
  Trigger with phrases like "remember when", "like before", or "what was our decision about".
allowed-tools: Read, Write
license: MIT
---

## Prerequisites

Before using this skill, ensure you have:
- Project memory file at `{baseDir}/.memories/project_memory.json`
- Read permissions for the memory storage location
- Understanding that memories persist across sessions
- Knowledge of slash commands for manual memory management

## Instructions

### Step 1: Access Project Memories
Retrieve stored memories from previous sessions:
1. Locate memory file using Read tool
2. Parse JSON structure containing memory entries
3. Identify relevant memories based on current context
4. Extract applicable decisions, conventions, or preferences

### Step 2: Apply Memories to Current Context
Integrate past decisions into current work:
- Use remembered library/tool choices when making similar decisions
- Apply architectural patterns established in prior sessions
- Reference user preferences for coding style or conventions
- Consider past decisions as context for new features

### Step 3: Update Memories When Needed
Store new decisions for future reference:
- Add significant architectural choices
- Document tool or library selections with rationale
- Record user preferences and conventions
- Update changed decisions to avoid conflicts

### Step 4: Resolve Memory Conflicts
Handle situations where memories conflict with current requests:
- Prioritize current explicit user requests over stored memories
- Flag conflicts for user awareness when appropriate
- Update memories that have become outdated
- Remove memories that are no longer relevant

## Output

The skill provides seamless memory-enhanced responses:

### Silent Integration
- Memories applied automatically without announcement
- Decisions informed by historical context
- Consistent behavior aligned with past choices
- Natural incorporation of established patterns

### Memory Status
When using slash commands:
- List of all stored memories with timestamps
- Confirmation of newly added memories
- Notification of removed or updated memories
- Summary of applicable memories for current task

## Error Handling

Common issues and solutions:

**Memory File Not Found**
- Error: Cannot locate project memory file
- Solution: Initialize new memory file in standard location, prompt user to set up memory persistence

**Conflicting Memories**
- Error: Multiple memories contradict each other
- Solution: Apply most recent memory, allow current request to override, suggest cleanup

**Invalid Memory Format**
- Error: Memory file corrupted or improperly formatted
- Solution: Backup existing file, recreate with valid JSON structure, restore recoverable entries

**Permission Denied**
- Error: Cannot read or write memory file
- Solution: Check file permissions, request necessary access, use alternative storage location

## Resources

### Memory Management Commands
- `/remember [text]` - Add new memory to manual_memories array
- `/forget [text]` - Remove matching memory from storage
- `/memories` - Display all currently stored memories

### Best Practices
- Apply memories silently without announcing to user
- Current explicit requests always override stored memories
- Store significant decisions that affect future work
- Regularly review and clean up outdated memories
- Use memories as context, not rigid constraints

### Memory Categories
- **Architecture decisions**: Framework choices, design patterns
- **Tool selections**: Libraries, dependencies, build tools
- **Code conventions**: Style preferences, naming patterns
- **User preferences**: Communication style, detail level
- **Project constraints**: Performance targets, compatibility requirements

### Integration Guidelines
- Memory retrieval happens automatically during task analysis
- Memories inform recommendations and implementation choices
- User can override any memory-based decision at any time
- Regular memory updates keep context current and relevant
