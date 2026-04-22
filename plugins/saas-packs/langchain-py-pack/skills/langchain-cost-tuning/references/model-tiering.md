# Model Tiering

Most production chains overspend by running one expensive model for every
call. Tiering splits the chain into cheap "understand the request" and
expensive "produce the final artifact" calls, evaluated against a gold set to
prove no quality regression.

## Per-1M pricing snapshot (2026-04)

**Verify current prices before shipping** at:
- Anthropic: https://www.anthropic.com/pricing
- OpenAI: https://openai.com/api/pricing/

| Model | Tier | Input $/1M | Output $/1M | Cache read $/1M |
|---|---|---|---|---|
| `claude-haiku-4-5` | Cheap | $1.00 | $5.00 | $0.10 |
| `claude-sonnet-4-6` | Mid | $3.00 | $15.00 | $0.30 |
| `claude-opus-4-5` | Expensive | $15.00 | $75.00 | $1.50 |
| `gpt-4o-mini` | Cheap | $0.15 | $0.60 | prefix-cache only |
| `gpt-4o` | Mid | $2.50 | $10.00 | prefix-cache only |
| `gpt-o3-mini` | Reasoning | $1.10 | $4.40 | n/a |
| `gemini-2.5-flash` | Cheap | ~$0.30 | ~$2.50 | n/a |
| `gemini-2.5-pro` | Mid | ~$2.50 | ~$10.00 | n/a |

Gemini rates are approximate and region-dependent — confirm in the GCP
billing console for your region.

## The draft-then-finalize pattern

```python
from langchain_anthropic import ChatAnthropic

draft_model    = ChatAnthropic(model="claude-haiku-4-5",  temperature=0, max_retries=2)
finalize_model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_retries=2)

async def extract(document: str) -> dict:
    # Draft: rough extraction, 80% of input tokens land here.
    draft = await draft_model.ainvoke(DRAFT_PROMPT.format(doc=document))
    # Finalize: validate + fill missing, smaller input (draft + schema).
    final = await finalize_model.with_structured_output(Record).ainvoke(
        FINALIZE_PROMPT.format(draft=draft.content, schema=Record.model_json_schema())
    )
    return final
```

On a 10K-doc batch, a Sonnet-only baseline costs ~$14/1K docs at typical doc
sizes; draft-then-finalize costs ~$4.20/1K docs (~70% reduction) with F1
within 0.01 on the evaluation gold set.

## Intent-classification router

For chat apps, route on a classifier before generation:

```python
classifier = ChatAnthropic(
    model="claude-haiku-4-5",
    temperature=0,
    max_retries=2,
).with_structured_output(Intent)

async def route(user_message: str) -> str:
    intent = await classifier.ainvoke(CLASSIFY_PROMPT.format(msg=user_message))
    if intent.category == "greeting":
        return await haiku.ainvoke(user_message)      # trivial path
    if intent.category == "billing_question":
        return await sonnet_with_rag.ainvoke(...)     # mid path
    if intent.category == "contract_review":
        return await opus_with_tools.ainvoke(...)     # expensive path
```

The classifier costs ~$0.001 per call on Haiku, routes 70% of traffic to the
cheap path, and reserves Opus for the ~5% where it matters.

## When tiering is wrong

Tiering fails silently when quality degrades on the cheap tier for cases the
expensive tier would have caught. Three classes of task where Haiku / gpt-4o-mini
consistently underperform Sonnet / gpt-4o in our measurements:

1. **High-stakes entity extraction** — Contracts, medical records, financial
   documents. Haiku misses 10-15% of rare entity types on the same gold set
   where Sonnet scores 98%+.
2. **Multi-hop reasoning** — Planning tasks with 4+ steps. Haiku skips
   intermediate steps and hallucinates the conclusion.
3. **Long context (>50k tokens)** — Haiku quality degrades faster than Sonnet
   past ~50k tokens of context.

Always evaluate before shipping a tier. Do not assume the cheaper model works
because the outputs "look right."

## Evaluation harness

Build a gold set of 50-200 examples with known-correct outputs. Score both
tiers on the same set. A useful scoring function for extraction tasks:

```python
def score(predicted: Record, gold: Record) -> float:
    # F1 over required fields.
    p_fields = {k: v for k, v in predicted.model_dump().items() if v is not None}
    g_fields = {k: v for k, v in gold.model_dump().items() if v is not None}
    tp = len([k for k, v in p_fields.items() if g_fields.get(k) == v])
    fp = len(p_fields) - tp
    fn = len(g_fields) - tp
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0
```

Ship tiering only when the cheap-tier mean F1 is within 0.01-0.02 of the
expensive tier on your gold set. Re-evaluate quarterly — model updates (and
prompt drift) can silently shift quality.

## Cost modeling before migration

Before switching a production chain to a cheaper tier, estimate savings:

```python
def estimate_monthly_savings(
    calls_per_month: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    old_in_rate: float,   # $/1M
    old_out_rate: float,
    new_in_rate: float,
    new_out_rate: float,
) -> float:
    old = calls_per_month * (avg_input_tokens * old_in_rate + avg_output_tokens * old_out_rate) / 1_000_000
    new = calls_per_month * (avg_input_tokens * new_in_rate + avg_output_tokens * new_out_rate) / 1_000_000
    return old - new
```

Combine with the evaluation F1 delta to build a quality-per-dollar view. A
0.02 F1 regression that saves $50K/month may be acceptable; a 0.05 F1
regression that saves $500/month is not.

## Don't tier in the same call

A common anti-pattern: `ChatOpenAI(model="gpt-4o-mini", ...).with_fallbacks([gpt4o])`.
This runs mini first, then gpt-4o on failure — you pay for both when the
fallback triggers. Tiering is a **routing** decision (pick one model per
logical step), not a **fallback** decision (fallbacks are for availability,
not cost).

Use `with_fallbacks` for provider outages; use the router in this doc for
cost tiering. Cross-reference: `langchain-sdk-patterns` for fallback discipline.
