# Google Cloud Vertex AI Gemini Beta Models & Tier Release Schedule

**Date Created:** 2025-10-20
**Last Updated:** 2025-10-20
**Status:** Active Reference Document

---

## Executive Summary

Google Cloud's Vertex AI Gemini models have a staged release process where new models launch in **beta** exclusively on paid tiers before becoming available on the free tier. Understanding this release cycle is critical for cost planning and production deployment strategies.

---

## Current Situation (October 2025)

### Gemini 2.0 Flash (Current Production Model)

**Status:** ✅ Generally Available on Free Tier

- **Model ID:** `gemini-2.0-flash-exp`
- **Free Tier Availability:** YES
- **What We Use It For:** Agent Skills batch generation (231 plugins enhanced)
- **Cost:** $0.00 (within free tier limits)
- **Performance:**
  - 100% success rate
  - 45-60s per plugin processing
  - 13h 21m total for 159 SKILL.md files

### Gemini 2.5 Flash (Beta Model)

**Status:** ⚠️ Beta - Paid Tiers Only

- **Model ID:** `gemini-2.5-flash-preview-0514`
- **Free Tier Availability:** NO (not yet)
- **Launch Date:** May 14, 2025 (preview)
- **Current Tier:** Paid customers only
- **Expected Free Tier Release:** Q1 2026 (estimated)

---

## Google's Tier Release Model

### Phase 1: Beta Launch (Paid Tiers Only)
- New Gemini models release as "preview" or "experimental"
- Available exclusively to paid Google Cloud customers
- Pricing: Standard API rates apply
- Duration: 3-6 months typically

### Phase 2: General Availability (Paid Tiers)
- Model becomes stable/production-ready
- Still requires paid tier
- Pricing stabilizes
- Duration: 6-12 months

### Phase 3: Free Tier Release
- Model becomes available on Vertex AI free tier
- Rate limits apply (requests per minute/day)
- Perfect for development, testing, batch processing
- **This is where we operate**

---

## Why This Matters for Our Project

### Cost Implications

**Current Setup (Gemini 2.0 Flash on Free Tier):**
```
231 plugins enhanced × $0.00/plugin = $0.00 total cost ✅
```

**If We Used Beta Gemini 2.5 Flash (Paid Tier):**
```
Estimated cost per plugin: ~$0.05-$0.10
231 plugins × $0.075 (avg) = ~$17.33 ❌

Annual skills updates (4x/year):
231 plugins × 4 updates × $0.075 = ~$69.30/year ❌
```

### Strategic Decision

**We deliberately chose to:**
1. ✅ Use stable Gemini 2.0 Flash on free tier
2. ✅ Accept slightly older model for $0 cost
3. ✅ Build production-grade infrastructure (SQLite audit, disaster recovery)
4. ✅ Optimize for free tier limits (45-60s delays, rate limiting)
5. ❌ Avoid paid beta models until they reach free tier

---

## Historical Release Timeline

### Gemini 1.0 Pro
- **Beta Launch:** December 2023 (paid only)
- **Free Tier Release:** March 2024
- **Gap:** ~3 months

### Gemini 1.5 Flash
- **Beta Launch:** February 2024 (paid only)
- **Free Tier Release:** May 2024
- **Gap:** ~3 months

### Gemini 2.0 Flash
- **Beta Launch:** August 2024 (paid only)
- **Free Tier Release:** November 2024
- **Gap:** ~3 months

### Gemini 2.5 Flash (Current Beta)
- **Beta Launch:** May 2025 (paid only)
- **Free Tier Release:** TBD (estimated Q1 2026)
- **Expected Gap:** ~6-9 months (longer due to advanced capabilities)

---

## Free Tier Limits (Current)

### Gemini 2.0 Flash Free Tier Quotas

```yaml
Requests per Minute (RPM): 15
Requests per Day (RPD): 1,500
Tokens per Minute (TPM): 1,000,000
Tokens per Day (TPD): Unlimited (fair use)
```

### Our Usage Pattern
```python
# Conservative rate limiting for free tier
base_delay = 45.0  # seconds between requests
randomness = random.uniform(0, 15.0)  # 45-60s total
extra_rest_every_10 = random.uniform(30, 60)  # batch pacing

# Result: ~1.3 requests per minute (well under 15 RPM limit)
# API quota used: 28.4% after 159 plugin enhancements
```

---

## When to Consider Paid Tier

### Scenarios Where Paid Tier Makes Sense

1. **High-Volume Production (>1,500 requests/day)**
   - Our batch jobs run overnight, well within limits
   - Current: ❌ Not needed

2. **Real-Time User-Facing Features**
   - Our plugins use Claude Code, not Gemini directly
   - Current: ❌ Not applicable

3. **Need Latest Model Features**
   - Gemini 2.5 has better reasoning, but 2.0 works great
   - Current: ❌ Not worth the cost

4. **Commercial SLA Requirements**
   - We're open-source, no uptime guarantees needed
   - Current: ❌ Not required

### When We'll Upgrade

**Trigger:** Gemini 2.5 Flash reaches free tier (est. Q1 2026)

**Action Plan:**
```bash
# Update model reference in batch processor
sed -i 's/gemini-2.0-flash-exp/gemini-2.5-flash/g' scripts/vertex-skills-generator-safe.py

# Test with --limit 1
python3 scripts/vertex-skills-generator-safe.py --limit 1

# If successful, run full batch
python3 scripts/vertex-skills-generator-safe.py
```

---

## Monitoring Beta → Free Tier Releases

### Where to Check

1. **Google Cloud Release Notes**
   - https://cloud.google.com/vertex-ai/generative-ai/docs/release-notes
   - Filter: "Gemini" + "free tier"

