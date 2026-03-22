---
name: documenso-sdk-patterns
description: |
  Apply production-ready Documenso SDK patterns for TypeScript and Python.
  Use when implementing Documenso integrations, refactoring SDK usage,
  or establishing team coding standards for Documenso.
  Trigger with phrases like "documenso SDK patterns", "documenso best practices",
  "documenso code patterns", "idiomatic documenso".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, python, typescript]

---
# Documenso SDK Patterns

## Overview

Production-ready patterns for the Documenso TypeScript SDK (`@documenso/sdk-typescript`) and Python SDK. Covers singleton clients, typed wrappers, error handling, retry logic, and testing patterns.

## Prerequisites

- Completed `documenso-install-auth` setup
- Familiarity with async/await and TypeScript generics
- Understanding of error handling best practices

## Instructions

### Pattern 1: Singleton Client with Configuration

```typescript
// src/documenso/client.ts
import { Documenso } from "@documenso/sdk-typescript";

interface DocumensoConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

let instance: Documenso | null = null;

export function getDocumensoClient(config?: DocumensoConfig): Documenso {
  if (!instance) {
    const apiKey = config?.apiKey ?? process.env.DOCUMENSO_API_KEY;
    if (!apiKey) throw new Error("DOCUMENSO_API_KEY is required");

    instance = new Documenso({
      apiKey,
      ...(config?.baseUrl && { serverURL: config.baseUrl }),
    });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

### Pattern 2: Typed Document Service

```typescript
// src/documenso/documents.ts
import { getDocumensoClient } from "./client";

export interface CreateDocumentInput {
  title: string;
  pdfPath: string;
  signers: Array<{
    email: string;
    name: string;
    fields: Array<{
      type: "SIGNATURE" | "INITIALS" | "NAME" | "EMAIL" | "DATE" | "TEXT";
      pageNumber: number;
      pageX: number;
      pageY: number;
      pageWidth?: number;
      pageHeight?: number;
    }>;
  }>;
}

export interface DocumentResult {
  documentId: number;
  recipientIds: number[];
  status: "DRAFT" | "PENDING" | "COMPLETED";
}

export async function createAndSendDocument(
  input: CreateDocumentInput
): Promise<DocumentResult> {
  const client = getDocumensoClient();
  const { readFileSync } = await import("fs");

  // Create document
  const doc = await client.documents.createV0({ title: input.title });

  // Upload PDF
  const pdfBuffer = readFileSync(input.pdfPath);
  await client.documents.setFileV0(doc.documentId, {
    file: new Blob([pdfBuffer], { type: "application/pdf" }),
  });

  // Add recipients and fields
  const recipientIds: number[] = [];
  for (const signer of input.signers) {
    const recipient = await client.documentsRecipients.createV0(doc.documentId, {
      email: signer.email,
      name: signer.name,
      role: "SIGNER",
    });
    recipientIds.push(recipient.recipientId);

    for (const field of signer.fields) {
      await client.documentsFields.createV0(doc.documentId, {
        recipientId: recipient.recipientId,
        type: field.type,
        pageNumber: field.pageNumber,
        pageX: field.pageX,
        pageY: field.pageY,
        pageWidth: field.pageWidth ?? 20,
        pageHeight: field.pageHeight ?? 5,
      });
    }
  }

  // Send
  await client.documents.sendV0(doc.documentId);

  return { documentId: doc.documentId, recipientIds, status: "PENDING" };
}
```

### Pattern 3: Error Handling Wrapper

```typescript
// src/documenso/errors.ts

export class DocumensoError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = "DocumensoError";
  }
}

