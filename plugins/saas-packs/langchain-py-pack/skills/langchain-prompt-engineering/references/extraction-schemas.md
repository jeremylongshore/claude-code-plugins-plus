# Extraction Schemas — Discriminated Unions, Field Ordering, Pydantic Config

Reference for `langchain-prompt-engineering`. Covers the Pydantic patterns that
make `with_structured_output` robust across Claude, GPT-4o, and Gemini —
specifically, how to avoid the silent drops, validation rejections, and
helpful-extra-field failures that appear only in production.

Pin: `pydantic >= 2.5`, `langchain-core 1.0.x`. Pain-catalog entries: P03,
P53, P54, P68.

## Pydantic v2 `ConfigDict(extra="ignore")` — the P53 fix

Pydantic v2 defaults to `extra="forbid"` on `model_validate`. Models love to
add a helpful-but-unrequested field (`"notes": "This invoice looks unusual"`).
Pydantic rejects the whole response:

```
pydantic.ValidationError: 1 validation error for Invoice
notes
  Extra inputs are not permitted [type=extra_forbidden, ...]
```

Fix: set `extra="ignore"` on every schema used for `with_structured_output`:

```python
from pydantic import BaseModel, ConfigDict

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vendor: str
    total_usd: float
```

Alternative: instruct the model in the system prompt to return *only* the
declared fields. Less reliable than `extra="ignore"` — models generalize.

## Avoid `Optional[list[X]]` — the P03 fix

`Optional[list[Item]]` serializes as
`{"anyOf": [{"type": "array"}, {"type": "null"}]}`. Under
`with_structured_output(method="function_calling")`, ~40% of providers strip
the array branch and the field comes back as `None` even when items are
clearly described in the source text. Three fixes, in preference order:

### 1. Use `list[X]` with a default factory

```python
class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vendor: str
    line_items: list[LineItem] = Field(default_factory=list)
    # "no items" is represented by [], not None. Schema is {type: array}.
```

`default_factory=list` keeps the field required in type theory but provides a
sensible default on parse. The JSON schema is unambiguous.

### 2. Flatten `Optional[Union[A, B]]` into a discriminated union

```python
from typing import Annotated, Literal, Union
from pydantic import Field

class CashPayment(BaseModel):
    kind: Literal["cash"]
    amount_usd: float

class CardPayment(BaseModel):
    kind: Literal["card"]
    amount_usd: float
    last4: str = Field(..., pattern=r"^\d{4}$")

class NoPayment(BaseModel):
    kind: Literal["none"]

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vendor: str
    payment: Annotated[
        Union[CashPayment, CardPayment, NoPayment],
        Field(discriminator="kind"),
    ]
```

The `kind` field tells the parser which variant to expect. Robust across all
three structured-output methods. The `NoPayment` explicit variant is safer
than `Optional` because it forces the model to state absence.

### 3. Switch to `method="json_schema"`

`method="json_schema"` (supported on Claude 3.5+, GPT-4o+, Gemini 2.5+) enforces
the full JSON Schema including `anyOf`, so `Optional[list[X]]` works. Prefer
this when available:

```python
structured = llm.with_structured_output(Invoice, method="json_schema")
```

Do not rely on `method="json_mode"` for schema compliance — it only enforces
JSON-parseable output, not schema fidelity (P54).

## Field ordering affects model compliance

Model attention biases toward earlier fields in a schema. Ordering matters:

1. **Required fields before optional.** Even with `extra="ignore"`, required
   fields listed first are filled more reliably.
2. **Concrete before abstract.** `vendor: str` before `category: Literal[...]`.
   The model anchors on the concrete field and the abstract one becomes
   context-dependent.
3. **Short before long.** `vendor: str` before `notes: str` (a free-text field).
   The model commits to short fields first and is less likely to truncate.
4. **Discriminator first in union variants.** `kind` appears before the
   variant-specific fields so the model picks a variant early.

```python
class LineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # REQUIRED, SHORT, CONCRETE FIRST
    description: str
    quantity: int
    unit_price_usd: float
    # OPTIONAL, LONGER LAST
    notes: str = ""
```

## Pydantic-first, prompt-second

Write the Pydantic schema before writing the prompt. The schema names become
the prompt's extraction targets; consistent naming reduces model confusion:

```python
class Invoice(BaseModel):
    vendor: str
    total_usd: float
    # ...

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Extract an Invoice. Fields: vendor (string), total_usd (number). "
     "Do not invent fields that are absent."),
    ("user", "<document>{{ doc }}</document>"),
], template_format="jinja2")
```

Use exact field names from the schema in the prompt. Swap `total` for
`total_usd` in the prompt and you will see degraded extraction accuracy — the
model starts guessing which field each number belongs to.

## Descriptions as prompts within the schema

Pydantic `Field(description=...)` is serialized into the JSON schema and
surfaced to the model by `with_structured_output`. This is a prompt-engineering
lever:

```python
class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vendor: str = Field(
        ...,
        description="The legal name of the entity issuing the invoice. "
                    "Use the name printed on the letterhead, not the signature.",
    )
    total_usd: float = Field(
        ...,
        description="The grand total after taxes, in USD. If the invoice "
                    "is in a foreign currency, convert at the stated rate.",
        ge=0,
    )
```

This is the lowest-friction way to inject extraction instructions — the model
receives them as part of the tool/schema spec, with no extra prompt length.
Prefer this over stuffing instructions into the system prompt when the
instruction applies to a single field.

## Fallback: `method="json_mode"` + Pydantic validate + retry

When a model does not support `json_schema` (older OpenAI, some OSS
deployments), use `json_mode` and validate manually:

```python
from pydantic import ValidationError

raw = llm.with_structured_output(Invoice, method="json_mode").invoke(input_)
try:
    invoice = Invoice.model_validate(raw)
except ValidationError as e:
    # Retry once with the error message fed back
    retry_prompt = f"{original_prompt}\n\nPrevious attempt failed validation:\n{e}"
    raw = llm.with_structured_output(Invoice, method="json_mode").invoke(retry_prompt)
    invoice = Invoice.model_validate(raw)  # if this fails, raise
```

One retry is usually enough. More than two retries signals a schema-prompt
mismatch — fix the schema, don't keep retrying.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `ValidationError: extra fields not permitted` | Pydantic v2 strict default (P53) | `model_config = ConfigDict(extra="ignore")` |
| `Optional[list[X]]` returns `None` despite content | `method="function_calling"` drops `anyOf` (P03) | Use `list[X]` with `default_factory=list`, or switch to `method="json_schema"` |
| Valid JSON but required fields missing | `method="json_mode"` does not enforce schema (P54) | Use `method="json_schema"` on capable models; validate + retry on older ones |
| Discriminated union picks wrong variant | `kind` field placed last; model guessed variant from content | Put discriminator field first in each variant class |
| Extraction accuracy degrades after schema refactor | Field names changed in schema, prompt still uses old names | Keep schema and prompt in sync; use `Field(description=...)` for per-field instructions |

## Sources

- LangChain: Structured outputs — https://python.langchain.com/docs/how_to/structured_output/
- Pydantic v2: `model_config` / `ConfigDict` — https://docs.pydantic.dev/latest/api/config/
- Pydantic v2: Discriminated unions — https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions
- Pack pain catalog entries: P03, P53, P54, P68
