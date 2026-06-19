# Glossary schema

The glossary is an optional companion to `seo-blog-writer`. When you supply a
`glossary.json` file and run `scripts/inject-glossary-links.py` against your
draft HTML, the first mention of each known term in the post becomes an
auto-link to a definition page on your site (with a tooltip-ready
`data-definition` attribute the bundled `decorate.js` snippet picks up).

This file documents the JSON shape. Nothing in this repo generates the
definition pages themselves yet (Tier B work, future release) — you bring the
template and the URL space.

## File shape

```json
{
  "version": "1.0",
  "generated_at": "2026-05-25",
  "terms": [
    { "slug": "...", "term": "...", "aliases": [...], "short": "...", ... },
    ...
  ]
}
```

The injector also accepts a top-level JSON array of terms (no wrapping
object), so the smallest valid file is just `[{"slug": "mcp", ...}]`.

## Per-term fields

| Field | Required | What it does |
|---|---|---|
| `slug` | **yes** | URL slug appended to `--base-url`. Becomes the `<a href>` target (`/glossary/<slug>/`). Must be unique. |
| `term` | **yes** | Canonical display name. Used as a fallback alias if `aliases` is missing. |
| `aliases` | recommended | List of lowercase strings the injector matches against (case-insensitive). Include singular + plural, acronym + expansion, hyphenated + spaced variants. Longest alias wins per match, so you can safely list `"mcp"` alongside `"model context protocol"`. |
| `short` | recommended | One sentence (~120 chars). Becomes the `data-definition` attribute on the link — the hover tooltip when `decorate.js` is on the page. Plain text only (no HTML). |
| `priority` | optional | Lower number = picked first when the per-post link cap is reached. Default `99`. Use `1` for the few terms you most want linked everywhere. |
| `definition` | optional | Long-form definition (40–200 words). Not consumed by the injector; reserved for the future static-page generator. |
| `when_to_use` | optional | One short paragraph. Not consumed by the injector. |
| `see_also` | optional | List of other slugs. Not consumed by the injector. |

Unknown fields are ignored, so you can extend the schema for your own
templating without breaking anything.

## Worked starter file

A minimum-viable `glossary.json` you can copy and grow:

```json
{
  "version": "1.0",
  "generated_at": "2026-05-25",
  "terms": [
    {
      "slug": "mcp",
      "term": "MCP",
      "aliases": ["mcp", "model context protocol"],
      "short": "Anthropic's open standard for connecting LLMs to external tools and data over JSON-RPC.",
      "priority": 1
    },
    {
      "slug": "webhook",
      "term": "webhook",
      "aliases": ["webhook", "webhooks"],
      "short": "An HTTP POST one system sends to another when an event occurs — push, not poll.",
      "priority": 1
    },
    {
      "slug": "idempotency",
      "term": "idempotency",
      "aliases": ["idempotency", "idempotent", "idempotence"],
      "short": "Calling the operation twice has the same effect as calling it once.",
      "priority": 2
    },
    {
      "slug": "llm",
      "term": "LLM",
      "aliases": ["llm", "large language model"],
      "short": "Large Language Model — a transformer-based model trained on internet-scale text.",
      "priority": 2
    }
  ]
}
```

## Choosing aliases well

The injector matches on word boundaries and rejects matches embedded in
identifier-like compounds (so `agent` won't fire inside `user-agent`, and
`mcp` won't fire inside `@scope/ai-seo-mcp`). That eliminates most false
positives. Two practical rules:

1. **Include plurals and the expanded form together.** `"aliases":
   ["mcp", "model context protocol"]` lets either phrasing in the post link
   to the same page; the injector picks the longest match per location.
2. **Don't add aliases that overlap with common English.** Aliasing a term
   to `"app"` or `"tool"` will saturate the link cap on the first three
   sentences. Keep aliases technical and specific.

## Per-post linking rules (enforced by the injector)

- **First occurrence only** per term per post (Wikipedia rule).
- **Hard cap** (default 6) of total auto-links per document. Tunable with
  `--max-links`.
- **Priority-sorted** when the cap is reached: lower `priority` numbers win.
- **Skip zones**: headings, code/pre, tables, blockquotes, asides, existing
  links, and the opening TL;DR paragraph. The injector handles this
  automatically.

## File location

There's no required path. Common patterns:

- **Repo-local file** committed alongside the post sources:
  `content/glossary.json` (matches the automatelab convention).
- **External file** fetched at publish time from a known URL (e.g. an
  exported CMS collection).

Pass the path explicitly each run:

```bash
python3 scripts/inject-glossary-links.py post.html \
    --glossary content/glossary.json > post.linked.html
```
