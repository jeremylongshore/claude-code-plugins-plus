---
title: "How to Get Your ADK Agent into Google's Official Community Showcase"
description: "A tactical breakdown of contributing to Google's agent-starter-pack repository and getting recognized as a production-grade ADK reference implementation."
date: "2025-12-11"
tags: ["adk", "google-cloud", "vertex-ai", "open-source", "agent-development-kit"]
featured: false
---
# How to Get Your ADK Agent into Google's Official Community Showcase

Last week, Bob's Brain became one of only **4 projects** in Google's official Agent Starter Pack community showcase. Here's the tactical playbook for how we got there—and what it means for your ADK projects.

## The Numbers That Matter

| Metric | Value |
|--------|-------|
| Repository Stars | 3,690 |
| Total Forks | 1,041 |
| External Contributors | **1** (us) |
| Community Showcase Projects | **4** |

Out of 1,041 forks, we're the only external contributor. That's a 0.1% conversion rate from "forked the repo" to "actually contributed back."

## What We Submitted

PR #580 added Bob's Brain to the community showcase with:

- **Production deployment** on Vertex AI Agent Engine
- **Multi-agent architecture** (10 agents: orchestrator → foreman → 8 specialists)
- **Hard Mode compliance** (R1-R8 architectural rules enforced via CI)
- **95/100 quality score** with 65%+ test coverage
- **145 documentation files** including 28 canonical standards

## The Review Process

1. **Automated CLA check** - Sign Google's Contributor License Agreement
2. **Gemini Code Assist review** - Automated code analysis and suggestions
3. **Maintainer review** - Human approval from Google team

Total time from PR submission to merge: **~36 hours**

Google maintainer's response: *"thanks for this, approved and merged!"*

## Why This Matters for Your ADK Projects

Being in Google's showcase provides:

1. **Third-party validation** - Google's team reviewed and approved your architecture
2. **Discoverability** - 3,690+ developers see your reference implementation
3. **Credibility** - "Google-recognized" carries weight in other contributions

We immediately leveraged this in our other open PRs:

- A2A Samples PR #419 (foreman-worker pattern demo)
- Linux Foundation AI Card PR #7 (reference implementation)

Both now include a "Google Recognition" section citing the merged PR.

## The Technical Bar

What gets accepted into the showcase:

| Requirement | Our Implementation |
|-------------|-------------------|
| Production-ready | Deployed on Vertex AI Agent Engine |
| Well-documented | 145 docs, 28 canonical standards |
| ADK patterns | Hard Mode R1-R8 compliance |
| Real-world use case | Multi-agent SWE department |

What doesn't matter:

- Repo stars (we had ~50)
- Team size (solo developer)
- Company backing (independent)

## Tactical Recommendations

1. **Focus on documentation** - Google values comprehensive docs over clever code
2. **Show production deployment** - Demos are nice; production deployments convince
3. **Follow ADK patterns strictly** - Hard Mode compliance signals seriousness
4. **Be the first** - Empty showcases need content; yours could be featured

## Repository Links

- **Bob's Brain**: [github.com/jeremylongshore/bobs-brain](https://github.com/jeremylongshore/bobs-brain)
- **Merged PR #580**: [GoogleCloudPlatform/agent-starter-pack/pull/580](https://github.com/GoogleCloudPlatform/agent-starter-pack/pull/580)
- **Community Showcase**: [agent-starter-pack docs](https://github.com/GoogleCloudPlatform/agent-starter-pack/blob/main/docs/guide/community-showcase.md)

## What's Next

With Google recognition secured, we're pursuing:

- A2A Protocol samples (PR #419 pending)
- Linux Foundation AI Card standard (PR #7 pending)
- Conference speaking opportunities

The community contribution strategy is working. Build something real, document it thoroughly, contribute upstream. Recognition follows.

*Building production ADK agents? [Intent Solutions](https://intentsolutions.io) helps teams deploy multi-agent systems on Vertex AI Agent Engine.*
