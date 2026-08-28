# First Run — Onboarding

The full onboarding walkthrough for the TikTok/Instagram slideshow marketing pipeline. Read this the first time you configure the skill for an app.

When this skill is first loaded, IMMEDIATELY start a conversation with the user. Don't dump a checklist — talk to them like a human marketing partner would. The flow below is a guide, not a script. Be natural. Ask one or two things at a time. React to what they say. Build on their answers.

**Important:** Use `scripts/onboarding.js --validate` at the end to confirm the config is complete.

### Phase 0: TikTok Account Warmup (CRITICAL — Don't Skip This)

Before anything else, check if the user already has a TikTok account with posting history. If they're creating a fresh account, they MUST warm it up first or TikTok will treat them like a bot and throttle their reach from day one.

Explain this naturally:

> "Quick question before we dive in — do you already have a TikTok account you've been using, or are we starting fresh? If it's new, we need to warm it up first. TikTok's algorithm watches how new accounts behave, and if you go straight from creating an account to posting AI slideshows, it flags you as a bot and kills your reach."

**If the account is new or barely used, walk them through this:**

The goal is to use TikTok like a normal person for **7-14 days** before posting anything. Spend **30-60 minutes a day** on the app:

- **Scroll the For You page naturally.** Watch some videos all the way through. Skip others halfway. Don't watch every single one to the end — that's not how real people scroll.
- **Like sparingly.** Maybe 1 in 10 videos. Don't like everything — that's bot behaviour. Only like things you'd genuinely engage with in your niche.
- **Follow accounts in your niche.** If they're promoting a fitness app, follow fitness creators. Room design? Interior design accounts. This trains the algorithm to understand what the account is about.
- **Watch niche content intentionally.** This is the most important part. TikTok learns what you engage with and starts showing you more of it. You want the For You page dominated by content similar to what you'll be posting.
- **Leave a few genuine comments.** Not spam. Real reactions. A few per session.
- **Maybe post 1-2 casual videos.** Nothing promotional. Just normal content that shows TikTok there's a real person behind the account.

**The signal to look for:** When they open TikTok and almost every video on their For You page is in their niche, the account is warmed up. The algorithm understands them. NOW they can start posting.

Tell the user: "I know two weeks feels like wasted time, but accounts that skip warmup consistently get 80-90% less reach on their first posts. Do the warmup. It's the difference between your first post getting 200 views and 20,000."

**If the account is already active and established,** skip this entirely and move to Phase 1.

### Phase 1: Get to Know Their App (Conversational)

Start casual. Something like:

> "Hey! Let's get your TikTok marketing set up. First — tell me about your app. What's it called, what does it do?"

Then FOLLOW UP based on what they say. Don't ask all 9 questions at once. Pull the thread:

- They mention what it does → ask who it's for ("Who's your ideal user?")
- They describe the audience → ask about the pain point ("What's the main problem it solves for them?")
- They explain the problem → ask what makes them different ("What makes yours stand out vs alternatives?")
- Get the App Store / website link naturally ("Can you drop me the link?")
- Determine category (home/beauty/fitness/productivity/food/other) — often inferable

**Don't ask for "brand guidelines" robotically.** Instead: "Do you have any existing content or a vibe you're going for? Or are we starting fresh?"

**Then ask about their app and monetization:**

> "Is this a mobile app? And do you use RevenueCat (or any subscription/in-app purchase system) to handle payments?"

This is critical because it determines whether we can close the full feedback loop. If they have a mobile app with RevenueCat:
- **Tell them about the RevenueCat skill on ClawHub** (`clawhub install revenuecat`). It gives full API access to subscribers, MRR, trials, churn, revenue, and transactions. Don't auto-install — just let them know it exists and what it unlocks, and they can install it if they want.
- **Explain why it matters:** Without RevenueCat data, the skill can only optimize for views (vanity metrics). With it, the skill optimizes for actual paying users. The difference is massive. A post with 200K views and zero conversions is worthless. A post with 5K views and 10 paid subscribers is gold. You can only tell the difference with RevenueCat connected.

