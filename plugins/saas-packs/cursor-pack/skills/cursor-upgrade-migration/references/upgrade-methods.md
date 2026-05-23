# Upgrade Methods

## Upgrade Methods

### Auto-Update (Recommended)

```
Cursor auto-updates by default:
1. Notification appears when update ready
2. Click "Restart to Update"
3. Cursor restarts with new version
4. Settings preserved automatically
```

### Manual Update

#### macOS

```bash
# Download latest from cursor.com
# Or via Homebrew
brew upgrade --cask cursor
```

#### Linux

```bash
# Download new AppImage from cursor.com
chmod +x cursor-new-version.AppImage

# Replace old version
mv cursor-new-version.AppImage /opt/cursor/cursor.AppImage
```

#### Windows

```powershell
# Download installer from cursor.com
# Run installer - updates in place

# Or via winget
winget upgrade Cursor.Cursor
```
