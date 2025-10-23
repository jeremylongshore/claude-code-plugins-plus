# Scripts Directory

**Professional DevOps script organization with flat structure and categorized naming.**

## Directory Structure

**FLAT STRUCTURE:** All scripts in single directory with no subdirectories.

**Total:** 33 files
- 3 documentation files (.md)
- 30 executable scripts (.sh, .py, .cjs, .pl)
- 0 subdirectories ✅

---

## Naming Convention

**Format:** `[category]-[purpose]-[descriptive-name].[ext]`

### Categories

| Prefix | Category | Purpose |
|--------|----------|---------|
| `archive-` | Archived | Historical/deprecated scripts |
| `audit-` | Auditing | Plugin validation and auditing |
| `automation-` | Automation | Automated workflows |
| `backup-` | Backup | Data backup operations |
| `build-` | Build | Build and sync operations |
| `enhance-` | Enhancement | Plugin enhancement scripts |
| `fix-` | Fixes | Bug fixes and corrections |
| `migrate-` | Migration | Data/config migration |
| `skills-` | Agent Skills | Skills generation and management |
| `test-` | Testing | Test and validation scripts |
| `util-` | Utilities | General-purpose utilities |
| `validate-` | Validation | Validation and checking |
| `verify-` | Verification | Verification operations |

---

## Scripts Inventory

### 📚 Documentation

```
PRODUCTION_SAFETY_GUIDE.md       # Production deployment safety guide
SKILLS_AUTOMATION.md             # Agent Skills automation documentation
TURSO-BACKUP-GUIDE.md            # Turso database backup guide
```

### 🔍 Auditing Scripts

```
audit-plugin-agents.sh           # Audit plugin agents
audit-plugin-commands.sh         # Audit slash commands
audit-plugin-directories.sh      # Audit directory structures
audit-plugin-manifests.sh        # Audit plugin.json files
audit-run-full.sh                # Run complete audit suite
```

### 🤖 Automation Scripts

```
automation-post-batch.sh         # Post-batch automation workflow
automation-trigger-post-batch.sh # Trigger post-batch automation
```

### 📦 Archive Scripts

```
archive-organize-docs.py         # Historical docs organization script
```

### 💾 Backup Scripts

```
backup-turso-database.sh         # Backup Turso SQLite database
```

### 🔨 Build Scripts

```
build-sync-marketplace.cjs       # Sync marketplace.json from extended
```

### ✨ Enhancement Scripts

```
enhance-add-agent-capabilities.sh # Add agent capabilities to plugins
enhance-cleanup-directories.sh    # Clean up empty directories
enhance-expand-content.sh         # Expand minimal plugin content
enhance-fix-emails.sh             # Fix placeholder email addresses
enhance-run-all.sh                # Run all enhancement scripts
```

### 🛠️ Fix Scripts

```
fix-plugin-manifests.sh          # Fix invalid plugin manifest fields
```

### 🔄 Migration Scripts

```
migrate-credentials.sh           # Credential migration script
```

### 🧠 Agent Skills Scripts

```
skills-enhancer-batch.py         # Batch Agent Skills enhancement
skills-enhancer-gcloud.sh        # GCloud-based skills enhancer
skills-generate-gemini.py        # Generate skills with Gemini API
skills-generate-vertex-safe.py   # Safe Vertex AI skills generator
skills-generate-vertex.py        # Vertex AI skills generator
skills-process-next.sh           # Process next plugin in queue
```

### 🧪 Testing Scripts

```
test-plugin-installation.sh      # Test plugin installation locally
```

### 🔧 Utility Scripts

```
util-remove-emojis.pl            # Remove emojis (Perl)
util-remove-emojis.py            # Remove emojis (Python)
util-remove-emojis.sh            # Remove emojis (Shell)
```

### ✅ Validation Scripts

```
validate-all-plugins.sh          # Validate all plugins
validate-frontmatter.py          # Validate YAML frontmatter
verify-skill-enhancements.sh     # Verify Agent Skills enhancements
```

---

## Common Operations

### Audit Plugins

```bash
# Run full audit
./audit-run-full.sh

# Audit specific component
./audit-plugin-manifests.sh
./audit-plugin-agents.sh
./audit-plugin-commands.sh
```

### Generate Agent Skills

```bash
# Safe Vertex AI generation (recommended)
python3 skills-generate-vertex-safe.py

# Process next plugin in queue
./skills-process-next.sh

# Batch enhancement
python3 skills-enhancer-batch.py --limit 10
```

