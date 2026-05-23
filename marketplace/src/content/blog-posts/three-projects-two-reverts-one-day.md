---
title: "Three Projects, Two Reverts, One Day"
description: "A domain migration saga with two reverts, a broadcast dashboard hitting production, and DWG support on Cloud Run — all in one day."
date: "2026-03-03"
tags: ["devops", "web-development", "ci-cd", "full-stack", "firebase"]
featured: false
---
Nothing teaches you Firebase Hosting like renaming your domain three times before lunch.

March 3rd was a heavy day. Three projects, dozens of commits, and a domain migration that went sideways twice before landing. Here's the unfiltered timeline.

## The Domain Migration Saga

The claude-code-plugins marketplace needed a new home. `claudecodeplugins.io` was fine for a developer tool, but `tonsofskills.com` was the brand direction. Simple domain swap. Should take 20 minutes.

It took six commits and two reverts.

### The Timeline

Here's the actual commit sequence. Read it slowly.

1. `feat: migrate domain from claudecodeplugins.io to tonsofskills.com`
2. `feat: add tonsofskills.com Firebase hosting and claudecodeplugins.io redirect`
3. `Revert "feat: add tonsofskills.com Firebase hosting..."`
4. `Revert "feat: migrate domain from claudecodeplugins.io to tonsofskills.com"`
5. `feat: add tonsofskills.com 301 redirect to claudecodeplugins.io`
6. `feat: migrate primary domain to tonsofskills.com`

Commits 3 and 4 are the reverts. Two of them. Back to back. In production.

### What Went Wrong

The first attempt (commits 1-2) seemed correct. Update `firebase.json` with both domains, set up redirects from old to new. Deploy. Done.

Except Firebase Hosting doesn't work the way you think it does.

When you configure two custom domains on a single Firebase Hosting site, the **order of hosting targets in `firebase.json` determines the canonical domain**. I had `tonsofskills.com` first and `claudecodeplugins.io` second. Firebase treated `tonsofskills.com` as primary — good — but the redirect from `claudecodeplugins.io` wasn't a redirect at all. It was serving the same site on both domains. No 301. No canonical signal. Just two identical sites competing for search ranking.

DNS propagation made this worse. The new domain was live but not fully propagated. Some users hit the old domain and got the site. Others hit the new domain and got a certificate error because the SSL cert hadn't provisioned yet. For about 15 minutes, neither domain worked reliably.

This is the moment where you stop deploying and start reverting.

### The Fix

Revert everything. Go back to the known working state. Then approach it differently.

Commit 5 was the key insight: instead of trying to serve both domains simultaneously, set up a **standalone redirect**. The old domain gets a 301 pointing to the new one. No shared hosting target. No ambiguity about which domain is canonical.

Commit 6 completed the migration by making `tonsofskills.com` the sole primary domain with its own Firebase Hosting target.

### The Lesson

Firebase Hosting redirect rules and custom domain configuration are two separate systems. Redirect rules in `firebase.json` handle path-level redirects within a site. Custom domain redirects need to be configured at the hosting target level — or better yet, use a dedicated redirect target.

Don't try to be clever with multi-domain hosting configs. One domain per hosting target. 301 redirect everything else.

Meanwhile, the rest of the domain day wasn't wasted. The homepage got a full redesign with a dark theme matching the Braves Booth aesthetic. A `/research` page launched with 6 data-driven analysis documents. UTM tracking and full event instrumentation went in across the site. And a subtle "by intent solutions io" byline landed in the hero section.

All of that shipped cleanly. The domain migration was the only thing that fought back.

## Braves Goes to Production

While the domain migration was imploding, the Braves Booth Intelligence dashboard was quietly shipping to GCP.

Three PRs landed on March 3rd:

**PR #4: GCP Deploy Pipeline** — Gemini 2.5 Pro integration with Firebase Cloud Run. The backend rewrite moved from a local Fastify server to a Cloud Run service. This is a broadcast tool, so cold start latency matters. Cloud Run's minimum instances setting keeps one container warm at all times.

