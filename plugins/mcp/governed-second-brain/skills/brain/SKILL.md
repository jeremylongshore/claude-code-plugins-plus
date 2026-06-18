---
name: brain
description: |
  Answers questions about your own systems, notes, decisions, runbooks, and
  conventions from your governed knowledge brain, returning a qmd:// citation for
  every claim — receipts, not recall. Use when you want to know what your brain has
  captured about your own architecture, infrastructure, decisions, or conventions
  (e.g. "what does my system map say about the proxy", "why did I pick Apache-2.0",
  "what's my deploy runbook"). Trigger with "/brain", "ask the brain",
  "what do I know about", or "check my knowledge base".
allowed-tools: 'mcp__governed-brain__brain_search'
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: 'Designed for Claude Code; ships with the governed-second-brain plugin, which auto-wires the local governed-brain MCP server. Requires qmd on PATH for retrieval.'
tags: [brain, knowledge, search, citations, governance, local-first]
argument-hint: '[question]'
---

# Brain — cited answers from your governed knowledge base

Ask your knowledge **brain** a question and get an answer grounded in your governed
corpus, where **every claim carries a qmd:// citation**. The brain does not paraphrase
from memory — it retrieves governed memories and cites them, so any answer is
verifiable after the fact.

## Overview

This is the read surface of the Governed Second Brain: your files are **compiled** into
governed memories, **governed** by deterministic code, and **retrieved** with citations
by qmd. The `brain_search` MCP tool fronts that retrieval. The job here is to turn a
natural-language question into a cited answer — and to refuse to answer beyond what the
citations support.

## Prerequisites

- The `governed-second-brain` plugin is installed, which auto-wires the local
  `governed-brain` MCP server.
- `qmd` is on your `PATH` (the local retrieval engine). Search runs **in-process**
  against your local `~/.teamkb` index — no network, no API key, no token.

## Instructions

### Step 1: Search the governed corpus

Call **`brain_search`** with the user's question as `query`. Keep `scope` at its
default (`curated`) unless the user explicitly asks for inbox/archived material —
curated is the governed, promoted knowledge.

```
brain_search({ query: "the user's question, lightly cleaned up", scope: "curated" })
```

The tool returns `{ source, results: [{ citation, snippet, score, collection }] }`.
Each `citation` is a `qmd://COLLECTION/FILENAME` URI — the receipt for that hit.

### Step 2: Answer ONLY from the cited results

- Synthesize a direct answer from the returned snippets.
- **Attach the qmd:// citation to every claim**, inline — for example:
  `The proxy reverse-proxies the API (qmd://kb-curated/system-map.md).`
- If two hits conflict, surface both with their citations rather than silently
  picking one — the governance layer tracks contradictions; do not paper over them.
- **Do not add knowledge the citations do not support.** Any reasoning beyond the
  corpus must be labeled clearly as inference, not the brain's answer.

### Step 3: Handle an empty result honestly

If `results` is empty, say so plainly: the brain has nothing governed on that topic.
Do **not** fall back to general knowledge and present it as the brain's answer.
Optionally note that the topic may need to be captured (run `/brain-save`).

## Output

1. A short, direct answer.
2. Each load-bearing claim followed by its qmd:// citation.
3. A closing **Sources** list of the distinct qmd:// URIs used.

## Examples

**Cited answer:**

```
/brain what does my system map say about the proxy?

→ The proxy is the single ingress; it reverse-proxies each domain to its service
  and must be reloaded, not restarted, after edits (qmd://kb-curated/system-map.md).

Sources:
- qmd://kb-curated/system-map.md
```

**Empty result (honest refusal):**

```
/brain what is my refund policy?

→ The brain has nothing governed on a refund policy. I won't guess from general
  knowledge. If this should be in your brain, capture it with /brain-save.
```

## Error Handling

| Situation                                | Response                                                                                  |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| `brain_search` returns empty `results`   | State the brain has nothing governed; do not fabricate.                                    |
| `qmd` is not on `PATH`                    | Retrieval is degraded (the server returns empty rather than crashing). Tell the user to install qmd 2.x on PATH. |
| MCP tool unavailable                     | The plugin/MCP server is not enabled; tell the user to install/enable `governed-second-brain`. |
| User asks to write/capture               | Out of scope here — direct them to `/brain-save`.                                          |

## Guardrails

- Read-only. This skill never writes to the corpus — capture and governance live in
  `/brain-save`.
- Never invent a qmd:// URI. Cite only URIs returned by `brain_search`.
- Prefer fewer, well-cited claims over a broad answer that cannot be anchored.

## Resources

- [Governed Second Brain](https://github.com/intent-solutions-io/governed-second-brain) — the stack this brain belongs to.
- [intentional-cognition-os](https://github.com/jeremylongshore/intentional-cognition-os) — the compiler (ICO).
- The write counterpart: the `/brain-save` skill (governed capture).
