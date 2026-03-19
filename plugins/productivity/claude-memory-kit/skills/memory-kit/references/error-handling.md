# Error Handling

## Error Scenarios

| Scenario | Command | Behavior |
|----------|---------|----------|
| MEMORY.md missing | memory-load | "No memory file found. Starting fresh." |
| MEMORY.md missing | memory-update | Create the file with proper section structure first, then append |
| MEMORY.md missing | memory-audit | "No MEMORY.md to audit." |
| MEMORY.md empty | memory-load | Treat as fresh — "Memory file is empty. Starting fresh." |
| No changes to audit | memory-audit | "All entries current. Nothing to prune." |
| Git push fails | memory-share | Report the error message, suggest manual resolution |
| No git repo | memory-share | "Not a git repository. memory-share requires git." |
| No staged changes | memory-share | Stage MEMORY.md automatically, then commit and push |
| Merge conflict on push | memory-share | Report conflict, suggest `git pull --rebase` then retry |

## Recovery

If MEMORY.md becomes corrupted (malformed markdown):
1. Check git log for the last good version: `git log --oneline MEMORY.md`
2. Restore: `git checkout HEAD~1 -- MEMORY.md`
3. Re-run `/memory-save` to capture current state fresh
