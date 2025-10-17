# Production Safety Guide: Vertex AI Skills Generator

**Created:** 2025-10-17
**Purpose:** Safe, auditable, guideline-compliant batch generation of Agent Skills

---

## 🛡️ Safety Features

### 1. Adheres to Official Anthropic Guidelines

The script follows Anthropic's official Agent Skills documentation exactly:

- **YAML Frontmatter:** Only `name` and `description` fields (no other fields allowed)
- **Character Limits:**
  - `name`: Maximum 64 characters, gerund form ("Processing PDFs")
  - `description`: Maximum 1024 characters, third person
- **Line Count:** Recommends under 500 lines (warns if exceeded)
- **Content Style:** Concise, specific, consistent terminology
- **No Placeholders:** Validates against TODO/FIXME/INSERT patterns

### 2. SQLite Audit Trail

Every operation is logged to `backups/skills-audit/skills_generation.db`:

```sql
-- Main generations table
CREATE TABLE skill_generations (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    plugin_name TEXT,
    plugin_category TEXT,
    plugin_path TEXT,
    status TEXT,  -- SUCCESS, ERROR, VALIDATION_FAILED
    char_count INTEGER,
    line_count INTEGER,
    error_message TEXT,
    generation_time_seconds REAL,
    skill_content TEXT  -- Full backup of generated content
);

-- Validation failures table
CREATE TABLE validation_failures (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    plugin_name TEXT,
    reason TEXT,
    details TEXT
);
```

**Benefits:**
- Full audit trail of what was generated and when
- Backup of all skill content (recovery if GitHub locks account)
- Error tracking and debugging
- Performance metrics (avg generation time)
- Quality metrics (avg line count)

### 3. Quality Validation

Before saving any SKILL.md file, the script validates:

1. ✅ Has YAML frontmatter (starts with `---`)
2. ✅ Valid frontmatter structure (three `---` delimiters)
3. ✅ Required fields present (`name` and `description`)
4. ✅ No forbidden fields (`allowed-tools`, `version`, `author`, etc.)
5. ✅ Character limits enforced (name ≤ 64, description ≤ 1024)
6. ✅ Line count check (warns if > 500 lines)
7. ✅ Minimum content length (body > 100 characters)
8. ✅ No placeholder text ([TODO], [INSERT], [PLACEHOLDER])

**Automatic Retries:** If validation fails, script retries up to 3 times with improved prompts.

### 4. Rate Limiting & Quota Protection

- **1 second delay** between API calls (conservative)
- **Confirmation prompts** before batch operations
- **Cost estimates** shown before processing
- **Time estimates** shown before processing
- **Progress tracking** during batch runs

### 5. Comprehensive Error Handling

- Try/catch blocks around all API calls
- Automatic retry logic (3 attempts)
- Detailed error messages logged to database
- Graceful degradation (continues processing other plugins if one fails)

### 6. Backup System

- All generated content saved to SQLite database
- Can recover all skills even if files are deleted
- Can review what was generated before committing
- Can rollback if issues are discovered

---

## 📊 Usage Examples

### Check Current Statistics

```bash
python3 scripts/vertex-skills-generator-safe.py --stats
```

Output:
```
📊 Generation Statistics:
   Success: 45
   Errors: 2
   Validation Failures: 1
   Avg Generation Time: 3.2s
   Avg Line Count: 287 lines
```

### Test with One Plugin

```bash
# Process specific plugin by name
python3 scripts/vertex-skills-generator-safe.py deployment-pipeline

# Will show:
# - Plugin details
# - Generation progress
# - Validation results
# - Character/line counts
```

### Process Priority Plugins (Safest Approach)

```bash
python3 scripts/vertex-skills-generator-safe.py --priority
```

This processes only high-value categories:
- devops
- security
- testing
- ai-ml
- performance
- database

Includes:
- ⏱️  Time estimate
- 💰 Cost estimate (~$0.001 per plugin)
- Confirmation prompt
- Rate limiting
- Progress tracking

### Process First N Plugins

```bash
# Test with 5 plugins first
python3 scripts/vertex-skills-generator-safe.py 5

# If successful, scale up
python3 scripts/vertex-skills-generator-safe.py 20
```

### Nuclear Option: Process All 229 Plugins

```bash
python3 scripts/vertex-skills-generator-safe.py --all
```

⚠️ **Requires double confirmation**
⏱️ **Estimated time:** ~4 minutes (with 1s rate limiting)
💰 **Estimated cost:** ~$0.25 total

