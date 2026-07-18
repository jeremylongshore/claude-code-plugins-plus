# Groq Enterprise Access Management — Worked Examples

## Example 1: Weekly per-team usage dashboard

Aggregate recorded usage into a per-team cost/token report. This consumes the usage records
written by `recordTeamUsage` (see [implementation.md](implementation.md) Step 4) and the
`TEAM_CONFIGS` budgets (Step 2).

```typescript
// Weekly usage report per team
function weeklyReport(records: Array<{ team: string; model: string; cost: number; tokens: number }>) {
  const byTeam: Record<string, { cost: number; tokens: number; topModel: string }> = {};

  for (const r of records) {
    if (!byTeam[r.team]) byTeam[r.team] = { cost: 0, tokens: 0, topModel: "" };
    byTeam[r.team].cost += r.cost;
    byTeam[r.team].tokens += r.tokens;
  }

  console.table(
    Object.entries(byTeam).map(([team, data]) => ({
      team,
      cost: `$${data.cost.toFixed(2)}`,
      tokens: data.tokens.toLocaleString(),
      budget: `$${TEAM_CONFIGS[team]?.monthlyBudgetUsd || "N/A"}`,
    }))
  );
}
```

Sample console output:

```text
┌─────────┬───────────┬─────────────┬──────────┐
│  team   │   cost    │   tokens    │  budget  │
├─────────┼───────────┼─────────────┼──────────┤
│ chatbot │  $142.87  │ 48,120,441  │  $200    │
│ analytics│  $11.03  │  9,880,210  │  $50     │
└─────────┴───────────┴─────────────┴──────────┘
```

## Example 2: A blocked request end-to-end

The `analytics` team is scoped to only `llama-3.1-8b-instant`. A call to a larger model is
rejected before it ever reaches Groq:

```typescript
// analytics is NOT authorized for the 70b model
await groqGateway(
  "analytics",
  [{ role: "user", content: "Summarize Q3 revenue" }],
  "llama-3.3-70b-versatile",   // blocked by validateRequest
  512
);
// throws: "Team analytics not authorized for model llama-3.3-70b-versatile"
```

Swapping to the authorized model succeeds and increments the team's tracked spend:

```typescript
await groqGateway(
  "analytics",
  [{ role: "user", content: "Summarize Q3 revenue" }],
  "llama-3.1-8b-instant",      // allowed
  512
);
// returns a chat completion; recordTeamUsage adds the cost to teamSpending["analytics"]
```
