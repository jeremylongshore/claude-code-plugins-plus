# Examples — Orchestrating Multi-Agent Systems (AI SDK v5)

## Example 1: Customer Support Triage System

A coordinator agent classifies incoming support tickets and hands off to specialist agents.

### Setup

```typescript
// package.json dependencies
// "ai": "^5.0.0", "@ai-sdk/openai": "^1.0.0", "@ai-sdk/anthropic": "^1.0.0", "zod": "^3.23.0"

import { openai } from "@ai-sdk/openai";
import { anthropic } from "@ai-sdk/anthropic";
import { generateText, tool } from "ai";
import { z } from "zod";
```

### Agent Definitions

```typescript
// agents/triage-agent.ts
import { generateText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const classifyTicket = tool({
  description: "Classify a support ticket into a category",
  parameters: z.object({
    ticket: z.string().describe("The support ticket text"),
  }),
  execute: async ({ ticket }) => {
    const { text } = await generateText({
      model: openai("gpt-4o-mini"),
      prompt: `Classify this ticket into exactly one category: billing, technical, general.\n\nTicket: ${ticket}\n\nRespond with only the category name.`,
    });
    return { category: text.trim().toLowerCase() };
  },
});

export async function triageTicket(ticket: string) {
  const result = await classifyTicket.execute({ ticket }, { toolCallId: "triage", messages: [] });
  return result.category;
}
```

```typescript
// agents/billing-agent.ts
import { generateText, tool } from "ai";
import { anthropic } from "@ai-sdk/anthropic";
import { z } from "zod";

const lookupInvoice = tool({
  description: "Look up a customer invoice by ID",
  parameters: z.object({
    customerId: z.string(),
  }),
  execute: async ({ customerId }) => {
    // Simulated Stripe lookup
    return {
      customerId,
      lastInvoice: "INV-2024-1234",
      amount: 99.00,
      status: "paid",
      date: "2024-12-01",
    };
  },
});

export async function handleBillingQuery(ticket: string, customerId: string) {
  const { text } = await generateText({
    model: anthropic("claude-sonnet-4-20250514"),
    system: `You are a billing support specialist. Use the invoice lookup tool to answer billing questions. Be concise and helpful.`,
    prompt: `Customer ${customerId} asks: ${ticket}`,
    tools: { lookupInvoice },
    maxSteps: 3,
  });
  return text;
}
```

```typescript
// agents/technical-agent.ts
import { generateText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const searchDocs = tool({
  description: "Search technical documentation",
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }) => {
    // Simulated doc search
    return {
      results: [
        { title: "API Rate Limits", content: "Default rate limit is 100 req/min..." },
        { title: "Authentication Guide", content: "Use Bearer tokens for API auth..." },
      ],
    };
  },
});

export async function handleTechnicalQuery(ticket: string) {
  const { text } = await generateText({
    model: openai("gpt-4o"),
    system: `You are a technical support engineer. Search docs to find solutions. Provide step-by-step fixes.`,
    prompt: ticket,
    tools: { searchDocs },
    maxSteps: 5,
  });
  return text;
}
```

### Coordinator Orchestration

```typescript
// orchestrator.ts
import { triageTicket } from "./agents/triage-agent";
import { handleBillingQuery } from "./agents/billing-agent";
import { handleTechnicalQuery } from "./agents/technical-agent";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

interface TicketResult {
  ticketId: string;
  category: string;
  resolution: string;
  handoffDepth: number;
}

export async function processTicket(
  ticketId: string,
  ticketText: string,
  customerId: string,
  maxHandoffDepth: number = 3
): Promise<TicketResult> {
  let handoffDepth = 0;

  // Step 1: Classify the ticket
  const category = await triageTicket(ticketText);
  handoffDepth++;

  // Step 2: Route to specialist
  let resolution: string;
  switch (category) {
    case "billing":
      resolution = await handleBillingQuery(ticketText, customerId);
      handoffDepth++;
      break;
    case "technical":
      resolution = await handleTechnicalQuery(ticketText);
      handoffDepth++;
      break;
    default:
      // General queries handled by a simple generation
      const { text } = await generateText({
        model: openai("gpt-4o-mini"),
        prompt: `Answer this customer question helpfully: ${ticketText}`,
      });
      resolution = text;
      handoffDepth++;
  }

  return { ticketId, category, resolution, handoffDepth };
}

// Usage
const result = await processTicket(
  "TK-5678",
  "I was charged twice for my subscription last month",
  "CUST-1234"
);
console.log(result);
```

