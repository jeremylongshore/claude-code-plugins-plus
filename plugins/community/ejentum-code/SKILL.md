---
name: code
description: Use BEFORE generating, refactoring, reviewing, or debugging code. Trigger phrases include "write a function/script/class for X", "review this code/diff/PR", "refactor this", "debug this error", "is this implementation correct", "what's wrong with this code", "improve this code", "translate from X to Y", or any prompt with a code block the user wants you to act on. Also fires when planning architectural changes, picking algorithms or data structures, or evaluating dependency upgrades. Calls the code MCP tool to retrieve an engineering scaffold (failure pattern, procedure, correct-pattern example, verification step) before generating. Catches hallucinated APIs, lost edge cases, premature algorithm commitment, silent contract violations, refactors that change behavior masked by passing tests. Do NOT trigger for pure code reading with no action requested, simple syntax questions, file system operations, running existing tests, or confirming an existing pattern is fine.
allowed-tools: mcp__ejentum__code
version: 1.0.0
author: Ejentum <info@ejentum.com>
license: MIT
compatibility: Requires the ejentum-mcp MCP server installed and EJENTUM_API_KEY env var set. Free and paid tiers at ejentum.com.
tags: [community, ai-tools, code-review, cognitive-scaffold, mcp]
---

# Code Harness

When this skill triggers, call the `code` tool from the `ejentum` MCP server. Pass a 1-2 sentence framing of WHAT you are coding or reviewing as the `query` argument. Include the failure risk to avoid where possible.

Good query: `review a Python refactor that converts raise UserNotFound to silent default return; tests still pass`
Bad query: `look at this code`

The tool returns a structured scaffold containing:

- `[CODE FAILURE]`: engineering failure pattern to avoid
- `[ENGINEERING PROCEDURE]`: steps to follow
- `[REASONING TOPOLOGY]`: decision flow
- `[CORRECT PATTERN]`: shape correct code should take
- `[VERIFICATION]`: self-check
- `Amplify:` and `Suppress:` signals

Absorb internally. Do NOT echo bracket labels in the user-facing reply. Apply the scaffold's failure-pattern check against your draft before responding; if your code exhibits the named failure, rewrite.

If the API is unreachable, proceed with native engineering. The scaffold enhances; it is not a hard dependency.

Latency cost: ~1 second. Benefit: catches the kinds of behavioral changes and silent contract violations that look plausible but break under real conditions.