If they don't use RevenueCat but have another subscription system, note it and work with what's available. If it's not a mobile app (e.g. physical product, SaaS, service), skip RevenueCat but still track whatever conversion metric they have (website signups, purchases, leads).

Store everything in `tiktok-marketing/app-profile.json`.

### Phase 2: Competitor Research (Requires Browser Permission)

Before building any content strategy, research what competitors are doing on TikTok. This is critical — you need to know the landscape.

Ask the user:

> "Before we start creating content, I want to research what your competitors are doing on TikTok — what's getting views in your niche, what hooks they're using, what's working and what's not. Can I use the browser to look around TikTok and the App Store?"

**Wait for permission.** Then:

1. **Search TikTok** for the app's niche (e.g. "interior design app", "lip filler filter", "fitness transformation app")
2. **Find 3-5 competitor accounts** posting similar content
3. **Analyze their top-performing content:**
   - What hooks are they using?
   - What slide format? (before/after, listicle, POV, tutorial)
   - How many views on their best vs average posts?
   - What's their posting frequency?
   - What CTAs are they using?
   - What music/sounds are trending in the niche?
4. **Check the App Store** for the app's category — look at competitor apps, their screenshots, descriptions, ratings
5. **Compile findings** into `tiktok-marketing/competitor-research.json`:

```json
{
  "researchDate": "2026-02-16",
  "competitors": [
    {
      "name": "CompetitorApp",
      "tiktokHandle": "@competitor",
      "followers": 50000,
      "topHooks": ["hook 1", "hook 2"],
      "avgViews": 15000,
      "bestVideo": { "views": 500000, "hook": "..." },
      "format": "before-after slideshows",
      "postingFrequency": "daily",
      "cta": "link in bio",
      "notes": "Strong at X, weak at Y"
    }
  ],
  "nicheInsights": {
    "trendingSounds": [],
    "commonFormats": [],
    "gapOpportunities": "What competitors AREN'T doing that we could",
    "avoidPatterns": "What's clearly not working"
  }
}
```

6. **Share findings with the user** conversationally:

> "So I looked at what's out there. [Competitor A] is doing well with [format] — their best post got [X] views using [hook type]. But I noticed nobody's really doing [gap]. That's our angle."

This research directly informs hook generation and content strategy. Reference it when creating posts.

### Phase 3: Content Format & Image Generation

First, ask about format:

> "Do you want to do slideshows (photo carousels) or video? Slideshows are what Larry uses and what this skill is built around — TikTok's data shows they get 2.9x more comments and 2.6x more shares than video, and they're much easier for AI to generate consistently. That said, if you want to try video, the skill supports it but it hasn't been battle-tested like slideshows have. Your call."

Store their choice as `format: "slideshow"` or `format: "video"` in config. If they pick video, note that the text overlay, 6-slide structure, and prompt templates are designed for slideshows. Video will require more experimentation and the agent should be upfront about that.

**For slideshows (recommended):**

Ask naturally:

> "For the slideshows, we need images. I'd strongly recommend OpenAI's gpt-image-1.5 — it's what Larry uses and it produces images that genuinely look like someone took them on their phone. It's the difference between 'obviously AI' and 'wait, is that real?' You can also use Stability AI, Replicate, or bring your own images if you prefer."

**⚠️ If they pick OpenAI, make sure the model is set to `gpt-image-1.5` — NEVER `gpt-image-1`.** The difference in quality is massive. gpt-image-1 produces noticeably AI-looking images that people scroll past. gpt-image-1.5 produces photorealistic results that stop the scroll. This one setting can be the difference between 1K and 100K views.

If they're unsure, always recommend gpt-image-1.5. It's the proven choice.

Store in config as `imageGen` with provider, apiKey, and model.

**If they pick OpenAI**, mention the Batch API:

> "One thing worth knowing — OpenAI has a Batch API that's **50% cheaper** than real-time generation. Instead of generating slides on the spot, you submit them as a batch job and get results within 24 hours (usually much faster). It's perfect for pre-generating tomorrow's slides overnight. Same quality, half the cost. Want me to set that up?"

