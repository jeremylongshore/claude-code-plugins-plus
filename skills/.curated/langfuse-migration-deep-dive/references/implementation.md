# Langfuse Migration Deep Dive - Implementation Details

## Scenario 1: Cloud to Self-Hosted

### Export Data from Cloud

```typescript
async function exportCloudData() {
  const langfuse = new Langfuse({
    publicKey: process.env.LANGFUSE_CLOUD_PUBLIC_KEY!,
    secretKey: process.env.LANGFUSE_CLOUD_SECRET_KEY!,
    baseUrl: "https://cloud.langfuse.com",
  });

  const exportDir = `export-${Date.now()}`;
  await fs.mkdir(exportDir, { recursive: true });

  let page = 1;
  let totalTraces = 0;
  while (true) {
    const traces = await langfuse.fetchTraces({ limit: 100, page });
    if (traces.data.length === 0) break;
    await fs.writeFile(`${exportDir}/traces-${page}.json`, JSON.stringify(traces.data, null, 2));
    totalTraces += traces.data.length;
    page++;
    await new Promise((r) => setTimeout(r, 200));
  }
  console.log(`Exported ${totalTraces} traces`);
}
```

### Docker Compose Self-Hosted

```yaml
version: "3.8"
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/langfuse
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXTAUTH_URL=${LANGFUSE_URL}
      - SALT=${LANGFUSE_SALT}
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-db:/var/lib/postgresql/data
volumes:
  langfuse-db:
```

### Import Data to Self-Hosted

```typescript
async function importToSelfHosted(exportDir: string) {
  const langfuse = new Langfuse({
    publicKey: process.env.LANGFUSE_SELF_HOSTED_PUBLIC_KEY!,
    secretKey: process.env.LANGFUSE_SELF_HOSTED_SECRET_KEY!,
    baseUrl: process.env.LANGFUSE_SELF_HOSTED_URL!,
  });

  const files = await fs.readdir(exportDir);
  for (const file of files.filter((f) => f.startsWith("traces-"))) {
    const traces = JSON.parse(await fs.readFile(path.join(exportDir, file), "utf-8"));
    for (const traceData of traces) {
      langfuse.trace({
        name: traceData.name,
        userId: traceData.userId,
        sessionId: traceData.sessionId,
        metadata: { ...traceData.metadata, migratedFrom: "cloud", originalId: traceData.id },
      });
    }
    await langfuse.flushAsync();
  }
}
```

## Scenario 2: LangSmith to Langfuse

### Adapter for LangSmith Data

```typescript
interface LangSmithRun {
  id: string;
  name: string;
  run_type: "chain" | "llm" | "tool";
  inputs: any;
  outputs: any;
  start_time: string;
  end_time: string;
  child_runs?: LangSmithRun[];
}

function convertLangSmithRun(run: LangSmithRun) {
  const spans = [];
  const generations = [];

  function processRun(r: LangSmithRun) {
    if (r.run_type === "llm") {
      generations.push({ name: r.name, model: r.extra?.metadata?.model || "unknown", input: r.inputs, output: r.outputs });
    } else {
      spans.push({ name: r.name, input: r.inputs, output: r.outputs });
    }
    for (const child of r.child_runs || []) processRun(child);
  }
  processRun(run);

  return { name: run.name, input: run.inputs, output: run.outputs, metadata: { migratedFrom: "langsmith", originalId: run.id }, spans, generations };
}
```

## Scenario 3: Zero-Downtime Dual Write

```typescript
class DualWriteLangfuse {
  private oldClient: any;
  private newClient: Langfuse;
  private writeToOld: boolean = true;
  private writeToNew: boolean = true;

  trace(params: any) {
    if (this.writeToOld) this.oldClient.trace(params);
    if (this.writeToNew) this.newClient.trace(params);
  }

  setWriteMode(options: { old: boolean; new: boolean }) {
    this.writeToOld = options.old;
    this.writeToNew = options.new;
  }
}

// Week 1: dual write, Week 2: verify, Week 3: cutover, Week 4: cleanup
```

## Validation and Verification

```typescript
async function validateMigration(sourceClient: any, targetClient: Langfuse) {
  const sourceTraces = await sourceClient.fetchTraces({ limit: 1 });
  const targetTraces = await targetClient.fetchTraces({ limit: 1 });

  const discrepancies = [];
  const countDiff = Math.abs(sourceTraces.totalCount - targetTraces.totalCount);
  if (countDiff > sourceTraces.totalCount * 0.01) {
    discrepancies.push(`Trace count mismatch: source=${sourceTraces.totalCount}, target=${targetTraces.totalCount}`);
  }

  return { discrepancies, passed: discrepancies.length === 0 };
}
```

## Rollback

```typescript
async function rollback() {
  process.env.LANGFUSE_PUBLIC_KEY = process.env.OLD_LANGFUSE_PUBLIC_KEY;
  process.env.LANGFUSE_SECRET_KEY = process.env.OLD_LANGFUSE_SECRET_KEY;
  process.env.LANGFUSE_HOST = process.env.OLD_LANGFUSE_HOST;
  console.log("Rollback complete. Restart application to apply.");
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