### Expected Output

```json
{
  "ticketId": "TK-5678",
  "category": "billing",
  "resolution": "I found your last invoice INV-2024-1234 for $99.00 dated 2024-12-01, which shows as paid. Let me look into the duplicate charge. I recommend contacting your payment processor to dispute the second charge, or I can escalate this to our billing team for a refund.",
  "handoffDepth": 2
}
```

---

## Example 2: Research Pipeline (Sequential Workflow)

A sequential chain of agents: web search, summarization, and report writing.

```typescript
// pipeline/research-pipeline.ts
import { generateText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

// Schema for structured data passing between agents
const ResearchResultSchema = z.object({
  query: z.string(),
  sources: z.array(z.object({
    title: z.string(),
    url: z.string(),
    snippet: z.string(),
  })),
});

const SummarySchema = z.object({
  query: z.string(),
  keyFindings: z.array(z.string()),
  themes: z.array(z.string()),
});

// Agent 1: Web Search Agent
async function searchAgent(query: string) {
  const webSearch = tool({
    description: "Search the web for information",
    parameters: z.object({ query: z.string() }),
    execute: async ({ query }) => ({
      sources: [
        { title: "AI Trends 2025", url: "https://example.com/ai-trends", snippet: "Key developments in AI..." },
        { title: "LLM Benchmarks", url: "https://example.com/benchmarks", snippet: "Latest model comparisons..." },
        { title: "Enterprise AI Adoption", url: "https://example.com/enterprise", snippet: "82% of enterprises now use AI..." },
      ],
    }),
  });

  const { text } = await generateText({
    model: openai("gpt-4o-mini"),
    system: "You are a research assistant. Search for relevant sources and return structured results as JSON.",
    prompt: `Find sources about: ${query}. Return JSON with query and sources array.`,
    tools: { webSearch },
    maxSteps: 3,
  });

  return JSON.parse(text);
}

// Agent 2: Summarization Agent
async function summarizeAgent(researchResults: z.infer<typeof ResearchResultSchema>) {
  const { text } = await generateText({
    model: openai("gpt-4o"),
    system: "You are an expert summarizer. Extract key findings and themes from research sources. Return JSON.",
    prompt: `Summarize these research results:\n${JSON.stringify(researchResults, null, 2)}\n\nReturn JSON with keyFindings (array of strings) and themes (array of strings).`,
  });

  return JSON.parse(text);
}

// Agent 3: Report Writer Agent
async function reportAgent(summary: z.infer<typeof SummarySchema>) {
  const { text } = await generateText({
    model: openai("gpt-4o"),
    system: "You are a professional report writer. Create a concise executive summary from the provided analysis.",
    prompt: `Write a 200-word executive report based on:\nFindings: ${summary.keyFindings.join("; ")}\nThemes: ${summary.themes.join(", ")}`,
  });

  return text;
}

// Sequential pipeline orchestrator
async function runResearchPipeline(query: string) {
  console.time("pipeline");

  const sources = await searchAgent(query);
  console.log(`[Search] Found ${sources.sources.length} sources`);

  const summary = await summarizeAgent(sources);
  console.log(`[Summary] Extracted ${summary.keyFindings.length} findings`);

  const report = await reportAgent(summary);
  console.log(`[Report] Generated ${report.split(" ").length} word report`);

  console.timeEnd("pipeline");

  return { sources, summary, report };
}

// Usage
const pipeline = await runResearchPipeline("AI agent frameworks 2025");
console.log(pipeline.report);
```

### Expected Output

