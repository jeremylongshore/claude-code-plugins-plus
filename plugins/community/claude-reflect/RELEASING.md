# Release Process

## Version Bump Checklist

1. **Update version in these files:**
   - `.claude-plugin/plugin.json` — `"version": "X.Y.Z"`
   - `README.md` — version badge URL

2. **Update CHANGELOG.md** with new version section

3. **Update test count** in README.md badge if changed

4. **Run validation:**
   ```bash
   claude plugin validate .
   python -m pytest tests/ -v
   ```

## Versioning (Semantic Versioning)

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backward-compatible)
- **PATCH** (0.0.X): Bug fixes

## Files to Update

| File | Field |
|------|-------|
| `.claude-plugin/plugin.json` | `version` |
| `README.md` | Version badge, test count badge |
| `CHANGELOG.md` | New version section at top |

## Commit & Release

```bash
# Stage and commit
git add -A
git commit -m "chore: Release vX.Y.Z"

# Tag and push
git tag vX.Y.Z
git push origin main --tags
```

## Plugin Validation

```bash
claude plugin validate .
```

Common warnings:
- `metadata.description` — Add description to marketplace.json (optional)
