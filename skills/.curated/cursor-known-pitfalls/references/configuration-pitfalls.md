# Configuration Pitfalls

## Configuration Pitfalls

### Missing .cursorrules

```
PITFALL:
AI doesn't know your project conventions.
Inconsistent code generation.

SOLUTION:
- Always create .cursorrules for projects
- Include coding standards
- Document framework/library choices
- Add examples of preferred patterns
```

### Poor .cursorignore

```
PITFALL:
Indexing node_modules, build outputs.
Slow indexing, irrelevant search results.

SOLUTION:
- Create comprehensive .cursorignore
- Exclude all dependency folders
- Exclude build outputs
- Exclude large data files
```

### Settings Not Synced

```
PITFALL:
Different settings on different machines.
Inconsistent Cursor behavior.

SOLUTION:
- Enable Settings Sync
- Commit .vscode/settings.json to repo
- Document team settings
- Use workspace settings for project-specific
```