### Validate Plugins

```bash
# Validate all plugins
./validate-all-plugins.sh

# Validate specific plugin
./validate-all-plugins.sh plugins/mcp/plugin-name/

# Validate frontmatter
python3 validate-frontmatter.py
```

### Enhance Plugins

```bash
# Run all enhancements
./enhance-run-all.sh

# Individual enhancements
./enhance-add-agent-capabilities.sh
./enhance-cleanup-directories.sh
./enhance-expand-content.sh
```

### Build & Sync

```bash
# Sync marketplace catalogs
node build-sync-marketplace.cjs
```

### Backup Operations

```bash
# Backup Turso database
./backup-turso-database.sh
```

---

## Script Dependencies

### Python Scripts (Python 3.11+)

```
skills-enhancer-batch.py
skills-generate-gemini.py
skills-generate-vertex-safe.py
skills-generate-vertex.py
validate-frontmatter.py
util-remove-emojis.py
archive-organize-docs.py
```

**Required packages:**
- google-cloud-aiplatform (Vertex AI)
- google-generativeai (Gemini)
- PyYAML (frontmatter validation)

### Shell Scripts (Bash 4.0+)

All `.sh` files require Bash 4.0+

**Common tools used:**
- jq (JSON processing)
- yq (YAML processing)
- git (version control)
- find, grep, sed (text processing)

### Node.js Scripts (Node 20+)

```
build-sync-marketplace.cjs
```

**Required packages:**
- Defined in project root package.json

### Perl Scripts (Perl 5.10+)

```
util-remove-emojis.pl
```

---

## Best Practices

### 1. Always Run Validation Before Committing

```bash
./validate-all-plugins.sh
```

### 2. Use Safe Mode for Production

```bash
# Use the -safe variant for production
python3 skills-generate-vertex-safe.py
```

### 3. Backup Before Bulk Operations

```bash
./backup-turso-database.sh
python3 skills-enhancer-batch.py --limit 100
```

### 4. Test Locally Before Deployment

```bash
./test-plugin-installation.sh
```

### 5. Sync Marketplace After Changes

```bash
node build-sync-marketplace.cjs
git diff .claude-plugin/marketplace.json  # Should show changes
```

---

## Script Permissions

All shell scripts must be executable:

```bash
# Make all scripts executable
chmod +x *.sh

# Verify permissions
ls -la *.sh | awk '{print $1, $NF}'
```

---

## Adding New Scripts

When adding new scripts:

1. **Use categorized naming:** `[category]-[purpose]-[name].[ext]`
2. **Save to scripts/ root** (NO subdirectories)
3. **Make executable:** `chmod +x script-name.sh`
4. **Add to this README** under appropriate category
5. **Document dependencies** if any

### Example

```bash
# Creating new validation script
cat > scripts/validate-plugin-structure.sh << 'EOF'
#!/bin/bash
# Validate plugin directory structure
EOF

chmod +x scripts/validate-plugin-structure.sh
```

Then add to README:

```markdown
### ✅ Validation Scripts

validate-plugin-structure.sh    # Validate plugin directory structure
```

---

## Troubleshooting

### Permission Denied

```bash
chmod +x script-name.sh
```

### Python Module Not Found

```bash
pip install -r requirements.txt  # If exists
pip install google-cloud-aiplatform google-generativeai PyYAML
```

### jq Command Not Found

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

### Script Not in PATH

```bash
# Run from scripts directory
cd scripts/
./script-name.sh

# Or use absolute path
/home/jeremy/000-projects/claude-code-plugins/scripts/script-name.sh
```

---

## Maintenance

### Regular Tasks

**Weekly:**
- Run `validate-all-plugins.sh`
- Check for script updates in upstream
- Review audit logs

**Monthly:**
- Run full audit suite
- Backup Turso database
- Review and archive old logs

**Per Release:**
- Sync marketplace catalogs
- Validate all plugins
- Test plugin installations

---

## Related Documentation

- **Production Safety:** `PRODUCTION_SAFETY_GUIDE.md`
- **Skills Automation:** `SKILLS_AUTOMATION.md`
- **Turso Backup:** `TURSO-BACKUP-GUIDE.md`
- **Main Documentation:** `../000-docs/`

---

**Last Updated:** 2025-10-20
**Total Scripts:** 33
**Subdirectories:** 0 (FLAT structure)
**Status:** ✅ Production-ready