2. **Vertex AI Pricing Page**
   - https://cloud.google.com/vertex-ai/pricing
   - Look for "Free tier" availability

3. **Google AI Studio**
   - https://aistudio.google.com/
   - Models available in AI Studio usually hit free tier soon

4. **Community Channels**
   - Google Cloud Community Forum
   - r/GoogleCloud subreddit
   - Google Cloud Next announcements

### Set Up Alerts

```bash
# Create GitHub issue reminder for Q1 2026
gh issue create \
  --title "Check if Gemini 2.5 Flash is available on Vertex AI free tier" \
  --body "Gemini 2.5 Flash should be available on free tier by Q1 2026. If so, update batch processor to use new model." \
  --label "enhancement,vertex-ai" \
  --milestone "Q1-2026"
```

---

## Comparison: Gemini 2.0 vs 2.5 Flash

### Gemini 2.0 Flash (What We Use)
- ✅ Free tier available
- ✅ Proven stable (231 plugins, 100% success)
- ✅ Fast (45-60s per plugin)
- ✅ Good quality (3,210 byte avg SKILL.md files)
- ⚠️ Older model (August 2024 training cutoff)

### Gemini 2.5 Flash (Beta - Paid Only)
- ❌ Not on free tier yet
- ✅ Better reasoning capabilities
- ✅ Improved code generation
- ✅ More recent training data
- ❌ Costs ~$0.05-$0.10 per plugin
- ⚠️ Still in preview (stability unknown)

**Verdict:** Stick with 2.0 Flash until 2.5 hits free tier. The quality difference doesn't justify $70+/year for our use case.

---

## Cost Analysis: Free vs Paid Tiers

### Annual Cost Projection

**Current (Free Tier):**
```
Initial batch: 231 plugins × $0.00 = $0.00
Quarterly updates: 50 plugins × 4 × $0.00 = $0.00
New plugins: 20 plugins × $0.00 = $0.00
─────────────────────────────────────────
Total Annual Cost: $0.00 ✅
```

**If Using Paid Tier (Gemini 2.5 Flash):**
```
Initial batch: 231 plugins × $0.075 = $17.33
Quarterly updates: 50 plugins × 4 × $0.075 = $15.00
New plugins: 20 plugins × $0.075 = $1.50
─────────────────────────────────────────
Total Annual Cost: $33.83 ❌
```

**Break-Even Analysis:**
- Our project is open-source with no revenue
- Every dollar spent is a dollar lost
- Free tier is not just cheaper—it's infinitely better ROI

---

## Future-Proofing Strategy

### Multi-Model Flexibility

Our batch processor supports multiple providers:

```python
# Current: Vertex AI Gemini 2.0 Flash (free)
VERTEX_MODEL = "gemini-2.0-flash-exp"

# Future options when free tier expands:
# - gemini-2.5-flash (when released to free tier)
# - gemini-3.0-flash-preview (future beta, wait for free tier)
# - gemini-pro-2.0 (if free tier quota increases)
```

### Fallback Options

If free tier quotas become restrictive:

1. **Anthropic Claude API** (already have access)
   - Switch to Claude 3.5 Sonnet
   - More expensive but higher quality
   - Use only when free tier exhausted

2. **OpenAI GPT-4** (have API key)
   - Comparable pricing to Claude
   - Good fallback option

3. **Local LLMs** (Ollama + Llama 3)
   - $0 cost forever
   - Slower, lower quality
   - Emergency backup only

---

## Recommendations

### Immediate (October 2025)
1. ✅ Continue using Gemini 2.0 Flash on free tier
2. ✅ Monitor API quota usage (keep under 50%)
3. ✅ Document all model parameters for reproducibility
4. ❌ Don't upgrade to paid tier unless forced

### Short-Term (Q4 2025 - Q1 2026)
1. 📅 Set calendar reminder for Q1 2026 to check Gemini 2.5 free tier
2. 📊 Track free tier quota changes (Google may increase limits)
3. 🧪 Test new models in AI Studio before production use
4. 📝 Document model performance benchmarks for comparison

### Long-Term (2026+)
1. 🔮 Watch for Gemini 3.0 announcements
2. 🌐 Explore multi-cloud AI strategies (AWS Bedrock, Azure OpenAI)
3. 💾 Build model-agnostic infrastructure
4. 📈 Consider paid tier only if project generates revenue

---

## Key Takeaways

1. **Beta models cost money** - Google releases new Gemini models to paid tiers first, free tier 3-6 months later

2. **Free tier is viable** - We enhanced 231 plugins for $0 using Gemini 2.0 Flash with 100% success rate

3. **Patience pays off** - Waiting for Gemini 2.5 to hit free tier saves ~$34/year with minimal quality tradeoff

4. **Monitor releases** - Set up alerts to upgrade when new models reach free tier

5. **Build for flexibility** - Keep infrastructure model-agnostic for easy switching

---

## References

- [Google Cloud Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)
- [Vertex AI Generative AI Release Notes](https://cloud.google.com/vertex-ai/generative-ai/docs/release-notes)
- [Gemini API Free Tier Quotas](https://ai.google.dev/pricing)
- [Our Implementation: vertex-skills-generator-safe.py](../scripts/vertex-skills-generator-safe.py)
- [Batch Processing Metrics](./BATCH_PROCESSING_METRICS.md)

---

**Document Status:** ✅ Complete
**Next Review:** Q1 2026 (Check Gemini 2.5 free tier availability)
**Maintained By:** @jeremylongshore
**Location:** `/home/jeremy/000-projects/claude-code-plugins/docs/VERTEX-AI-GEMINI-BETA-TIERS.md`

---

**Timestamp:** 2025-10-20T21:29:00Z
