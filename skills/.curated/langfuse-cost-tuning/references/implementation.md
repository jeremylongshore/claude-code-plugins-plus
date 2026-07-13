# Langfuse Cost Tuning - Implementation Details

## Token Usage Tracking

```typescript
import { Langfuse } from "langfuse";

const MODEL_PRICING: Record<string, { input: number; output: number }> = {
  "gpt-4-turbo": { input: 10.0, output: 30.0 },
  "gpt-4o": { input: 5.0, output: 15.0 },
  "gpt-4o-mini": { input: 0.15, output: 0.6 },
  "gpt-3.5-turbo": { input: 0.5, output: 1.5 },
  "claude-3-opus": { input: 15.0, output: 75.0 },
  "claude-3-sonnet": { input: 3.0, output: 15.0 },
  "claude-3-haiku": { input: 0.25, output: 1.25 },
};

function calculateCost(model: string, promptTokens: number, completionTokens: number): number {
  const pricing = MODEL_PRICING[model] || { input: 0, output: 0 };
  return (promptTokens / 1_000_000) * pricing.input + (completionTokens / 1_000_000) * pricing.output;
}

async function tracedLLMCall(trace: any, model: string, messages: any[]) {
  const generation = trace.generation({ name: "llm-call", model, input: messages });
  const response = await openai.chat.completions.create({ model, messages });
  const usage = response.usage!;
  const cost = calculateCost(model, usage.prompt_tokens, usage.completion_tokens);

  generation.end({
    output: response.choices[0].message,
    usage: { promptTokens: usage.prompt_tokens, completionTokens: usage.completion_tokens, totalTokens: usage.total_tokens },
    metadata: { cost_usd: cost, model_version: model },
  });
  return response;
}
```

## Cost Analytics Dashboard

```typescript
async function getCostAnalytics(days: number = 30) {
  const langfuse = new Langfuse();
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - days);

  const generations = await langfuse.fetchGenerations({ fromTimestamp: fromDate });

  const costByModel: Record<string, number> = {};
  const costByDay: Record<string, number> = {};
  const tokensByModel: Record<string, { prompt: number; completion: number }> = {};

  for (const gen of generations.data) {
    const model = gen.model || "unknown";
    const date = new Date(gen.startTime).toISOString().split("T")[0];
    const cost = gen.metadata?.cost_usd || calculateCost(model, gen.usage?.promptTokens || 0, gen.usage?.completionTokens || 0);

    costByModel[model] = (costByModel[model] || 0) + cost;
    costByDay[date] = (costByDay[date] || 0) + cost;
    if (!tokensByModel[model]) tokensByModel[model] = { prompt: 0, completion: 0 };
    tokensByModel[model].prompt += gen.usage?.promptTokens || 0;
    tokensByModel[model].completion += gen.usage?.completionTokens || 0;
  }

  return {
    totalCost: Object.values(costByModel).reduce((a, b) => a + b, 0),
    costByModel, costByDay, tokensByModel,
    generationCount: generations.data.length,
  };
}
```

## Cost Alerts

```typescript
class CostMonitor {
  private hourlySpend: Map<string, number> = new Map();
  private dailySpend: Map<string, number> = new Map();

  trackCost(cost: number) {
    const hourKey = new Date().toISOString().slice(0, 13);
    const dayKey = new Date().toISOString().slice(0, 10);
    this.hourlySpend.set(hourKey, (this.hourlySpend.get(hourKey) || 0) + cost);
    this.dailySpend.set(dayKey, (this.dailySpend.get(dayKey) || 0) + cost);
    this.checkAlerts(cost);
  }

  private checkAlerts(requestCost: number) {
    const dayKey = new Date().toISOString().slice(0, 10);
    const dailyTotal = this.dailySpend.get(dayKey) || 0;

    const COST_ALERTS = [
      { type: "daily", threshold: 100, action: "warn" },
      { type: "daily", threshold: 500, action: "notify" },
      { type: "per-request", threshold: 1, action: "warn" },
    ];

    for (const alert of COST_ALERTS) {
      const currentValue = alert.type === "daily" ? dailyTotal : requestCost;
      if (currentValue >= alert.threshold) {
        const message = `Cost alert: ${alert.type} spend $${currentValue.toFixed(2)} exceeded threshold $${alert.threshold}`;
        if (alert.action === "warn") console.warn(message);
        else if (alert.action === "notify") this.sendNotification(message);
      }
    }
  }

  private async sendNotification(message: string) {
    await fetch(process.env.SLACK_WEBHOOK_URL!, {
      method: "POST", body: JSON.stringify({ text: message }),
    });
  }

  getStats() {
    const dayKey = new Date().toISOString().slice(0, 10);
    return { dailySpend: this.dailySpend.get(dayKey) || 0, dailyBudgetRemaining: 100 - (this.dailySpend.get(dayKey) || 0) };
  }
}
```

## Cost Optimization Strategies

```typescript
class CostOptimizedModelSelector {
  selectModel(task: string, inputLength: number): string {
    const simpleTasks = ["summarize", "classify", "extract"];
    if (simpleTasks.some((t) => task.toLowerCase().includes(t))) return "gpt-4o-mini";
    if (inputLength < 500) return "gpt-4o-mini";
    const complexTasks = ["analyze", "reason", "code", "math"];
    if (complexTasks.some((t) => task.toLowerCase().includes(t))) return "gpt-4o";
    return "gpt-4o-mini";
  }
}

function optimizePrompt(prompt: string): string {
  let optimized = prompt.replace(/\s+/g, " ").trim();
  optimized = optimized.replace(/please |kindly |could you /gi, "");
  return optimized;
}

const responseCache = new Map<string, { response: string; timestamp: Date }>();

async function cachedLLMCall(prompt: string, model: string, ttlMs: number = 3600000): Promise<string> {
  const cacheKey = `${model}:${prompt}`;
  const cached = responseCache.get(cacheKey);
  if (cached && Date.now() - cached.timestamp.getTime() < ttlMs) return cached.response;
  const response = await callLLM(prompt, model);
  responseCache.set(cacheKey, { response, timestamp: new Date() });
  return response;
}
```

## Cost Reports

```typescript
async function generateCostReport(period: "daily" | "weekly" | "monthly") {
  const days = period === "daily" ? 1 : period === "weekly" ? 7 : 30;
  const analytics = await getCostAnalytics(days);

  return `
# LLM Cost Report - ${period}
Generated: ${new Date().toISOString()}

## Summary
- Total Cost: $${analytics.totalCost.toFixed(2)}
- Total Generations: ${analytics.generationCount}
- Average Cost per Generation: $${(analytics.totalCost / analytics.generationCount).toFixed(4)}

## Cost by Model
${Object.entries(analytics.costByModel).sort(([, a], [, b]) => b - a).map(([model, cost]) => `- ${model}: $${cost.toFixed(2)}`).join("\n")}

## Recommendations
${generateRecommendations(analytics)}
`;
}

function generateRecommendations(analytics: any): string {
  const recommendations: string[] = [];
  const gpt4Cost = analytics.costByModel["gpt-4-turbo"] || 0;
  if (gpt4Cost > analytics.totalCost * 0.5) {
    recommendations.push("- Consider GPT-4o or GPT-4o-mini for simpler tasks");
  }
  for (const [model, tokens] of Object.entries(analytics.tokensByModel)) {
    const { prompt, completion } = tokens as any;
    if (completion > prompt * 2) {
      recommendations.push(`- ${model}: High output ratio. Consider limiting max_tokens`);
    }
  }
  return recommendations.length > 0 ? recommendations.join("\n") : "- No immediate optimization opportunities identified";
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
