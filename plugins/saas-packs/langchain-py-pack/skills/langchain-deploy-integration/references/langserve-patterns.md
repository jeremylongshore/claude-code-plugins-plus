# LangServe Patterns Reference

LangServe turns any `Runnable` into a typed FastAPI endpoint. The patterns
below cover production mounting — typed schemas, playground gating, custom
middleware, and coexisting with raw FastAPI handlers.

## Minimal mount

```python
from fastapi import FastAPI
from langserve import add_routes
from app.chain import chain

app = FastAPI()
add_routes(app, chain, path="/chat")
```

This exposes:

- `POST /chat/invoke` — single-shot `chain.invoke(input)`
- `POST /chat/batch` — `chain.batch([inputs])`
- `POST /chat/stream` — `chain.stream(input)` as SSE
- `POST /chat/stream_events` — `chain.astream_events(input, version="v2")` as SSE
- `GET /chat/playground` — browser playground UI (dev only)
- `GET /chat/input_schema` — JSON Schema for input
- `GET /chat/output_schema` — JSON Schema for output

## Production mount with lifespan and playground gating

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langserve import add_routes
from app.chain import build_chain, close_pools

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chain = build_chain()
    yield
    await close_pools()

app = FastAPI(lifespan=lifespan)

IS_PROD = __debug__ is False  # set PYTHONOPTIMIZE=1 in prod
add_routes(
    app,
    app.state.chain if False else build_chain(),  # see note below
    path="/chat",
    playground_type="chat" if not IS_PROD else None,  # None disables in prod
    enable_feedback_endpoint=False,  # don't expose until LangSmith auth wired
    enabled_endpoints=("invoke", "batch", "stream", "stream_events"),
)
```

Note: `add_routes` binds the Runnable eagerly. If you need request-scoped
chain instances (rare — usually chain state is immutable), use a factory
wrapper that builds per request. For most apps, build once at startup.

## Typed input and output schemas

LangServe uses Pydantic to validate request bodies. Explicit schemas produce
better client SDKs and OpenAPI docs:

```python
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

class ChatInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    temperature: float = Field(0.0, ge=0.0, le=2.0)

class ChatOutput(BaseModel):
    answer: str
    tokens_in: int
    tokens_out: int

typed_chain = (
    RunnablePassthrough()
    .with_types(input_type=ChatInput, output_type=ChatOutput)
    | chain
)

add_routes(app, typed_chain, path="/chat")
```

The generated `/chat/input_schema` endpoint now returns a schema that
front-end teams can codegen TypeScript types from.

## Custom middleware: auth, rate limit, request ID

LangServe mounts are plain FastAPI routes — standard middleware applies:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response

app.add_middleware(RequestIDMiddleware)
```

For auth, use FastAPI `Depends` on a custom route that wraps the chain, or
insert a global dependency on `/chat/*`:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def require_api_key(key: str = Security(api_key_header)):
    if key != settings.api_key.get_secret_value():
        raise HTTPException(401, "invalid or missing x-api-key")

# Apply to all LangServe routes
app = FastAPI(dependencies=[Depends(require_api_key)])
add_routes(app, chain, path="/chat")
```

## Per-request configurable fields

Expose chain config without rebuilding the chain:

```python
from langchain_core.runnables import ConfigurableField

chain = (
    prompt
    | model.configurable_fields(
        temperature=ConfigurableField(id="temperature"),
        model_name=ConfigurableField(id="model_name"),
    )
    | parser
)

add_routes(app, chain, path="/chat",
           per_req_config_modifier=lambda config, request: {
               **config,
               "configurable": {"temperature": request.headers.get("x-temp", 0.0)},
           })
```

## Coexisting with raw FastAPI handlers

LangServe mounts on a path prefix; other routes work normally:

```python
app = FastAPI(lifespan=lifespan)

# LangServe mounts
add_routes(app, chat_chain, path="/chat")
add_routes(app, embed_chain, path="/embed")

# Raw FastAPI handlers
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/webhook")
async def webhook(payload: dict):
    # custom logic, not a Runnable
    return {"received": True}
```

## Disabling the playground in production

The playground is extremely useful in dev but leaks chain topology —
it returns the Runnable graph, input/output schemas, and will happily run
any input that validates against the schema. Two ways to disable:

```python
# Option 1: None removes the playground route
add_routes(app, chain, path="/chat", playground_type=None)

# Option 2: gate by env / debug flag
add_routes(app, chain, path="/chat",
           playground_type="chat" if settings.env == "dev" else None)
```

Also disable `enable_feedback_endpoint=False` in prod unless LangSmith auth
is wired — by default, anyone can POST feedback to any run.

## SSE headers on LangServe stream routes

LangServe's `/stream` and `/stream_events` routes already set `Content-Type:
text/event-stream`. You still need `X-Accel-Buffering: no` to defeat Nginx
and Cloud Run buffering (P46). Add via middleware:

```python
class SSEHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if response.media_type == "text/event-stream":
            response.headers["x-accel-buffering"] = "no"
            response.headers["cache-control"] = "no-cache, no-transform"
        return response

app.add_middleware(SSEHeadersMiddleware)
```

## Versioning a LangServe API

Mount each version on its own path. Chains evolve; client deprecation takes
time. Two paths, two chain versions:

```python
add_routes(app, chain_v1, path="/v1/chat")
add_routes(app, chain_v2, path="/v2/chat")
```

Put the version in the path, not a header — CDN caching and client libraries
handle path versioning better.
