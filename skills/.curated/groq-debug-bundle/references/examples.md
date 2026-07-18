# Groq Debug Bundle — Examples

## Programmatic Debug Check (TypeScript)

When you would rather generate a machine-readable diagnostic than a tarball, run
this SDK-based check. It confirms auth, lists available models, times a minimal
completion, and prints a JSON report you can attach to a ticket.

```typescript
import Groq from "groq-sdk";

async function groqDiagnostic() {
  const groq = new Groq();
  const report: Record<string, any> = {};

  // Test auth
  try {
    const models = await groq.models.list();
    report.auth = "OK";
    report.modelsAvailable = models.data.map((m) => m.id);
  } catch (err) {
    report.auth = `FAILED: ${(err as Error).message}`;
    return report;
  }

  // Test completion
  try {
    const start = performance.now();
    const completion = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Reply: OK" }],
      max_tokens: 5,
      temperature: 0,
    });
    report.completion = "OK";
    report.latencyMs = Math.round(performance.now() - start);
    report.model = completion.model;
    report.usage = completion.usage;
  } catch (err: any) {
    report.completion = `FAILED: ${err.status} ${err.message}`;
  }

  return report;
}

groqDiagnostic().then((r) => console.log(JSON.stringify(r, null, 2)));
```

### Sample output — healthy account

```json
{
  "auth": "OK",
  "modelsAvailable": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
  "completion": "OK",
  "latencyMs": 214,
  "model": "llama-3.1-8b-instant",
  "usage": { "prompt_tokens": 11, "completion_tokens": 2, "total_tokens": 13 }
}
```

### Sample output — bad key

```json
{
  "auth": "FAILED: 401 Invalid API Key"
}
```

## Shell bundle — end-to-end run

```console
$ export GROQ_API_KEY=gsk_...        # your key
$ bash collect-groq-bundle.sh
Collecting Groq debug bundle...
Bundle created: groq-debug-20260717-142233.tar.gz
Review before sharing -- ensure no secrets are included.

$ tar tzf groq-debug-20260717-142233.tar.gz
groq-debug-20260717-142233/environment.txt
groq-debug-20260717-142233/connectivity.txt
groq-debug-20260717-142233/rate-limits.txt
groq-debug-20260717-142233/latency.txt
groq-debug-20260717-142233/app-logs.txt
groq-debug-20260717-142233/config-redacted.txt
```

The full six-step collection script that produces this tarball lives in
[implementation.md](implementation.md).
