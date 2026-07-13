# Linear Debug Bundle - Detailed Implementation

## Debug Client Wrapper

```typescript
import { LinearClient } from "@linear/sdk";

interface DebugOptions {
  logRequests?: boolean;
  logResponses?: boolean;
  logErrors?: boolean;
  onRequest?: (query: string, variables: unknown) => void;
  onResponse?: (data: unknown, duration: number) => void;
  onError?: (error: Error, duration: number) => void;
}

export function createDebugClient(apiKey: string, options: DebugOptions = {}): LinearClient {
  const { logRequests = true, logResponses = true, logErrors = true } = options;

  const client = new LinearClient({
    apiKey,
    fetch: async (url, init) => {
      const start = Date.now();
      const body = init?.body ? JSON.parse(init.body as string) : null;

      if (logRequests && body) {
        console.log("[Linear Request]", {
          query: body.query?.slice(0, 100) + "...",
          variables: body.variables,
        });
        options.onRequest?.(body.query, body.variables);
      }

      try {
        const response = await fetch(url, init);
        const duration = Date.now() - start;
        const data = await response.clone().json();

        if (logResponses) {
          console.log("[Linear Response]", {
            duration: `${duration}ms`,
            hasErrors: !!data.errors,
            dataKeys: data.data ? Object.keys(data.data) : [],
          });
          options.onResponse?.(data, duration);
        }

        return response;
      } catch (error) {
        const duration = Date.now() - start;
        if (logErrors) {
          console.error("[Linear Error]", {
            duration: `${duration}ms`,
            error: error instanceof Error ? error.message : error,
          });
          options.onError?.(error as Error, duration);
        }
        throw error;
      }
    },
  });

  return client;
}
```

## Request Tracer

```typescript
interface TraceEntry {
  id: string;
  operation: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  success: boolean;
  error?: string;
  metadata?: Record<string, unknown>;
}

class LinearTracer {
  private traces: TraceEntry[] = [];
  private maxTraces = 100;

  startTrace(operation: string, metadata?: Record<string, unknown>): string {
    const id = crypto.randomUUID();
    this.traces.push({ id, operation, startTime: new Date(), success: false, metadata });

    if (this.traces.length > this.maxTraces) {
      this.traces = this.traces.slice(-this.maxTraces);
    }

    return id;
  }

  endTrace(id: string, success: boolean, error?: string): void {
    const trace = this.traces.find(t => t.id === id);
    if (trace) {
      trace.endTime = new Date();
      trace.duration = trace.endTime.getTime() - trace.startTime.getTime();
      trace.success = success;
      trace.error = error;
    }
  }

  getTraces(): TraceEntry[] {
    return [...this.traces];
  }

  getSlowTraces(thresholdMs = 1000): TraceEntry[] {
    return this.traces.filter(t => (t.duration ?? 0) > thresholdMs);
  }

  getFailedTraces(): TraceEntry[] {
    return this.traces.filter(t => !t.success);
  }

  getSummary(): Record<string, unknown> {
    const completed = this.traces.filter(t => t.duration !== undefined);
    const durations = completed.map(t => t.duration!);

    return {
      total: this.traces.length,
      completed: completed.length,
      failed: this.getFailedTraces().length,
      avgDuration: durations.length
        ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
        : 0,
      maxDuration: Math.max(...durations, 0),
    };
  }
}

export const tracer = new LinearTracer();
```

## Health Check Utility

```typescript
import { LinearClient } from "@linear/sdk";

interface HealthCheckResult {
  healthy: boolean;
  latencyMs: number;
  user?: { name: string; email: string };
  teams?: number;
  error?: string;
  timestamp: Date;
}

export async function checkLinearHealth(client: LinearClient): Promise<HealthCheckResult> {
  const start = Date.now();

  try {
    const [viewer, teams] = await Promise.all([client.viewer, client.teams()]);

    return {
      healthy: true,
      latencyMs: Date.now() - start,
      user: { name: viewer.name, email: viewer.email },
      teams: teams.nodes.length,
      timestamp: new Date(),
    };
  } catch (error) {
    return {
      healthy: false,
      latencyMs: Date.now() - start,
      error: error instanceof Error ? error.message : "Unknown error",
      timestamp: new Date(),
    };
  }
}

export function healthEndpoint(client: LinearClient) {
  return async (req: any, res: any) => {
    const result = await checkLinearHealth(client);
    res.status(result.healthy ? 200 : 503).json(result);
  };
}
```

## Debug Console Commands

```typescript
import { LinearClient } from "@linear/sdk";
import readline from "readline";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

const commands: Record<string, () => Promise<void>> = {
  async me() {
    const viewer = await client.viewer;
    console.log("Current user:", viewer.name, viewer.email);
  },

  async teams() {
    const teams = await client.teams();
    console.log("Teams:");
    teams.nodes.forEach(t => console.log(`  ${t.key}: ${t.name}`));
  },

  async issues() {
    const issues = await client.issues({ first: 10 });
    console.log("Recent issues:");
    issues.nodes.forEach(i => console.log(`  ${i.identifier}: ${i.title}`));
  },

  async states() {
    const teams = await client.teams();
    for (const team of teams.nodes) {
      const states = await team.states();
      console.log(`\n${team.key} workflow:`);
      states.nodes.forEach(s => console.log(`  ${s.name} (${s.type})`));
    }
  },

  help() {
    console.log("Commands: me, teams, issues, states, help, exit");
    return Promise.resolve();
  },
};

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, prompt: "linear> " });

rl.prompt();
rl.on("line", async (line) => {
  const cmd = line.trim().toLowerCase();
  if (cmd === "exit") { rl.close(); return; }
  if (commands[cmd]) { await commands[cmd](); }
  else { console.log("Unknown command. Type 'help' for available commands."); }
  rl.prompt();
});
```

## Environment Validator

```typescript
interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export function validateLinearEnv(): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!process.env.LINEAR_API_KEY) {
    errors.push("LINEAR_API_KEY is not set");
  } else if (!process.env.LINEAR_API_KEY.startsWith("lin_api_")) {
    errors.push("LINEAR_API_KEY has invalid format (should start with lin_api_)");
  }

  if (!process.env.LINEAR_WEBHOOK_SECRET) {
    warnings.push("LINEAR_WEBHOOK_SECRET not set (webhooks won't be verified)");
  }

  if (process.env.NODE_ENV === "production" && !process.env.LINEAR_API_KEY?.includes("prod")) {
    warnings.push("Using non-production API key in production environment");
  }

  return { valid: errors.length === 0, errors, warnings };
}

// Run validation on import
const result = validateLinearEnv();
if (!result.valid) {
  console.error("Linear environment validation failed:", result.errors);
}
result.warnings.forEach(w => console.warn("Linear warning:", w));
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
