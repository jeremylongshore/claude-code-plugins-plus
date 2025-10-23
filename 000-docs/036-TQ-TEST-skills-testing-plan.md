# Agent Skills Testing & Validation Plan

**Date:** 2025-10-17
**Purpose:** Ensure generated SKILL.md files are high quality and function correctly

---

## Phase 1: Automated Validation (Already Running) ✅

### Built-in Quality Checks

The generation script validates every SKILL.md against 8 quality criteria:

1. **YAML Frontmatter Structure** - Must have `---` delimiters
2. **Required Fields** - Must have `name` and `description`
3. **No Forbidden Fields** - Cannot have `allowed-tools`, `version`, `author`, etc.
4. **Character Limits** - Name ≤ 64 chars, description ≤ 1024 chars
5. **Line Count** - Warns if > 500 lines (Anthropic recommendation)
6. **Minimum Content** - Body must be > 100 characters
7. **No Placeholders** - No `[TODO]`, `[INSERT]`, `[PLACEHOLDER]` text
8. **Markdown Code Fence Stripping** - Removes ```markdown wrappers if present

### Database Audit Trail

Every generation attempt is logged with:
- Timestamp
- Success/error status
- Character count and line count
- Full backup of SKILL.md content
- Error messages for failures

**Check validation results:**
```bash
sqlite3 backups/skills-audit/skills_generation.db "SELECT COUNT(*) FROM validation_failures;"
# Should be 0
```

---

## Phase 2: Sample Quality Review

### Random Sampling Strategy

Test 10-15 randomly selected skills for manual quality review.

**Commands:**
```bash
# Get 10 random successful generations
sqlite3 backups/skills-audit/skills_generation.db "SELECT plugin_name FROM skill_generations WHERE status = 'SUCCESS' ORDER BY RANDOM() LIMIT 10;" > /tmp/sample_plugins.txt

# View each one
while read plugin; do
  echo "=== $plugin ==="
  find plugins -name "SKILL.md" -path "*/$plugin/*" -exec head -50 {} \;
  echo ""
done < /tmp/sample_plugins.txt
```

### Quality Criteria Checklist

For each sampled skill, verify:

- [ ] **Name is descriptive** - Uses gerund form (e.g., "Creating Docker Compose Files")
- [ ] **Description has trigger phrases** - Clear terms Claude will match
- [ ] **Description explains WHEN to use** - Not just what it does
- [ ] **Body has clear structure** - Sections like "How It Works", "When to Use", "Examples"
- [ ] **Instructions are actionable** - Not vague or generic
- [ ] **No hallucinations** - Information matches actual plugin functionality
- [ ] **Trigger phrases are appropriate** - Match what users would actually say
- [ ] **Examples are realistic** - Show actual use cases

---

## Phase 3: Statistical Analysis

### Overall Metrics

**Run statistics:**
```bash
python3 scripts/vertex-skills-generator-safe.py --stats
```

**Expected output:**
```
Success: ~157 (100% of priority plugins)
Errors: 0 (with 30s rate limit)
Validation Failures: 0
Avg Generation Time: ~5 seconds
Avg Line Count: ~51 lines
```

### Character Count Distribution

**Check for outliers:**
```bash
sqlite3 backups/skills-audit/skills_generation.db <<EOF
SELECT
  MIN(char_count) as min_chars,
  AVG(char_count) as avg_chars,
  MAX(char_count) as max_chars,
  MIN(line_count) as min_lines,
  AVG(line_count) as avg_lines,
  MAX(line_count) as max_lines
