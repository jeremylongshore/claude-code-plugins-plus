# Recommended Configurations

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
