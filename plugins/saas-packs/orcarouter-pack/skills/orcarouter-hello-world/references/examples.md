# OrcaRouter Hello World — References

## Routing behavior

When you call a first-party router such as `orcarouter/fusion`, the concrete model that served the request is reported in the `X-Orca-Resolved-Model` response header; `X-Orca-Router` names the router you invoked. The response body's top-level `model` field carries the identifier from your request. See [Response Headers](https://docs.orcarouter.ai/routing/response-headers).

To read the resolved model with cURL, use `-i` (headers) or `-D -` to dump headers:

```bash
curl -si https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"orcarouter/auto","messages":[{"role":"user","content":"Say OK"}],"max_tokens":200}' \
  | grep -i x-orca-resolved-model
```

## Full cURL with expected response

```bash
curl -s https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"orcarouter/fusion","messages":[{"role":"user","content":"Say OK"}],"max_tokens":200}' \
  | jq '{content: .choices[0].message.content, model: .model, finish_reason: .choices[0].finish_reason}'
```

Expected shape:

```json
{
  "content": "OK",
  "model": "orcarouter/fusion",
  "finish_reason": "stop"
}
```

## Reading usage

`usage` carries token counts:

```json
{
  "prompt_tokens": 69,
  "completion_tokens": 34,
  "total_tokens": 103
}
```

For per-request cost, send the opt-in header `X-OrcaRouter-Include-Cost: true` and read `usage.cost_usd`, or look the request up afterwards with `GET /v1/generation?id=<request-id>` using the `X-Orca-Request-Id` header. See [Per-request cost](https://docs.orcarouter.ai/operations/per-request-cost).

## Listing the catalog

```bash
curl -s https://api.orcarouter.ai/v1/models -H "Authorization: Bearer $ORCAROUTER_API_KEY" | jq '.data | length'
```

Models are provider-prefixed (`openai/gpt-4o-mini`, `anthropic/claude-sonnet-4.6`) plus first-party routers (`orcarouter/fusion`, `orcarouter/auto`, `orcarouter/free`). The list only includes models your account can access.

## Streaming

OrcaRouter supports SSE streaming via the OpenAI shape:

```python
stream = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Count to five"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

## Next skills

- `orcarouter-model-routing` — task-based model selection with the `orcarouter/*` routers and provider-prefixed IDs
- `orcarouter-fallback-reliability` — failover and reliability patterns
- `orcarouter-cost-observability` — cost tracking and budget controls
