# Error Handling Reference

## Genkit Flow Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `SAFETY_BLOCK` response | Model safety filters triggered on input or output | Review prompt content for policy violations; adjust safety settings in `GenerationConfig`; add input sanitization before `ai.generate()` |
| `QUOTA_EXCEEDED` | API rate limit or daily token quota reached | Implement exponential backoff with jitter; request quota increase via Cloud Console; cache repeated prompts with TTL |
| `ZodError: invalid input` | Runtime input does not match Zod schema | Add `.describe()` to schema fields for better error messages; validate inputs upstream before calling the flow |
| `ZodError: invalid output` | Model output does not match expected output schema | Tighten the prompt to match schema structure; use `response_mime_type: application/json`; add a retry with rephrased prompt |

## Retriever & RAG Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Empty retrieval results | Vector database query found no matches above similarity threshold | Lower the similarity threshold; verify documents are indexed with matching embedding model version; run `ai.index()` to re-index |
| `Embedding dimension mismatch` | Retriever uses different embedding model than indexer | Ensure both indexer and retriever use the same embedder (e.g., `textEmbedding004`); re-index if model changed |
| `Firestore findNearest: index not found` | Firestore vector index not created for the collection | Create a composite index with `gcloud firestore indexes composite create` including the embedding field |
| Retriever returns stale documents | Indexed content was updated but embeddings were not regenerated | Implement an update pipeline that re-embeds documents on change; add `updatedAt` timestamps for cache invalidation |

## Deployment Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Function timeout` on Firebase Functions | Cold start or flow execution exceeds 60s default limit | Increase `timeoutSeconds` in function config (max 540s for 2nd gen); set `minInstances: 1` to avoid cold starts; use Cloud Run for long-running flows |
| `ENOMEM` or container OOM | Insufficient memory for model response processing | Increase memory allocation (`--memory 1Gi`); reduce `maxOutputTokens`; stream responses instead of buffering |
| `ERR_MODULE_NOT_FOUND` in deployed function | Dependencies not bundled correctly | Verify `tsconfig.json` `outDir` matches function entry point; run `npm run build` before deploy; check `package.json` exports field |
| `Cloud Run: service unavailable` after deploy | Health check fails during startup | Ensure the flow server binds to `0.0.0.0:$PORT`; add a health check endpoint at `/` or `/_ah/health` |

## Model & Provider Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Model not found` | Model ID doesn't match provider format | Use `gemini25Flash` or `gemini25Pro` exports from `@genkit-ai/googleai`; don't use raw model strings unless explicitly supported |
| `API key not valid` | Missing or expired Google AI API key | Set `GOOGLE_GENAI_API_KEY` env var; rotate keys periodically; use `gcloud secrets` for production |
| `INVALID_ARGUMENT: max tokens exceeded` | Prompt plus expected output exceeds model context window | Reduce prompt size; summarize context; use retrieval to inject only relevant snippets |
| Provider timeout | Network or API latency spike | Set `timeout` in generation config; implement circuit breaker pattern; add fallback to alternative model |

## Local Development Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Genkit Developer UI won't start | Port 4000 already in use or missing `genkit` CLI | Kill process on port 4000 (`lsof -i :4000`); ensure `genkit` CLI is installed globally (`npm install -g genkit`) |
| `tsx` not found | TypeScript execution tool not installed | Install `tsx` as dev dependency: `npm install -D tsx`; or use `npx tsx` |
| Flow test hangs indefinitely | Async flow never resolves or rejects | Add timeout to test cases; verify all async branches have proper error handling; mock external API calls in tests |
| `ECONNREFUSED` when testing flows | Flow server not running or wrong port | Start server with `npx genkit start -- tsx src/index.ts`; verify URL matches the flow server port (default 3400) |

## Tracing & Monitoring Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No traces appearing in Firebase Console | `enableTracingAndMetrics` not set or wrong project | Pass `enableTracingAndMetrics: true` in Genkit config; verify `GOOGLE_CLOUD_PROJECT` env var matches Firebase project |
| Missing custom span attributes | Span not properly closed or attribute key rejected | Use OpenTelemetry-compliant attribute names; ensure spans are ended in `finally` blocks |
| High cardinality warning in monitoring | Too many unique flow names or label values | Use parameterized flow names; avoid dynamic values in metric labels |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
