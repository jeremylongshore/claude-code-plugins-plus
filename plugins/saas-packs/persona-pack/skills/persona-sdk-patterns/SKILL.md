---
name: persona-sdk-patterns
description: |
  Production Persona API client wrapper with retry, pagination, typed responses.
  Use when working with Persona identity verification.
  Trigger with phrases like "persona sdk-patterns", "persona sdk-patterns".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, verification]
compatible-with: claude-code, codex, openclaw
---

# persona sdk patterns | sed 's/\b\(.\)/\u\1/g'

## Overview
Singleton API client, typed verification results, pagination through inquiries, error classification.

## Prerequisites
- Completed `persona-install-auth` setup
- Valid Persona API key (sandbox or production)

## Instructions

### Step 1: Typed API Client Wrapper
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

interface PersonaConfig {
  apiKey: string;
  version?: string;
  baseURL?: string;
}

class PersonaClient {
  private http: AxiosInstance;

  constructor(config: PersonaConfig) {
    this.http = axios.create({
      baseURL: config.baseURL || 'https://withpersona.com/api/v1',
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Persona-Version': config.version || '2023-01-05',
        'Content-Type': 'application/json',
      },
    });
  }

  async createInquiry(templateId: string, referenceId: string, fields?: Record<string, any>) {
    const { data } = await this.http.post('/inquiries', {
      data: { attributes: { 'inquiry-template-id': templateId, 'reference-id': referenceId, fields } },
    });
    return data.data;
  }

  async getInquiry(inquiryId: string) {
    const { data } = await this.http.get(`/inquiries/${inquiryId}`);
    return data.data;
  }

  async listInquiries(params: { referenceId?: string; status?: string; pageSize?: number } = {}) {
    const { data } = await this.http.get('/inquiries', {
      params: {
        'filter[reference-id]': params.referenceId,
        'filter[status]': params.status,
        'page[size]': params.pageSize || 25,
      },
    });
    return data.data;
  }

  async getVerification(verificationId: string) {
    const { data } = await this.http.get(`/verifications/${verificationId}`);
    return data.data;
  }
}

// Singleton
let _client: PersonaClient | null = null;
export function getPersonaClient(): PersonaClient {
  if (!_client) {
    _client = new PersonaClient({ apiKey: process.env.PERSONA_API_KEY! });
  }
  return _client;
}
```

### Step 2: Error Classification
```typescript
function classifyPersonaError(error: AxiosError): { retryable: boolean; message: string } {
  const status = error.response?.status;
  if (status === 429) return { retryable: true, message: 'Rate limited' };
  if (status && status >= 500) return { retryable: true, message: 'Server error' };
  if (status === 401) return { retryable: false, message: 'Invalid API key' };
  if (status === 422) return { retryable: false, message: 'Invalid request' };
  return { retryable: false, message: error.message };
}
```

## Output
- Typed Persona API client with inquiry and verification methods
- Singleton pattern for reuse
- Error classification for retry decisions
- Paginated inquiry listing

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | All API calls | One client, consistent headers |
| Error classifier | Retry decisions | Only retry 429/5xx |
| Typed responses | Data access | Autocomplete, type safety |

## Resources
- [Persona API Reference](https://docs.withpersona.com/reference/introduction)
- [API Introduction](https://docs.withpersona.com/api-introduction)

## Next Steps
Apply in `persona-core-workflow-a` for real KYC flows.
