---
name: obsidian-incident-runbook
description: |
  Troubleshoot Obsidian plugin failures with systematic incident response.
  Use when plugins crash, data is corrupted, or users report critical issues
  with your Obsidian plugin.
  Trigger with phrases like "obsidian crash", "obsidian plugin broken",
  "obsidian incident", "debug obsidian failure", "obsidian emergency".
allowed-tools: Read, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Incident Runbook

## Overview
Systematic procedures for diagnosing and resolving Obsidian failures: plugin crashes, vault corruption, sync conflicts, performance degradation, and broken CSS/themes. Each section is a self-contained runbook -- jump to the relevant one.

## Prerequisites
- Access to the affected Obsidian vault directory
- Developer Console access (Ctrl+Shift+I / Cmd+Option+I)
- Terminal access for filesystem operations
- Backup awareness (know where your backups are before making changes)

## Instructions

### Step 1: Quick Triage

Determine the category before diving in:

| Symptom | Category | Go to |
|---------|----------|-------|
| Obsidian crashes on open or plugin enable | Plugin crash | Step 2 |
| Notes missing, corrupted, or garbled | Vault corruption | Step 3 |
| Duplicate files, conflicting edits | Sync conflicts | Step 4 |
| Obsidian slow, high CPU/memory, lag while typing | Performance | Step 5 |
| UI elements missing, wrong colors, broken layout | CSS/Theme | Step 6 |

### Step 2: Plugin Crash Recovery

**Immediate: Enter Safe Mode**

If Obsidian crashes on startup, force safe mode:

```bash
VAULT_PATH=~/path/to/vault

# Option A: Disable all community plugins
echo '[]' > "$VAULT_PATH/.obsidian/community-plugins.json"

# Option B: Disable a specific suspect plugin
python3 -c "
import json
plugins = json.load(open('$VAULT_PATH/.obsidian/community-plugins.json'))
suspect = 'plugin-id-here'
if suspect in plugins:
    plugins.remove(suspect)
    json.dump(plugins, open('$VAULT_PATH/.obsidian/community-plugins.json', 'w'))
    print(f'Disabled {suspect}')
else:
    print(f'{suspect} not in active plugins')
"
```

Reopen Obsidian. If it loads, the disabled plugin was the cause.

**Diagnose from Console**

Open Developer Console (Ctrl+Shift+I) and look for errors:

```javascript
// Check for plugin load failures
Object.entries(app.plugins.manifests).forEach(([id, manifest]) => {
  const loaded = app.plugins.plugins[id];
  if (!loaded) console.error(`FAILED TO LOAD: ${id} v${manifest.version}`);
});

// Check for unhandled rejections in recent history
// (must be open before reproducing the issue)
window.addEventListener('unhandledrejection', (e) => {
  console.error('Unhandled rejection:', e.reason);
});
```

**Binary search for the offending plugin**

If multiple plugins could be the cause:

```bash
VAULT_PATH=~/path/to/vault
PLUGINS_FILE="$VAULT_PATH/.obsidian/community-plugins.json"

# Save original list
cp "$PLUGINS_FILE" "$PLUGINS_FILE.bak"

# Get all plugins
python3 -c "
import json
plugins = json.load(open('$PLUGINS_FILE'))
half = len(plugins) // 2

# Enable only first half
json.dump(plugins[:half], open('$PLUGINS_FILE', 'w'))
print(f'Enabled {half} of {len(plugins)} plugins: {plugins[:half]}')
print(f'Disabled: {plugins[half:]}')
print('Open Obsidian. If it crashes, problem is in first half. If stable, second half.')
"
```

Repeat halving until you isolate the single offending plugin.

### Step 3: Vault Corruption Recovery

**Check for corrupted files**

```bash
VAULT_PATH=~/path/to/vault

# Find files with null bytes (corruption indicator)
echo "=== Files with null bytes ==="
find "$VAULT_PATH" -name '*.md' -not -path '*/.obsidian/*' -exec grep -Pl '\x00' {} \;

# Find zero-byte files (likely lost content)
echo "=== Empty files ==="
find "$VAULT_PATH" -name '*.md' -not -path '*/.obsidian/*' -empty

# Find files with broken YAML frontmatter
echo "=== Broken frontmatter ==="
for f in "$VAULT_PATH"/*.md "$VAULT_PATH"/**/*.md; do
  [ -f "$f" ] || continue
  if head -1 "$f" | grep -q '^---' && ! awk '/^---/{c++; if(c==2) exit 0} END{exit (c<2)}' "$f"; then
    echo "  Unclosed frontmatter: $f"
  fi
done
```

**Recover from .trash**

