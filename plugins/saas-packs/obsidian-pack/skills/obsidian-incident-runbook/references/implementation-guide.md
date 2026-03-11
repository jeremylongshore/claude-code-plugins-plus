# Obsidian Incident Runbook - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Quick Triage
```markdown


## Complete Examples

### Quick Health Check Script
```javascript
// Run in Obsidian console
(function checkPluginHealth() {
  const plugin = app.plugins.getPlugin('my-plugin-id');

  console.log('Plugin Status:');
  console.log('- Loaded:', !!plugin);
  console.log('- Enabled:', app.plugins.enabledPlugins.has('my-plugin-id'));

  if (plugin) {
    console.log('- Version:', plugin.manifest.version);
    console.log('- Settings valid:', !!plugin.settings);
  }

  console.log('\nRecent Errors:');
  // Check for recent errors in your error tracking
})();
```


## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Data loss/corruption | Immediate | Notes deleted, vault corrupted |
| P2 | Plugin unusable | < 1 hour | Crash on load, all features broken |
| P3 | Feature degraded | < 4 hours | One feature not working |
| P4 | Minor issue | Next release | UI glitch, minor inconvenience |


## Initial Assessment

1. **Identify the issue**
   - What is the user-reported symptom?
   - When did it start?
   - What changed (Obsidian update, plugin update, new plugins)?

2. **Check the basics**
   - [ ] Obsidian version?
   - [ ] Plugin version?
   - [ ] Desktop or mobile?
   - [ ] Operating system?

3. **Reproduce the issue**
   - [ ] Can you reproduce it?
   - [ ] Is it consistent or intermittent?
   - [ ] Does it happen in a new vault?
```

### Step 2: Gather Diagnostic Information
```markdown


## Diagnostic Commands

### In Obsidian (Ctrl/Cmd+Shift+I)

1. **Check Console for errors:**
   - Look for red error messages
   - Note any stack traces
   - Check for repeated errors

2. **Check plugin status:**
   ```javascript
   // In console
   app.plugins.getPlugin('my-plugin-id')
   ```

3. **Check settings:**
   ```javascript
   // View plugin settings
   app.plugins.getPlugin('my-plugin-id').settings
   ```

4. **Check loaded status:**
   ```javascript
   // Is plugin loaded?
   app.plugins.enabledPlugins.has('my-plugin-id')
   ```

### File System Checks

```bash
ls -la /path/to/vault/.obsidian/plugins/my-plugin/

cat /path/to/vault/.obsidian/plugins/my-plugin/manifest.json | jq .
cat /path/to/vault/.obsidian/plugins/my-plugin/data.json | jq .

ls -la /path/to/vault/.obsidian/plugins/my-plugin/*
```
```

### Step 3: Decision Tree
```
Plugin not loading?
├─ Error in console?
│   ├─ "Cannot find module" → Missing dependency, rebuild plugin
│   ├─ Syntax error → Check main.js, rebuild
│   ├─ "Plugin failed to load" → Check manifest.json
│   └─ Runtime error → Check onload() code
├─ No error, plugin enabled but not working?
│   ├─ Commands not appearing → Check addCommand() calls
│   ├─ Settings not showing → Check addSettingTab()
│   └─ Features not working → Check specific feature code
└─ Plugin not in list?
    ├─ Check .obsidian/plugins folder
    └─ Check community-plugins.json

Data corruption suspected?
├─ Settings corrupted → Delete data.json, restart
├─ Notes corrupted → Check recent vault backups
├─ Links broken → Run link consistency check
└─ Frontmatter corrupted → Parse and fix YAML
```

### Step 4: Common Fixes by Error Type

#### Plugin Fails to Load
```bash
cd /path/to/plugin
npm run build

rm /path/to/vault/.obsidian/plugins/my-plugin/data.json

rm -rf /path/to/vault/.obsidian/plugins/my-plugin
```

#### Settings Corrupted
```javascript
// In console - reset to defaults
const plugin = app.plugins.getPlugin('my-plugin-id');
plugin.settings = { /* DEFAULT_SETTINGS */ };
await plugin.saveSettings();
// Restart Obsidian
```

#### Crash on Specific File
```javascript
// Identify problematic file
// Check recent file-open events in console

// Test with specific file
const file = app.vault.getAbstractFileByPath('problematic/file.md');
const content = await app.vault.read(file);
// Check for unusual content/frontmatter
```

### Step 5: Emergency Procedures

#### P1: Data Loss Prevention
```bash
#!/bin/bash

VAULT_PATH="/path/to/vault"
BACKUP_PATH="/path/to/backup-$(date +%Y%m%d-%H%M%S)"

cp -r "$VAULT_PATH" "$BACKUP_PATH"
echo "Backup created at: $BACKUP_PATH"

echo '[]' > "$VAULT_PATH/.obsidian/community-plugins.json"
echo "All plugins disabled. Restart Obsidian."
```

#### P1: Vault Corruption Recovery
```markdown


## Vault Recovery Steps

1. **Stop Obsidian immediately**
   - Don't make any changes
   - Close all Obsidian windows

2. **Create backup of current state**
   ```bash
   cp -r /path/to/vault /path/to/vault-corrupted-backup
   ```

3. **Check for Obsidian sync backup**
   - Obsidian Sync: Settings > Sync > View version history
   - Manual: Check your backup solution

4. **Restore from backup**
   ```bash
   # If using git
   cd /path/to/vault
   git log --oneline -20  # Find good commit
   git checkout <commit>
   ```

5. **Disable plugins**
   - Start Obsidian in safe mode (hold Shift on startup)
   - Or manually: `echo '[]' > .obsidian/community-plugins.json`
```

### Step 6: Communication Templates

#### User Response Template
```markdown


## Response to User

Hi,

Thank you for reporting this issue. I'm sorry you're experiencing problems with [plugin name].

**What I understand:**
- [Summarize the issue]

**Immediate steps to try:**
1. [First thing to try]
2. [Second thing to try]

**Information I need:**
- Obsidian version (Settings > About)
- Plugin version
- Any error messages from Developer Console (Ctrl/Cmd+Shift+I)

**Workaround (if available):**
[Describe temporary workaround]

I'll investigate this as a priority and provide an update within [timeframe].
```

#### GitHub Issue Template
```markdown


## Bug Report

**Plugin:** [name] v[version]
**Obsidian:** v[version]
**OS:** [Windows/macOS/Linux]

### Issue Description
[Clear description]

### Steps to Reproduce
1.
2.
3.

### Expected Behavior
[What should happen]

### Actual Behavior
[What happens]

### Console Errors
```
[Paste errors]
```

### Additional Context
- Started after: [event/update]
- Frequency: [always/sometimes/once]
- Workaround: [if any]
```

### Step 7: Post-Incident Actions

#### Root Cause Analysis Template
```markdown


## Post-Incident Review

**Incident:** [Brief description]
**Date:** [Date]
**Duration:** [Time to resolution]
**Severity:** P[1-4]

### Timeline
- [Time] - Issue reported
- [Time] - Investigation started
- [Time] - Root cause identified
- [Time] - Fix deployed
- [Time] - Confirmed resolved

### Root Cause
[Technical explanation]

### Impact
- Users affected: [estimate]
- Data loss: [yes/no, details]

### Action Items
- [ ] [Preventive measure] - Due: [date]
- [ ] [Documentation update] - Due: [date]
- [ ] [Test coverage] - Due: [date]

### Lessons Learned
[What can we do better]
```
