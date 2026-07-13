# Monitoring Configuration Examples

## Call Quality Webhook Handler

```typescript
// retell-webhook-handler.ts
app.post('/webhooks/retell', (req, res) => {
  const { call_id, agent_id, status, duration_seconds, cost_usd, disconnect_reason } = req.body;

  emitCounter('retell_calls_total', 1, { agent: agent_id, status });
  emitHistogram('retell_call_duration_sec', duration_seconds, { agent: agent_id });
  emitCounter('retell_cost_usd', cost_usd, { agent: agent_id });

  if (disconnect_reason === 'agent_error' || disconnect_reason === 'system_error') {
    emitCounter('retell_call_errors_total', 1, { agent: agent_id, reason: disconnect_reason });
  }

  res.sendStatus(200);
});
```

## Conversational Latency Query

```bash
set -euo pipefail
# Query recent calls for response latency metrics
curl "https://api.retellai.com/v1/calls?limit=20&sort=-created_at" \
  -H "Authorization: Bearer $RETELL_API_KEY" | \
  jq '.[] | {
    call_id, agent_name, duration_sec: .duration,
    avg_response_latency_ms: .avg_agent_response_latency_ms,
    cost_usd: .cost,
    disconnect_reason
  }'
```

## Per-Agent Performance Report

```typescript
// Track which agents are performing well vs poorly
async function agentPerformanceReport() {
  const agents = await retellApi.listAgents();
  for (const agent of agents) {
    const calls = await retellApi.listCalls({ agent_id: agent.agent_id, limit: 100 });
    const completed = calls.filter(c => c.status === 'completed').length;
    const avgDuration = calls.reduce((s, c) => s + c.duration, 0) / calls.length;
    const totalCost = calls.reduce((s, c) => s + c.cost, 0);

    emitGauge('retell_agent_completion_rate', completed / calls.length * 100, { agent: agent.agent_name });
    emitGauge('retell_agent_avg_duration_sec', avgDuration, { agent: agent.agent_name });
    emitGauge('retell_agent_total_cost_usd', totalCost, { agent: agent.agent_name });
  }
}
```

## Prometheus Alert Rules

```yaml
groups:
  - name: retell
    rules:
      - alert: RetellHighDropRate
        expr: rate(retell_calls_total{status="failed"}[1h]) / rate(retell_calls_total[1h]) > 0.1
        annotations: { summary: "Retell call failure rate exceeds 10%" }
      - alert: RetellHighLatency
        expr: histogram_quantile(0.95, rate(retell_response_latency_ms_bucket[1h])) > 2000
        annotations: { summary: "Retell agent response latency P95 exceeds 2 seconds" }
      - alert: RetellCostSpike
        expr: increase(retell_cost_usd[1h]) > 50
        annotations: { summary: "Retell voice costs exceed $50/hour" }
      - alert: RetellShortCalls
        expr: histogram_quantile(0.25, rate(retell_call_duration_sec_bucket[1h])) < 10
        annotations: { summary: "25% of calls ending in <10 seconds (agent issue?)" }
```