**PR #5: Responsive Layout** — The dashboard was built for a desktop monitor in a broadcast booth. But producers also check it on phones during commutes. Mobile layout stacks the panels vertically. Desktop preserves the 3-column grid. No CSS framework gymnastics — just a media query breakpoint at 768px.

**PR #6: Real Weather** — The original dashboard had a weather stub returning hardcoded "72°F, Clear." That's fine for development. Not fine when a broadcaster says "it's a beautiful night here at Truist Park" and the dashboard disagrees. Open-Meteo API provides free, no-key-required weather data. The integration pulls current conditions for the game venue coordinates.

Also landed: 6 missing Braves broadcast co-host profiles. The dashboard serves context about who's on the broadcast — bio snippets, preferred stat categories, conversation style notes. Missing profiles meant blank panels during games with those co-hosts.

The PR review cycle was productive. Refactored test patterns to use `it.each` for cohost profile coverage — testing 8 profiles with 8 individual test cases is noisy. One parameterized test with all profiles is cleaner and catches the same bugs.

```typescript
it.each([
  ["Joe Simpson", "veteran analyst"],
  ["Nick Green", "former player"],
  ["Brian Jordan", "former outfielder"],
  // ... all 8 co-hosts
])("getCohostProfile(%s) returns role %s", (name, expectedRole) => {
  const profile = getCohostProfile(name);
  expect(profile.role).toContain(expectedRole);
});
```

## CAD Agent Gets DWG Support

The third project of the day: `cad-dxf-agent` gained DWG file support on Cloud Run.

DWG is Autodesk's proprietary binary format. You can't just parse it like DXF. You need the ODA File Converter — a binary tool from the Open Design Alliance that converts DWG to DXF on the fly.

Getting ODA File Converter running in a Cloud Run container required:

- Downloading the Linux installer into the Docker image
- Installing its dependencies (Qt5 libraries, which are not small)
- Setting up a temp directory workflow: upload DWG → convert to DXF → process DXF → clean up

The other significant change: anonymous Firebase users can now bypass the license check. The CAD agent is a tool for engineers. Forcing account creation before someone can test it with one file is a conversion killer. Anonymous auth lets them try it immediately. License enforcement kicks in after the free tier limit.

Testing was the real work. 25+ end-to-end tests using sourced DXF files, batched to avoid Firebase Auth rate-limiting. Firebase's auth API will throttle you if you create too many anonymous users in rapid succession. The solution: batch tests into groups of 5 with a small delay between batches. Not elegant, but it works without hitting 429s.

The DWG container image went from ~200MB to ~800MB thanks to the Qt5 dependencies. That's the price of supporting a proprietary format without paying for Autodesk's SDK. ODA File Converter is free for non-commercial use and handles AutoCAD 2024 files without issues. Worth the image bloat.

## The Scorecard

| Project | Commits | Key Outcome |
|---------|---------|-------------|
| claude-code-plugins | 10+ | Domain migrated (eventually) |
| braves | 3 PRs | Production on GCP |
| cad-dxf-agent | 2 features | DWG support + anonymous access |

The domain migration was the most frustrating work of the day. The Braves deploy was the most satisfying. The CAD agent changes were the most impactful for users.

Days like this are why I keep a commit log. The narrative in your head says "I migrated a domain." The commits say "I migrated a domain, broke it, reverted it, broke it differently, reverted again, and then migrated it correctly." The second version is more useful for next time.

Three projects in one day is not a flex. It's a Tuesday. The flex is having the discipline to revert when something breaks instead of pushing forward and making it worse.

---

## Related Posts

- [Zero to CI: Full-Stack Dashboard in One Session](/posts/zero-to-ci-full-stack-dashboard-one-session/) — The day the Braves dashboard was born
- [Production Release Engineering: Shipping v4.5.0](/posts/production-release-engineering-v450/) — Automated release workflows for the plugins marketplace
- [Scaling AI Batch Processing with Vertex AI Gemini](/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) — Earlier plugins marketplace infrastructure work