FROM skill_generations
WHERE status = 'SUCCESS';
EOF
```

### Detect Potential Issues

**Find suspiciously short skills:**
```bash
sqlite3 backups/skills-audit/skills_generation.db "SELECT plugin_name, char_count, line_count FROM skill_generations WHERE status = 'SUCCESS' AND char_count < 1500 ORDER BY char_count ASC LIMIT 10;"
```

**Find suspiciously long skills:**
```bash
sqlite3 backups/skills-audit/skills_generation.db "SELECT plugin_name, char_count, line_count FROM skill_generations WHERE status = 'SUCCESS' AND line_count > 60 ORDER BY line_count DESC LIMIT 10;"
```

---

## Phase 4: Local Integration Testing

### Test Plugin Installation with Skills

**Create test marketplace:**
```bash
mkdir -p ~/test-claude-skills/.claude-plugin

# Copy 3-5 plugins with newly generated skills
cat > ~/test-claude-skills/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "skills-test",
  "owner": {"name": "Test"},
  "plugins": [
    {
      "name": "ansible-playbook-creator",
      "source": "/home/jeremy/000-projects/claude-code-plugins/plugins/community/ansible-playbook-creator"
    },
    {
      "name": "docker-compose-generator",
      "source": "/home/jeremy/000-projects/claude-code-plugins/plugins/community/docker-compose-generator"
    },
    {
      "name": "terraform-module-builder",
      "source": "/home/jeremy/000-projects/claude-code-plugins/plugins/community/terraform-module-builder"
    }
  ]
}
EOF
```

**Add to Claude Code:**
```bash
/plugin marketplace add ~/test-claude-skills
```

**Install test plugins:**
```bash
/plugin install ansible-playbook-creator@skills-test
/plugin install docker-compose-generator@skills-test
/plugin install terraform-module-builder@skills-test
```

### Test Trigger Phrase Activation

**Test cases:**

1. **Ansible Playbook Creator**
   - Say: "Create an ansible playbook to install nginx"
   - Expected: Claude should automatically activate the plugin
   - Verify: Claude mentions using ansible-playbook-creator

2. **Docker Compose Generator**
   - Say: "Generate docker compose for postgres and redis"
   - Expected: Plugin activates automatically
   - Verify: Follows workflow from SKILL.md

3. **Terraform Module Builder**
   - Say: "Create terraform module for S3 bucket"
   - Expected: Plugin activates
   - Verify: Uses terraform best practices from skill

**Document results:**
```bash
# Create test results file
cat > ~/test-claude-skills/activation-test-results.md << 'EOF'
# Agent Skills Activation Test Results

## Test 1: Ansible Playbook Creator
**Trigger phrase:** "Create an ansible playbook to install nginx"
**Expected behavior:** Auto-activate ansible-playbook-creator plugin
**Actual result:** [PASS/FAIL]
**Notes:**

## Test 2: Docker Compose Generator
**Trigger phrase:** "Generate docker compose for postgres and redis"
**Expected behavior:** Auto-activate docker-compose-generator plugin
**Actual result:** [PASS/FAIL]
**Notes:**

## Test 3: Terraform Module Builder
**Trigger phrase:** "Create terraform module for S3 bucket"
**Expected behavior:** Auto-activate terraform-module-builder plugin
**Actual result:** [PASS/FAIL]
**Notes:**
EOF
```

---

## Phase 5: Content Quality Audit

### Check for Common Issues

**1. Duplicate descriptions across plugins:**
```bash
# Extract all descriptions
find plugins -name "SKILL.md" -exec grep -A 3 "^description:" {} \; | sort | uniq -c | sort -rn | head -20

# Should not see many duplicates
```

**2. Generic/vague descriptions:**
```bash
# Look for generic words like "helps", "allows", "enables"
find plugins -name "SKILL.md" -exec grep -l "helps you\|allows you\|enables you" {} \; | wc -l

# High count = too generic
```

**3. Missing trigger phrases:**
```bash
# Descriptions should contain specific keywords
# Check a sample for specificity

sqlite3 backups/skills-audit/skills_generation.db <<EOF
SELECT plugin_name,
       SUBSTR(skill_content,
              INSTR(skill_content, 'description:'),
              INSTR(SUBSTR(skill_content, INSTR(skill_content, 'description:')), '---') - 1
       ) as description