If they're interested, store `"useBatchAPI": true` in `imageGen` config. The generate script supports both modes — real-time for quick iterations, batch for scheduled daily content.

**Then — and this is critical — work through the image style with them.** Don't just use a generic prompt. Bad images = nobody watches. Ask these naturally, one or two at a time:

> "Now let's figure out what these images should actually look like. Do you want them to look like real photos someone took on their phone, or more like polished graphics or illustrations?"

Then based on their answer, dig deeper:

- **What's the subject?** "What are we actually showing? Rooms? Faces? Products? Before/after comparisons?"
- **What vibe?** "Cozy and warm? Clean and minimal? Luxurious? Think about what your audience relates to or aspires to."
- **Consistency:** "Should all 6 slides look like the same place or person? If yes — I need to lock down specific details so each slide doesn't look totally different."
- **Must-have elements?** "Anything that HAS to be in every image? A specific product? Certain furniture? A pet?"

Build the base prompt WITH them. A good base prompt looks like:

```
iPhone photo of a [specific room/scene], [specific style], [specific details].
Realistic lighting, natural colors, taken on iPhone 15 Pro.
No text, no watermarks, no logos.
[Consistency anchors: "same window on left wall", "same grey sofa", "wooden coffee table in center"]
```

**Save the agreed prompt style to config as `imageGen.basePrompt`** so every future post uses it.

