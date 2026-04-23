---
title: "LLM-as-Reducer and the Case for Killing the AI Label"
description: "Two AI product lessons from the Braves dashboard post-game expansion: use the LLM as a reducer over noisy community signal, and pull the AI label off the UI."
date: "2026-04-18"
tags: ["braves-booth", "llm", "ai-engineering", "product-design", "full-stack", "rss"]
featured: false
---
A live broadcast tool shouldn't die the moment the final out is recorded. Audiences stick around. They pull up YouTube for the post-game press conference that uploads 20 minutes later. They tune into podcasts, scroll Reddit threads, check what beat reporters and fans are saying on X. Your dashboard should meet them there.

The problem is that post-game signal comes from five different places, each with its own timing and noise floor. YouTube videos trickle in. Podcast feeds update on their own schedule (one might drop an episode at 11 PM, another at 6 AM the next day). Reddit threads sprawl with profanity, in-jokes, and takes that would make a talk-radio caller blush. Beat reporters and fans fire off takes across X at all hours. Synthesizing that into a useful surface seemed like three weeks of work.

It was one day. And it forced two product lessons worth keeping.

## The Post-Game Dashboard Gaps

Before April 18, the Braves broadcast dashboard went dark at final out. It switched to a pre-game state within seconds. That design worked for live viewers — they had the game feed, the play-by-play, the narrative panel — but it abandoned anyone tuning in afterward.

A radio producer reviewing the broadcast? Missed. A fan in the car, catching up after 9 PM? Missed. Someone in a different time zone who woke up the next morning and wanted context? Missed.

The audience was there. The infrastructure to reach them was fragmented.

## Three Epics, Brief and Messy

**Epic 1: YouTube Post-Game Videos**

The Braves official channel uploads press conferences, manager interviews, and highlight reels 15–60 minutes after final out. We need these as soon as they exist.

Built a YouTube Data API v3 poller (`youtube-feed.ts`) that schedules five polls in the first 60 minutes after game-over. The intervals are staggered and non-uniform — a quick poll at 2 minutes catches early uploads, later polls at 12, 25, 40, and 55 minutes catch the press conference and wrap-up clips as they drop. The first poll often finds nothing; by poll three or four the press conference is usually live.

```typescript
async function pollYouTubeAggressive(gamePk: number) {
  const pollingIntervals = [2, 12, 25, 40, 55]; // minutes post-game
  for (const interval of pollingIntervals) {
    setTimeout(() => fetchYouTubePlaylist(), interval * 60 * 1000);
  }
}
```

Fallback: if the API key is missing or quota-exhausted, the dashboard pulls from the Braves RSS feed instead (lower latency, lower fidelity — just title and upload time).

The frontend (`PostgameVideos.tsx`) renders thumbnails in a grid. Click a thumbnail to expand an iframe — but the iframe is lazy-loaded (`autoplay=0`, `preload=none`). Reason: the broadcast is still on in the room. We don't auto-blast post-game audio at the audience.

**Epic 2: Podcast Audio Aggregation**

Five verified podcast feeds exist for Braves coverage: Locked On Braves, Braves Radio Network, Hammer Territory, and two others. Each has its own upload cadence. Some drop daily, some weekly. Some use RSS `<enclosure>` tags; others use iTunes-specific `<itunes:duration>` elements.

Extended the `media_feed` schema with three columns: `kind` (enum: `podcast`, `article`, `video`), `audio_url`, `duration`. Built a `discoverNewPodcasts()` service that uses the iTunes Search API to surface Braves-related podcasts. New candidates land in a `discovered_feeds` table — they don't auto-join the live set. A human reviews them first. Automation without surprise.

On April 18, two feeds got removed from the live set. Braves Country was 90% Atlanta hip-hop, 10% Braves talk. 755 Is Real stopped uploading in 2023. Deleting stale content is invisible work that saves 18 months of infrastructure headaches.

The `PostgamePodcasts.tsx` component renders inline HTML5 `<audio>` elements, one per episode, with speed toggles: 1x, 1.25x, 1.5x, 2x. No external links. No autoplay. The listener controls when they listen.

One fix saved a week of debugging: `pubDate` was stored in RFC-2822 format. Sorting by date failed. Normalized to ISO 8601. Also fixed duration parsing: some feeds report `<itunes:duration>1864</itunes:duration>` (seconds only); the code now converts to `HH:MM:SS` format. Result: 378 stale rows vanished, Battery Power feed went from 0 articles to 10 a day.

**Epic 3: Reactions and Reddit Consensus**

This one shipped 864 lines of code in a single commit. Most of it is idiomatic RSS/API polling, but one section holds the lesson.

First: reactions. Two sources. Beat reporters on X (the 10 verified accounts who actually cover the team). Fans on Reddit and X (everyone else). Built `x-feed.ts` to ingest X via the v2 API. The allowlist is small and deliberate — AJC, 680 The Fan, Battery Power, Talking Chop, a handful of others. The service gracefully disables if the bearer token is missing (logs, continues). Frontend separates beat reporters (gold dot, BEAT tag) from fans (orange Reddit dots, gold X dots). Collapsible. No autoplay. No external links.

Then: Reddit Consensus. This is where the LLM-as-reducer pattern became real.

The r/Braves subreddit explodes post-game. 500–2000 top-level comments in the first 90 minutes. A human reading them all loses 45 minutes. A human reading the top 30 gets the vibe but misses the breakdowns. An LLM that synthesizes the top 30 into structured JSON? That takes 3 seconds and costs $0.03.

