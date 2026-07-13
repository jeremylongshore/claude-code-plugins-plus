# Granola Detailed Error Reference

## Processing Issues

### Error: "Notes Not Appearing"

**Symptoms:** Meeting ended but no notes generated

| Timeframe | Action |
|-----------|--------|
| < 2 min | Wait - processing takes time |
| 2-5 min | Check internet connection |
| 5-10 min | Restart Granola app |
| > 10 min | Contact support |

### Error: "Processing Failed"

**Symptoms:** Error message after meeting
**Causes:**

- Audio file corrupted
- Meeting too short (< 2 min)
- Server issues
- Storage full

**Solutions:**

1. Check Granola status page
2. Verify sufficient disk space
3. Try re-uploading if option available
4. Contact support with meeting ID

## Integration Issues

### Error: "Zapier Connection Lost"

**Symptoms:** Automations not triggering

1. Open Zapier dashboard
2. Find Granola connection
3. Click "Reconnect"
4. Re-authorize access
5. Test Zap manually

### Error: "Slack/Notion Sync Failed"

**Symptoms:** Notes not appearing in connected apps

1. Check integration status in Settings
2. Verify target workspace permissions
3. Re-authenticate if expired
4. Check target channel/database exists

## App Issues

### Error: "App Won't Start"

**macOS:**

```bash
set -euo pipefail
# Force quit Granola
killall Granola

# Clear preferences (caution: resets settings)
rm -rf ~/Library/Preferences/com.granola.*
rm -rf ~/Library/Application\ Support/Granola

# Reinstall
brew reinstall granola
```

**Windows:**

1. Task Manager > End Granola process
2. Settings > Apps > Granola > Repair
3. If repair fails, uninstall and reinstall

### Error: "Update Failed"

1. Close Granola completely
2. Download latest from granola.ai/download
3. Install over existing version
4. Restart computer if needed

## Error Code Reference

| Code | Meaning | Action |
|------|---------|--------|
| E001 | Authentication failed | Re-login to Granola |
| E002 | Audio capture error | Check microphone |
| E003 | Network error | Check internet |
| E004 | Processing timeout | Retry or contact support |
| E005 | Storage full | Free up disk space |
| E006 | Calendar sync error | Reconnect calendar |

## When to Contact Support

- Errors persist after troubleshooting
- Data loss or corruption
- Billing issues
- Feature requests

**Support:** help@granola.ai
