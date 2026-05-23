# Team Configuration

## Team Configuration

### Shared Settings

```json
// .vscode/settings.json (committed)
{
  // Cursor AI Settings
  "cursor.completion.enabled": true,
  "cursor.chat.defaultModel": "gpt-4-turbo",

  // Editor Settings
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },

  // File Associations
  "files.associations": {
    ".cursorrules": "yaml"
  },

  // Search Exclusions (mirrors .cursorignore)
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/.next": true
  }
}
```

### Recommended Extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "prisma.prisma",
    "bradlc.vscode-tailwindcss",
    "eamodio.gitlens",
    "github.copilot"  // Optional, may conflict
  ],
  "unwantedRecommendations": [
    "visualstudioexptteam.vscodeintellicode"  // Conflicts with Cursor
  ]
}
```
