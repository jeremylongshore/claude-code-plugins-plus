# Troubleshooting

## Troubleshooting

**Issue:** Hooks are not running.

**Solution:** Make sure the hooks are executable:

```bash
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

**Issue:** Tests are failing immediately.

**Solution:** Ensure you have at least one passing test:

```bash
npm test # Should see: Tests passed
```

**Issue:** Lint errors are blocking everything.

**Solution:** Enable auto-fix:

```json
{
  "autoFix": true
}
```

Or fix manually:

```bash
npm run lint -- --fix
```
