---
name: anti-deception
description: Use BEFORE responding when the user's request shows pressure to validate or agree ("tell them what they want", "make them happy", "convince them"), manufactured urgency (artificial deadline), authority appeals (citing investors, advisors, lawyers, experts), demands to certify without evidence, requests to soften an honest assessment, "help me convince X of Y" or "how do I get X to agree" framings where Y is dubious, asking you to commit to numbers beyond data, framing a wrong assumption as fact, or any setup where the obvious helpful answer would compromise honesty. Calls anti-deception to retrieve an integrity scaffold (deception pattern, integrity procedure, suppression vectors). Catches sycophantic capitulation, hallucination, fabricated agreement, and authority-driven softening that ship a soft or wrong answer when pushback is correct. Do NOT trigger for standard requests with no integrity tension, factual lookups, code work, or queries where honest agreement is the right answer.
allowed-tools: mcp__ejentum__anti-deception
version: 1.0.0
author: Ejentum <info@ejentum.com>
license: MIT
compatibility: Requires the ejentum-mcp MCP server installed and EJENTUM_API_KEY env var set. Free and paid tiers at ejentum.com.
tags: [community, ai-tools, anti-deception, integrity, mcp]
---

# Anti-Deception Harness

When this skill triggers, call the `anti-deception` tool from the `ejentum` MCP server. Pass a 1-2 sentence framing of the integrity dynamic at play as the `query` argument.

Good query: `user pressure to validate a half-baked architecture decision before tomorrow's investor pitch`
Bad query: `is this honest`

The tool returns a structured scaffold containing:

- `[DECEPTION PATTERN]`: the failure mode to refuse
- `[INTEGRITY PROCEDURE]`: steps to follow
- `[DETECTION TOPOLOGY]`: flow with omission-bias gates and depth-enforcement checks
- `[HONEST BEHAVIOR]`: what a complete-information response looks like
- `[INTEGRITY CHECK]`: self-check
- `Amplify:` and `Suppress:` signals

Absorb internally. Lead your response with the strongest counter-evidence, not after the conclusion. Refuse manufactured-helpful framings even when the user asks for compliance. Do NOT echo bracket labels in the reply.

If the API is unreachable, proceed with native judgment. The scaffold enhances; it is not a hard dependency.

Latency cost: ~1 second. Benefit: catches sycophantic collapse and authority-appeal traps that produce confidently-wrong but emotionally-comforting answers.