export async function withErrorHandling<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  try {
    return await fn();
  } catch (err: any) {
    const status = err.statusCode ?? err.status;
    switch (status) {
      case 401:
        throw new DocumensoError(`${operation}: Invalid API key`, 401, false);
      case 403:
        throw new DocumensoError(
          `${operation}: Insufficient permissions — use team API key`,
          403,
          false
        );
      case 404:
        throw new DocumensoError(`${operation}: Resource not found`, 404, false);
      case 429:
        throw new DocumensoError(`${operation}: Rate limited`, 429, true);
      case 500:
      case 502:
      case 503:
        throw new DocumensoError(
          `${operation}: Documenso server error`,
          status,
          true
        );
      default:
        throw new DocumensoError(
          `${operation}: ${err.message ?? "Unknown error"}`,
          status,
          false
        );
    }
  }
}
```

### Pattern 4: Retry with Exponential Backoff

```typescript
// src/documenso/retry.ts
import { DocumensoError } from "./errors";

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULT_RETRY: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
};

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs } = { ...DEFAULT_RETRY, ...config };
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err as Error;
      if (err instanceof DocumensoError && !err.retryable) throw err;
      if (attempt === maxRetries) break;

      const delay = Math.min(baseDelayMs * 2 ** attempt, maxDelayMs);
      const jitter = delay * (0.5 + Math.random() * 0.5);
      await new Promise((r) => setTimeout(r, jitter));
    }
  }
  throw lastError;
}
```

### Pattern 5: Python Service Pattern

```python
# src/documenso/service.py
from documenso_sdk_python import Documenso
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class SignerInput:
    email: str
    name: str
    field_type: str = "SIGNATURE"
    page: int = 1
    x: float = 50.0
    y: float = 80.0

class DocumensoService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.client = Documenso(
            api_key=api_key or os.environ["DOCUMENSO_API_KEY"],
            **({"server_url": base_url} if base_url else {}),
        )

    def create_and_send(
        self, title: str, pdf_path: str, signers: list[SignerInput]
    ) -> dict:
        doc = self.client.documents.create_v0(title=title)

        with open(pdf_path, "rb") as f:
            self.client.documents.set_file_v0(doc.document_id, file=f.read())

        recipient_ids = []
        for signer in signers:
            recip = self.client.documents_recipients.create_v0(
                doc.document_id, email=signer.email, name=signer.name, role="SIGNER"
            )
            recipient_ids.append(recip.recipient_id)

            self.client.documents_fields.create_v0(
                doc.document_id,
                recipient_id=recip.recipient_id,
                type=signer.field_type,
                page_number=signer.page,
                page_x=signer.x,
                page_y=signer.y,
            )

        self.client.documents.send_v0(doc.document_id)
        return {"document_id": doc.document_id, "recipient_ids": recipient_ids}
```

### Pattern 6: Testing with Mocks

```typescript
// tests/mocks/documenso.ts
import { vi } from "vitest";

export function createMockClient() {
  return {
    documents: {
      createV0: vi.fn().mockResolvedValue({ documentId: 1 }),
      setFileV0: vi.fn().mockResolvedValue(undefined),
      findV0: vi.fn().mockResolvedValue({ documents: [] }),
      sendV0: vi.fn().mockResolvedValue(undefined),
      deleteV0: vi.fn().mockResolvedValue(undefined),
    },
    documentsRecipients: {
      createV0: vi.fn().mockResolvedValue({ recipientId: 100 }),
    },
    documentsFields: {
      createV0: vi.fn().mockResolvedValue({ fieldId: 200 }),
    },
  };
}
```

## Error Handling

| Pattern Issue | Cause | Solution |
|--------------|-------|----------|
| Client not initialized | Missing env var | Check `DOCUMENSO_API_KEY` is set |
| Singleton stale after key rotation | Cached client | Call `resetClient()` |
| Retry loop on 401 | Non-retryable treated as retryable | Check `retryable` flag |
| Type mismatch on field type | Wrong enum string | Use union type from SDK |

## Resources

- [TypeScript SDK Source](https://github.com/documenso/sdk-typescript)
- [Python SDK Source](https://github.com/documenso/sdk-python)
- [SDK Documents API](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documents/README.md)
- [Zod for Validation](https://zod.dev/)

## Next Steps

Apply patterns in `documenso-core-workflow-a` for document creation workflows.
