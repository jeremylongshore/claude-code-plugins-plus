# Apify Local Dev Loop — Worked Examples

Three end-to-end scenarios for the develop-test-deploy loop. Each uses only the
Apify CLI and the local `storage/` emulation created by `apify run`.

## 1. Scaffold a new Actor and run it locally

Create a project from the Cheerio TypeScript template, then run it against a
default input:

```bash
# Create from specific template
apify create my-actor --template project_cheerio_crawler_ts
# Templates: project_empty, project_cheerio_crawler_ts,
#   project_playwright_crawler_ts, project_puppeteer_crawler_ts

cd my-actor
apify run
```

`apify run` creates the local `storage/` tree and writes scraped rows to
`storage/datasets/default/`.

## 2. Provide a local input file and inspect results

Seed a persistent input at `storage/key_value_stores/default/INPUT.json`, run,
then read back the dataset:

```json
{
  "startUrls": [{ "url": "https://example.com" }],
  "maxPages": 5
}
```

```bash
apify run

# View results as pretty-printed JSON
cat storage/datasets/default/*.json | jq '.'

# Or list dataset files
ls storage/datasets/default/
```

Each item matches the shape pushed by `Actor.pushData()`:

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "h1": "Example Domain",
  "timestamp": "2026-07-17T14:03:22.481Z"
}
```

## 3. One-shot run with inline input (no file)

Pass input directly on the command line for a quick throwaway run — handy while
iterating on selectors:

```bash
apify run --input='{"startUrls":[{"url":"https://example.com"}],"maxPages":5}'
```

For the fastest inner loop, skip the CLI entirely and run the entry point with
`tsx watch` (see [implementation.md](implementation.md) § Hot Reload Development)
so edits to `src/main.ts` re-run automatically.
