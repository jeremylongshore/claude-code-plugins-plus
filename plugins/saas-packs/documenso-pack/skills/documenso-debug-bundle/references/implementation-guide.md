# Documenso Debug Bundle - Implementation Guide

## Debug Scripts

### Script 1: Connection Diagnostic

```typescript
// scripts/documenso-diagnostic.ts
import { Documenso } from "@documenso/sdk-typescript";

interface DiagnosticResult {
  timestamp: string;
  environment: {
    nodeVersion: string;
    sdkVersion: string;
    apiKeyPresent: boolean;
    apiKeyPrefix: string;
    baseUrl: string;
  };
  connectivity: {
    canConnect: boolean;
    latencyMs: number;
    error?: string;
  };
  account: {
    documentsCount?: number;
    templatesCount?: number;
    error?: string;
  };
}

async function runDiagnostic(): Promise<DiagnosticResult> {
  const result: DiagnosticResult = {
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      sdkVersion: "latest", // Get from package.json
      apiKeyPresent: !!process.env.DOCUMENSO_API_KEY,
      apiKeyPrefix: process.env.DOCUMENSO_API_KEY?.substring(0, 7) ?? "missing",
      baseUrl: process.env.DOCUMENSO_BASE_URL ?? "https://app.documenso.com/api/v2/",
    },
    connectivity: {
      canConnect: false,
      latencyMs: 0,
    },
    account: {},
  };

  if (!process.env.DOCUMENSO_API_KEY) {
    result.connectivity.error = "DOCUMENSO_API_KEY not set";
    return result;
  }

  const client = new Documenso({
    apiKey: process.env.DOCUMENSO_API_KEY,
    serverURL: process.env.DOCUMENSO_BASE_URL,
  });

  // Test connectivity
  const startTime = Date.now();
  try {
    const docs = await client.documents.findV0({ perPage: 1 });
    result.connectivity.canConnect = true;
    result.connectivity.latencyMs = Date.now() - startTime;
    result.account.documentsCount = docs.totalPages ?? 0;
  } catch (error: any) {
    result.connectivity.error = `${error.statusCode}: ${error.message}`;
    result.connectivity.latencyMs = Date.now() - startTime;
  }

  // Test templates access
  try {
    const templates = await client.templates.findV0({ perPage: 1 });
    result.account.templatesCount = templates.totalPages ?? 0;
  } catch (error: any) {
    result.account.error = error.message;
  }

  return result;
}

// Run and output
runDiagnostic().then(result => {
  console.log("\n=== Documenso Diagnostic Report ===\n");
  console.log(JSON.stringify(result, null, 2));

  // Summary
  console.log("\n=== Summary ===");
  if (result.connectivity.canConnect) {
    console.log("Connection: OK");
    console.log(`Latency: ${result.connectivity.latencyMs}ms`);
  } else {
    console.log("Connection: FAILED");
    console.log(`Error: ${result.connectivity.error}`);
  }
});
```

### Script 2: Document Inspector

```typescript
// scripts/inspect-document.ts
import { Documenso } from "@documenso/sdk-typescript";

async function inspectDocument(documentId: string) {
  const client = new Documenso({
    apiKey: process.env.DOCUMENSO_API_KEY ?? "",
  });

  console.log(`\n=== Inspecting Document: ${documentId} ===\n`);

  try {
    const doc = await client.documents.getV0({ documentId });

    console.log("Document Details:");
    console.log(`  ID: ${doc.id}`);
    console.log(`  Title: ${doc.title}`);
    console.log(`  Status: ${doc.status}`);
    console.log(`  Created: ${doc.createdAt}`);
    console.log(`  Updated: ${doc.updatedAt}`);

    console.log("\nRecipients:");
    for (const recipient of doc.recipients ?? []) {
      console.log(`  - ${recipient.email}`);
      console.log(`    Name: ${recipient.name}`);
      console.log(`    Role: ${recipient.role}`);
      console.log(`    Status: ${recipient.signingStatus}`);
      console.log(`    Signing Order: ${recipient.signingOrder}`);
    }

    console.log("\nFields:");
    for (const field of doc.fields ?? []) {
      console.log(`  - Type: ${field.type}`);
      console.log(`    Page: ${field.page}`);
      console.log(`    Position: (${field.positionX}, ${field.positionY})`);
      console.log(`    Size: ${field.width}x${field.height}`);
      console.log(`    Recipient: ${field.recipientId}`);
    }

    return doc;
  } catch (error: any) {
    console.error(`Failed to inspect document: ${error.message}`);
    console.error(`Status: ${error.statusCode}`);
    throw error;
  }
}

// Usage: npx tsx scripts/inspect-document.ts doc_abc123
const documentId = process.argv[2];
if (documentId) {
  inspectDocument(documentId);
} else {
  console.log("Usage: npx tsx scripts/inspect-document.ts <documentId>");
}
```

