# Documenso SDK Patterns - Implementation Guide

## Instructions

### Step 1: Singleton Client Pattern

```typescript
// src/documenso/client.ts
import { Documenso } from "@documenso/sdk-typescript";

let instance: Documenso | null = null;

export interface DocumensoClientConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
}

export function getDocumensoClient(config?: DocumensoClientConfig): Documenso {
  if (!instance) {
    const apiKey = config?.apiKey ?? process.env.DOCUMENSO_API_KEY;

    if (!apiKey) {
      throw new Error(
        "DOCUMENSO_API_KEY environment variable is required"
      );
    }

    instance = new Documenso({
      apiKey,
      serverURL: config?.baseUrl ?? process.env.DOCUMENSO_BASE_URL,
      timeoutMs: config?.timeout ?? 30000,
    });
  }
  return instance;
}

// For testing - allows resetting the singleton
export function resetDocumensoClient(): void {
  instance = null;
}
```

### Step 2: Type-Safe Error Handling

```typescript
// src/documenso/errors.ts
import { SDKError } from "@documenso/sdk-typescript";

export class DocumensoError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = "DocumensoError";
  }
}

export function wrapDocumensoError(error: unknown): DocumensoError {
  if (error instanceof SDKError) {
    const retryable = error.statusCode >= 500 || error.statusCode === 429;
    return new DocumensoError(
      error.message,
      `DOCUMENSO_${error.statusCode}`,
      error.statusCode,
      retryable,
      error
    );
  }

  if (error instanceof Error) {
    return new DocumensoError(
      error.message,
      "DOCUMENSO_UNKNOWN",
      0,
      false,
      error
    );
  }

  return new DocumensoError(
    String(error),
    "DOCUMENSO_UNKNOWN",
    0,
    false
  );
}

// Safe wrapper for API calls
export async function safeDocumensoCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: DocumensoError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    const error = wrapDocumensoError(err);
    console.error({
      code: error.code,
      message: error.message,
      statusCode: error.statusCode,
      retryable: error.retryable,
    });
    return { data: null, error };
  }
}
```

### Step 3: Retry Logic with Exponential Backoff

```typescript
// src/documenso/retry.ts
interface RetryConfig {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  jitterMs?: number;
}

const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
  jitterMs: 500,
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, jitterMs } = {
    ...DEFAULT_RETRY_CONFIG,
    ...config,
  };

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const statusCode = error.statusCode ?? error.status ?? 0;

      // Only retry on 429 (rate limit) and 5xx (server errors)
      const isRetryable = statusCode === 429 || statusCode >= 500;

      if (attempt === maxRetries || !isRetryable) {
        throw error;
      }

      const exponentialDelay = baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * jitterMs;
      const delay = Math.min(exponentialDelay + jitter, maxDelayMs);

      console.log(
        `Attempt ${attempt + 1} failed. Retrying in ${delay.toFixed(0)}ms...`
      );
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 4: Document Service Facade

```typescript
// src/services/document-service.ts
import { getDocumensoClient } from "../documenso/client";
import { withRetry } from "../documenso/retry";
import { safeDocumensoCall, DocumensoError } from "../documenso/errors";

export interface CreateDocumentInput {
  title: string;
  file?: Blob;
  recipients: Array<{
    email: string;
    name: string;
    role?: "SIGNER" | "VIEWER" | "APPROVER";
  }>;
  fields?: Array<{
    recipientIndex: number;
    type: "SIGNATURE" | "INITIALS" | "NAME" | "EMAIL" | "DATE" | "TEXT";
    page: number;
    x: number;
    y: number;
    width?: number;
    height?: number;
  }>;
  sendImmediately?: boolean;
}

export interface DocumentResult {
  documentId: string;
  status: string;
  recipients: Array<{ id: string; email: string }>;
}

export class DocumentService {
  private client = getDocumensoClient();