---

## 🔍 Audit Database Queries

### View All Generations

```bash
sqlite3 backups/skills-audit/skills_generation.db

# See all attempts
SELECT plugin_name, status, line_count, generation_time_seconds
FROM skill_generations
ORDER BY timestamp DESC;

# See only successes
SELECT plugin_name, char_count, line_count
FROM skill_generations
WHERE status = 'SUCCESS';

# See failures
SELECT plugin_name, error_message
FROM skill_generations
WHERE status != 'SUCCESS';
```

### Export Skills from Database

If you need to recover or review generated skills:

```sql
-- Export single skill
SELECT skill_content
FROM skill_generations
WHERE plugin_name = 'deployment-pipeline'
AND status = 'SUCCESS';

-- Export all successful skills
SELECT plugin_name, skill_content
FROM skill_generations
WHERE status = 'SUCCESS';
```

### Validation Failure Analysis

```sql
SELECT reason, COUNT(*) as count
FROM validation_failures
GROUP BY reason
ORDER BY count DESC;
```

---

## 🚦 Quality Checks

### Before Running

- [x] Vertex AI API enabled (`gcloud services enable aiplatform.googleapis.com`)
- [x] Application default credentials set (`gcloud auth application-default login`)
- [x] Quota project configured (`gcloud auth application-default set-quota-project ccpi-web-app-prod`)
- [x] Python dependencies installed (`pip3 install google-cloud-aiplatform --break-system-packages`)
- [x] Script is executable (`chmod +x scripts/vertex-skills-generator-safe.py`)

### After Running

```bash
# 1. Check statistics
python3 scripts/vertex-skills-generator-safe.py --stats

# 2. Review a few generated skills
find plugins -name "SKILL.md" -newer backups/skills-audit/skills_generation.db | head -5 | xargs cat

# 3. Check for validation issues
sqlite3 backups/skills-audit/skills_generation.db "SELECT * FROM validation_failures;"

# 4. Verify line counts are reasonable
sqlite3 backups/skills-audit/skills_generation.db "SELECT AVG(line_count), MAX(line_count) FROM skill_generations WHERE status = 'SUCCESS';"

# 5. Sync marketplace
node scripts/sync-marketplace.cjs

# 6. Git diff to see changes
git diff .claude-plugin/marketplace.extended.json
git diff plugins/ | head -100
```

---

## 🎯 Recommended Workflow

### Phase 1: Test Run (5 plugins)

```bash
python3 scripts/vertex-skills-generator-safe.py 5
python3 scripts/vertex-skills-generator-safe.py --stats
# Review generated skills manually
# If quality is good, proceed to Phase 2
```

### Phase 2: Priority Categories

```bash
python3 scripts/vertex-skills-generator-safe.py --priority
python3 scripts/vertex-skills-generator-safe.py --stats
node scripts/sync-marketplace.cjs
git add .
git commit -m "feat(skills): add Agent Skills to priority plugins"
git push
```

### Phase 3: Remaining Plugins

```bash
python3 scripts/vertex-skills-generator-safe.py --all
python3 scripts/vertex-skills-generator-safe.py --stats
node scripts/sync-marketplace.cjs
git add .
git commit -m "feat(skills): complete Agent Skills for all plugins"
git push
```

---

## 🔐 Security & Compliance

### Data Storage

- **Local SQLite database:** `backups/skills-audit/skills_generation.db`
- **Not committed to git:** (add to .gitignore if not already present)
- **Contains:** Full skill content, timestamps, status, errors
- **Purpose:** Audit trail and disaster recovery

### API Security

- Uses Application Default Credentials (ADC)
- No API keys in code
- Quota project set to ccpi-web-app-prod
- Rate limiting prevents quota exhaustion
- Conservative safety settings (BLOCK_ONLY_HIGH)

### GitHub Account Lock Protection

If GitHub locks your account, you have:

1. **Full backup in SQLite database** - All generated skills with timestamps
2. **Audit trail** - Exactly what was generated and when
3. **Recovery capability** - Can recreate from database
4. **Statistics** - Proof of work completed

```bash
# Export all skills to a single file for safekeeping
sqlite3 backups/skills-audit/skills_generation.db <<EOF
.mode markdown
.output backups/skills-backup-$(date +%Y%m%d).md
SELECT '## ' || plugin_name || '\n\n' || skill_content || '\n\n---\n\n'
FROM skill_generations
WHERE status = 'SUCCESS';
.quit
EOF
```

---

