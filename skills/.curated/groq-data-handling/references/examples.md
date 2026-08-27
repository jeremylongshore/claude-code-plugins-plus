# Groq Data Handling — Examples

Two ready-to-use add-ons that build on the core pipeline in
[implementation.md](implementation.md): content moderation via Llama Guard,
and a daily cost report aggregated from the usage records emitted by
`trackUsage`.

## Example: Content Safety Check

Route text through Groq's Llama Guard model for moderation before (or after)
your main completion. Returns a `safe` boolean plus any triggered category
labels.

```typescript
// Use Groq's Llama Guard for content moderation
async function moderateContent(text: string): Promise<{
  safe: boolean;
  categories: string[];
}> {
  const completion = await groq.chat.completions.create({
    model: "meta-llama/llama-guard-4-12b",
    messages: [{ role: "user", content: text }],
    max_tokens: 100,
  });

  const response = completion.choices[0].message.content || "";
  const safe = response.trim().toLowerCase().startsWith("safe");

  return {
    safe,
    categories: safe ? [] : response.split("\n").slice(1).map((l) => l.trim()).filter(Boolean),
  };
}
```

## Example: Daily Cost Report

Aggregate an array of `UsageRecord` (the objects `trackUsage` returns) into a
per-model cost/tokens/calls breakdown plus grand totals.

```typescript
function generateCostReport(records: UsageRecord[]) {
  const totalCost = records.reduce((sum, r) => sum + r.estimatedCostUsd, 0);
  const totalTokens = records.reduce((sum, r) => sum + r.totalTokens, 0);

  const byModel: Record<string, { cost: number; tokens: number; calls: number }> = {};
  for (const r of records) {
    if (!byModel[r.model]) byModel[r.model] = { cost: 0, tokens: 0, calls: 0 };
    byModel[r.model].cost += r.estimatedCostUsd;
    byModel[r.model].tokens += r.totalTokens;
    byModel[r.model].calls++;
  }

  return {
    totalCost: `$${totalCost.toFixed(4)}`,
    totalTokens,
    totalCalls: records.length,
    byModel: Object.fromEntries(
      Object.entries(byModel).map(([model, data]) => [
        model,
        { cost: `$${data.cost.toFixed(4)}`, tokens: data.tokens, calls: data.calls },
      ])
    ),
  };
}
```

### Expected report shape

```json
{
  "totalCost": "$0.0431",
  "totalTokens": 84210,
  "totalCalls": 37,
  "byModel": {
    "llama-3.3-70b-versatile": { "cost": "$0.0402", "tokens": 61200, "calls": 21 },
    "llama-3.1-8b-instant":    { "cost": "$0.0029", "tokens": 23010, "calls": 16 }
  }
}
```
