---
name: mistral-security-basics
description: |
  Apply Mistral AI security best practices for secrets, prompt injection, and access control.
  Use when securing API keys, defending against prompt injection,
  or auditing Mistral AI security configuration.
  Trigger with phrases like "mistral security", "mistral secrets",
  "secure mistral", "mistral prompt injection".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api, security, audit]

---
# Mistral Security Basics

## Overview
Security practices for Mistral AI integrations: API key management, prompt injection defense, output sanitization, content moderation with `mistral-moderation-latest`, request logging without secrets, and key rotation.

## Prerequisites
- Mistral API key provisioned
- Understanding of OWASP LLM Top 10 risks
- Secret management infrastructure

## Instructions

### Step 1: API Key Management

```python
import os

# NEVER: api_key = "sk-abc123"

# Development — env vars
api_key = os.environ.get("MISTRAL_API_KEY")
if not api_key:
    raise RuntimeError("MISTRAL_API_KEY not set")

# Production — secret manager
from google.cloud import secretmanager

def get_api_key() -> str:
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(
        name="projects/my-project/secrets/mistral-api-key/versions/latest"
    )
    return response.payload.data.decode("UTF-8")
```

### Step 2: Prompt Injection Defense

```typescript
function sanitizeUserInput(input: string): string {
  // Strip common injection patterns
  const patterns = [
    /ignore (?:previous|all|above) instructions/gi,
    /you are now/gi,
    /system prompt/gi,
    /\boverride\b/gi,
    /\bforget\b.*\binstructions\b/gi,
  ];

  let sanitized = input;
  for (const pattern of patterns) {
    sanitized = sanitized.replace(pattern, '[FILTERED]');
  }

  // Limit length to prevent context stuffing
  return sanitized.slice(0, 4000);
}

function buildSafeMessages(system: string, userInput: string) {
  return [
    { role: 'system', content: system },
    {
      role: 'user',
      content: `<user_query>\n${sanitizeUserInput(userInput)}\n</user_query>`,
    },
  ];
}
```

### Step 3: Content Moderation with Mistral API

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function moderateContent(text: string): Promise<{ safe: boolean; flags: string[] }> {
  const result = await client.classifiers.moderate({
    model: 'mistral-moderation-latest',
    inputs: [text],
  });

  const categories = result.results[0].categories;
  const flags = Object.entries(categories)
    .filter(([, flagged]) => flagged)
    .map(([category]) => category);

  return { safe: flags.length === 0, flags };
}

// Gate user input before processing
async function safeChatFlow(userInput: string) {
  const inputCheck = await moderateContent(userInput);
  if (!inputCheck.safe) {
    throw new Error(`Input flagged: ${inputCheck.flags.join(', ')}`);
  }

  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [{ role: 'user', content: userInput }],
    safePrompt: true, // Built-in safety system prompt
  });

  const output = response.choices?.[0]?.message?.content ?? '';
  const outputCheck = await moderateContent(output);
  if (!outputCheck.safe) {
    return 'I cannot provide that response.';
  }

  return output;
}
```

### Step 4: Output Sanitization

```typescript
function sanitizeOutput(response: string): string {
  let cleaned = response;

  // Remove leaked system prompts
  cleaned = cleaned.replace(/(?:system prompt|instructions):?\s*.*/gi, '[REDACTED]');

  // Remove script tags (XSS prevention)
  cleaned = cleaned.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');

  // Remove PII patterns
  cleaned = cleaned.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]');
  cleaned = cleaned.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b/gi, '[EMAIL]');

  return cleaned;
}
```

### Step 5: Request Logging Without Secrets

```typescript
function logRequest(model: string, messages: any[], response: any): void {
  // Log metadata ONLY — never log content (may contain PII)
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    model,
    messageCount: messages.length,
    inputChars: messages.reduce((sum, m) => sum + (m.content?.length ?? 0), 0),
    outputChars: response.choices?.[0]?.message?.content?.length ?? 0,
    usage: {
      promptTokens: response.usage?.promptTokens,
      completionTokens: response.usage?.completionTokens,
    },
    // NEVER log: API keys, message content, user identifiers
  }));
}
```

### Step 6: API Key Rotation

```typescript
class KeyRotator {
  private keys: string[];
  private current = 0;
  private lastRotated = Date.now();
  private readonly rotationIntervalMs = 3_600_000; // 1 hour

  constructor(keys: string[]) {
    if (keys.length === 0) throw new Error('At least one API key required');
    this.keys = keys;
  }

  getKey(): string {
    if (Date.now() - this.lastRotated > this.rotationIntervalMs) {
      this.rotate();
    }
    return this.keys[this.current];
  }

  reportAuthFailure(): void {
    console.error(`Key ${this.current} failed auth, rotating`);
    this.rotate();
  }

  private rotate(): void {
    this.current = (this.current + 1) % this.keys.length;
    this.lastRotated = Date.now();
  }
}
```

## Security Audit Checklist

```python
def audit_mistral_security():
    checks = {
        "api_key_from_env": bool(os.environ.get("MISTRAL_API_KEY")),
        "gitignore_has_env": ".env" in open(".gitignore").read() if os.path.exists(".gitignore") else False,
        "no_hardcoded_keys": True,  # scan src/ for patterns
        "moderation_enabled": True,  # verify in code
        "output_sanitization": True,  # verify in code
        "audit_logging": True,  # verify in code
    }
    passed = all(checks.values())
    return {"passed": passed, "checks": checks}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Key in logs | Logging full request | Log metadata only |
| Prompt injection | Unsanitized user input | Filter + XML-wrap user content |
| PII in responses | Model generating PII | Sanitize output + use moderation |
| Key compromise | Hardcoded or leaked | Use secret manager, rotate immediately |
| XSS via output | Model generating HTML/JS | Strip script tags before rendering |

## Resources
- [Mistral Guardrails](https://docs.mistral.ai/capabilities/guardrailing/)
- [Mistral Moderation API](https://docs.mistral.ai/api/endpoint/moderations/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

## Output
- API key management via secret managers
- Prompt injection defense layer
- Content moderation with `mistral-moderation-latest`
- Output sanitization pipeline
- Secure audit logging
- Key rotation automation
