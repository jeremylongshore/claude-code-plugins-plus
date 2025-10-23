# Credential Migration Status
**Date:** 2025-10-19
**Target User:** admincostplus
**Source User:** jeremy

---

## ✅ Successfully Completed

### .env Files (Automated)
- **Status:** ✅ COMPLETE
- **Count:** 75+ files copied
- **Method:** Automated find/copy script
- **Locations:**
  - `/home/admincostplus/005-waygate-mcp/.env`
  - `/home/admincostplus/000-projects/bobs-brain/.env`
  - `/home/admincostplus/000-projects/hustle/.env`
  - `/home/admincostplus/000-projects/ccpiweb/.env`
  - `/home/admincostplus/000-projects/diagnostic-platform/DiagnosticPro/.env`
  - `/home/admincostplus/000-projects/intent-solutions-landing/.env`
  - And 60+ more across all projects

---

## ⚠️ Requires Manual Execution

### GPG Keys
- **Status:** ⚠️ MANUAL REQUIRED
- **Reason:** Sudo authentication in non-interactive mode
- **Source:** `/home/jeremy/.gnupg`
- **Target:** `/home/admincostplus/.gnupg`

### SSH Keys
- **Status:** ⚠️ MANUAL REQUIRED
- **Reason:** Sudo authentication in non-interactive mode
- **Source:** `/home/jeremy/.ssh`
- **Target:** `/home/admincostplus/.ssh`

### GCP Credentials
- **Status:** ⚠️ MANUAL REQUIRED
- **Reason:** Sudo authentication in non-interactive mode
- **Source:** `/home/jeremy/.config/gcloud`
- **Target:** `/home/admincostplus/.config/gcloud`

### Password Store (pass)
- **Status:** ⚠️ MANUAL REQUIRED
- **Source:** `/home/jeremy/.password-store` or `/home/jeremy/004-security/password-store`
- **Target:** `/home/admincostplus/.password-store`

### GitHub CLI Config
- **Status:** ⚠️ MANUAL REQUIRED
- **Source:** `/home/jeremy/.config/gh`
- **Target:** `/home/admincostplus/.config/gh`

---

## 🚀 How to Complete Migration

### Option 1: Run the Migration Script (Recommended)

```bash
# Navigate to the script
cd /home/jeremy/000-projects/claude-code-plugins

# Run with sudo (you'll be prompted for password: TheCitadel2003)
sudo bash COMPLETE-CREDENTIAL-MIGRATION.sh
```

### Option 2: Manual Commands

```bash
# Copy GPG keys
sudo cp -r /home/jeremy/.gnupg /home/admincostplus/
sudo chmod 700 /home/admincostplus/.gnupg
sudo chmod 600 /home/admincostplus/.gnupg/* 2>/dev/null

# Copy SSH keys
sudo cp -r /home/jeremy/.ssh /home/admincostplus/
sudo chmod 700 /home/admincostplus/.ssh
sudo chmod 600 /home/admincostplus/.ssh/id_* 2>/dev/null
sudo chmod 644 /home/admincostplus/.ssh/*.pub 2>/dev/null

# Copy GCP credentials
sudo mkdir -p /home/admincostplus/.config
sudo cp -r /home/jeremy/.config/gcloud /home/admincostplus/.config/

# Copy password store
sudo cp -r /home/jeremy/.password-store /home/admincostplus/
sudo chmod 700 /home/admincostplus/.password-store

# Copy GitHub CLI config
sudo cp -r /home/jeremy/.config/gh /home/admincostplus/.config/

# Set ownership for all copied files
sudo chown -R admincostplus:admincostplus /home/admincostplus
```

---

## 🔍 Verification Commands

After running the migration, verify everything was copied:

```bash
# Check .env files
find /home/admincostplus -name ".env*" -type f | wc -l
# Expected: 75+

# Check GPG
sudo ls -la /home/admincostplus/.gnupg
# Should see: pubring.kbx, trustdb.gpg, private-keys-v1.d/

# Check SSH
sudo ls -la /home/admincostplus/.ssh
# Should see: id_rsa, id_rsa.pub, known_hosts, config

# Check GCP
sudo ls -la /home/admincostplus/.config/gcloud
# Should see: configurations/, credentials.db, access_tokens.db

# Check password store
sudo ls -la /home/admincostplus/.password-store
# Should see: .gpg-id and password entries

# Test login as admincostplus
sudo su - admincostplus
gcloud auth list
ssh-add -l
pass ls
```

---

## 📋 Summary

**What's Done:**
- ✅ 75+ .env files copied and verified

**What's Needed:**
- ⚠️ Run `sudo bash COMPLETE-CREDENTIAL-MIGRATION.sh`
- ⚠️ Or manually execute the commands above

**Total Migration Time:** ~2 minutes

**Why Manual?**
Non-interactive shell cannot prompt for sudo password. The automated portion (copying .env files) completed successfully. The sensitive credentials (GPG, SSH, GCP) require sudo elevation which needs interactive password entry.

---

**Next Task After Migration:**
Reset admincostplus sudo password with:
```bash
sudo passwd admincostplus
# Enter: TheCitadel2003 (your main sudo password)
# Set new password: Admincostplus2003!
```