### Script 3: API Request Logger

```typescript
// scripts/logged-client.ts
import { Documenso } from "@documenso/sdk-typescript";

// Create a logged wrapper
function createLoggedClient(): Documenso {
  const client = new Documenso({
    apiKey: process.env.DOCUMENSO_API_KEY ?? "",
    serverURL: process.env.DOCUMENSO_BASE_URL,
    debugLogger: {
      log: (...args) => {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] DEBUG:`, ...args);
      },
      warn: (...args) => {
        const timestamp = new Date().toISOString();
        console.warn(`[${timestamp}] WARN:`, ...args);
      },
      error: (...args) => {
        const timestamp = new Date().toISOString();
        console.error(`[${timestamp}] ERROR:`, ...args);
      },
    },
  });

  return client;
}

export { createLoggedClient };
```

### Script 4: Webhook Tester

```typescript
// scripts/test-webhook.ts
import express from "express";
import crypto from "crypto";

const app = express();

// Log all incoming requests
app.use((req, res, next) => {
  console.log(`\n=== Incoming Request ===`);
  console.log(`Time: ${new Date().toISOString()}`);
  console.log(`Method: ${req.method}`);
  console.log(`Path: ${req.path}`);
  console.log(`Headers:`, JSON.stringify(req.headers, null, 2));
  next();
});

// Parse raw body for signature verification
app.use(express.raw({ type: "application/json" }));

app.post("/webhook/documenso", (req, res) => {
  const secret = req.headers["x-documenso-secret"];
  const expectedSecret = process.env.DOCUMENSO_WEBHOOK_SECRET;

  console.log(`\n=== Webhook Received ===`);
  console.log(`Secret Header: ${secret ? "present" : "missing"}`);
  console.log(`Secret Valid: ${secret === expectedSecret}`);

  try {
    const payload = JSON.parse(req.body.toString());
    console.log(`Event: ${payload.event}`);
    console.log(`Document ID: ${payload.payload?.id}`);
    console.log(`Status: ${payload.payload?.status}`);
    console.log(`Full Payload:`, JSON.stringify(payload, null, 2));

    res.status(200).json({ received: true });
  } catch (error) {
    console.error(`Failed to parse webhook:`, error);
    res.status(400).json({ error: "Invalid JSON" });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Webhook test server running on port ${PORT}`);
  console.log(`Endpoint: POST http://localhost:${PORT}/webhook/documenso`);
  console.log(`\nUse ngrok to expose: ngrok http ${PORT}`);
});
```

### Script 5: Bulk Document Status Check

```typescript
// scripts/check-document-status.ts
import { Documenso } from "@documenso/sdk-typescript";

async function checkAllDocuments() {
  const client = new Documenso({
    apiKey: process.env.DOCUMENSO_API_KEY ?? "",
  });

  console.log("Fetching all documents...\n");

  const statusCounts: Record<string, number> = {};
  const pendingDocs: Array<{ id: string; title: string; age: string }> = [];

  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const result = await client.documents.findV0({
      page,
      perPage: 100,
    });

    for (const doc of result.documents ?? []) {
      const status = doc.status ?? "UNKNOWN";
      statusCounts[status] = (statusCounts[status] ?? 0) + 1;

      // Track pending documents
      if (status === "PENDING") {
        const createdAt = new Date(doc.createdAt!);
        const age = getAge(createdAt);
        pendingDocs.push({
          id: doc.id!,
          title: doc.title ?? "Untitled",
          age,
        });
      }
    }

    hasMore = (result.documents?.length ?? 0) === 100;
    page++;
  }

  console.log("=== Document Status Summary ===");
  for (const [status, count] of Object.entries(statusCounts)) {
    console.log(`${status}: ${count}`);
  }

  if (pendingDocs.length > 0) {
    console.log("\n=== Pending Documents ===");
    for (const doc of pendingDocs.slice(0, 10)) {
      console.log(`- ${doc.title} (${doc.id}) - ${doc.age} old`);
    }
    if (pendingDocs.length > 10) {
      console.log(`... and ${pendingDocs.length - 10} more`);
    }
  }
}

