---
name: apify-local-dev-loop
description: |
  Set up local Apify Actor development with the Apify CLI and Crawlee.
  Use when creating Actors locally, testing with the apify run command,
  inspecting local storage, or establishing a fast develop-test-deploy cycle
  before pushing to the platform.
  Trigger with "apify dev setup", "apify local development", "develop actor
  locally", "apify run local".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(apify:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Local Dev Loop

## Overview

Build and test Apify Actors on your local machine before deploying to the platform. The Apify CLI (`apify run`) emulates the platform environment locally — creating storage directories for datasets, key-value stores, and request queues — giving you a tight edit → run → inspect loop with no cloud round-trip.

## Prerequisites

- `npm install -g apify-cli` (global CLI)
- `apify login` completed with valid token
- Node.js 18+

## Authentication

The CLI authenticates with your Apify API token. Run `apify login` once (it stores
the token under `~/.apify/`), or export `APIFY_TOKEN` in the shell for
non-interactive use. Local runs (`apify run`) do not require auth — only
`apify push` / `apify call` reach the platform. Never commit the token or a
plaintext `.env` containing it.

## Actor Project Structure

```
my-actor/
├── .actor/
│   ├── actor.json          # Actor metadata and config
│   └── INPUT_SCHEMA.json   # Input schema (auto-generates UI on platform)
├── src/
│   └── main.ts             # Entry point
├── storage/                # Created by apify run (git-ignored)
│   ├── datasets/default/
│   ├── key_value_stores/default/
│   └── request_queues/default/
├── package.json
└── tsconfig.json
```

## Instructions

Full config files and Actor source live in
[implementation.md](references/implementation.md); the high-level loop is:

### Step 1: Create a New Actor Project

```bash
# Create from template (interactive)
apify create my-actor

# Or create from specific template
apify create my-actor --template project_cheerio_crawler_ts
# Templates: project_empty, project_cheerio_crawler_ts,
#   project_playwright_crawler_ts, project_puppeteer_crawler_ts
```

### Step 2: Configure and code

Read and Edit the scaffolded `.actor/actor.json` (metadata + optional dataset
view), define `.actor/INPUT_SCHEMA.json` (validates input and auto-generates the
platform UI), and write your crawler in `src/main.ts`. See
[implementation.md](references/implementation.md) for the complete `actor.json`,
input schema, and a Cheerio-based `main.ts` that reads validated input and pushes
structured rows via `Actor.pushData()`.

### Step 3: Run Locally

```bash
# Run with default input from storage/key_value_stores/default/INPUT.json
apify run

# Run with input from command line
apify run --input='{"startUrls":[{"url":"https://example.com"}],"maxPages":5}'

# View results
cat storage/datasets/default/*.json | jq '.'
```

### Step 4: Provide Local Input

Create `storage/key_value_stores/default/INPUT.json` so repeated `apify run`
invocations reuse the same input:

```json
{
  "startUrls": [{ "url": "https://example.com" }],
  "maxPages": 5
}
```

For the fastest inner loop, run the entry point directly with `tsx watch` instead
of `apify run` — wiring and platform-emulating env vars are in
[implementation.md](references/implementation.md) § Hot Reload Development. Unit
tests that mock the SDK boundary are in that same file.

## Local Storage Emulation

`apify run` creates a `storage/` directory that mirrors platform storage:

| Platform Storage | Local Path | Access via SDK |
|-----------------|------------|----------------|
| Default dataset | `storage/datasets/default/` | `Actor.pushData()` |
| Default KV store | `storage/key_value_stores/default/` | `Actor.setValue()` / `Actor.getValue()` |
| Default request queue | `storage/request_queues/default/` | Managed by crawler |

## Output

- A runnable Actor project scaffolded from a template (`.actor/`, `src/`, `package.json`)
- A typed input schema that validates locally and generates the platform UI
- Scraped rows written to `storage/datasets/default/` as JSON files
- A local `storage/` tree mirroring platform datasets, KV stores, and request queues
- A watch-mode dev loop (`tsx watch`) and a Vitest test that mocks the SDK boundary

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `apify: command not found` | CLI not installed | `npm i -g apify-cli` |
| `INPUT.json not found` | No input provided | Create `storage/key_value_stores/default/INPUT.json` |
| `Cannot find module 'apify'` | SDK not installed | `npm install apify crawlee` |
| `Dockerfile not found` | Missing actor config | Run `apify create` or create `.actor/actor.json` |

## Examples

A quick end-to-end run — seed a local input, run the Actor, and inspect results:

```bash
mkdir -p storage/key_value_stores/default
echo '{"startUrls":[{"url":"https://example.com"}],"maxPages":5}' \
  > storage/key_value_stores/default/INPUT.json
apify run
cat storage/datasets/default/*.json | jq '.'
```

Three fuller worked scenarios live in [examples.md](references/examples.md):

- **Scaffold a new Actor and run it locally** — `apify create` from a template through the first `apify run`.
- **Provide a local input file and inspect results** — persistent `INPUT.json`, plus the exact dataset row shape.
- **One-shot run with inline input** — throwaway `--input` runs while iterating on selectors.

## Resources

- [Local Actor Development](https://docs.apify.com/platform/actors/development/quick-start/locally)
- [Apify CLI Reference](https://docs.apify.com/cli/docs/reference)
- [Actor Templates](https://docs.apify.com/platform/actors/development/quick-start)
- [Full implementation walkthrough](references/implementation.md) — complete `actor.json`, input schema, `main.ts`, hot reload, and tests
- [Worked examples](references/examples.md) — three end-to-end run scenarios

## Next Steps

Once the local loop is producing clean data, move on to production-ready Actor
code patterns — routing, proxy configuration, retries, and dataset shaping —
covered in `apify-sdk-patterns`.