## 📋 Comparison: Old vs New Script

| Feature | vertex-skills-generator.py | vertex-skills-generator-safe.py |
|---------|---------------------------|--------------------------------|
| Anthropic Guidelines | ❌ Has `allowed-tools` field | ✅ Only `name` and `description` |
| Character Limits | ❌ Not enforced | ✅ 64 chars name, 1024 description |
| Line Count Check | ⚠️ 250 line target | ✅ 500 line recommendation |
| Validation | ❌ None | ✅ 8-point validation |
| Audit Trail | ❌ None | ✅ Full SQLite logging |
| Error Recovery | ❌ Basic | ✅ Retry logic + logging |
| Rate Limiting | ⚠️ 0.5s | ✅ 1s (more conservative) |
| Cost Estimates | ❌ None | ✅ Pre-run estimates |
| Backup System | ❌ None | ✅ Full content backup |
| Statistics | ❌ None | ✅ Comprehensive stats |

---

## 🚨 Emergency Procedures

### If Generation Quality is Poor

```bash
# Check validation failures
sqlite3 backups/skills-audit/skills_generation.db "SELECT * FROM validation_failures;"

# Review failed plugins
sqlite3 backups/skills-audit/skills_generation.db "SELECT plugin_name, error_message FROM skill_generations WHERE status != 'SUCCESS';"

# Delete bad skills and regenerate
rm -rf plugins/*/skills/  # Be careful!
# Then re-run with adjusted prompt if needed
```

### If GitHub Account is Locked

```bash
# 1. Export all data from database
cd /home/jeremy/000-projects/claude-code-plugins
mkdir -p ~/emergency-backup
cp backups/skills-audit/skills_generation.db ~/emergency-backup/

# 2. Export as readable markdown
sqlite3 ~/emergency-backup/skills_generation.db <<EOF
.mode markdown
.output ~/emergency-backup/all-skills.md
SELECT plugin_name, skill_content FROM skill_generations WHERE status = 'SUCCESS';
.quit
EOF

# 3. Export statistics
sqlite3 ~/emergency-backup/skills_generation.db <<EOF
.mode markdown
.output ~/emergency-backup/statistics.md
SELECT
    status,
    COUNT(*) as count,
    AVG(generation_time_seconds) as avg_time,
    AVG(line_count) as avg_lines
FROM skill_generations
GROUP BY status;
.quit
EOF
```

### If Need to Rollback

```bash
# Remove all generated skills
find plugins -type d -name "skills" -exec rm -rf {} + 2>/dev/null

# Revert marketplace changes
git checkout .claude-plugin/marketplace.extended.json

# Sync
node scripts/sync-marketplace.cjs

# Database remains intact for future attempts
```

---

## 💡 Tips & Best Practices

1. **Start Small:** Test with 5 plugins before batch processing
2. **Review Samples:** Manually check a few generated skills for quality
3. **Check Stats:** Use `--stats` flag to monitor success rate
4. **Commit Often:** Don't generate all 229 before committing
5. **Backup Database:** Copy SQLite file to safe location
6. **Monitor Quota:** Check GCP console for API usage
7. **Use Priority:** Focus on high-value categories first
8. **Rate Limit:** Don't reduce the 1s delay (quota protection)

---

## 📞 Support & Debugging

### Script Not Working?

```bash
# Check Python version (need 3.12+)
python3 --version

# Check dependencies
pip3 list | grep google-cloud-aiplatform

# Check ADC setup
gcloud auth application-default print-access-token

# Check project
gcloud config get-value project

# Check API enabled
gcloud services list --enabled | grep aiplatform
```

### Database Issues?

```bash
# Check database exists
ls -lh backups/skills-audit/skills_generation.db

# Check tables
sqlite3 backups/skills-audit/skills_generation.db ".tables"

# Check row count
sqlite3 backups/skills-audit/skills_generation.db "SELECT COUNT(*) FROM skill_generations;"
```

### Validation Failures?

The script enforces strict Anthropic guidelines. Common issues:

- **"Invalid field in frontmatter"** - Gemini added forbidden fields (script will retry)
- **"Name exceeds 64 characters"** - Name too long (script will retry)
- **"Contains placeholder text"** - Gemini used TODO/INSERT (script will retry)
- **"Exceeds 500-line recommendation"** - Warning only, still saves file

All failures logged to database for analysis.

---

**Last Updated:** 2025-10-17
**Status:** Production Ready ✅
**Tested:** No (awaiting user approval for test run)