function getAge(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "< 1 day";
  if (diffDays === 1) return "1 day";
  if (diffDays < 7) return `${diffDays} days`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks`;
  return `${Math.floor(diffDays / 30)} months`;
}

checkAllDocuments().catch(console.error);
```

## curl Debug Commands

```bash
# Test API connectivity
curl -v -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  https://app.documenso.com/api/v2/documents

# Get specific document
curl -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  https://app.documenso.com/api/v2/documents/{documentId}

# List templates
curl -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  https://app.documenso.com/api/v2/templates

# Test webhook endpoint
curl -X POST http://localhost:3000/webhook/documenso \
  -H "Content-Type: application/json" \
  -H "X-Documenso-Secret: your-secret" \
  -d '{"event":"document.completed","payload":{"id":"test"}}'
```

## Environment Checklist

```bash
#!/bin/bash
# scripts/check-env.sh

echo "=== Documenso Environment Check ==="

# Check API key
if [ -z "$DOCUMENSO_API_KEY" ]; then
  echo "DOCUMENSO_API_KEY: NOT SET"
else
  echo "DOCUMENSO_API_KEY: SET (${DOCUMENSO_API_KEY:0:7}...)"
fi

# Check base URL
if [ -z "$DOCUMENSO_BASE_URL" ]; then
  echo "DOCUMENSO_BASE_URL: NOT SET (using default)"
else
  echo "DOCUMENSO_BASE_URL: $DOCUMENSO_BASE_URL"
fi

# Check webhook secret
if [ -z "$DOCUMENSO_WEBHOOK_SECRET" ]; then
  echo "DOCUMENSO_WEBHOOK_SECRET: NOT SET"
else
  echo "DOCUMENSO_WEBHOOK_SECRET: SET"
fi

# Test connectivity
echo ""
echo "Testing connectivity..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  ${DOCUMENSO_BASE_URL:-https://app.documenso.com/api/v2/}documents?perPage=1)

if [ "$response" = "200" ]; then
  echo "API Connection: OK"
elif [ "$response" = "401" ]; then
  echo "API Connection: UNAUTHORIZED (check API key)"
else
  echo "API Connection: FAILED (HTTP $response)"
fi
```

## Support Ticket Template

When creating a support ticket, include:

```markdown
## Documenso Support Request

### Environment
- SDK Version: @documenso/sdk-typescript@x.x.x
- Node.js Version: v20.x.x
- Environment: Production / Staging
- API Base URL: https://app.documenso.com/api/v2/

### Issue Description
[Describe what you expected vs what happened]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Error Details
```
[Paste error message and stack trace]
```

### Diagnostic Output
```json
[Paste output from documenso-diagnostic.ts]
```

### Document IDs (if applicable)
- Document ID: doc_xxx
- Template ID: tmpl_xxx

### Request/Response (if applicable)
```
[Paste relevant API request and response]
```
```
