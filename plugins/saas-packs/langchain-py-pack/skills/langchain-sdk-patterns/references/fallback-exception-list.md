# Fallback Exception List — Curated Whitelist per Provider

`.with_fallbacks([backup], exceptions_to_handle=(...))` defaults to
`(Exception,)`, which is too broad on Python <3.12 (catches `KeyboardInterrupt`
— pain-catalog P07) and semantically wrong everywhere: a `ValidationError` or
`AuthenticationError` should surface, not silently trigger a backup call.

This is the curated whitelist per provider.

## Rules

1. **Only transient provider errors** go in `exceptions_to_handle`. Rate limits, timeouts, 5xx responses — those are worth retrying on a backup.
2. **Never include base `Exception`, `BaseException`, or bare `()` (tuple-of-all)** — explicit is better than surprising.
3. **Never include `BadRequestError` / `ValidationError` / `AuthenticationError`** — these are bugs in your code, schema, or credentials. A fallback call will either crash the same way or produce garbage.
4. **Never include `KeyboardInterrupt` or `SystemExit`** — users need a kill switch; CI needs a timeout.
5. **Match the specific SDK's exception tree.** `anthropic.APIError` and `openai.APIError` are different classes; you must import both if both providers are in the fallback chain.

## Anthropic

```python
from anthropic import (
    APIError,           # Base class for Anthropic API errors
    APITimeoutError,    # Client-side timeout
    APIConnectionError, # Network unreachable
    RateLimitError,     # 429
    InternalServerError, # 500
)

exceptions_to_handle = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)
# Note: APIError is the base — including it catches all of the above plus
# BadRequestError, AuthenticationError, NotFoundError, etc. Don't use it.
```

**Do not include**: `AuthenticationError`, `PermissionDeniedError`,
`NotFoundError`, `BadRequestError`, `UnprocessableEntityError`. These are
configuration/schema bugs.

## OpenAI

```python
from openai import (
    APIError,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

exceptions_to_handle = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)
```

Same shape as Anthropic. OpenAI and Anthropic define their own `APIError` base
classes; they are not shared. If your fallback is cross-provider, import from
both.

## Google (Gemini)

```python
from google.api_core.exceptions import (
    DeadlineExceeded,         # Timeout
    ResourceExhausted,        # Rate limit
    ServiceUnavailable,       # 503
    InternalServerError,      # 500
    GatewayTimeout,           # 504
)

exceptions_to_handle = (
    DeadlineExceeded,
    ResourceExhausted,
    ServiceUnavailable,
    InternalServerError,
    GatewayTimeout,
)
```

**Gotcha**: `InvalidArgument` (including `finish_reason=SAFETY` — pain-catalog
P65) is not transient. Gemini safety blocks are deterministic for the same
input — fallback to another provider is appropriate, but put the safety-block
check in the condition, not the exception handler.

## Cross-provider fallback chain

```python
from anthropic import APIError as AnthropicAPIError, RateLimitError as AnthropicRateLimit
from openai import APIError as OpenAIAPIError, RateLimitError as OpenAIRateLimit

primary = prompt | claude | parser
backup = prompt | gpt4o | parser

resilient = primary.with_fallbacks(
    [backup],
    exceptions_to_handle=(
        AnthropicRateLimit,
        AnthropicAPIError,  # scope narrowly — see per-provider section above
        # Do NOT include OpenAI errors here — those apply to the backup, not primary
    ),
)
```

Each fallback's `exceptions_to_handle` applies to the **upstream** runnable's
failures. In a chain of 3 runnables (A → B → C) with `C` as fallback for `B`,
only `B`'s exceptions matter for the handoff.

## Multi-level fallbacks

```python
resilient = (
    primary
    .with_fallbacks([backup], exceptions_to_handle=(AnthropicRateLimit,))
    .with_fallbacks([last_resort], exceptions_to_handle=(OpenAIRateLimit,))
)
```

Flattens to: try `primary`; on `AnthropicRateLimit`, try `backup`; if `backup`
raises `OpenAIRateLimit`, try `last_resort`. Any other exception anywhere
propagates.

## Interaction with `max_retries`

If the primary chat model has `max_retries=6`, it burns through six retries
(with exponential backoff) before the fallback fires. At that point the user
has waited 30+ seconds. For fallback-first reliability, set `max_retries=0` on
the primary and let `with_fallbacks` handle resilience:

```python
primary = ChatAnthropic(model="claude-sonnet-4-6", max_retries=0, timeout=15)
backup = ChatOpenAI(model="gpt-4o", max_retries=0, timeout=15)

chain = (prompt | primary | parser).with_fallbacks(
    [prompt | backup | parser],
    exceptions_to_handle=(AnthropicRateLimit, AnthropicAPIError),
)
```

## What NOT to put in the whitelist

| Exception | Why not |
|---|---|
| `Exception` | Catches `KeyboardInterrupt` on Python <3.12 (P07) |
| `BaseException` | Always catches `KeyboardInterrupt` and `SystemExit` |
| `AuthenticationError` | Configuration bug — will fail the same way on backup |
| `BadRequestError` | Schema/payload bug — fallback will crash identically |
| `pydantic.ValidationError` | Structured-output schema mismatch — backup has the same schema |
| `ToolException` | Tool invocation bug — fallback does not run the tool any differently |
| `asyncio.CancelledError` | Task was cancelled on purpose; do not revive it |

When unsure, **narrower is better**. You can always widen the whitelist on the
next incident.
