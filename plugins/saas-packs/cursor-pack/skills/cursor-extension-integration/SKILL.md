---
name: cursor-extension-integration
description: |
  Integrate VS Code extensions with Cursor. Triggers on "cursor extensions",
  "cursor vscode extensions", "cursor plugins", "cursor marketplace".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Extension Integration

## Extension Compatibility

### What Works
```
Most VS Code extensions work in Cursor:
- Language extensions (syntax, snippets)
- Themes and icons
- Formatters (Prettier, ESLint)
- Git extensions (GitLens)
- Debug extensions
- Framework tools (Tailwind, Prisma)
```

### What May Conflict
```
Extensions to disable or avoid:
- GitHub Copilot (conflicts with Cursor AI)
- TabNine (conflicts with completions)
- IntelliCode (conflicts with suggestions)
- Other AI coding assistants
```

## Installing Extensions

### From Marketplace
```
1. Open Extensions panel: Cmd+Shift+X
2. Search for extension
3. Click Install
4. Reload if prompted
```

### From Command Line
```bash
# Install extension
cursor --install-extension <extension-id>

# Example
cursor --install-extension esbenp.prettier-vscode
cursor --install-extension dbaeumer.vscode-eslint

# List installed extensions
cursor --list-extensions

# Uninstall extension
cursor --uninstall-extension <extension-id>
```

### From VSIX File
```bash
# Install from local file
cursor --install-extension path/to/extension.vsix

# Useful for:
- Private extensions
- Specific versions
- Offline installation
```

## Essential Extensions

### Code Quality
```
ESLint (dbaeumer.vscode-eslint)
- Integrates ESLint into Cursor
- Real-time linting
- Auto-fix on save

Prettier (esbenp.prettier-vscode)
- Code formatting
- Consistent style
- Format on save

SonarLint (sonarsource.sonarlint-vscode)
- Security issues
- Code smells
- Best practices
```

### Language Support
```
TypeScript:
- Built-in (no extension needed)

Python:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)

Go:
- Go (golang.go)

Rust:
- rust-analyzer (rust-lang.rust-analyzer)

Java:
- Language Support (redhat.java)
```

### Framework Extensions
```
React/Next.js:
- ES7+ Snippets (dsznajder.es7-react-js-snippets)
- Auto Import (steoates.autoimport)

Tailwind CSS:
- Tailwind IntelliSense (bradlc.vscode-tailwindcss)

Prisma:
- Prisma (prisma.prisma)

Docker:
- Docker (ms-azuretools.vscode-docker)
```

### Git Extensions
```
GitLens (eamodio.gitlens)
- Inline blame
- File history
- Compare branches
- Commit details

Git Graph (mhutchie.git-graph)
- Visual branch graph
- Easy checkout/merge
```

## Recommended Configurations

### .vscode/extensions.json
```json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "prisma.prisma",
    "eamodio.gitlens"
  ],
  "unwantedRecommendations": [
    "github.copilot",
    "github.copilot-chat"
  ]
}
```

### Per-Extension Settings
```json
// settings.json
{
  // Prettier
  "prettier.singleQuote": true,
  "prettier.trailingComma": "es5",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },

  // ESLint
  "eslint.validate": ["javascript", "typescript"],
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },

  // Tailwind
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  },

  // GitLens
  "gitlens.hovers.currentLine.over": "line",
  "gitlens.codeLens.enabled": false
}
```

## Managing Conflicts

### Cursor AI vs Other AI
```
Disable conflicting extensions:
1. Extensions panel (Cmd+Shift+X)
2. Find Copilot/TabNine/IntelliCode
3. Click "Disable"
4. Reload Cursor

Or via settings:
{
  "github.copilot.enable": {
    "*": false
  }
}
```

### Completion Conflicts
```
If completions behave strangely:

1. Disable other suggestion providers:
{
  "editor.suggest.showMethods": false,
  // from non-Cursor sources
}

2. Ensure Cursor completions enabled:
{
  "cursor.completion.enabled": true,
  "editor.inlineSuggest.enabled": true
}

3. Check extension interference:
- Disable extensions one by one
- Find the conflicting one
- Keep disabled or configure
```

### Keybinding Conflicts
```
Find conflicts:
1. Cmd+K Cmd+S (Keyboard Shortcuts)
2. Search for conflicting key
3. See which extensions bind it
4. Rebind as needed

Common conflicts:
- Cmd+K (Cursor inline edit)
- Cmd+L (Cursor chat)
- Tab (completions)
```

## Extension Development

### Using Extensions with Cursor AI
```
Ask AI about extensions:
"How do I configure ESLint to work with TypeScript?"
"What GitLens settings improve blame visibility?"
"Help me set up Tailwind IntelliSense for CSS modules"
```

### Creating Custom Extensions
```
Cursor supports VS Code extension development:

1. Generate extension:
   yo code

2. Develop with Cursor
3. Test with F5 (Extension Host)
4. Package:
   vsce package
5. Install in Cursor
```

## Performance Optimization

### Reducing Extension Overhead
```
Disable when not needed:
- Project-specific extensions
- Heavy language servers
- Visual decorations

Check extension impact:
- Help > Process Explorer
- Look for high CPU extensions
```

### Workspace-Specific Extensions
```json
// .vscode/settings.json
{
  // Enable only for this workspace
  "extensions.autoUpdate": "onlyEnabledExtensions",
  "extensions.ignoreRecommendations": true
}
```

### Remote/SSH Considerations
```
When using remote development:
- Install extensions on remote
- Minimize local extensions
- Use extension packs
```

## Syncing Extensions

### Settings Sync
```
Enable sync for extensions:
1. Settings Sync (Gear icon)
2. Enable "Extensions"
3. Sign in
4. Sync across machines

Select what to sync:
- Extension list
- Extension settings
- Keybindings
```

### Manual Export/Import
```bash
# Export extensions list
cursor --list-extensions > extensions.txt

# Import on new machine
cat extensions.txt | xargs -L 1 cursor --install-extension
```

## Troubleshooting

### Extension Not Working
```
Steps:
1. Check compatibility (VS Code version)
2. Reload Cursor (Cmd+Shift+P > Reload)
3. Check extension output (Output panel)
4. Disable/enable extension
5. Reinstall extension
6. Check for updates
```

### Extension Causing Issues
```
Isolate the problem:
1. Disable all extensions
   cursor --disable-extensions
2. Test Cursor
3. Enable extensions one by one
4. Find problematic extension
5. Report to extension author
```

### Extension Settings Reset
```bash
# Reset extension data
rm -rf ~/.cursor/extensions/[extension-name]/

# Or reinstall
cursor --uninstall-extension [id]
cursor --install-extension [id]
```
