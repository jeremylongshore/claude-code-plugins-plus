# Documenso Local Dev Loop - Implementation Guide

# Documenso Local Dev Loop

## Overview
Configure a productive local development environment for Documenso integrations with fast iteration cycles.

## Prerequisites
- Completed `documenso-install-auth` setup
- Node.js 18+ or Python 3.10+
- Docker (optional, for self-hosted testing)
- Code editor with TypeScript support

## Instructions

### Step 1: Project Structure

```
my-documenso-project/
├── src/
│   ├── documenso/
│   │   ├── client.ts           # SDK client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   └── types.ts            # Custom TypeScript types
│   ├── services/
│   │   └── signing.ts          # Signing service layer
│   └── index.ts                # Main entry point
├── tests/
│   ├── unit/
│   │   └── signing.test.ts
│   └── integration/
│       └── documenso.test.ts
├── fixtures/
│   └── sample.pdf              # Test PDF files
├── .env.development
├── .env.test
└── package.json
```

### Step 2: Environment Configuration

**.env.development:**
```bash
# Use staging API for development
DOCUMENSO_API_KEY=your-dev-api-key
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2/

# Test recipient (use your own email for testing)
TEST_RECIPIENT_EMAIL=developer@yourcompany.com
TEST_RECIPIENT_NAME=Dev Tester
```

**.env.test:**
```bash
# Use staging with test-specific key
DOCUMENSO_API_KEY=your-test-api-key
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2/

# CI test recipient
TEST_RECIPIENT_EMAIL=ci-test@yourcompany.com
```

### Step 3: Client Wrapper with Dev Helpers

```typescript
// src/documenso/client.ts
import { Documenso } from "@documenso/sdk-typescript";

interface DocumensoConfig {
  apiKey: string;
  baseUrl?: string;
  debug?: boolean;
}

let clientInstance: Documenso | null = null;

export function getDocumensoClient(config?: DocumensoConfig): Documenso {
  if (!clientInstance) {
    const apiKey = config?.apiKey ?? process.env.DOCUMENSO_API_KEY;
    const baseUrl = config?.baseUrl ?? process.env.DOCUMENSO_BASE_URL;

    if (!apiKey) {
      throw new Error("DOCUMENSO_API_KEY is required");
    }

    clientInstance = new Documenso({
      apiKey,
      serverURL: baseUrl,
      debugLogger: config?.debug ? console : undefined,
    });
  }
  return clientInstance;
}

// Helper for testing - reset singleton
export function resetClient(): void {
  clientInstance = null;
}

// Development helper - create test document quickly
export async function createTestDocument(
  title = "Test Document"
): Promise<{ documentId: string }> {
  const client = getDocumensoClient();
  const doc = await client.documents.createV0({ title });
  return { documentId: doc.documentId! };
}
```

### Step 4: Development Scripts

**package.json:**
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:integration": "vitest run tests/integration/",
    "test:watch": "vitest watch",
    "documenso:verify": "tsx scripts/verify-connection.ts",
    "documenso:cleanup": "tsx scripts/cleanup-test-docs.ts"
  }
}
```

### Step 5: Quick Verification Script

```typescript
// scripts/verify-connection.ts
import { getDocumensoClient } from "../src/documenso/client";

async function verify() {
  console.log("Verifying Documenso connection...");
  console.log(`Base URL: ${process.env.DOCUMENSO_BASE_URL || "default"}`);

  try {
    const client = getDocumensoClient({ debug: true });
    const result = await client.documents.findV0({ perPage: 1 });

    console.log("Connection successful!");
    console.log(`Total documents in account: ${result.totalPages ?? 0} pages`);

    return true;
  } catch (error: any) {
    console.error("Connection failed!");
    console.error(`Error: ${error.message}`);

    if (error.statusCode === 401) {
      console.error("Hint: Check your DOCUMENSO_API_KEY");
    }

    return false;
  }
}

verify().then(success => process.exit(success ? 0 : 1));
```

### Step 6: Test Cleanup Script

```typescript
// scripts/cleanup-test-docs.ts
import { getDocumensoClient } from "../src/documenso/client";

async function cleanup() {
  const client = getDocumensoClient();
  const testPrefix = "Test Document";

  console.log("Finding test documents to clean up...");

  const docs = await client.documents.findV0({});
  const testDocs = docs.documents?.filter(d =>
    d.title?.startsWith(testPrefix)
  ) ?? [];

  console.log(`Found ${testDocs.length} test documents`);

  for (const doc of testDocs) {
    try {
      await client.documents.deleteV0({ documentId: doc.id! });
      console.log(`Deleted: ${doc.title} (${doc.id})`);
    } catch (error: any) {
      console.error(`Failed to delete ${doc.id}: ${error.message}`);
    }
  }

  console.log("Cleanup complete!");
}

cleanup().catch(console.error);
```

### Step 7: Integration Test Example

```typescript
// tests/integration/documenso.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { getDocumensoClient, resetClient } from "../../src/documenso/client";

describe("Documenso Integration", () => {
  let testDocumentId: string;

  beforeAll(() => {
    resetClient();
  });

  afterAll(async () => {
    // Clean up test document
    if (testDocumentId) {
      const client = getDocumensoClient();
      await client.documents.deleteV0({ documentId: testDocumentId });
    }
  });

  it("should create a document", async () => {
    const client = getDocumensoClient();

    const doc = await client.documents.createV0({
      title: "Test Document - Integration",
    });

    expect(doc.documentId).toBeDefined();
    testDocumentId = doc.documentId!;
  });

  it("should add a recipient", async () => {
    const client = getDocumensoClient();

    const recipient = await client.documentsRecipients.createV0({
      documentId: testDocumentId,
      email: process.env.TEST_RECIPIENT_EMAIL!,
      name: process.env.TEST_RECIPIENT_NAME ?? "Test User",
      role: "SIGNER",
    });

    expect(recipient.recipientId).toBeDefined();
  });

  it("should retrieve document details", async () => {
    const client = getDocumensoClient();

    const doc = await client.documents.getV0({
      documentId: testDocumentId,
    });

    expect(doc.title).toBe("Test Document - Integration");
    expect(doc.recipients?.length).toBeGreaterThan(0);
  });
});
```

## Self-Hosted Local Development

For testing against a local Documenso instance:

```bash
# Clone Documenso
git clone https://github.com/documenso/documenso.git
cd documenso

# Start with Docker Compose
docker-compose up -d

# Your local instance is now at http://localhost:3000
```

**.env.local (for self-hosted):**
```bash
DOCUMENSO_API_KEY=your-local-api-key
DOCUMENSO_BASE_URL=http://localhost:3000/api/v2/
```

## Output
- Configured development environment
- Verification script passing
- Integration tests running against staging
- Cleanup script for test documents

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Wrong base URL | Check DOCUMENSO_BASE_URL |
| 401 on staging | Wrong API key | Get staging-specific key |
| Tests failing | Stale test data | Run cleanup script |
| Rate limited | Too many requests | Add delays between tests |

## Resources
- [Documenso Staging Environment](https://stg-app.documenso.com)
- [Self-Hosting Guide](https://docs.documenso.com/developers/self-hosting)
- [Developer Quickstart](https://docs.documenso.com/developers/local-development/quickstart)

## Next Steps
Apply patterns in `documenso-sdk-patterns` for production-ready code.
