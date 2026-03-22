---
name: abridge-sdk-patterns
description: |
  Apply production-ready patterns for Abridge clinical AI integration.
  Use when building reusable Abridge client wrappers, implementing HIPAA-compliant
  error handling, or establishing team coding standards for healthcare AI.
  Trigger: "abridge SDK patterns", "abridge best practices", "abridge code patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, patterns]
compatible-with: claude-code
---

# Abridge SDK Patterns

## Overview

Production-ready patterns for Abridge clinical AI integration. Since Abridge operates via partner APIs (not a public SDK), these patterns wrap the REST API with type-safe clients, HIPAA-compliant logging, and healthcare-specific error handling.

## Prerequisites

- Completed `abridge-install-auth` setup
- TypeScript project with strict mode enabled
- Understanding of HIPAA audit logging requirements

## Instructions

### Step 1: Type-Safe API Client Singleton

```typescript
// src/abridge/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

interface AbridgeConfig {
  baseUrl: string;
  clientSecret: string;
  orgId: string;
  timeoutMs?: number;
  maxRetries?: number;
}

class AbridgeApiClient {
  private static instance: AbridgeApiClient | null = null;
  private api: AxiosInstance;
  private config: AbridgeConfig;

  private constructor(config: AbridgeConfig) {
    this.config = config;
    this.api = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeoutMs || 30000,
      headers: {
        'Authorization': `Bearer ${config.clientSecret}`,
        'X-Org-Id': config.orgId,
        'Content-Type': 'application/json',
        'X-Request-Source': 'partner-integration',
      },
    });

    // Request/response interceptors for audit logging
    this.api.interceptors.request.use((req) => {
      req.headers['X-Correlation-Id'] = crypto.randomUUID();
      this.auditLog('request', req.method!, req.url!, req.headers['X-Correlation-Id']);
      return req;
    });

    this.api.interceptors.response.use(
      (res) => { this.auditLog('response', res.config.method!, res.config.url!, res.status); return res; },
      (err) => { this.auditLog('error', err.config?.method, err.config?.url, err.response?.status); throw err; }
    );
  }

  static getInstance(): AbridgeApiClient {
    if (!AbridgeApiClient.instance) {
      AbridgeApiClient.instance = new AbridgeApiClient({
        baseUrl: process.env.ABRIDGE_BASE_URL!,
        clientSecret: process.env.ABRIDGE_CLIENT_SECRET!,
        orgId: process.env.ABRIDGE_ORG_ID!,
      });
    }
    return AbridgeApiClient.instance;
  }

  // HIPAA-compliant audit log — never log PHI
  private auditLog(type: string, method: string, url: string, detail: any): void {
    const entry = {
      timestamp: new Date().toISOString(),
      type,
      method: method?.toUpperCase(),
      endpoint: url?.replace(/\/sessions\/[^/]+/, '/sessions/{id}'), // Redact IDs
      detail: typeof detail === 'number' ? `status:${detail}` : `id:${detail}`,
    };
    console.log(JSON.stringify(entry));
  }

  get http(): AxiosInstance { return this.api; }
}

export { AbridgeApiClient };
```

### Step 2: HIPAA-Safe Error Handler

```typescript
// src/abridge/errors.ts
class AbridgeApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly errorCode: string,
    public readonly correlationId: string,
    public readonly retryable: boolean,
  ) {
    super(message);
    this.name = 'AbridgeApiError';
  }

  // Sanitized error — safe for logging (no PHI)
  toSafeLog(): Record<string, unknown> {
    return {
      name: this.name,
      statusCode: this.statusCode,
      errorCode: this.errorCode,
      correlationId: this.correlationId,
      retryable: this.retryable,
      // Never include message in logs — may contain PHI
    };
  }
}

function parseAbridgeError(err: AxiosError): AbridgeApiError {
  const data = err.response?.data as any;
  const status = err.response?.status || 500;

  const retryableCodes = [429, 502, 503, 504];

  return new AbridgeApiError(
    data?.message || err.message,
    status,
    data?.error_code || 'UNKNOWN',
    err.config?.headers?.['X-Correlation-Id'] as string || 'none',
    retryableCodes.includes(status),
  );
}

export { AbridgeApiError, parseAbridgeError };
```

