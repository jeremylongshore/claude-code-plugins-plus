---
name: cursor-common-errors
description: |
  Troubleshoot common Cursor IDE errors and issues. Triggers on "cursor error",
  "cursor not working", "cursor issue", "cursor problem", "fix cursor".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Common Errors & Solutions

## Authentication Errors

### "Authentication Failed"
```
Symptoms: Can't sign in, "Authentication failed" message

Solutions:
1. Clear browser cookies and cache
2. Try different auth method (GitHub/Google/Email)
3. Check firewall/VPN settings
4. Verify account at cursor.com
5. Restart Cursor completely
```

### "Session Expired"
```
Symptoms: Logged out unexpectedly, features stop working

Solutions:
1. Sign out and sign back in
2. Check internet connection
3. Verify subscription status
4. Clear Cursor cache: Cmd+Shift+P > "Clear Cache"
```

## Completion Errors

### "Completions Not Appearing"
```
Symptoms: No ghost text, Tab does nothing

Checklist:
[ ] Check rate limits (status bar)
[ ] Verify completion is enabled (Settings)
[ ] Check network connectivity
[ ] Restart Cursor
[ ] Check file type is supported

Settings to verify:
{
  "cursor.completion.enabled": true,
  "editor.inlineSuggest.enabled": true
}
```

### "Slow Completions"
```
Symptoms: Long delay before suggestions appear

Solutions:
1. Switch to faster model (GPT-3.5-turbo)
2. Check network latency
3. Reduce context size
4. Close unused tabs
5. Check CPU usage
```

### "Wrong/Irrelevant Completions"
```
Symptoms: Suggestions don't match context

Solutions:
1. Add better comments/docstrings
2. Update .cursorrules file
3. Re-index codebase
4. Clear chat context
5. Verify correct language mode
```

## Indexing Errors

### "Indexing Failed"
```
Symptoms: @codebase doesn't work, search fails

Solutions:
1. Check disk space
2. Exclude large folders (.git, node_modules)
3. Restart indexing: Cmd+Shift+P > "Reindex"
4. Check file permissions
5. Reduce codebase size if too large

Exclusions (.cursorignore):
node_modules/
.git/
dist/
build/
*.lock
```

### "Indexing Stuck"
```
Symptoms: Progress bar frozen, never completes

Solutions:
1. Cancel and restart indexing
2. Clear index cache
3. Check for circular symlinks
4. Exclude problematic directories
5. Restart Cursor
```

## API Key Errors

### "Invalid API Key"
```
Symptoms: "API key invalid" message

Checklist:
[ ] Key hasn't expired
[ ] Key has correct permissions
[ ] Key is for correct service (OpenAI/Anthropic)
[ ] No extra spaces in key
[ ] Account has credits/active subscription
```

### "Rate Limited"
```
Symptoms: "Rate limit exceeded" errors

Solutions:
1. Wait for limit reset (usually hourly)
2. Upgrade plan for higher limits
3. Use your own API key
4. Switch to different model
5. Reduce request frequency
```

## Extension Conflicts

### "Extensions Not Working"
```
Symptoms: VS Code extensions behave differently

Common conflicts:
- Copilot (disable one or the other)
- TabNine
- IntelliCode
- Other AI assistants

Solution: Disable conflicting extensions
```

### "Keybinding Conflicts"
```
Symptoms: Shortcuts don't work, wrong actions

Debug steps:
1. Cmd+K Cmd+S > Search for shortcut
2. Identify conflicts
3. Rebind conflicting keys
4. Check extension keybindings
```

## Performance Errors

### "High CPU Usage"
```
Symptoms: Cursor uses 100% CPU, system slow

Solutions:
1. Disable unused extensions
2. Close unused tabs
3. Exclude large folders from watch
4. Reduce completion model complexity
5. Check for infinite loops in extensions

Settings:
{
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.git/**": true
  }
}
```

### "High Memory Usage"
```
Symptoms: Cursor using GB of RAM

Solutions:
1. Restart Cursor
2. Close unused workspaces
3. Limit search scope
4. Disable memory-heavy extensions
5. Reduce open files
```

## Chat Errors

### "Chat Not Responding"
```
Symptoms: Messages not sent, spinning forever

Solutions:
1. Check network connection
2. Verify API key/subscription
3. Start new chat (Cmd+Shift+L)
4. Check rate limits
5. Restart Cursor
```

### "Context Too Large"
```
Symptoms: "Context length exceeded" error

Solutions:
1. Start new chat
2. Select less code
3. Be more specific in @-mentions
4. Remove unnecessary context
5. Use summary instead of full files
```

## Crash Recovery

### Cursor Crashes on Launch
```
Solutions:
1. Start with extensions disabled:
   cursor --disable-extensions

2. Reset user data:
   rm -rf ~/Library/Application\ Support/Cursor/

3. Reinstall Cursor

4. Check system requirements
```

### Unsaved Work Lost
```
Recovery options:
1. Check backup folder:
   ~/Library/Application Support/Cursor/Backups/

2. Check git stash:
   git stash list

3. Check local history:
   Right-click file > "Local History"
```

## Error Log Locations

### Finding Logs
```bash
# macOS
~/Library/Logs/Cursor/

# Linux
~/.config/Cursor/logs/

# Windows
%APPDATA%\Cursor\logs\

# View in Cursor
Help > Toggle Developer Tools > Console
```

### Reporting Issues
```
Include:
- Cursor version (Help > About)
- OS version
- Error message
- Steps to reproduce
- Relevant logs
```
