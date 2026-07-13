# Langfuse Production Checklist - Implementation Details

## Production Configuration

```typescript
import { Langfuse } from "langfuse";

function validateConfig(config: Record<string, any>): void {
  const required = ["publicKey", "secretKey"];
  const missing = required.filter((key) => !config[key]);
  if (missing.length > 0) {
    throw new Error(`Missing Langfuse config: ${missing.join(", ")}`);
  }
  if (config.publicKey.includes("test") || config.publicKey.includes("dev")) {
    console.warn("WARNING: Using non-production API keys!");
  }
}

export function createProductionLangfuse() {
  const config = {
    publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
    secretKey: process.env.LANGFUSE_SECRET_KEY!,
    baseUrl: process.env.LANGFUSE_HOST || "https://cloud.langfuse.com",
    flushAt: 25,
    flushInterval: 5000,
    requestTimeout: 15000,
    enabled: process.env.NODE_ENV === "production",
  };
  validateConfig(config);
  return new Langfuse(config);
}
```

## Production Error Handling

```typescript
let langfuseInstance: Langfuse | null = null;

export function getLangfuse(): Langfuse {
  if (!langfuseInstance) {
    langfuseInstance = createProductionLangfuse();
    const shutdown = async () => {
      console.log("Flushing Langfuse traces...");
      await langfuseInstance?.shutdownAsync();
      console.log("Langfuse shutdown complete");
    };
    process.on("SIGTERM", shutdown);
    process.on("SIGINT", shutdown);
    process.on("beforeExit", shutdown);
  }
  return langfuseInstance;
}

export async function safeTrace<T>(
  name: string,
  operation: (trace: ReturnType<typeof langfuse.trace>) => Promise<T>,
  metadata?: Record<string, any>
): Promise<T> {
  const langfuse = getLangfuse();
  let trace;
  try {
    trace = langfuse.trace({ name, metadata: { ...metadata, environment: "production" } });
  } catch (error) {
    console.error("Failed to create Langfuse trace:", error);
    return operation(null as any);
  }
  try {
    const result = await operation(trace);
    trace.update({ output: { success: true } });
    return result;
  } catch (error) {
    trace.update({ output: { error: String(error) }, level: "ERROR" });
    throw error;
  }
}
```

## Pre-Deployment Verification Script

```typescript
async function verifyProduction() {
  console.log("=== Langfuse Production Verification ===\n");

  const checks: Array<{ name: string; check: () => Promise<boolean> }> = [
    {
      name: "Environment variables set",
      check: async () => {
        const required = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"];
        const missing = required.filter((key) => !process.env[key]);
        if (missing.length > 0) { console.log(`  Missing: ${missing.join(", ")}`); return false; }
        return true;
      },
    },
    {
      name: "API keys are production keys",
      check: async () => {
        const key = process.env.LANGFUSE_PUBLIC_KEY || "";
        const isProduction = !key.includes("test") && !key.includes("dev") && key.startsWith("pk-lf-");
        if (!isProduction) console.log("  Key appears to be non-production");
        return isProduction;
      },
    },
    {
      name: "Can create trace",
      check: async () => {
        const langfuse = new Langfuse();
        langfuse.trace({ name: "production-verification", metadata: { test: true } });
        await langfuse.flushAsync();
        return true;
      },
    },
    {
      name: "Graceful shutdown works",
      check: async () => {
        const langfuse = new Langfuse();
        langfuse.trace({ name: "shutdown-test" });
        await langfuse.shutdownAsync();
        return true;
      },
    },
  ];

  let passed = 0, failed = 0;
  for (const { name, check } of checks) {
    process.stdout.write(`[ ] ${name}...`);
    try {
      const result = await check();
      if (result) { console.log("\r[+]"); passed++; } else { console.log("\r[-]"); failed++; }
    } catch (error) { console.log(`\r[-] Error: ${error}`); failed++; }
  }
  console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
  if (failed > 0) process.exit(1);
}

verifyProduction();
```

## Production Monitoring

```typescript
interface LangfuseMetrics {
  tracesCreated: number;
  tracesFailed: number;
  flushLatencyMs: number[];
  lastFlushTime: Date | null;
}

const metrics: LangfuseMetrics = {
  tracesCreated: 0,
  tracesFailed: 0,
  flushLatencyMs: [],
  lastFlushTime: null,
};

app.get("/metrics/langfuse", (req, res) => {
  const avgFlushLatency = metrics.flushLatencyMs.length > 0
    ? metrics.flushLatencyMs.reduce((a, b) => a + b) / metrics.flushLatencyMs.length : 0;
  res.json({
    tracesCreated: metrics.tracesCreated,
    tracesFailed: metrics.tracesFailed,
    avgFlushLatencyMs: avgFlushLatency.toFixed(2),
    lastFlushTime: metrics.lastFlushTime?.toISOString(),
    errorRate: ((metrics.tracesFailed / (metrics.tracesCreated || 1)) * 100).toFixed(2),
  });
});
```

## Final Production Configuration

```typescript
export const productionLangfuseConfig = {
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST || "https://cloud.langfuse.com",
  flushAt: 25,
  flushInterval: 5000,
  requestTimeout: 15000,
  enabled: process.env.NODE_ENV === "production",
  debug: false,
};
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
