# Privacy Mode

## Privacy Mode

### Understanding Privacy Mode

```
Privacy Mode OFF (default):
- Full AI features enabled
- Code sent to AI providers for processing
- Best completions and suggestions
- Chat with full context

Privacy Mode ON:
- Limited AI features
- Code NOT sent to external AI
- Only local processing
- Reduced functionality
```

### Enabling Privacy Mode

```
Global:
Settings > Cursor > Privacy Mode > Enable

Per-workspace:
Add to .vscode/settings.json:
{
  "cursor.privacy.enabled": true
}
```

### When to Use Privacy Mode

```
Enable for:
- Proprietary algorithms
- Security-sensitive code
- Compliance requirements
- Client confidential work
- Pre-release features

Keep disabled for:
- Open source projects
- General development
- Learning/tutorials
- Public APIs
```