```
[Search] Found 3 sources
[Summary] Extracted 4 findings
[Report] Generated 195 word report
pipeline: 8.2s

Executive Report: AI Agent Frameworks 2025

The landscape of AI agent frameworks has matured significantly in 2025...
```

---

## Example 3: Code Review Multi-Agent with Supervisor

Parallel specialist reviewers aggregated by a supervisor.

```typescript
// review/code-review-system.ts
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

interface ReviewFinding {
  file: string;
  line: number;
  severity: "critical" | "warning" | "info";
  category: string;
  message: string;
}

// Specialist: Security Reviewer
async function securityReview(diff: string): Promise<ReviewFinding[]> {
  const { text } = await generateText({
    model: openai("gpt-4o"),
    system: `You are a security code reviewer. Analyze diffs for vulnerabilities: SQL injection, XSS, hardcoded secrets, insecure crypto, SSRF. Return JSON array of findings with file, line, severity, category, message.`,
    prompt: `Review this diff for security issues:\n\n${diff}`,
  });
  return JSON.parse(text);
}

// Specialist: Performance Reviewer
async function performanceReview(diff: string): Promise<ReviewFinding[]> {
  const { text } = await generateText({
    model: openai("gpt-4o"),
    system: `You are a performance code reviewer. Analyze diffs for N+1 queries, missing indexes, unbounded loops, memory leaks, blocking I/O. Return JSON array of findings.`,
    prompt: `Review this diff for performance issues:\n\n${diff}`,
  });
  return JSON.parse(text);
}

// Specialist: Style Reviewer
async function styleReview(diff: string): Promise<ReviewFinding[]> {
  const { text } = await generateText({
    model: openai("gpt-4o-mini"),
    system: `You are a code style reviewer. Check naming conventions, function length, complexity, documentation. Return JSON array of findings.`,
    prompt: `Review this diff for style issues:\n\n${diff}`,
  });
  return JSON.parse(text);
}

// Supervisor: Aggregate and prioritize
async function supervisorAggregate(allFindings: ReviewFinding[]): Promise<string> {
  const { text } = await generateText({
    model: openai("gpt-4o"),
    system: `You are a senior engineering lead. Aggregate code review findings into a unified report. Prioritize critical items first. Deduplicate similar findings. Format as a clear, actionable review comment.`,
    prompt: `Create a unified code review from these findings:\n${JSON.stringify(allFindings, null, 2)}`,
  });
  return text;
}

// Orchestrator: parallel fan-out, fan-in
export async function reviewPullRequest(diff: string) {
  // Fan out to specialists in parallel
  const [security, performance, style] = await Promise.all([
    securityReview(diff),
    performanceReview(diff),
    styleReview(diff),
  ]);

  const allFindings = [...security, ...performance, ...style];
  const criticalCount = allFindings.filter(f => f.severity === "critical").length;

  // Fan in to supervisor
  const unifiedReview = await supervisorAggregate(allFindings);

  return {
    totalFindings: allFindings.length,
    criticalCount,
    breakdown: {
      security: security.length,
      performance: performance.length,
      style: style.length,
    },
    review: unifiedReview,
  };
}

// Usage
const review = await reviewPullRequest(`
diff --git a/src/api/users.ts b/src/api/users.ts
+  const user = await db.query(\`SELECT * FROM users WHERE id = \${req.params.id}\`);
+  const password = "admin123";
`);

console.log(`Findings: ${review.totalFindings} (${review.criticalCount} critical)`);
console.log(review.review);
```

### Expected Output

```
Findings: 5 (2 critical)

## Code Review Summary

### Critical Issues
1. **SQL Injection** (src/api/users.ts:1) — String interpolation in SQL query. Use parameterized queries: `db.query('SELECT * FROM users WHERE id = $1', [req.params.id])`
2. **Hardcoded Secret** (src/api/users.ts:2) — Password "admin123" is hardcoded. Move to environment variable or secret manager.

### Warnings
3. **SELECT *** (src/api/users.ts:1) — Avoid SELECT *; specify only needed columns for performance.

### Suggestions
4. Input validation missing for `req.params.id` — add Zod schema validation.
5. Consider adding rate limiting to this endpoint.
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
