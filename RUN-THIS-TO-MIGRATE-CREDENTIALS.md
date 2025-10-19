# 🔐 Complete Credential Migration to admincostplus

**Date:** 2025-10-19
**Status:** Ready to execute

---

## What This Does

Copies ALL your credentials from `/home/jeremy` to `/home/admincostplus`:
- ✅ **75+ .env files** from all projects
- ✅ **GPG keys** from `~/.gnupg`
- ✅ **SSH keys** from `~/.ssh`
- ✅ **GCP credentials** from `~/.config/gcloud`
- ✅ **Password store** from `~/.password-store`
- ✅ **GitHub CLI config** from `~/.config/gh`

---

## Quick Start (One Command)

```bash
sudo bash /tmp/run-migration-now.sh
```

When prompted, enter your sudo password: **TheCitadel2003**

---

## What It Will Do

```
🔐 Starting credential migration to admincostplus...
📦 Copying .env files...
🔑 Copying GPG keys...
🔐 Copying SSH keys...
☁️  Copying GCP credentials...
🔒 Copying password store...
🐙 Copying GitHub CLI config...
👤 Setting ownership...

✅ Migration complete!

Verification:
  .env files: 75
  GPG: ✓
  SSH: ✓
  GCP: ✓
  Pass: ✓
```

---

## After Migration

### Test Login
```bash
sudo su - admincostplus
```

### Verify Credentials Work
```bash
# Test GCP
gcloud auth list

# Test SSH
ssh-add -l

# Test password store
pass ls

# Check .env files
find ~ -name ".env*" | wc -l
```

---

## Reset admincostplus Sudo Password

After migration, set the sudo password:

```bash
sudo passwd admincostplus
```

Enter your main sudo password (**TheCitadel2003**), then set new password for admincostplus:
- **Recommended:** `Admincostplus2003!`

---

## Full Project List (.env files being copied)

From your projects:
1. `/home/jeremy/005-waygate-mcp/.env`
2. `/home/jeremy/000-projects/bobs-brain/.env`
3. `/home/jeremy/000-projects/hustle/.env`
4. `/home/jeremy/000-projects/ccpiweb/.env`
5. `/home/jeremy/000-projects/diagnostic-platform/DiagnosticPro/.env`
6. `/home/jeremy/000-projects/intent-solutions-landing/.env`
7. `/home/jeremy/000-projects/blog/startaitools/.env`
8. And 60+ more from all your projects

---

## Alternative: Manual Step-by-Step

If you prefer to run commands individually:

```bash
# 1. Ensure home directory exists
sudo mkdir -p /home/admincostplus
sudo chown admincostplus:admincostplus /home/admincostplus

# 2. Copy .env files
sudo find /home/jeremy -name ".env*" -type f -exec bash -c '
    file="{}";
    relative_path="${file#/home/jeremy/}";
    target_dir="/home/admincostplus/$(dirname "$relative_path")";
    mkdir -p "$target_dir";
    cp "$file" "$target_dir/"
' \;

# 3. Copy GPG keys
sudo cp -r /home/jeremy/.gnupg /home/admincostplus/
sudo chmod 700 /home/admincostplus/.gnupg

# 4. Copy SSH keys
sudo cp -r /home/jeremy/.ssh /home/admincostplus/
sudo chmod 700 /home/admincostplus/.ssh
sudo chmod 600 /home/admincostplus/.ssh/id_* 2>/dev/null

# 5. Copy GCP credentials
sudo mkdir -p /home/admincostplus/.config
sudo cp -r /home/jeremy/.config/gcloud /home/admincostplus/.config/

# 6. Copy password store
sudo cp -r /home/jeremy/.password-store /home/admincostplus/
sudo chmod 700 /home/admincostplus/.password-store

# 7. Copy GitHub CLI config
sudo cp -r /home/jeremy/.config/gh /home/admincostplus/.config/

# 8. Set ownership
sudo chown -R admincostplus:admincostplus /home/admincostplus
```

---

## Troubleshooting

### "Permission denied"
You need to run with `sudo`. The script requires root privileges to:
- Access jeremy's GPG/SSH keys
- Create directories in /home/admincostplus
- Set ownership to admincostplus user

### "admincostplus user does not exist"
The user should exist. Verify with:
```bash
id admincostplus
```

If not, create it:
```bash
sudo useradd -m -s /bin/bash admincostplus
sudo usermod -aG sudo admincostplus
```

### "Cannot find .env files"
The script searches for any file matching `.env*` in /home/jeremy. If you have custom locations, edit the script to include them.

---

## Summary

**Run this one command:**
```bash
sudo bash /tmp/run-migration-now.sh
```

**Expected result:**
- All credentials copied to admincostplus
- All ownership set correctly
- All permissions configured securely

**Time required:** ~1-2 minutes

**Your sudo password:** TheCitadel2003

---

**Ready to run?** Just execute the command above and you're done! 🚀
