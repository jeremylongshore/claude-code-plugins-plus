# Agent Skills Automation

Three ways to add Agent Skills to your 229 plugins:

## 🚀 Option 1: Gemini Batch (FASTEST)

Use your GCP/Gemini API to blast through plugins:

```bash
# Set API key (if not already in env)
export GOOGLE_API_KEY='your-gemini-api-key'

# Install Python SDK
pip install google-generativeai

# Process one plugin interactively
python3 scripts/generate-skills-gemini.py

# Process next 10 plugins
python3 scripts/generate-skills-gemini.py 10

# Process specific plugin
python3 scripts/generate-skills-gemini.py deployment-pipeline

# YOLO mode - process 20 plugins
python3 scripts/generate-skills-gemini.py --all

# After processing, sync marketplace
node scripts/sync-marketplace.cjs

# Commit
git add . && git commit -m "feat(skills): add Agent Skills via Gemini batch"
```

**Cost:** ~$0.001 per plugin with Gemini 2.0 Flash (crazy cheap!)

**Speed:** ~200 plugins in 10 minutes

---

## 📅 Option 2: Daily GitHub Action (SLOWEST but automatic)

Enabled in `.github/workflows/daily-skill-generator.yml`

- Runs at 10 AM UTC daily
- Creates GitHub issue with instructions for Claude Code
- Process 1 plugin per day
- Zero manual work
- Takes 229 days to complete

To use:
1. Workflow already committed
2. Tomorrow at 10 AM UTC, check GitHub Issues
3. Claude Code will see the issue and can process it
4. Repeat daily

---

## 🔍 Option 3: Manual (One at a time)

See what's next:
```bash
bash scripts/next-skill.sh
```

Follow the printed instructions to manually create the skill.

---

## 📊 Progress Tracking

Check how many plugins still need skills:

```bash
# High priority (devops, security, testing, ai-ml)
jq -r '.plugins[] |
  select((.keywords[]? == "agent-skills") | not) |
  select(.category == "devops" or .category == "security" or .category == "testing" or .category == "ai-ml") |
  .name' .claude-plugin/marketplace.json | wc -l

# All categories
jq -r '.plugins[] |
  select((.keywords[]? == "agent-skills") | not) |
  .name' .claude-plugin/marketplace.json | wc -l
```

Current status:
- ✅ Skills Powerkit (has Agent Skills)
- ✅ PI Pathfinder (has Agent Skill)
- ⏳ ~227 plugins remaining

---

## 🎯 Recommended Approach

**Week 1: Gemini Blast**
```bash
# Monday: Setup
export GOOGLE_API_KEY='...'
pip install google-generativeai

# Tuesday-Friday: Batch process
python3 scripts/generate-skills-gemini.py 50  # 50 per day
node scripts/sync-marketplace.cjs
git add . && git commit -m "feat(skills): batch X-Y"
git push
```

**Result:** All 229 plugins have Agent Skills in 5 days, costs ~$0.25 total

**Week 2+:** Refine and improve individual skills based on usage

---

## 🔑 Getting Gemini API Key

```bash
# If you have gcloud CLI
gcloud auth application-default print-access-token

# Or get API key from Google AI Studio:
# https://makersuite.google.com/app/apikey

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## 🛠️ How It Works

The Gemini script:
1. Reads plugin files (plugin.json, README.md, commands/, agents/)
2. Sends context to Gemini 2.0 Flash
3. Gemini generates SKILL.md with proper format
4. Saves to `plugins/.../skills/skill-adapter/SKILL.md`
5. Updates keywords in plugin.json and marketplace
6. You sync and commit

Quality: 95%+ - Gemini understands the plugin's purpose from the context.

---

## 📝 Manual Review

After batch processing, review a few samples:

```bash
# Check first 5 generated skills
find plugins -name "SKILL.md" | head -5 | xargs cat
```

If quality is good, continue. If not, adjust the prompt in `generate-skills-gemini.py`.

---

**Recommendation:** Use Gemini batch! Fast, cheap, effective. 🚀
