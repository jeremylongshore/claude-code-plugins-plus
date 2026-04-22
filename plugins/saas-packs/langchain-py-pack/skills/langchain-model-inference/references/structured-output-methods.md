# `with_structured_output` Method Decision Tree

LangChain 1.0 ships three methods for structured output. The wrong pick silently
degrades success rate — not crashes — which is why this is pain-catalog entry P03
and P54.

## The three methods

| Method | What it does | Schema enforcement |
|---|---|---|
| `json_schema` | Passes schema to provider's native structured-output feature | Provider-enforced, hard fail on violation |
| `function_calling` | Binds schema as a tool and forces a call | Provider-enforced via tool schema |
| `json_mode` | Sets response format to "JSON" | Parseable JSON only — schema ignored |

## Decision tree

```
Is your model in this list?
  Claude 3.5 Sonnet, 4.x, Opus         -> json_schema
  GPT-4o, GPT-4-turbo, GPT-4.1         -> json_schema
  Gemini 2.5 Pro, 2.5 Flash            -> json_schema
  GPT-3.5-turbo                         -> function_calling
  Older OpenAI, older Anthropic         -> function_calling
  Unknown / new / local                 -> json_mode + Pydantic validate + retry
```

If in doubt, run both on a 20-example eval set and compare field-level correctness.

## Field-level pitfalls

### P03 — `Optional[list[X]]` silently becomes `None`

```python
# BAD — ~40% silent failure rate with method="function_calling"
class Report(BaseModel):
    title: str
    bullets: Optional[list[str]] = None

# GOOD — either required, or explicitly empty
class Report(BaseModel):
    title: str
    bullets: list[str] = Field(default_factory=list)
```

Empty list is a signal. `None` is ambiguous — did the model skip, or did the
schema strip the field?

### P53 — Pydantic v2 strict-by-default rejects extras

```python
from pydantic import BaseModel, ConfigDict

class Classification(BaseModel):
    model_config = ConfigDict(extra="ignore")  # let the model be helpful
    category: Literal["billing", "technical", "sales"]
    confidence: float
```

Without `extra="ignore"`, a model that returns `{"category": "billing",
"confidence": 0.9, "reasoning": "..."}` fails validation with
`ValidationError: extra fields not permitted`.

### Nested unions break on most models

```python
# AVOID — even Claude 4 gets this wrong ~15% of the time
class Step(BaseModel):
    action: Union[DoThisAction, DoThatAction, NoAction]

# PREFER — discriminated union with a tag field
class DoThisAction(BaseModel):
    kind: Literal["do_this"]
    payload: str
class DoThatAction(BaseModel):
    kind: Literal["do_that"]
    payload: int
class Step(BaseModel):
    action: Union[DoThisAction, DoThatAction] = Field(discriminator="kind")
```

Discriminated unions give the schema a single unambiguous field to dispatch on,
which is what provider enforcement needs.

## Fallback pattern for `json_mode`

When the model lacks native schema support, layer Pydantic + retry:

```python
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, retry_if_exception_type

class Plan(BaseModel):
    steps: list[str]

@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(ValidationError))
def extract_plan(prompt: str) -> Plan:
    model = llm.with_structured_output(Plan, method="json_mode")
    return model.invoke(prompt)  # raises ValidationError if schema doesn't fit
```

Retry is essential — `json_mode` produces valid JSON but invalid *shape* a
nontrivial fraction of the time.

## When `with_structured_output` is the wrong tool

For multi-step extraction (read doc, identify fields, validate each, cross-reference)
prefer a small LangGraph graph with one node per step. `with_structured_output`
is one-shot; real extraction usually wants refinement.

For *forced* single-tool invocations (e.g., "always classify into exactly one of
these buckets"), you can use `bind_tools([Schema], tool_choice={"type": "tool",
"name": "Schema"})` — but never loop a forced choice (P63), because the model
cannot emit `stop_reason="end_turn"` under forced tool_choice.