  async createDocument(input: CreateDocumentInput): Promise<DocumentResult> {
    // Step 1: Create document
    const doc = await withRetry(() =>
      this.client.documents.createV0({
        title: input.title,
        file: input.file,
      })
    );

    const documentId = doc.documentId!;
    const recipientIds: Array<{ id: string; email: string }> = [];

    // Step 2: Add recipients
    for (const recipient of input.recipients) {
      const result = await withRetry(() =>
        this.client.documentsRecipients.createV0({
          documentId,
          email: recipient.email,
          name: recipient.name,
          role: recipient.role ?? "SIGNER",
        })
      );
      recipientIds.push({
        id: result.recipientId!,
        email: recipient.email,
      });
    }

    // Step 3: Add fields
    if (input.fields) {
      for (const field of input.fields) {
        const recipientId = recipientIds[field.recipientIndex]?.id;
        if (!recipientId) continue;

        await withRetry(() =>
          this.client.documentsFields.createV0({
            documentId,
            recipientId,
            type: field.type,
            page: field.page,
            positionX: field.x,
            positionY: field.y,
            width: field.width ?? 200,
            height: field.height ?? 60,
          })
        );
      }
    }

    // Step 4: Send if requested
    if (input.sendImmediately) {
      await withRetry(() =>
        this.client.documents.sendV0({ documentId })
      );
    }

    return {
      documentId,
      status: input.sendImmediately ? "SENT" : "DRAFT",
      recipients: recipientIds,
    };
  }

  async getDocument(documentId: string): Promise<DocumentResult | null> {
    const { data, error } = await safeDocumensoCall(() =>
      this.client.documents.getV0({ documentId })
    );

    if (error) {
      if (error.statusCode === 404) return null;
      throw error;
    }

    return {
      documentId: data!.id!,
      status: data!.status!,
      recipients:
        data!.recipients?.map((r) => ({
          id: r.id!,
          email: r.email!,
        })) ?? [],
    };
  }

  async deleteDocument(documentId: string): Promise<boolean> {
    const { error } = await safeDocumensoCall(() =>
      this.client.documents.deleteV0({ documentId })
    );
    return error === null;
  }
}

// Singleton instance
let documentService: DocumentService | null = null;

export function getDocumentService(): DocumentService {
  if (!documentService) {
    documentService = new DocumentService();
  }
  return documentService;
}
```

### Step 5: Response Validation with Zod

```typescript
// src/documenso/types.ts
import { z } from "zod";

export const DocumentStatusSchema = z.enum([
  "DRAFT",
  "PENDING",
  "COMPLETED",
  "REJECTED",
  "CANCELLED",
]);

export const RecipientSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  role: z.enum(["SIGNER", "VIEWER", "APPROVER", "CC"]),
  signingStatus: z.enum(["NOT_SIGNED", "SIGNED", "REJECTED"]).optional(),
});

export const DocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  status: DocumentStatusSchema,
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  recipients: z.array(RecipientSchema).optional(),
});

export type Document = z.infer<typeof DocumentSchema>;
export type DocumentStatus = z.infer<typeof DocumentStatusSchema>;

// Validate API response
export function validateDocument(data: unknown): Document {
  return DocumentSchema.parse(data);
}
```

### Python Patterns

```python
# src/documenso/client.py
import os
from typing import Optional
from functools import lru_cache
from documenso_sdk import Documenso

@lru_cache(maxsize=1)
def get_documenso_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Documenso:
    """Get singleton Documenso client."""
    key = api_key or os.environ.get("DOCUMENSO_API_KEY")
    if not key:
        raise ValueError("DOCUMENSO_API_KEY is required")

    return Documenso(
        api_key=key,
        server_url=base_url or os.environ.get("DOCUMENSO_BASE_URL"),
    )


# src/documenso/retry.py
import asyncio
import random
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")

async def with_retry(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> T:
    """Execute operation with exponential backoff retry."""
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as e:
            status = getattr(e, "status_code", 0)
            is_retryable = status == 429 or status >= 500

            if attempt == max_retries or not is_retryable:
                raise

            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.5), max_delay)
            print(f"Attempt {attempt + 1} failed. Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)

    raise RuntimeError("Unreachable")
```
