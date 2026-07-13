# Index Verification

## Index Verification

### Testing Index Works

```
Test 1: File search
Cmd+P > type filename > should appear instantly

Test 2: @codebase query
"@codebase where is the main function defined?"

Test 3: Symbol search
Cmd+Shift+O > type function name

Test 4: Reference finding
Right-click function > "Find All References"
```

### Index Health Check

```bash
# Check index size
du -sh ~/.cursor/index/

# Check index files
ls -la ~/.cursor/index/

# Clear and rebuild if corrupted
rm -rf ~/.cursor/index/
# Then reopen project and let it reindex
```
