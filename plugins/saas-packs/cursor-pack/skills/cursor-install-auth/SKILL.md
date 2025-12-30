---
name: cursor-install-auth
description: |
  Install Cursor IDE and configure authentication. Triggers on "install cursor",
  "setup cursor", "cursor authentication", "cursor login", "cursor license".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Installation & Authentication

## Installation Methods

### macOS
```bash
# Download from cursor.com or use Homebrew
brew install --cask cursor

# Verify installation
cursor --version
```

### Linux
```bash
# Download AppImage from cursor.com
chmod +x cursor-*.AppImage
./cursor-*.AppImage

# Or extract and install
./cursor-*.AppImage --appimage-extract
sudo mv squashfs-root /opt/cursor
sudo ln -s /opt/cursor/cursor /usr/local/bin/cursor
```

### Windows
```powershell
# Download installer from cursor.com
# Or use winget
winget install Cursor.Cursor
```

## Authentication Setup

### Sign In Options
1. **GitHub** - Recommended for developers
2. **Google** - Quick sign-in
3. **Email** - Traditional email/password

### First Launch Authentication
```
1. Launch Cursor
2. Click "Sign In" in bottom-left
3. Choose authentication method
4. Complete browser-based OAuth
5. Return to Cursor - automatically authenticated
```

## License Activation

### Free Tier
- 2000 completions/month
- 50 slow premium requests/month
- Basic AI features

### Pro Tier ($20/month)
- Unlimited completions
- 500 fast premium requests/month
- Priority support

### Business Tier ($40/user/month)
- Everything in Pro
- Admin dashboard
- SSO support
- Usage analytics

## API Key Configuration

### Using Your Own API Keys
```json
// Settings > Models > API Keys
{
  "openai": "sk-...",
  "anthropic": "sk-ant-...",
  "azure": {
    "apiKey": "...",
    "endpoint": "https://your-resource.openai.azure.com"
  }
}
```

### Model Selection with Custom Keys
- OpenAI: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- Anthropic: Claude 3.5 Sonnet, Claude 3 Opus
- Azure OpenAI: Your deployed models

## Verification Checklist

```
[ ] Cursor installed and launches
[ ] Signed in with preferred method
[ ] License tier confirmed (Free/Pro/Business)
[ ] API keys configured (if using own keys)
[ ] Test completion working
[ ] Settings synced (if applicable)
```

## Common Issues

### "Authentication Failed"
- Clear browser cache and retry
- Check firewall/proxy settings
- Try different auth method

### "License Not Found"
- Sign out and sign back in
- Check cursor.com account status
- Contact support if persists

### "API Key Invalid"
- Verify key hasn't expired
- Check key has correct permissions
- Ensure correct model access