### Step 3: Retry with Exponential Backoff

```typescript
// src/abridge/retry.ts
import { AbridgeApiError, parseAbridgeError } from './errors';

async function withRetry<T>(
  operation: () => Promise<T>,
  options: { maxRetries?: number; baseDelayMs?: number; maxDelayMs?: number } = {}
): Promise<T> {
  const { maxRetries = 3, baseDelayMs = 1000, maxDelayMs = 30000 } = options;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      const apiErr = err instanceof AbridgeApiError ? err : parseAbridgeError(err as any);

      if (!apiErr.retryable || attempt === maxRetries) throw apiErr;

      // Respect Retry-After header if present
      const retryAfter = (err as any).response?.headers?.['retry-after'];
      const delay = retryAfter
        ? parseInt(retryAfter) * 1000
        : Math.min(baseDelayMs * Math.pow(2, attempt - 1), maxDelayMs);

      console.log(`Retry ${attempt}/${maxRetries} after ${delay}ms (${apiErr.errorCode})`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

export { withRetry };
```

### Step 4: Session Manager Pattern

```typescript
// src/abridge/session-manager.ts
import { AbridgeApiClient } from './client';
import { withRetry } from './retry';

interface SessionState {
  sessionId: string;
  status: 'initialized' | 'recording' | 'processing' | 'completed' | 'error';
  createdAt: Date;
  segmentCount: number;
}

class EncounterSessionManager {
  private sessions = new Map<string, SessionState>();
  private api = AbridgeApiClient.getInstance().http;

  async create(patientId: string, providerId: string, specialty: string): Promise<SessionState> {
    const { data } = await withRetry(() =>
      this.api.post('/encounters/sessions', {
        patient_id: patientId,
        provider_id: providerId,
        specialty,
        encounter_type: 'outpatient',
      })
    );

    const state: SessionState = {
      sessionId: data.session_id,
      status: 'initialized',
      createdAt: new Date(),
      segmentCount: 0,
    };
    this.sessions.set(data.session_id, state);
    return state;
  }

  async addTranscript(sessionId: string, speaker: string, text: string): Promise<void> {
    await this.api.post(`/encounters/sessions/${sessionId}/transcript`, { speaker, text });
    const state = this.sessions.get(sessionId)!;
    state.segmentCount++;
    state.status = 'recording';
  }

  async finalize(sessionId: string): Promise<any> {
    await this.api.post(`/encounters/sessions/${sessionId}/finalize`);
    this.sessions.get(sessionId)!.status = 'processing';

    for (let i = 0; i < 60; i++) {
      const { data } = await this.api.get(`/encounters/sessions/${sessionId}/note`);
      if (data.status === 'completed') {
        this.sessions.get(sessionId)!.status = 'completed';
        return data.note;
      }
      await new Promise(r => setTimeout(r, 1000));
    }
    throw new Error('Note generation timed out');
  }
}

export { EncounterSessionManager };
```

## Output

- Type-safe singleton client with audit logging
- HIPAA-safe error handling (no PHI in logs)
- Exponential backoff with Retry-After support
- Session lifecycle manager with state tracking

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton client | All API calls | Single source of config, consistent headers |
| Safe error logging | HIPAA compliance | Prevents PHI leakage in error logs |
| Retry with backoff | Transient failures | Handles 429/5xx gracefully |
| Session manager | Encounter lifecycle | Tracks state, prevents orphaned sessions |

## Resources

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [Abridge Platform](https://www.abridge.com/product)

## Next Steps

Apply these patterns in `abridge-core-workflow-a` for real encounter processing.