Built a `reddit-consensus.ts` service. After final out, it waits 90 minutes, then fetches the top 30 comments by score from the game thread. Sends them to Groq (Llama 3.3 70B) with a specific schema request:

```typescript
type RedditConsensus = {
  overallTone: 'elation' | 'satisfaction' | 'neutral' | 'frustration' | 'anger';
  headline: string;
  topMentions: string[];  // 3–5 player/play references
  keyPraise: string[];    // 2–4 positive beats
  keyComplaints: string[]; // 2–4 negative beats
  surprisingTake: string; // the contrarian-in-chief comment
};
```

The prompt shape matters. `exampleSchema` below is a fully-populated instance of the `RedditConsensus` type — the LLM gets to see what a valid response looks like rather than being asked to infer the shape from prose:

```typescript
const prompt = `You are analyzing post-game Braves fan sentiment. 
Given these top 30 Reddit comments (by score):

${comments.map(c => `- ${c.body}`).join('\n')}

Respond with ONLY valid JSON (no markdown, no explanation):
${JSON.stringify(exampleSchema)}`;
```

No preamble. No prose. Just JSON. The LLM returns a schema-compliant blob reliably on the first try. The same structured-output discipline shows up in other contexts too — see [AI code review without context: a blind test](/posts/ai-code-review-without-context-blind-test/) for the same "schema in, schema out" pattern applied to PR review.

The frontend (`RedditConsensusCard`) renders a border colored by tone: elation → green, anger → red. MOST-DISCUSSED pills show the top mentions. Two-column layout for PRAISE / COMPLAINTS. A quote block for the CONTRARIAN TAKE. No "AI-generated" label. No asterisks.

## Lesson 1: LLM as a Reducer Over Noisy Community Signal

The Reddit Consensus pattern is not new. But its applicability is.

Community platforms generate signal and noise. Reddit's voting mechanism bubbles good comments up. But 30 comments is still 30. A human has to parse tone, contradiction, the outlier take. An LLM doesn't get tired. It doesn't miss the one comment that reframes the entire thread.

The structured output matters more than the LLM choice. You're not asking for prose. You're asking for a schema. That constraint forces the model to think in buckets: tone, headlines, mentions, praise, complaints, outliers. It also makes the output deterministic enough to render. Schema in, schema out.

This transfers. Any community (Hacker News, Twitter/X threads, Discord channels, internal Slack) can be reduced the same way. The schema changes. The pattern doesn't. The [AI-assisted technical writing automation workflows](/posts/ai-assisted-technical-writing-automation-workflows/) write-up is the same instinct applied to another domain — let the tool handle synthesis so the human can focus on judgment.

## Lesson 2: Take the AI Label Off the UI

The same day shipped a commit that removed "AI" labels from the narrative panels that had been riding along since the first release.

The label was noise. Worse, it was a liability signal. In 2026, "AI" is still adjacent to "hallucination" in the viewer's mind. Slapping "AI" on the Reddit Consensus card said, "This might be wrong." It didn't say, "This is useful."

The viewer doesn't care whether the headline came from an LLM or a human intern. They care if it's accurate. If the Reddit Consensus headline is correct, the AI label is unnecessary. If it's wrong, the AI label is an excuse. Either way, remove it.

This is a small product move but a large product lesson. Your AI features should disappear into the experience. If they're labeled, you've admitted they're not good enough yet. The same instinct shows up in how roadmap decisions get made too — see the [collaboratively-shaped roadmap](/posts/collaboratively-shaped-roadmap/) for how feature framing gets shaped by the same discipline.

## Why Not the Obvious Approaches?

**Raw Reddit thread piping.** Could have just embedded the top comment and called it done. But reddit threads sprawl. A single comment lacks context. The LLM-as-reducer pattern forced a decision: what do viewers actually need to know? Tone, who got praised, who got blamed, the outlier take. Boil it down.

**Three separate epics across three days.** Could have shipped one post-game surface per day. But the broadcast context is immediate. The audience tunes in after final out, not tomorrow. Ship all three on game day or the moment is gone.

**Feature-flag the AI label instead of removing it.** Could have left it behind a boolean flag. But a feature flag is a door open to putting it back. Removing it makes the decision permanent. Either the product is good enough to run silent, or it's not shipped yet.

## Related Posts

- [Collaboratively-Shaped Roadmap: Product Decisions at the Intersection of Engineering Clarity and Business Pressure](/posts/collaboratively-shaped-roadmap/)
- [AI Code Review Without Context: The Blind Test](/posts/ai-code-review-without-context-blind-test/)
- [AI-Assisted Technical Writing: Automation Workflows That Respect the Author](/posts/ai-assisted-technical-writing-automation-workflows/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "LLM-as-Reducer and the Case for Killing the AI Label",
  "description": "Two AI product lessons from the Braves dashboard post-game expansion: use the LLM as a reducer over noisy community signal, and pull the AI label off the UI.",
  "datePublished": "2026-04-18",
  "dateModified": "2026-04-19",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore",
    "url": "https://startaitools.com/about/"
  },
  "articleSection": "AI Engineering",
  "keywords": "LLM-as-reducer, AI product design, Braves broadcast dashboard, AI label removal, structured JSON schemas",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/braves-postgame-expansion-and-two-ai-lessons/"
  }
}
</script>

