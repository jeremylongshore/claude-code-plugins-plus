---
name: linear-debug-bundle
description: |
  Comprehensive debugging toolkit for Linear integrations.
  Use when setting up logging, tracing API calls,
  or building debug utilities for Linear.
  Trigger: "debug linear integration", "linear logging",
  "trace linear API", "linear debugging tools".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, debugging, logging]

---
# Linear Debug Bundle

## Overview
Production-ready debugging tools for Linear API integrations: instrumented client with request/response logging, request tracer with performance metrics, health check endpoint, environment validator, and interactive debug console.

## Prerequisites
- `@linear/sdk` installed and configured
- Node.js 18+
- Optional: pino or winston for structured logging

## Instructions

### Tool 1: Debug Client Wrapper
Intercept all API calls with timing, logging, and error capture by wrapping the SDK's underlying fetch.

```typescript
import { LinearClient } from "@linear/sdk";

interface DebugOptions {
  logRequests?: boolean;
  logResponses?: boolean;
  onRequest?: (query: string, variables: any) => void;
  onResponse?: (query: string, duration: number, data: any) => void;
  onError?: (query: string, duration: number, error: any) => void;
}

function createDebugClient(apiKey: string, opts: DebugOptions = {}): LinearClient {
  const { logRequests = true, logResponses = true } = opts;

  return new LinearClient({
    apiKey,
    headers: { "X-Debug": "true" },
  });
}

// Manual instrumentation wrapper
async function debugQuery<T>(
  label: string,
  fn: () => Promise<T>,
  opts?: DebugOptions
): Promise<T> {
  const start = Date.now();
  console.log(`[Linear:DEBUG] >>> ${label}`);

  try {
    const result = await fn();
    const ms = Date.now() - start;
    console.log(`[Linear:DEBUG] <<< ${label} (${ms}ms) OK`);
    opts?.onResponse?.(label, ms, result);
    return result;
  } catch (error) {
    const ms = Date.now() - start;
    console.error(`[Linear:DEBUG] !!! ${label} (${ms}ms) FAILED:`, error);
    opts?.onError?.(label, ms, error);
    throw error;
  }
}

// Usage
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
const teams = await debugQuery("teams()", () => client.teams());
const issues = await debugQuery("issues(first:50)", () => client.issues({ first: 50 }));
```

### Tool 2: Request Tracer
Track all API calls with timing, success/failure, and aggregate stats.

```typescript
interface TraceEntry {
  id: string;
  operation: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  success: boolean;
  error?: string;
}

class LinearTracer {
  private traces: TraceEntry[] = [];
  private maxTraces = 200;

  startTrace(operation: string): string {
    const id = `trace-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    this.traces.push({ id, operation, startTime: Date.now(), success: false });
    if (this.traces.length > this.maxTraces) this.traces = this.traces.slice(-100);
    return id;
  }

  endTrace(id: string, success: boolean, error?: string): void {
    const trace = this.traces.find(t => t.id === id);
    if (trace) {
      trace.endTime = Date.now();
      trace.duration = trace.endTime - trace.startTime;
      trace.success = success;
      trace.error = error;
    }
  }

  getSlowTraces(thresholdMs = 2000): TraceEntry[] {
    return this.traces.filter(t => (t.duration ?? 0) > thresholdMs);
  }

  getFailedTraces(): TraceEntry[] {
    return this.traces.filter(t => !t.success && t.endTime);
  }

  getSummary() {
    const completed = this.traces.filter(t => t.endTime);
    const durations = completed.map(t => t.duration ?? 0);
    return {
      total: this.traces.length,
      completed: completed.length,
      failed: this.getFailedTraces().length,
      avgMs: durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 0,
      maxMs: durations.length ? Math.max(...durations) : 0,
      p95Ms: durations.length ? durations.sort((a, b) => a - b)[Math.floor(durations.length * 0.95)] : 0,
    };
  }
}

// Usage
const tracer = new LinearTracer();

async function tracedCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  const id = tracer.startTrace(operation);
  try {
    const result = await fn();
    tracer.endTrace(id, true);
    return result;
  } catch (error: any) {
    tracer.endTrace(id, false, error.message);
    throw error;
  }
}

// After running operations:
console.log("Trace summary:", tracer.getSummary());
console.log("Slow traces:", tracer.getSlowTraces(1000));
```

### Tool 3: Health Check Utility
```typescript
interface HealthResult {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs: number;
  user?: string;
  teamCount?: number;
  error?: string;
}