Obsidian moves deleted files to `.trash/` in the vault:

```bash
# List recently deleted files
ls -lt "$VAULT_PATH/.trash/" 2>/dev/null | head -20

# Restore a specific file
cp "$VAULT_PATH/.trash/important-note.md" "$VAULT_PATH/recovered/"
```

**Recover from Git backup**

If the vault is under Git version control:

```bash
cd "$VAULT_PATH"

# See what changed recently
git log --oneline -20
git diff HEAD~1 --stat

# Restore a specific file to its last good state
git checkout HEAD~1 -- "path/to/corrupted-note.md"

# Restore the entire vault to last commit (DESTRUCTIVE -- stash first)
git stash
git checkout HEAD -- .
```

**Recover from filesystem snapshots**

```bash
# macOS Time Machine
tmutil listbackups 2>/dev/null | tail -5
# Then browse: /Volumes/TimeMachine/Backups.backupdb/.../path/to/vault

# Linux (btrfs snapshots)
ls /.snapshots/ 2>/dev/null
```

### Step 4: Sync Conflict Resolution

**Obsidian Sync conflicts**

Obsidian Sync creates conflict files named `Note (conflict YYYY-MM-DD).md`:

```bash
VAULT_PATH=~/path/to/vault

# Find all conflict files
echo "=== Sync Conflicts ==="
find "$VAULT_PATH" -name '*conflict*' -not -path '*/.obsidian/*'

# Compare a conflict with its original
ORIGINAL="$VAULT_PATH/Meeting Notes.md"
CONFLICT=$(find "$VAULT_PATH" -name "Meeting Notes*conflict*" | head -1)
if [ -n "$CONFLICT" ]; then
  diff "$ORIGINAL" "$CONFLICT"
fi
```

Resolution: Open both files in Obsidian, manually merge content into the original, delete the conflict file.

**Git sync conflicts**

```bash
cd "$VAULT_PATH"

# Check for merge conflicts
git status | grep 'both modified'

# For each conflicted file, resolve the conflict markers
# <<<<<<< HEAD
# (your changes)
# =======
# (their changes)
# >>>>>>> branch
grep -rl '<<<<<<< ' "$VAULT_PATH"/*.md 2>/dev/null
```

**Prevent future conflicts**

In `.obsidian/sync.json` or your Git workflow:
- Exclude `workspace.json` and `workspace-mobile.json` from sync (per-device files)
- Avoid editing the same note on two devices simultaneously
- For Git: commit and push frequently; pull before editing

### Step 5: Performance Degradation

**Diagnose the bottleneck**

```javascript
// Paste in Developer Console

// Check memory usage
console.log('Memory:', JSON.stringify(performance.memory, null, 2));

// Time plugin load
Object.entries(app.plugins.plugins).forEach(([id, plugin]) => {
  const start = performance.now();
  // Plugins are already loaded, but check their event listener count
  const events = plugin._events?.length || 0;
  console.log(`${id}: ${events} event listeners`);
});

// Check for expensive metadata cache operations
console.time('metadataCache');
const allFiles = app.vault.getMarkdownFiles();
allFiles.forEach(f => app.metadataCache.getFileCache(f));
console.timeEnd('metadataCache');
console.log(`Files scanned: ${allFiles.length}`);
```

**Disable plugins one by one**

Systematic approach to find the performance culprit:

```bash
VAULT_PATH=~/path/to/vault
PLUGINS_FILE="$VAULT_PATH/.obsidian/community-plugins.json"

# Save original
cp "$PLUGINS_FILE" "$PLUGINS_FILE.bak"

# Get plugin list
python3 -c "
import json
plugins = json.load(open('$PLUGINS_FILE'))
print('Current plugins:')
for i, p in enumerate(plugins):
    print(f'  {i}: {p}')
print(f'\nTotal: {len(plugins)} plugins')
print('\nTo disable one at a time:')
for p in plugins:
    without = [x for x in plugins if x != p]
    print(f'  Without {p}: {len(without)} remaining')
"
```

Then for each suspect:
1. Remove it from `community-plugins.json`
2. Restart Obsidian
3. Test performance
4. If improved, that plugin is the bottleneck
5. If unchanged, restore it and try the next

**Common performance fixes**
- Vault with 10,000+ files: disable Dataview's automatic refresh, use lazy loading
- Many backlinks: disable backlinks panel or set it to collapsed by default
- Large files (1MB+): split into smaller notes using note refactoring
- Too many plugins (20+): audit and remove unused plugins

### Step 6: CSS and Theme Issues

**Nuclear option: Reset all custom CSS**

