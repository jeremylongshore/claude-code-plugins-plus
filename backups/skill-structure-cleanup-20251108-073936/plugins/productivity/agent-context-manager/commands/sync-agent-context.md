# Sync Agent Context - Slash Command

**Command**: `/sync-agent-context`

**Purpose**: Permanently merge all `AGENTS.md` files in the project into `CLAUDE.md` under a dedicated section, ensuring agent-specific instructions are always loaded alongside project context.

---

## What This Command Does

1. **Finds all AGENTS.md files** in the current project directory (searches recursively)
2. **Reads each AGENTS.md file** and extracts its content
3. **Updates CLAUDE.md** by adding or updating the "## Agent-Specific Instructions" section
4. **Maintains both files**: Keeps original AGENTS.md files as the source of truth
5. **Creates backup**: Saves a backup of CLAUDE.md before making changes

---

## Execution Steps

### Step 1: Find All AGENTS.md Files

Search the current project for all files named `AGENTS.md`:

```bash
find . -name "AGENTS.md" -type f
```

**Expected output**:
```
./AGENTS.md
./subproject/AGENTS.md
```

### Step 2: Read Each AGENTS.md File

For each found file, read its full content using the Read tool:

```markdown
File: ./AGENTS.md
Content: [full content of AGENTS.md]

File: ./subproject/AGENTS.md
Content: [full content of subproject AGENTS.md]
```

### Step 3: Check if CLAUDE.md Exists

```bash
if [ -f "./CLAUDE.md" ]; then
    echo "CLAUDE.md found - will update"
else
    echo "CLAUDE.md not found - will create new file"
fi
```

### Step 4: Create Backup of CLAUDE.md

```bash
cp CLAUDE.md CLAUDE.md.backup.$(date +%Y%m%d-%H%M%S)
```

**Example**: `CLAUDE.md.backup.20251023-143022`

### Step 5: Merge AGENTS.md into CLAUDE.md

Add or update the following section in CLAUDE.md:

```markdown
---

## Agent-Specific Instructions

<!-- AUTO-SYNCED from AGENTS.md files - Last updated: 2025-10-23 14:30:22 -->
<!-- Source files: ./AGENTS.md, ./subproject/AGENTS.md -->

### Root Directory Agent Rules (./AGENTS.md)

[Content from ./AGENTS.md]

### Subproject Agent Rules (./subproject/AGENTS.md)

[Content from ./subproject/AGENTS.md]

---
```

### Step 6: Verify and Report

```markdown
✅ Agent Context Sync Complete!

📋 Summary:
- Found 2 AGENTS.md files
- Created backup: CLAUDE.md.backup.20251023-143022
- Updated CLAUDE.md with agent-specific instructions

📂 Synced files:
1. ./AGENTS.md → CLAUDE.md (Section: Root Directory Agent Rules)
2. ./subproject/AGENTS.md → CLAUDE.md (Section: Subproject Agent Rules)

⚠️ Note: Original AGENTS.md files remain unchanged (source of truth)

💡 Next time you start Claude Code, both CLAUDE.md and AGENTS.md will be loaded automatically.
```

---

## When to Use This Command

**Use `/sync-agent-context` when:**

1. **Initial setup**: First time using agent-specific instructions
2. **AGENTS.md not auto-loading**: If the proactive skill isn't triggering
3. **Permanent merge desired**: Want agent rules always in CLAUDE.md
4. **Multiple AGENTS.md files**: Have agent rules across different directories
5. **Manual control preferred**: Want explicit control over when rules are merged

**Don't use this command if:**

- Automatic loading is working fine (skill handles it)
- You want AGENTS.md and CLAUDE.md to remain separate
- You frequently update AGENTS.md (would require re-running sync)

---

## Merge Strategy

### If "Agent-Specific Instructions" section exists in CLAUDE.md:

**Replace** the existing section with updated content from all AGENTS.md files.