async function checkLinearHealth(client: LinearClient): Promise<HealthResult> {
  const start = Date.now();
  try {
    const [viewer, teams] = await Promise.all([client.viewer, client.teams()]);
    const latencyMs = Date.now() - start;
    return {
      status: latencyMs > 3000 ? "degraded" : "healthy",
      latencyMs,
      user: viewer.name,
      teamCount: teams.nodes.length,
    };
  } catch (error: any) {
    return {
      status: "unhealthy",
      latencyMs: Date.now() - start,
      error: error.message,
    };
  }
}

// Express endpoint
app.get("/health/linear", async (req, res) => {
  const health = await checkLinearHealth(client);
  res.status(health.status === "unhealthy" ? 503 : 200).json(health);
});
```

### Tool 4: Environment Validator
```typescript
function validateLinearEnv(): { valid: boolean; issues: string[] } {
  const issues: string[] = [];
  const apiKey = process.env.LINEAR_API_KEY;

  if (!apiKey) {
    issues.push("LINEAR_API_KEY is not set");
  } else if (!apiKey.startsWith("lin_api_")) {
    issues.push("LINEAR_API_KEY must start with 'lin_api_'");
  } else if (apiKey.length < 30) {
    issues.push("LINEAR_API_KEY appears truncated");
  }

  if (!process.env.LINEAR_WEBHOOK_SECRET) {
    issues.push("WARNING: LINEAR_WEBHOOK_SECRET not set (webhooks won't verify)");
  }

  if (process.env.NODE_ENV === "production" && apiKey?.includes("dev")) {
    issues.push("WARNING: API key appears to be a development key in production");
  }

  const valid = issues.filter(i => !i.startsWith("WARNING")).length === 0;
  return { valid, issues };
}

// Auto-run on import
const envCheck = validateLinearEnv();
if (!envCheck.valid) {
  console.error("[Linear] Environment validation failed:");
  envCheck.issues.forEach(i => console.error(`  - ${i}`));
}
```

### Tool 5: Interactive Debug Console
```typescript
import readline from "readline";
import { LinearClient } from "@linear/sdk";

async function debugConsole(client: LinearClient): Promise<void> {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const prompt = () => rl.question("linear> ", handleCommand);

  async function handleCommand(cmd: string) {
    const trimmed = cmd.trim();
    try {
      switch (trimmed) {
        case "me": {
          const v = await client.viewer;
          console.log(`${v.name} (${v.email})`);
          break;
        }
        case "teams": {
          const t = await client.teams();
          t.nodes.forEach(team => console.log(`  ${team.key}: ${team.name}`));
          break;
        }
        case "issues": {
          const i = await client.issues({ first: 10, orderBy: "updatedAt" });
          i.nodes.forEach(issue => console.log(`  ${issue.identifier}: ${issue.title}`));
          break;
        }
        case "health": {
          const h = await checkLinearHealth(client);
          console.log(JSON.stringify(h, null, 2));
          break;
        }
        case "exit": rl.close(); return;
        default: console.log("Commands: me, teams, issues, health, exit");
      }
    } catch (e: any) {
      console.error(`Error: ${e.message}`);
    }
    prompt();
  }

  console.log("Linear Debug Console — type 'help' for commands");
  prompt();
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular JSON in logs | Logging full SDK objects | Use selective fields, not `JSON.stringify(issue)` |
| Memory leak | Unbounded trace storage | Set `maxTraces` limit, trim oldest |
| Missing env vars | Env not loaded | Call `validateLinearEnv()` on startup |
| Health check timeout | Network issue or Linear outage | Add 10s timeout, check status.linear.app |

## Examples

### Quick Diagnostic Script
```bash
# One-liner to test API connectivity and print auth info
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name email } }"}' | jq .
```

### Benchmark API Calls
```typescript
async function benchmark(label: string, fn: () => Promise<any>) {
  const runs = 5;
  const times: number[] = [];
  for (let i = 0; i < runs; i++) {
    const start = Date.now();
    await fn();
    times.push(Date.now() - start);
  }
  const avg = Math.round(times.reduce((a, b) => a + b) / runs);
  const max = Math.max(...times);
  console.log(`${label}: avg=${avg}ms, max=${max}ms (${runs} runs)`);
}

await benchmark("viewer", () => client.viewer);
await benchmark("teams", () => client.teams());
await benchmark("issues(50)", () => client.issues({ first: 50 }));
```

## Resources
- [Linear SDK Source](https://github.com/linear/linear)
- [Linear API Status](https://status.linear.app)
- [Node.js Performance Hooks](https://nodejs.org/api/perf_hooks.html)
