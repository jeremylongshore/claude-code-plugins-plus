# Obsidian Common Errors - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Open Developer Console
Press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (macOS) to open Developer Tools.

### Step 2: Identify the Error
Check the Console tab for red error messages related to your plugin.

### Step 3: Match Error to Solutions Below
Find your error type and apply the fix.


## Complete Examples

### Debug Logging Helper
```typescript
// Add at top of main.ts for debugging
const DEBUG = true;

function debug(...args: any[]) {
  if (DEBUG) {
    console.log('[MyPlugin]', ...args);
  }
}

// Use throughout code
debug('Loading settings', this.settings);
debug('Processing file', file.path);
```

### Quick Diagnostic Commands
```typescript
// Add debug commands during development
this.addCommand({
  id: 'debug-dump-settings',
  name: 'Debug: Dump Settings',
  callback: () => {
    console.log('Settings:', JSON.stringify(this.settings, null, 2));
  }
});

this.addCommand({
  id: 'debug-list-views',
  name: 'Debug: List Open Views',
  callback: () => {
    const leaves = this.app.workspace.getLeavesOfType('markdown');
    console.log('Open views:', leaves.length);
    leaves.forEach(leaf => {
      console.log('-', leaf.view.file?.path);
    });
  }
});
```

### Escalation Path
1. Check Developer Console for errors
2. Collect evidence with `obsidian-debug-bundle`
3. Search [Obsidian Forum](https://forum.obsidian.md/)
4. Check [GitHub Issues](https://github.com/obsidianmd/obsidian-api/issues)
5. Ask in [Obsidian Discord](https://discord.gg/obsidianmd)
