# Team Configuration

## Team Configuration

### Shared Settings

```json
// Recommended team settings (share via repo)

// .vscode/settings.json
{
  // Cursor defaults for team
  "cursor.chat.defaultModel": "gpt-4-turbo",
  "cursor.completion.model": "gpt-3.5-turbo",

  // Formatting consistency
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",

  // Disable conflicting features
  "editor.suggest.showInlineDetails": false
}
```

### Team .cursorrules

```yaml
# .cursorrules (committed to repo)

team: engineering
project: main-product

standards:
  # Coding standards
  - TypeScript strict mode required
  - ESLint + Prettier formatting
  - Conventional commits

  # Documentation
  - JSDoc for public functions
  - README for each module
  - ADRs for decisions

  # Testing
  - Unit tests for business logic
  - Integration tests for APIs
  - 80% coverage minimum

patterns:
  # Follow company patterns
  - See @docs/patterns.md
  - Use shared components from @ui
```
