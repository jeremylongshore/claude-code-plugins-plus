# Security Best Practices

## Security Best Practices

### Secure Storage

```
DO:
- Use environment variables
- Use secrets managers
- Encrypt backup files
- Restrict file permissions

DON'T:
- Hardcode in settings.json
- Commit to version control
- Share in plain text
- Use in screenshots
```

### File Permissions

```bash
# Secure settings file
chmod 600 ~/.config/Cursor/User/settings.json

# Verify permissions
ls -la ~/.config/Cursor/User/settings.json
# Should show: -rw------- (owner read/write only)
```

### Key Rotation

```
Regular rotation schedule:
- Development keys: Every 90 days
- Production keys: Every 30 days
- After any potential exposure: Immediately

Rotation process:
1. Generate new key from provider
2. Update in Cursor settings
3. Verify functionality
4. Revoke old key
5. Document rotation
```
