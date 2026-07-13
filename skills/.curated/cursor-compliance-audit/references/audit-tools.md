# Audit Tools

## Audit Tools

### Automated Scanning

```bash
# Scan for secrets in codebase
git secrets --scan

# Check for exposed credentials
trufflehog filesystem --directory=.

# Review git history for secrets
git log --all --full-history -- "*.env"
```

### Configuration Verification

```bash
# Verify .cursorignore covers sensitive files
cat .cursorignore | grep -E "(env|secret|key|credential)"

# Check for sensitive files not excluded
find . -name "*.env*" -o -name "*.key" -o -name "*secret*" \
  | grep -v node_modules

# List files being indexed
# (Check Cursor index status in UI)
```

### Access Log Analysis

```
Review in Admin Dashboard:
- User login patterns
- Unusual access times
- Failed login attempts
- Admin action log
```