```bash
VAULT_PATH=~/path/to/vault

# Disable all CSS snippets
python3 -c "
import json
try:
    a = json.load(open('$VAULT_PATH/.obsidian/appearance.json'))
    a['enabledCssSnippets'] = []
    a['cssTheme'] = ''  # Reset to default theme
    json.dump(a, open('$VAULT_PATH/.obsidian/appearance.json', 'w'), indent=2)
    print('Reset theme and disabled all snippets')
except Exception as e:
    print(f'Error: {e}')
"
```

Restart Obsidian. If the UI is fixed, re-enable snippets and theme one at a time.

**Check for CSS conflicts**

```bash
VAULT_PATH=~/path/to/vault

# Find snippets with aggressive selectors
for snippet in "$VAULT_PATH/.obsidian/snippets"/*.css; do
  [ -f "$snippet" ] || continue
  name=$(basename "$snippet")
  important_count=$(grep -c '!important' "$snippet" 2>/dev/null)
  if [ "$important_count" -gt 0 ]; then
    echo "$name: $important_count !important declarations"
  fi
done

# Check theme compatibility with current Obsidian version
THEME_DIR="$VAULT_PATH/.obsidian/themes"
for theme in "$THEME_DIR"/*/manifest.json; do
  [ -f "$theme" ] || continue
  python3 -c "
import json
m = json.load(open('$theme'))
print(f\"{m.get('name')}: minAppVersion={m.get('minAppVersion', 'unspecified')}\")
"
done
```

**Diagnose specific CSS problems**

In Developer Console:

```javascript
// Find which CSS rule is affecting a specific element
// Right-click the broken element -> Inspect
// In the Elements panel, check Computed styles and look for overrides

// Programmatically check for theme variable conflicts
const root = getComputedStyle(document.body);
const vars = [
  '--background-primary', '--background-secondary',
  '--text-normal', '--text-accent',
  '--interactive-accent', '--interactive-hover'
];
vars.forEach(v => console.log(`${v}: ${root.getPropertyValue(v)}`));
```

## Output
- Identified root cause of the incident
- Applied fix (plugin disabled, file recovered, conflict resolved, CSS reset)
- Documented what happened for future reference
- Preventive measures configured (backups, sync exclusions, performance monitoring)

## Error Handling
| Issue | Cause | Quick Fix |
|-------|-------|-----------|
| Console won't open (Obsidian crashes immediately) | Plugin error in `onload()` | Disable all plugins via filesystem (Step 2) |
| Can't access vault directory | Filesystem permissions | `chmod -R u+rw "$VAULT_PATH"` |
| Plugin won't disable via `community-plugins.json` | File locked by sync | Stop sync service, edit file, restart |
| Obsidian hangs (not crashing, just frozen) | Infinite loop in plugin | Force-quit (kill process), then disable suspect plugin |
| Safe mode still crashes | Core Obsidian issue, not plugins | Reinstall Obsidian; vault data is separate from app |
| Recovery file also corrupted | Filesystem-level issue | Check disk health (`fsck`, `diskutil`, `chkdsk`) |

## Examples

**Plugin crash on startup**: User reports Obsidian instantly closes after opening a vault. Enter safe mode by clearing `community-plugins.json` (Step 2). Reopen works. Binary search reveals `obsidian-excalidraw` conflicts with a newly installed `obsidian-kanban`. Disable one, report the conflict to both plugin authors.

**Missing notes after sync**: User opens vault on laptop, 20 notes are gone. Check `.trash/` -- empty. Check Git log -- notes were deleted in a commit from their phone. `git checkout HEAD~3 -- missing-folder/` restores them. Add the folder to selective sync to prevent mobile edits.

**Slow vault with 8,000 notes**: Obsidian takes 15 seconds to open and typing lags. Developer Console shows `metadataCache` taking 4 seconds. Disabling Dataview drops it to 1 second. Solution: configure Dataview to use manual refresh instead of auto-refresh, and add `dv.pages` limits to expensive queries.

## Resources
- [Obsidian Forum - Bug Reports](https://forum.obsidian.md/c/bug-reports/7)
- [Obsidian Discord - Help](https://discord.gg/obsidianmd)
- [Plugin Developer Documentation](https://docs.obsidian.md/Plugins)
- [Obsidian Safe Mode](https://help.obsidian.md/Extending+Obsidian/Safe+mode)
- [Obsidian Sync Troubleshooting](https://help.obsidian.md/Obsidian+Sync/Troubleshoot+Obsidian+Sync)

## Next Steps
For collecting detailed diagnostics to share with plugin developers, see `obsidian-debug-bundle`. For data backup and recovery strategies, see `obsidian-data-handling`.
