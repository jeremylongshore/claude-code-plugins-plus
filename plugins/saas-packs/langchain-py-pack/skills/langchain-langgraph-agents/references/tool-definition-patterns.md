# Tool Definition Patterns for LangGraph 1.0 Agents

LangGraph's `create_react_agent` consumes LangChain `BaseTool` instances. You
have three ways to produce one: the `@tool` decorator, the `tool()` factory,
and a `BaseTool` subclass. This reference covers the decision and the
gotchas — most of which trace back to P11 (tool descriptions > 1024 chars) and
the provider-enforcement model of tool calling.

## The three ways

### `@tool` decorator — the default

```python
from langchain_core.tools import tool

@tool
def search_kb(query: str) -> list[dict]:
    """Search the knowledge base. Returns the top 5 matching articles."""
    return _search(query)[:5]
```

The decorator infers the schema from the function signature and uses the
docstring as the tool description. This is what you want 80% of the time.

### `@tool` + `args_schema` — when you need validators

```python
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool

class SearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def no_sql(cls, v: str) -> str:
        if any(kw in v.upper() for kw in ["DROP ", "DELETE ", ";--"]):
            raise ValueError("query contains SQL keywords")
        return v

@tool("search_kb", args_schema=SearchArgs)
def search_kb(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base. Returns up to top_k hits."""
    return _search(query)[:top_k]
```

Pydantic validators run *before* your function. If the model passes bad args,
the agent sees a `ValidationError` it can retry against. This is cheaper than
letting your function raise mid-way through an expensive call.

### `BaseTool` subclass — when you need instance state

```python
from langchain_core.tools import BaseTool

class KBSearchTool(BaseTool):
    name: str = "search_kb"
    description: str = "Search the knowledge base. Returns top 5 matches."
    args_schema: type = SearchArgs
    client: Any  # your KB client — pydantic-validated

    def _run(self, query: str, top_k: int = 5) -> list[dict]:
        return self.client.search(query)[:top_k]

    async def _arun(self, query: str, top_k: int = 5) -> list[dict]:
        return await self.client.asearch(query)[:top_k]
```

Use when the tool needs config at construction time (per-tenant client, per-
environment base URL). With `@tool` you would end up closing over module
globals, which breaks testing.

## Docstring = tool description (P11)

Whatever you write in the docstring is the description the provider sees:

- **Anthropic Claude:** truncates at ~1024 characters per tool description.
- **OpenAI GPT-4o:** no hard cap, but descriptions > ~2KB degrade accuracy.

Validate before binding:

```python
for t in tools:
    if len(t.description) > 1024:
        raise ValueError(f"Tool {t.name} description too long: {len(t.description)} chars")
```

Long examples and format specs belong in the system prompt, not the docstring.
The docstring should answer *when* to use the tool in one or two sentences.

## Async tools

```python
@tool
async def fetch_url(url: str) -> str:
    """Fetch a URL and return the body as UTF-8 text."""
    async with httpx.AsyncClient() as c:
        r = await c.get(url, timeout=10)
        return r.text
```

LangGraph detects the coroutine and awaits it. Do not mix sync and async
wrappers — pick one per tool. If you need both, use a `BaseTool` subclass
with both `_run` and `_arun`.

## Return types the model can reason about

Tools should return one of:

- `str` — the model reads it as text in the next turn
- `dict` / `list` — serialized to JSON in the `ToolMessage.content`
- A Pydantic model — auto-serialized

Avoid returning binary data, large blobs, or raw HTML. If you must, summarize
in the tool itself before returning.

## Security-adjacent patterns

### Allowlist is wire-enforced — do not re-check

In legacy free-text ReAct (P32), agents could hallucinate tool names because
the parser took any string as a valid action. `create_react_agent` relies on
the provider's native tool-calling API, which enforces that only bound tools
are callable. You do not need to re-check `tool_name in allowed_tools` — the
provider will refuse to emit unknown tool calls.

### Validators are your authorization boundary

Pydantic `args_schema` validators are the right place to enforce tenant
isolation, PII policies, and rate-limits. They run before the tool body and
raise `ValidationError` cleanly.

```python
class AccountLookupArgs(BaseModel):
    account_id: str

    @field_validator("account_id")
    @classmethod
    def tenant_scoped(cls, v: str, info) -> str:
        tenant = info.context.get("tenant_id") if info.context else None
        if not v.startswith(f"{tenant}:"):
            raise ValueError("account_id is cross-tenant")
        return v
```

(`info.context` is threaded through `RunnableConfig.configurable.context` in
LangChain 1.0. See the core-workflow skill for the plumbing.)

## When a tool is not a tool

If the step is deterministic (e.g., format a date, stringify a number), do not
expose it as a tool — do it in your graph's pre-processing node. Tools should
have side effects or external-state dependencies. Every tool in the list
increases:

1. The token cost of each model call (descriptions are in the prompt).
2. The decision space the model has to search.
3. The surface area for the agent to get confused.

Aim for 3-7 tools per agent. More than that → split into supervisor + workers.
