# Vertex AI Quota Increase Instructions

**Date:** 2025-10-17
**Issue:** Hit rate limit on Gemini 2.0 Flash Experimental
**Error:** `429 Quota exceeded for aiplatform.googleapis.com/generate_content_requests_per_minute_per_project_per_base_model`

---

## What Happened?

You hit the **requests per minute** quota for Gemini 2.0 Flash Experimental model.

**Current Settings:**
- **Project:** ccpi-web-app-prod
- **Model:** gemini-2.0-flash-exp (experimental)
- **Location:** us-central1
- **Rate Limit:** Now set to 10 seconds between calls

**Default Quotas (Experimental Models):**
- Requests per minute: **Very low** (typically 5-10)
- Requests per day: Limited
- Tokens per minute: Limited

---

## Solution 1: Request Quota Increase (RECOMMENDED)

### Step 1: Check Current Quotas

```bash
# View current quotas for Vertex AI
gcloud services quota list \
  --service=aiplatform.googleapis.com \
  --project=ccpi-web-app-prod \
  --filter="metric.type=aiplatform.googleapis.com/generate_content_requests_per_minute_per_project_per_base_model"
```

### Step 2: Visit Quotas Page

**Direct Link:**
```
https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=ccpi-web-app-prod
```

**Or Navigate:**
1. Go to https://console.cloud.google.com/
2. Select project: **ccpi-web-app-prod**
3. Navigate to: **IAM & Admin → Quotas**
4. Filter by: **aiplatform.googleapis.com**

### Step 3: Find the Right Quota

Search for:
```
Generate content requests per minute per project per base model
```

Look for entry with:
- **Model:** gemini-2.0-flash-exp
- **Region:** us-central1

### Step 4: Request Increase

1. **Check the box** next to the quota
2. Click **"EDIT QUOTAS"** button at top
3. Fill out form:
   - **New quota value:** 60 (1 per second for smooth processing)
   - **Justification:**
     ```
     Batch processing Agent Skills generation for 227 Claude Code plugins.
     Currently limited to 5-10 requests/minute which causes frequent 429 errors.
     Need 60 requests/minute (1 per second) to process plugins efficiently.

     Use case: Generating instruction manuals (SKILL.md files) that teach
     Claude Code when and how to use each plugin. Each generation takes
     ~6 seconds with Gemini 2.0 Flash Experimental.

     Current rate: 10 seconds between requests (ultra-conservative)
     Desired rate: 1-2 seconds between requests
     Total batch size: 227 plugins
     Estimated processing time with 60 req/min: ~25 minutes
     ```
4. Click **"SUBMIT REQUEST"**

### Step 5: Wait for Approval

- **Typical approval time:** 24-48 hours
- **Email notification:** You'll get confirmation when approved
- **Check status:** Revisit the Quotas page

---

## Solution 2: Switch to Stable Model (FASTER, NO APPROVAL NEEDED)

Instead of waiting for quota increase, switch to the stable Gemini model.

### Current Model (Experimental):
```python
model = GenerativeModel("gemini-2.0-flash-exp")
```

**Pros:**
- Cutting edge features
- Potentially better quality

**Cons:**
- ❌ Very low quotas
- ❌ Frequent 429 errors
- ❌ Not production-ready

### Switch to Stable Model:
```python
model = GenerativeModel("gemini-1.5-flash-002")
```

**Pros:**
- ✅ Higher quotas (60+ requests/minute)
- ✅ Production-ready
- ✅ More reliable
- ✅ No approval needed

**Cons:**
- Slightly older model

### How to Switch

**Option A: Edit the script manually:**

```bash
# Edit the script
nano scripts/vertex-skills-generator-safe.py

# Find line ~26:
model = GenerativeModel("gemini-2.0-flash-exp")

# Change to:
model = GenerativeModel("gemini-1.5-flash-002")

# Save and exit (Ctrl+X, Y, Enter)
```

**Option B: Use sed to update automatically:**

```bash
sed -i 's/gemini-2.0-flash-exp/gemini-1.5-flash-002/g' scripts/vertex-skills-generator-safe.py

# Verify the change
grep "GenerativeModel" scripts/vertex-skills-generator-safe.py
```

---

## Solution 3: Use Standard Google AI API (Alternative)

Switch from Vertex AI to standard Google AI API (has different quotas).

### Step 1: Get API Key

1. Visit: https://aistudio.google.com/app/apikey
2. Click **"Create API Key"**
3. Select project: **ccpi-web-app-prod**
4. Copy the API key

### Step 2: Set Environment Variable

```bash
export GOOGLE_API_KEY='your-api-key-here'

# Add to ~/.bashrc for persistence
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
```

### Step 3: Use Alternative Script

We already have `scripts/generate-skills-gemini.py` that uses standard Google AI:

```bash
# This uses google.generativeai instead of vertexai
python3 scripts/generate-skills-gemini.py --priority
```

**Pros:**
- Different quota limits (may be higher)
- Uses API key instead of ADC
- Simpler authentication

**Cons:**
- Different billing
- Different rate limits (check at runtime)

---

## Current Workaround: 10-Second Delay

**What we did:**
- Set `RATE_LIMIT_DELAY = 10.0` (10 seconds between calls)
- This avoids quota issues but is SLOW

**Performance:**
- **Priority plugins (157):** ~26 minutes
- **All plugins (227):** ~38 minutes

**Cost:**
- Still ~$0.001 per plugin
- Total: ~$0.23 for all plugins

**Trade-off:**
- ✅ No quota errors
- ❌ Very slow processing

---

## Recommended Approach

### Immediate (Today):

