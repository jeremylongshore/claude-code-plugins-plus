# Turso Backup System - Quick Start Guide

**Created:** 2025-10-19
**Purpose:** Protect claude-code-plugins repository against GitHub lockout
**Script:** `scripts/turso-plugin-backup.sh`

---

## 🎯 What This Does

Backs up your entire plugin repository to **Turso** (edge SQLite database) for off-site protection:

- ✅ All 235 plugins archived (tar.gz)
- ✅ Enhancement database (SQLite with AI generation history)
- ✅ Plugin metadata inventory (JSON)
- ✅ File integrity hashes (SHA256)
- ✅ Backup history tracking in Turso

**Why Turso?**
- Edge SQLite database (distributed globally)
- Free tier: 500 databases, 9GB storage, 1B row reads/month
- Git-like branching and point-in-time recovery
- CLI-first workflow (perfect for automation)

---

## 🚀 First-Time Setup

### Step 1: Authenticate with Turso

```bash
# Login to Turso (opens browser for GitHub auth)
turso auth login

# Verify authentication
turso db list
```

You should see: `✓ Logged in as <your-github-username>`

### Step 2: Run First Backup

```bash
cd /home/jeremy/000-projects/claude-code-plugins

# Make script executable (if not already)
chmod +x scripts/turso-plugin-backup.sh

# Run backup
./scripts/turso-plugin-backup.sh
```

**What happens:**
1. Creates Turso database: `claude-code-plugins-backup`
2. Archives all plugins → `backups/turso-sync/plugins-archive/plugins-YYYYMMDD-HHMMSS.tar.gz`
3. Copies enhancement database → `backups/turso-sync/enhancement-data/enhancements-YYYYMMDD-HHMMSS.db`
4. Generates plugin inventory → `backups/turso-sync/metadata/plugin-inventory.json`
5. Uploads metadata to Turso (stores backup record with file references)

**Expected output:**
```
==================================
  TURSO PLUGIN BACKUP SYSTEM
==================================

[SUCCESS] Turso authentication verified
[SUCCESS] Database 'claude-code-plugins-backup' already exists
[SUCCESS] Backup directory initialized: /home/jeremy/000-projects/claude-code-plugins/backups/turso-sync
[SUCCESS] Metadata created: 235 plugins
[SUCCESS] Archive created: plugins-20251019-234500.tar.gz (15M)
[SUCCESS] Enhancement database exported
[SUCCESS] Plugin inventory created
[SUCCESS] Backup record created in Turso (ID: 1)
[SUCCESS] Plugin metadata uploaded to Turso
[SUCCESS] File references stored in Turso

==================================
  TURSO BACKUP COMPLETE
==================================

Backup ID: 1
Database: claude-code-plugins-backup
Timestamp: Sun Oct 19 23:45:00 UTC 2025

View backup in Turso:
  turso db shell claude-code-plugins-backup
  SELECT * FROM backup_history WHERE id = 1;

To restore from this backup:
  ./scripts/turso-plugin-restore.sh 1
```

### Step 3: Verify Backup in Turso

```bash
# Open Turso shell
turso db shell claude-code-plugins-backup

# Check backup history
SELECT id, timestamp, plugin_count, version FROM backup_history;

# Check stored files
SELECT file_type, file_path, file_size FROM backup_files WHERE backup_id = 1;

# Check plugin metadata (first 5 plugins)
SELECT plugin_name, category, version FROM plugin_metadata WHERE backup_id = 1 LIMIT 5;

# Exit shell
.quit
```

---

## 🔄 Regular Backups

### Manual Backups

Run whenever you make significant changes:

```bash
cd /home/jeremy/000-projects/claude-code-plugins
./scripts/turso-plugin-backup.sh
```

**When to backup:**
- ✅ After adding new plugins
- ✅ After v1.2.0 release (235 plugins enhanced)
- ✅ After major restructuring
- ✅ Before risky operations
- ✅ After bulk updates (like overnight AI enhancement)