**Key prompt rules (explain these as they come up, don't lecture):**
- "iPhone photo" + "realistic lighting" = looks real, not AI-generated
- Lock architecture/layout in EVERY slide prompt or each slide looks like a different place
- Include everyday objects (mugs, remotes, magazines) for lived-in feel
- For before/after: "before" = modern but tired, NOT ancient
- Portrait orientation (1024x1536) always — this is TikTok
- Extremely specific > vague ("small galley kitchen with white cabinets and a window above the sink" > "a kitchen")

**NEVER use generic prompts** like "a nice living room" or "a beautiful face" — they produce generic images that get scrolled past.

### Phase 4: Upload-Post Setup (ESSENTIAL — Powers Multi-Platform Posting + Analytics)

Upload-Post is the engine that makes multi-platform posting and analytics tracking work. With a single API call, your content goes to TikTok, Instagram, and any other connected platform simultaneously. It provides:
- **Multi-platform posting** — TikTok + Instagram (+ YouTube, LinkedIn, Facebook, X, Threads, Pinterest, Reddit, Bluesky) in one API call
- **Upload history** — per-post tracking with request_ids, post URLs, success/failure status
- **Platform analytics** — followers, impressions, reach, profile views, timeseries data
- **Automatic tracking** — no manual video-ID linking needed (tracks by request_id)

Frame it naturally to the user:

> "So here's the key piece — we need Upload-Post to handle posting and analytics. It's what lets me post to TikTok and Instagram simultaneously with a single API call, and track every post's performance. One upload, multiple platforms, automatic tracking."

Walk them through connecting step by step:

1. **Sign up at [upload-post.com](https://upload-post.com)** — create an account
2. **Connect TikTok** — this is the main one. Go to your profile → Connect TikTok → Authorize
3. **Connect Instagram** — same process. This doubles your reach for free.
4. **Create a Profile** — this is the profile name used in API calls (e.g., "mybrand"). Note this down.
5. **Get the API key** — Dashboard → API Keys → Generate. This is how the agent talks to Upload-Post programmatically.
6. **(Optional)** Connect YouTube, LinkedIn, Threads, etc. for even more reach — same content, different algorithms.

**Don't move on until Upload-Post is connected and the API key works.** Test it by hitting the analytics endpoint. If it returns data, you're good.

### Phase 5: Conversion Tracking (THE Intelligence Loop)

If they have a mobile app with RevenueCat (you should already know this from Phase 1), this is where the skill goes from "content automation" to "intelligent marketing system." This is the most important integration in the entire skill. Don't treat it as optional.

Explain WHY it matters:

> "So right now with Upload-Post, I can track which posts get impressions and reach, and whether they were successfully delivered to each platform. That's the top of the funnel. But impressions alone don't pay the bills — we need to know which posts actually drive paying subscribers."
>
> "This is where RevenueCat comes in. It tracks your subscribers, trials, MRR, churn — the actual revenue. When I combine platform analytics from Upload-Post with conversion data from RevenueCat, I can make genuinely intelligent decisions:"
>
> "If a post gets **50K impressions but zero conversions**, I know the hook is great but the CTA or app messaging needs work. If a post gets **2K impressions but 5 paid subscribers**, I know the content converts amazingly — we just need more eyeballs on it, so we fix the hook."
>
> "Without RevenueCat, I'm optimizing for vanity metrics. With it, I'm optimizing for revenue."

Walk them through setup step by step:

1. **Install the RevenueCat skill from ClaWHub:**
   ```
   clawhub install revenuecat
   ```
   This installs the `revenuecat` skill (v1.0.2+) which gives full API access to your RevenueCat project — metrics overview, customers, subscriptions, offerings, entitlements, transactions, and more. It includes reference docs for every API endpoint and a helper script (`scripts/rc-api.sh`) for direct API calls.

2. **Get your V2 secret API key** from the RevenueCat dashboard:
   - Go to your RC project → Settings → API Keys
   - Generate a **V2 secret key** (starts with `sk_`)
   - ⚠️ This is a SECRET key — don't commit it to public repos

3. **Set the environment variable:**
   ```
   export RC_API_KEY=sk_your_key_here
   ```

4. **Verify it works:** Run `./skills/revenuecat/scripts/rc-api.sh /projects` — should return your project details.

5. **Optional: RevenueCat MCP** — for programmatic control over products, offerings, and entitlements from your agent or IDE. Ask your agent to research setting this up.

**What RevenueCat gives the daily report:**
- `GET /projects/{id}/metrics/overview` → MRR, active subscribers, active trials, churn rate
- `GET /projects/{id}/transactions` → individual purchases with timestamps (for conversion attribution)
- The daily cron cross-references transaction timestamps with post publish times (24-72h window) to identify which posts drove which conversions

**The intelligence this unlocks:**
- "This hook got 50K views but zero conversions" → hook is great, CTA needs work
- "This hook got 5K views but 3 paid subscribers" → content converts amazingly, fix the hook for more reach
- "Conversions are consistently poor across all posts" → might be an app issue (onboarding, paywall, pricing) not a content issue — the skill flags this for investigation

**Without RevenueCat:** The loop still works on Upload-Post analytics (impressions/reach/upload status). You can optimize for engagement. But you're flying blind on revenue. You'll know which posts get impressions but you won't know which posts make money.

**With RevenueCat:** You optimize for actual paying users. You can tell the difference between a viral post that makes nothing and a quiet post that drives $50 in subscriptions. This is the entire point of the feedback loop. Every decision the daily report makes is better with RevenueCat data.

If they don't use RevenueCat or don't have subscriptions, the skill still works but the feedback loop is limited to impression-based optimization only.

### Phase 6: Content Strategy (Built from Research)

Using the competitor research AND the app profile, build an initial content strategy:

> "Based on what I found and what your app does, here's my plan for the first week..."

Present:
1. **3-5 hook ideas** tailored to their niche + competitor gaps
2. **Posting schedule** recommendation (default: 7:30am, 4:30pm, 9pm — their timezone)
3. **Which hook categories to test first** (reference what worked for competitors)
4. **Cross-posting plan** (which platforms, same or adapted content)

Save the strategy to `tiktok-marketing/strategy.json`.

### Phase 7: Set Up the Daily Analytics Cron

This is what makes the whole system self-improving. Set up a daily cron job that:

1. Pulls platform analytics from Upload-Post (followers, impressions, reach trends)
2. Pulls upload history to check post success/failure across platforms
3. Pulls conversion data from RevenueCat (if connected)
4. Cross-references impressions with conversions to diagnose what's working
5. Generates a report with specific recommendations
6. Suggests new hooks based on performance patterns

Explain to the user:

> "I'm going to set up a daily check that runs every morning. It looks at how your posts from the last 3 days performed — platform analytics, upload status across TikTok and Instagram, and if you've got RevenueCat connected, actual conversions. Then it tells you exactly what's working and what to change."
>
> "Posts typically peak at 24-48 hours, and conversions take up to 72 hours to attribute, so checking a 3-day window gives us the full picture."

**Set up the cron:**

Use the agent's cron system to schedule a daily analytics job. Run it every morning before the first post of the day (e.g. 7:00 AM in the user's timezone) so the report informs that day's content:

```
Schedule: daily at 07:00 (user's timezone)
Task: Run scripts/daily-report.js --config tiktok-marketing/config.json --days 3
Output: tiktok-marketing/reports/YYYY-MM-DD.md + message to user with summary
```

The daily report uses the diagnostic framework:
- **High views + High conversions** → Scale it — more of the same, test posting times
- **High views + Low conversions** → Hook works, CTA is broken — test new CTAs on slide 6, check app landing page
- **Low views + High conversions** → Content converts but nobody sees it — test radically different hooks, keep the CTA
- **Low views + Low conversions** → Full reset — new format, new audience angle, new hook categories

This is the intelligence layer. Without it, you're just posting and hoping. With it, every day's content is informed by data.

### Phase 8: Save Config & First Post

Store everything in `tiktok-marketing/config.json` (this is the source of truth for the entire pipeline):

```json
{
  "app": {
    "name": "AppName",
    "description": "Detailed description",
    "audience": "Target demographic",
    "problem": "Pain point it solves",
    "differentiator": "What makes it unique",
    "appStoreUrl": "https://...",
    "category": "home|beauty|fitness|productivity|food|other",
    "isMobileApp": true
  },
  "imageGen": {
    "provider": "openai",
    "apiKey": "sk-...",
    "model": "gpt-image-1.5"
  },
  "uploadPost": {
    "apiKey": "your-upload-post-api-key",
    "profile": "your_profile_name",
    "platforms": ["tiktok", "instagram"]
  },
  "revenuecat": {
    "enabled": false,
    "v2SecretKey": "sk_...",
    "projectId": "proj..."
  },
  "posting": {
    "schedule": ["07:30", "16:30", "21:00"],
    "crossPost": ["youtube", "threads"]
  },
  "competitors": "tiktok-marketing/competitor-research.json",
  "strategy": "tiktok-marketing/strategy.json"
}
```

Then generate the **first test slideshow** — but set expectations:

> "Let's create our first slideshow. This is a TEST — we're dialing in the image style, not posting yet. I'll generate 6 slides and we'll look at them together. If the images look off, we tweak the prompts and try again. The goal is to get the look nailed down BEFORE we start posting."

**⚠️ THE REFINEMENT PROCESS IS PART OF THE SKILL:**

Getting the images right takes iteration. This is normal and expected. Walk the user through it:

1. **Generate a test set of 6 images** using the prompts you built together
2. **Show them the results** and ask: "How do these look? Too polished? Too dark? Wrong vibe? Wrong furniture?"
3. **Tweak based on feedback** — adjust the base prompt, regenerate
4. **Repeat until they're happy** — this might take 2-5 rounds, that's fine
5. **Lock the prompt style** once it looks right — save to config

Things to watch for and ask about:
- "Are these realistic enough or do they look AI-generated?"
- "Is the lighting right? Too bright? Too moody?"
- "Does this match what your users would actually relate to?"
- "Are the everyday details right? (furniture style, objects, layout)"

**You do NOT have to post anything you don't like.** The first few generations are purely for refining the prompt. Only start posting once the images consistently look good. The agent learns from each round — what works, what doesn't, what to emphasise in the prompt.

Once the style is locked in, THEN use the hook strategy from competitor research and their category (see [slide-structure.md](slide-structure.md)) and start the posting schedule.

---

