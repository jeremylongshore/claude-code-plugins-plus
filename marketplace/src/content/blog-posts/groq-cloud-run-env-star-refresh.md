---
title: "Groq on Cloud Run, a Dep Bump, and a Star Refresh"
description: "Three quick fixes across three repos — a missing env var that broke production inference, a dependency bump, and a GitHub star count update."
date: "2026-04-12"
tags: ["devops", "automation"]
featured: false
---
Production was calling Vertex AI. It was supposed to call Groq.

April 12th was a three-commit day across three repos. No new features. No architecture decisions. Just the kind of small, necessary fixes that keep things running correctly.

## The Missing Environment Variable

The braves broadcast dashboard uses Groq for LLM inference. Locally, everything worked. The `GROQ_API_KEY` env var was in my `.env` file, the Groq client initialized, responses came back fast. Ship it to Cloud Run. Deploy succeeds. Dashboard loads.

Then inference calls start falling back to Vertex AI.

Cloud Run didn't have the `GROQ_API_KEY` in its environment. The application code had a fallback chain: try Groq, if the key is missing, fall back to Vertex AI. Silent. No error. No log entry saying "hey, you forgot to pass your API key." The fallback worked exactly as designed, which made the bug invisible.

The fix was one line in the Cloud Run service config:

```
fix: pass GROQ_API_KEY to Cloud Run so production uses Groq instead of Vertex AI
```

That's the whole commit message because that's the whole change. Add the env var to the deployment config. Redeploy. Production now hits Groq.

The real lesson: silent fallbacks are dangerous. The code did the right thing by not crashing. But it also did the wrong thing by not telling anyone it was degraded. A log line at WARNING level — "GROQ_API_KEY not set, falling back to Vertex AI" — would have caught this on the first deploy. I'll add that.

## Dependency Maintenance

The [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent) repo got an automated PR from Dependabot bumping the `google-adk` dev dependency. PR #155. Review, merge, move on.

Dependabot PRs are boring by design. That's the point. You want dependency updates to be boring. The alternative — ignoring them until something breaks or a CVE drops — is significantly less boring.

## Star Count Refresh

The [jeremylongshore.com](https://github.com/jeremylongshore/jeremylongshore.com) portfolio site displays GitHub star counts for featured projects. Those counts are hardcoded. Not fetched live, not cached — just numbers in the markup.

`claude-code-plugins` went from 1,725 to 1,912 stars. That's 187 new stars since the last refresh. The portfolio page was showing stale numbers. One commit to update them.

This is the kind of thing that should be automated. A GitHub Action that runs weekly, fetches current star counts via the API, and opens a PR if anything changed. It's 20 lines of workflow YAML. I haven't written it yet because manually updating a number every few weeks takes 30 seconds. But every time I do it manually, I think about writing the automation. One day the annoyance will cross the threshold.

## The Pattern

Three repos. Three commits. No drama. Days like this aren't interesting to read about, but they're the majority of real software work. You check production, fix a config, merge a dep bump, update a stale number. Then you move on to the thing that actually matters tomorrow.

---

**Related Posts:**

- [Building CAD DXF Agent From Zero to v0.1.0](/posts/building-cad-dxf-agent-from-zero-to-v010/)
- [SSE on Cloud Run: Every Platform Lie](/posts/sse-cloud-run-every-platform-lie/)
- [Three Projects, Two Reverts, One Day](/posts/three-projects-two-reverts-one-day/)
