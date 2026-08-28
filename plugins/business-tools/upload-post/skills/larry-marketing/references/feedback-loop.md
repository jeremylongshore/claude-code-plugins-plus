# The Feedback Loop

The mechanism that makes the pipeline improve instead of repeating itself. This is the detailed version of the summary in SKILL.md.

This is what separates "posting TikToks" from "running a marketing machine." The daily cron pulls data from two sources:

1. **Upload-Post** → platform analytics (followers, impressions, reach) + upload history (per-post success, post URLs)
2. **RevenueCat** (if connected) → conversion data (trial starts, paid subscriptions, revenue)

Combined, the agent can make intelligent decisions about what to do next — not guessing, not vibes, actual data-driven optimization.

### The Daily Cron (Set Up During Onboarding)

Every morning before the first post, the cron runs `scripts/daily-report.js`:

1. Pulls platform analytics from Upload-Post (followers, impressions, reach timeseries)
2. Pulls upload history for the last 3 days (per-post status, post URLs)
3. If RevenueCat is connected, pulls conversion events in the same window (24-72h attribution)
4. Cross-references: which posts drove views AND which drove paying users
5. Applies the diagnostic framework (below) to determine what's working
6. Generates `tiktok-marketing/reports/YYYY-MM-DD.md` with findings
7. Messages the user with a summary + suggested hooks for today

### The Diagnostic Framework

This is the core intelligence. Two axes: **views** (are people seeing it?) and **conversions** (are people paying?).

**High views + High conversions** → 🟢 SCALE IT
- This is working. Make 3 variations of the winning hook immediately
- Test different posting times to find the sweet spot
- Cross-post to more platforms for extra reach
- Don't change anything about the CTA — it's converting

**High views + Low conversions** → 🟡 FIX THE CTA
- The hook is doing its job — people are watching. But they're not downloading/subscribing
- Try different CTAs on slide 6 (direct vs subtle, "download" vs "search on App Store")
- Check if the app landing page matches the promise in the slideshow
- Test different caption structures — maybe the CTA is buried
- The hook is gold — don't touch it. Fix everything downstream

**Low views + High conversions** → 🟡 FIX THE HOOKS
- The people who DO see it are converting — the content and CTA are great
- But not enough people are seeing it, so the hook/thumbnail isn't stopping the scroll
- Test radically different hooks (person+conflict, POV, listicle, mistakes format)
- Try different posting times and different slide 1 images
- Keep the CTA and content structure identical — just change the hook

**Low views + Low conversions** → 🔴 FULL RESET
- Neither the hook nor the conversion path is working
- Try a completely different format or approach
- Research what's trending in the niche RIGHT NOW (use browser)
- Consider a different target audience angle
- Test new hook categories from scratch
- Reference competitor research for what's working for others

**High views + High downloads + Low paying subscribers** → 🔴 APP ISSUE
- The marketing is working. People are watching AND downloading. But they're not paying.
- This is NOT a content problem — the app onboarding, paywall, or pricing needs fixing.
- Check: Is the paywall shown at the right time? Is the free experience too generous?
- Check: Does the onboarding guide users to the "aha moment" before the paywall?
- Check: Is the pricing right? Too expensive for the perceived value?
- **This is a signal to pause posting and fix the app experience first**

**High views + Low downloads** → 🟡 CTA ISSUE
- People are watching but not downloading. The hooks work, the CTAs don't.
- Rotate through different CTAs: "link in bio", "search on App Store", app name only, "free to try"
- Check the App Store page — does it match what the TikTok shows?
- Check that "link in bio" actually works and goes to the right place

**The daily report automates all of this.** It cross-references platform impressions (Upload-Post) with downloads and revenue (RevenueCat) and tells you exactly which part of the funnel is broken — per post. It also auto-generates new hook suggestions based on your winning patterns and flags when CTAs need rotating.

### Hook Evolution

Track in `tiktok-marketing/hook-performance.json`:

```json
{
  "hooks": [
    {
      "requestId": "abc123def456",
      "text": "My boyfriend said our flat looks like a catalogue",
      "date": "2026-02-15",
      "platforms": {
        "tiktok": { "success": true, "postUrl": "..." },
        "instagram": { "success": true, "postUrl": "..." }
      },
      "conversions": 4,
      "cta": "Download Snugly — link in bio",
      "lastChecked": "2026-02-16"
    }
  ],
  "ctas": [
    {
      "text": "Download [App] — link in bio",
      "timesUsed": 5,
      "totalConversions": 8,
      "conversionRate": 0.067
    },
    {
      "text": "Search [App] on the App Store",
      "timesUsed": 3,
      "totalConversions": 12,
      "conversionRate": 0.141
    }
  ],
  "rules": {
    "doubleDown": ["person-conflict-ai"],
    "testing": ["listicle", "pov-format"],
    "dropped": ["self-complaint", "price-comparison"]
  }
}
```

**The daily report updates this automatically.** Each post gets tagged with its hook text, CTA, and attributed conversions. Over time, this builds a clear picture of which hook + CTA combinations actually drive revenue — not just views.

**CTA rotation:** When the report detects high impressions but low conversions, it automatically recommends rotating to a different CTA and tracks performance of each CTA separately. The agent should tag every post with the CTA used so the data accumulates.

**Decision rules:**
- Growing impressions + conversions → DOUBLE DOWN — make 3 variations immediately
- Steady impressions → Good — keep in rotation
- Declining impressions → Try 1 more variation
- Consistently low → DROP — try something radically different

### CTA Testing

When views are good but conversions are low, cycle through CTAs:
- "Download [App] — link in bio"
- "[App] is free to try — link in bio"
- "I used [App] for this — link in bio"
- "Search [App] on the App Store"
- No explicit CTA (just app name visible)

Track which CTAs convert best per hook category.

---