```markdown
## Agent-Specific Instructions
<!-- OLD CONTENT - WILL BE REPLACED -->

↓↓↓ BECOMES ↓↓↓

## Agent-Specific Instructions
<!-- NEW CONTENT FROM AGENTS.MD FILES -->
```

### If "Agent-Specific Instructions" section doesn't exist:

**Append** new section to the end of CLAUDE.md.

```markdown
[Existing CLAUDE.md content]

---

## Agent-Specific Instructions
<!-- NEW SECTION ADDED -->
[Content from AGENTS.md files]
```

---

## Conflict Resolution

**If both CLAUDE.md and AGENTS.md have conflicting rules:**

The sync command will:
1. Keep original CLAUDE.md content intact
2. Add AGENTS.md content in dedicated section
3. Document in the header: "In case of conflicts, Agent-Specific Instructions take precedence"

**Example merged output**:

```markdown
# CLAUDE.md

## General Project Instructions
- Use TypeScript for all code (from original CLAUDE.md)

---

## Agent-Specific Instructions
<!-- In case of conflicts, these rules take precedence for agent workflows -->

- Use JavaScript for agent-generated code (from AGENTS.md)
```

**Result**: Agent workflows use JavaScript; manual work uses TypeScript

---

## Automated Sync (Future Enhancement)

**Not currently implemented**, but could be added:

```json
// plugin.json future enhancement
{
  "hooks": {
    "onFileChange": {
      "pattern": "**/AGENTS.md",
      "action": "run /sync-agent-context automatically"
    }
  }
}
```

This would auto-sync whenever AGENTS.md is modified.

---

## Examples

### Example 1: Single AGENTS.md File

**Before**:
```
project/
├── CLAUDE.md (200 lines)
└── AGENTS.md (50 lines)
```

**Run**: `/sync-agent-context`

**After**:
```
project/
├── CLAUDE.md (250 lines - merged)
├── CLAUDE.md.backup.20251023-143022 (original)
└── AGENTS.md (50 lines - unchanged)
```

### Example 2: Multiple AGENTS.md Files

**Before**:
```
project/
├── CLAUDE.md
├── AGENTS.md
└── packages/
    └── plugin-a/
        └── AGENTS.md
```

**Run**: `/sync-agent-context`

**After**:
```
CLAUDE.md now contains:
## Agent-Specific Instructions

### Root Directory Agent Rules
[Content from ./AGENTS.md]

### Package Plugin-A Agent Rules
[Content from ./packages/plugin-a/AGENTS.md]
```

---

## Best Practices

1. **Run sync after updating AGENTS.md**: Keep CLAUDE.md synchronized
2. **Review backup before sync**: Check `CLAUDE.md.backup.*` files if needed
3. **Maintain AGENTS.md as source**: Edit AGENTS.md, then re-run sync
4. **Use version control**: Commit both files to git after sync
5. **Document sync frequency**: Add comment in AGENTS.md: "Sync to CLAUDE.md: monthly"

---

## Troubleshooting

**Problem**: Sync command not found

**Solution**: Ensure plugin is installed:
```bash
/plugin install agent-context-manager@claude-code-plugins-plus
```

**Problem**: CLAUDE.md section duplicated

**Solution**: Sync command should replace, not duplicate. Check for:
- Multiple "## Agent-Specific Instructions" headers (manual edit error)
- Re-run sync to clean up duplicates

**Problem**: Backup files accumulating

**Solution**: Clean old backups periodically:
```bash
find . -name "CLAUDE.md.backup.*" -mtime +30 -delete
```

---

## Related Features

- **Auto-Loading Skill**: `agent-context-loader` - Automatically loads AGENTS.md
- **Hook Script**: `check-agents-md.sh` - Detects AGENTS.md on directory change
- **Manual Loading**: Say "load agent context" to trigger skill manually

---

**Status**: Manual Command
**Requires User Action**: Yes (type `/sync-agent-context`)
**Permanent**: Yes (persists in CLAUDE.md)
