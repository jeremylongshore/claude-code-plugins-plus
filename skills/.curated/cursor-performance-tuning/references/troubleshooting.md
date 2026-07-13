# Troubleshooting

## Troubleshooting

### Cursor Won't Start

```bash
# Start without extensions
cursor --disable-extensions

# Reset user data
rm -rf ~/Library/Application\ Support/Cursor/

# Clear GPU cache
cursor --disable-gpu
```

### Extreme Slowness

```
1. Disable all extensions
2. Open empty folder
3. If fast: extension or project issue
4. If slow: reinstall Cursor
```

### Memory Leak

```
Symptoms: Memory grows over time

Solutions:
1. Restart Cursor periodically
2. Find leaking extension
3. Report to Cursor/extension devs
4. Reduce open files
```
