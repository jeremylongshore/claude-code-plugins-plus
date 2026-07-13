# Local Data Storage

## Local Data Storage

### Where Data is Stored

```bash
# Local Cursor data locations

macOS:
~/Library/Application Support/Cursor/
~/Library/Caches/Cursor/

Linux:
~/.config/Cursor/
~/.cache/Cursor/

Windows:
%APPDATA%\Cursor\
%LOCALAPPDATA%\Cursor\

# Index location
~/.cursor/index/
```

### Clearing Local Data

```bash
# Clear cache only
rm -rf ~/Library/Caches/Cursor/

# Clear all local data (reset)
rm -rf ~/Library/Application\ Support/Cursor/

# Clear just the index
rm -rf ~/.cursor/index/
```