```bash
# Option 1: Continue with 10-second delay (slow but safe)
python3 scripts/vertex-skills-generator-safe.py --priority --yes

# Option 2: Switch to stable model (faster, no approval)
sed -i 's/gemini-2.0-flash-exp/gemini-1.5-flash-002/g' scripts/vertex-skills-generator-safe.py
# Reduce delay back to 2 seconds
sed -i 's/RATE_LIMIT_DELAY = 10.0/RATE_LIMIT_DELAY = 2.0/g' scripts/vertex-skills-generator-safe.py
python3 scripts/vertex-skills-generator-safe.py --priority --yes
```

### Long-term (Next 24-48 hours):

1. **Request quota increase** (see Step 4 above)
2. **Justification:** Batch processing 227 plugins for Agent Skills
3. **Requested limit:** 60 requests/minute
4. **Wait for approval**
5. **Once approved:** Reduce delay to 1-2 seconds, process everything

---

## Check Your Current Quotas

### View All Vertex AI Quotas:

```bash
gcloud services quota list \
  --service=aiplatform.googleapis.com \
  --project=ccpi-web-app-prod \
  --format="table(metric.type,limit,usage)"
```

### Check Specific Model Quota:

```bash
gcloud services quota list \
  --service=aiplatform.googleapis.com \
  --project=ccpi-web-app-prod \
  --filter="gemini"
```

### View in Console (Visual):

```
https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=ccpi-web-app-prod
```

---

## Alternative: Process in Small Batches

Instead of processing all at once, break it into daily batches:

```bash
# Day 1: Process 20 plugins
python3 scripts/vertex-skills-generator-safe.py 20 --yes

# Day 2: Process next 20 plugins
python3 scripts/vertex-skills-generator-safe.py 20 --yes

# Continue until done (11 days for all 227 plugins)
```

**Pros:**
- Stays within quota limits
- No approval needed
- Zero risk of 429 errors

**Cons:**
- Takes 11 days to complete
- Need to remember to run daily

---

## What's Actually Happening?

### The 429 Error Breakdown:

```
Error: 429 Quota exceeded for
  aiplatform.googleapis.com/generate_content_requests_per_minute_per_project_per_base_model
  with base model: gemini-experimental
```

**Translation:**
- **429:** "Too Many Requests" HTTP status
- **Quota exceeded:** You hit the rate limit
- **per_minute:** Resets every 60 seconds
- **per_project:** Specific to ccpi-web-app-prod
- **per_base_model:** Specific to gemini-2.0-flash-exp
- **gemini-experimental:** Experimental models have VERY low quotas

### Why Experimental Has Low Quotas:

Google limits experimental model access to:
1. Reduce abuse/spam
2. Manage compute costs
3. Test stability with limited load
4. Encourage production model usage

**Solution:** Request increase OR switch to stable model

---

## Quick Decision Matrix

| Scenario | Action | Speed | Approval Needed |
|----------|--------|-------|-----------------|
| Need it NOW | Switch to gemini-1.5-flash-002 | Fast | ❌ No |
| Can wait 24-48h | Request quota increase | Fast (after approval) | ✅ Yes |
| No rush | Continue with 10s delay | Slow (~38 min) | ❌ No |
| Very patient | Process 20/day for 11 days | Very slow | ❌ No |

---

## Commands to Run

### Check Current Model:

```bash
grep "GenerativeModel" scripts/vertex-skills-generator-safe.py
```

### Switch to Stable Model:

```bash
# Update model
sed -i 's/gemini-2.0-flash-exp/gemini-1.5-flash-002/g' scripts/vertex-skills-generator-safe.py

# Reduce delay (stable model has higher quotas)
sed -i 's/RATE_LIMIT_DELAY = 10.0/RATE_LIMIT_DELAY = 2.0/g' scripts/vertex-skills-generator-safe.py

# Verify changes
grep "GenerativeModel\|RATE_LIMIT_DELAY" scripts/vertex-skills-generator-safe.py

# Run priority batch
python3 scripts/vertex-skills-generator-safe.py --priority --yes
```

### Request Quota Increase (Manual):

```bash
# Open browser to quotas page
xdg-open "https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=ccpi-web-app-prod"

# Search for: generate_content_requests_per_minute
# Request new limit: 60
# Submit justification (see Step 4 above)
```

### Continue with Current Settings (Slow but Safe):

```bash
# Just run it with 10-second delay
python3 scripts/vertex-skills-generator-safe.py --priority --yes

# Will take ~26 minutes for 157 priority plugins
# Will cost ~$0.157
```

---

## Summary

**Problem:** Gemini 2.0 Flash Experimental has very low quotas (5-10 requests/minute)

**Quick Fix (No Approval):**
```bash
sed -i 's/gemini-2.0-flash-exp/gemini-1.5-flash-002/g' scripts/vertex-skills-generator-safe.py
sed -i 's/RATE_LIMIT_DELAY = 10.0/RATE_LIMIT_DELAY = 2.0/g' scripts/vertex-skills-generator-safe.py
python3 scripts/vertex-skills-generator-safe.py --priority --yes
```

**Proper Fix (Requires Approval):**
1. Visit: https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=ccpi-web-app-prod
2. Find: "Generate content requests per minute per project per base model"
3. Request: 60 requests/minute
4. Wait: 24-48 hours for approval

**Current Workaround:**
- 10-second delay between calls
- No quota errors
- Slow but safe
- ~38 minutes for all 227 plugins

---

**Recommendation:** Switch to stable model NOW (no approval needed), request quota increase for future runs.

**Last Updated:** 2025-10-17
**Project:** ccpi-web-app-prod
**Current Rate Limit:** 10 seconds between calls