FROM skill_generations
WHERE status = 'SUCCESS'
LIMIT 5;
EOF
```

**4. Hallucinated features:**
```bash
# Manually review skills for plugins you're familiar with
# Compare SKILL.md claims vs actual plugin capabilities

# Example: Check docker-compose-generator skill
cat plugins/community/docker-compose-generator/skills/skill-adapter/SKILL.md
cat plugins/community/docker-compose-generator/commands/*.md
cat plugins/community/docker-compose-generator/README.md

# Verify skill instructions match actual plugin functionality
```

---

## Phase 6: Prompt Quality Assessment

### Test Improved Prompt Context

Since we updated the prompt to teach Gemini about Claude Code plugins, we should compare quality before/after.

**Extract skills generated with OLD prompt (first 50):**
```bash
sqlite3 backups/skills-audit/skills_generation.db "SELECT skill_content FROM skill_generations WHERE status = 'SUCCESS' ORDER BY timestamp ASC LIMIT 3;" > /tmp/old_prompt_skills.txt
```

**Extract skills generated with NEW prompt (last 50):**
```bash
sqlite3 backups/skills-audit/skills_generation.db "SELECT skill_content FROM skill_generations WHERE status = 'SUCCESS' ORDER BY timestamp DESC LIMIT 3;" > /tmp/new_prompt_skills.txt
```

**Compare quality:**
- Are newer skills more specific about trigger phrases?
- Do newer skills better explain the 4-step activation flow?
- Are instructions clearer in newer skills?

---

## Phase 7: Keyword Integration Test

### Verify Marketplace Keywords Updated

**Check that agent-skills keyword was added:**
```bash
# Count plugins with agent-skills keyword in marketplace.extended.json
jq '[.plugins[] | select(.keywords[]? == "agent-skills")] | length' .claude-plugin/marketplace.extended.json

# Should match number of successfully generated skills
python3 scripts/vertex-skills-generator-safe.py --stats | grep "Success:"
```

**Verify individual plugins:**
```bash
# Sample 5 plugins with generated skills
for plugin in ansible-playbook-creator docker-compose-generator terraform-module-builder ci-cd-pipeline-builder kubernetes-deployment-creator; do
  echo "=== $plugin ==="
  jq -r ".plugins[] | select(.name == \"$plugin\") | .keywords" .claude-plugin/marketplace.extended.json
  echo ""
done

# Each should include "agent-skills"
```

---

## Phase 8: Regression Testing

### Before Committing Changes

**1. Marketplace sync check:**
```bash
# Ensure CLI catalog is in sync
node scripts/sync-marketplace.cjs

# Should show no changes if already synced
git diff .claude-plugin/marketplace.json

# If there are changes, commit them
```

**2. JSON validation:**
```bash
# Validate all JSON files
find .claude-plugin plugins -name "*.json" -exec sh -c 'jq empty {} || echo "Invalid: {}"' \;

# Should show no "Invalid" messages
```

**3. Plugin structure validation:**
```bash
# Run comprehensive validation
./scripts/validate-all.sh

# Should pass all checks
```

**4. Build marketplace website:**
```bash
cd marketplace
npm run build

# Should build without errors
```

---

## Phase 9: User Acceptance Testing

### Real-World Usage Scenarios

**Test with actual development tasks:**

1. **DevOps workflow:**
   - "I need to deploy a Node.js app to Kubernetes with CI/CD"
   - Expect: kubernetes-deployment-creator, ci-cd-pipeline-builder auto-activate

2. **Security workflow:**
   - "Scan this Docker image for vulnerabilities"
   - Expect: container-security-scanner auto-activates

3. **Testing workflow:**
   - "Set up visual regression testing for this React app"
   - Expect: visual-regression-tester auto-activates

4. **AI/ML workflow:**
   - "Train a model to predict customer churn"
   - Expect: ml-model-trainer auto-activates

**Document real-world test results:**
```bash
cat > backups/UAT_RESULTS.md << 'EOF'
# User Acceptance Testing Results

## DevOps Workflow Test
**Task:** Deploy Node.js app with K8s and CI/CD
**Plugins activated:** [list]
**Success:** [YES/NO]
**Issues:** [list]

## Security Workflow Test
**Task:** Scan Docker image
**Plugins activated:** [list]
**Success:** [YES/NO]
**Issues:** [list]

[Continue for each test...]
EOF
```

---

## Phase 10: Performance Testing

### Measure Impact on Claude Code Startup

**Before skills (baseline):**
```bash
time claude-code --version
# Record startup time
```

**After installing 20 plugins with skills:**
```bash
time claude-code --version
# Compare startup time
```

**Expected:** Minimal impact (<100ms increase) since skills are just markdown files

---

## Success Criteria

### Automated Validation
- [x] 0 validation failures in database
- [x] 0 forbidden fields detected
- [x] 100% of skills under 500 lines
- [x] No placeholder text in any skill

### Quality Review (Sample of 10-15)
- [ ] 100% have descriptive names in gerund form
- [ ] 100% have clear trigger phrases
- [ ] 90%+ have actionable instructions
- [ ] 0% have obvious hallucinations

### Integration Testing
- [ ] 5/5 test plugins activate with trigger phrases
- [ ] Claude follows workflow from SKILL.md
- [ ] No errors during plugin loading

### Marketplace Integration
- [ ] All successful plugins have "agent-skills" keyword
- [ ] CLI catalog syncs without errors
- [ ] Website builds successfully

### User Acceptance
- [ ] 4/4 real-world workflows succeed
- [ ] Users can easily trigger plugins
- [ ] Instructions are clear and helpful

---

## Quick Test Commands

**Full validation sequence:**
```bash
# 1. Check database for issues
python3 scripts/vertex-skills-generator-safe.py --stats

# 2. Find validation failures
sqlite3 backups/skills-audit/skills_generation.db "SELECT COUNT(*) FROM validation_failures;"

# 3. Sample 5 random skills for review
sqlite3 backups/skills-audit/skills_generation.db "SELECT plugin_name FROM skill_generations WHERE status = 'SUCCESS' ORDER BY RANDOM() LIMIT 5;" | while read plugin; do
  echo "=== $plugin ==="
  find plugins -name "SKILL.md" -path "*/$plugin/*" -exec cat {} \;
  echo ""
done

# 4. Check keyword integration
jq '[.plugins[] | select(.keywords[]? == "agent-skills")] | length' .claude-plugin/marketplace.extended.json

# 5. Sync and validate marketplace
node scripts/sync-marketplace.cjs
./scripts/validate-all.sh

# 6. Test website build
cd marketplace && npm run build
```

---

## Issue Remediation Plan

### If validation failures found:
1. Review failed plugins in database
2. Identify pattern (formatting, hallucination, etc.)
3. Update prompt or validation rules
4. Regenerate failed plugins only

### If quality issues found:
1. Document specific issues per plugin
2. Create fix script for systematic issues
3. Manually edit egregious cases
4. Re-validate after fixes

### If integration issues found:
1. Check SKILL.md trigger phrases match user language
2. Verify instructions are clear
3. Update descriptions if needed
4. Test again with revised skills

---

**Next Steps After Batch Completes:**

1. ✅ Run Phase 2 (Sample Quality Review)
2. ✅ Run Phase 3 (Statistical Analysis)
3. ✅ Run Phase 4 (Local Integration Testing)
4. ✅ Document results in UAT_RESULTS.md
5. ✅ Fix any issues found
6. ✅ Commit to git if all tests pass

---

**Last Updated:** 2025-10-17 14:50 UTC
**Status:** Testing plan ready, batch processing in progress