### Automated Backups (Recommended)

Add to crontab for daily backups at 2 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
0 2 * * * cd /home/jeremy/000-projects/claude-code-plugins && ./scripts/turso-plugin-backup.sh >> /home/jeremy/000-projects/claude-code-plugins/backups/turso-sync/backup.log 2>&1
```

**Alternative: Weekly backups (Sunday 3 AM):**
```bash
0 3 * * 0 cd /home/jeremy/000-projects/claude-code-plugins && ./scripts/turso-plugin-backup.sh >> /home/jeremy/000-projects/claude-code-plugins/backups/turso-sync/backup.log 2>&1
```

---

## 🔧 Restoring from Backup

### Step 1: List Available Backups

```bash
turso db shell claude-code-plugins-backup

SELECT
  id,
  timestamp,
  version,
  plugin_count,
  ROUND(archive_size / 1024.0 / 1024.0, 2) as size_mb
FROM backup_history
ORDER BY id DESC;
```

### Step 2: Create Restore Script (Future Enhancement)

**Note:** The restore script (`scripts/turso-plugin-restore.sh`) needs to be created. For now, manual restore process:

```bash
# 1. Find backup files locally
ls -lh backups/turso-sync/plugins-archive/
ls -lh backups/turso-sync/enhancement-data/

# 2. Extract specific backup
cd /tmp
tar -xzf /home/jeremy/000-projects/claude-code-plugins/backups/turso-sync/plugins-archive/plugins-YYYYMMDD-HHMMSS.tar.gz

