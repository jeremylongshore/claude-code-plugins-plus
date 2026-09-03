# API-Surface Review Matrix

Choose one supported surface deliberately and test its contract. Do not infer that parameters, endpoints, typed errors, or response fields transfer unchanged between surfaces.

| Surface | Best fit | Client contract to pin | Response fields to test |
|---|---|---|---|
| Official Perplexity SDK | New typed Python or TypeScript integrations | Package version, method, timeout, typed errors | Surface-specific typed response |
| Sonar API | Web-grounded generated answers | Canonical endpoint or documented SDK method | `choices`, `usage`, `citations`, `search_results` |
| OpenAI compatibility | Existing Chat Completions client infrastructure | Base URL and compatibility endpoint | OpenAI fields plus Perplexity extensions |
| Search API | Ranked results without generated prose | Query, result limit, filter schema | Result title, URL, date, snippet |
| Agent API | Agent loops using presets and tools | Preset, tool policy, model access | Output items and tool results |

## Review questions

- Is the imported package real, pinned, and owned by the expected publisher?
- Is the base URL a literal approved Perplexity HTTPS origin?
- Does the selected method match the intended API surface?
- Are provider-specific request and response extensions typed and tested?
- Does every call have an output limit, cancellation signal, and total deadline?
- Are retryable and permanent failures separated?
- Are cache keys tenant-scoped and cache writes explicitly classified?
- Are citation URLs treated as untrusted input and never fetched by the backend by default?
- Are logs limited to request IDs, status classes, timings, and aggregate counts?
- Does the upgrade suite fail on removed fields or a changed endpoint?

## Upgrade receipt

For each SDK or API migration, record the old and new package version, selected surface, tested endpoint, request fixture, response-schema fixture, negative security cases, rollback version, and approving owner. A README example is not a compatibility test.

## Primary references

- [Official Perplexity SDK overview](https://docs.perplexity.ai/docs/sdk/overview)
- [Sonar OpenAI compatibility](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
- [Perplexity quickstart](https://docs.perplexity.ai/docs/getting-started/quickstart)
- [Search filters](https://docs.perplexity.ai/docs/sonar/filters)