# 3. Copy to fresh directory
mkdir -p /home/jeremy/000-projects/claude-code-plugins-RESTORE
cp -r /tmp/* /home/jeremy/000-projects/claude-code-plugins-RESTORE/

# 4. Restore enhancement database
cp backups/turso-sync/enhancement-data/enhancements-YYYYMMDD-HHMMSS.db backups/plugin-enhancements/enhancements.db
```

**Future TODO:** Create `scripts/turso-plugin-restore.sh` for automated restore.

---

## 📊 Backup Monitoring

### Check Backup Status

```bash
# View backup history
turso db shell claude-code-plugins-backup
SELECT * FROM backup_history ORDER BY id DESC LIMIT 5;

# Check latest backup
SELECT
  timestamp,
  plugin_count,
  ROUND(archive_size / 1024.0 / 1024.0, 2) as size_mb
FROM backup_history
ORDER BY id DESC
LIMIT 1;
```

### Check Disk Usage

```bash
# Local backup storage
du -sh backups/turso-sync/

# Turso database storage
turso db show claude-code-plugins-backup
```

### Verify File Integrity

```bash
# Get stored hash from Turso
turso db shell claude-code-plugins-backup
SELECT file_hash FROM backup_files WHERE file_type = 'plugins_archive' ORDER BY id DESC LIMIT 1;

# Calculate current hash
sha256sum backups/turso-sync/plugins-archive/plugins-YYYYMMDD-HHMMSS.tar.gz

# Hashes should match
```

---

## 🛡️ GitHub Lockout Recovery Plan

### If You Get Locked Out of GitHub

**You have THREE backup locations:**

1. **Local machine:** `/home/jeremy/000-projects/claude-code-plugins/`
2. **Local backups:** `/home/jeremy/000-projects/claude-code-plugins/backups/turso-sync/`
3. **Turso (off-site):** Cloud database with metadata + file references

### Recovery Steps

```bash
# 1. Query Turso for latest backup info
turso db shell claude-code-plugins-backup
SELECT * FROM backup_history ORDER BY id DESC LIMIT 1;
SELECT * FROM backup_files WHERE backup_id = (SELECT MAX(id) FROM backup_history);

# 2. Extract from local backup
cd ~
mkdir claude-code-plugins-RECOVERED
cd claude-code-plugins-RECOVERED
tar -xzf /home/jeremy/000-projects/claude-code-plugins/backups/turso-sync/plugins-archive/plugins-YYYYMMDD-HHMMSS.tar.gz

# 3. Restore enhancement database
mkdir -p backups/plugin-enhancements
cp /home/jeremy/000-projects/claude-code-plugins/backups/turso-sync/enhancement-data/enhancements-YYYYMMDD-HHMMSS.db backups/plugin-enhancements/enhancements.db

# 4. Initialize new git repo
git init
git add .
git commit -m "Restored from Turso backup - $(date)"

# 5. Create new GitHub repo and push
# (Manually create repo on GitHub first)
git remote add origin https://github.com/jeremylongshore/claude-code-plugins-NEW.git
git push -u origin main
```

---

## 🔍 Troubleshooting

### "Not logged in to Turso"

```bash
turso auth login
turso auth whoami  # Verify
```

### "Database already exists"

This is normal. Script will use existing database. To start fresh:

```bash
turso db destroy claude-code-plugins-backup
./scripts/turso-plugin-backup.sh  # Creates new database
```

### "Command not found: turso"

```bash
# Reinstall Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Add to PATH (if needed)
echo 'export PATH="$HOME/.turso:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Script hangs at "Creating plugins archive"

Large archive (15MB+) takes 10-30 seconds. Wait for completion.

### "No space left on device"

```bash
# Check disk usage
df -h

# Clean old backups (keep last 5)
cd backups/turso-sync/plugins-archive/
ls -t | tail -n +6 | xargs rm

cd ../enhancement-data/
ls -t | tail -n +6 | xargs rm
```

---

## 📈 Backup Metrics

### Current Repository Size

```bash
# Calculate repo size
du -sh /home/jeremy/000-projects/claude-code-plugins/

# Expected: ~50-100MB (with 235 plugins)
```

### Backup Size Expectations

- **Plugins archive:** 10-20MB (tar.gz compressed)
- **Enhancement database:** 1-5MB (SQLite)
- **Turso metadata:** <100KB (text data)

### Free Tier Limits (Turso)

- ✅ 500 databases (using 1)
- ✅ 9GB total storage (using <100MB)
- ✅ 1B row reads/month (using <1000)
- ✅ Unlimited databases and storage with Turso Starter ($29/mo)

**You're well within free tier limits.**

---

## 🎯 Next Steps

### Immediate (Now)

1. ✅ Authenticate: `turso auth login`
2. ✅ Run first backup: `./scripts/turso-plugin-backup.sh`
3. ✅ Verify in Turso: `turso db shell claude-code-plugins-backup`

### Short-term (This Week)

1. ⏳ Set up automated daily backups (cron)
2. ⏳ Run backup after v1.2.0 release completes
3. ⏳ Document backup ID for v1.2.0 milestone

### Long-term (Future)

1. 🔮 Create `scripts/turso-plugin-restore.sh` for automated restore
2. 🔮 Add backup status to release checklist
3. 🔮 Consider Turso branching for experimental features
4. 🔮 Integrate with `/ccpi-release` workflow

---

## 📚 Resources

- **Turso Docs:** https://docs.turso.tech/
- **Turso CLI Reference:** https://docs.turso.tech/cli
- **Turso GitHub:** https://github.com/tursodatabase/turso
- **Backup Script:** `scripts/turso-plugin-backup.sh`
- **This Guide:** `scripts/TURSO-BACKUP-GUIDE.md`

---

## 🔗 Related Documentation

- **Release Standards:** `/home/jeremy/.claude/commands/ccpi-release.md`
- **Release Plan v1.2.0:** `RELEASE-PLAN-AGENT-SKILLS-v1.2.0.md`
- **Enhancement System:** `scripts/SKILLS_AUTOMATION.md`
- **Repository CLAUDE.md:** `CLAUDE.md`

---

**Last Updated:** 2025-10-19
**Status:** ✅ Backup script ready, authentication required
**Next Action:** Run `turso auth login` and execute first backup
