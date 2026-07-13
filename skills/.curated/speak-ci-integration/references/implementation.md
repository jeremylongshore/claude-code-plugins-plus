# Speak CI Integration -- Implementation Reference

## Overview

Configure automated testing for Speak language learning integrations using
GitHub Actions, including API connectivity checks, content validation,
and user progress tracking verification.

## Prerequisites

- Speak API key or embed credentials
- GitHub Actions workflow access
- Node.js 18+ or Python 3.9+

## GitHub Actions Workflow

```yaml
# .github/workflows/speak-integration-tests.yml
name: Speak Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run Speak integration tests
        env:
          SPEAK_API_KEY: ${{ secrets.SPEAK_API_KEY }}
          SPEAK_TENANT_ID: ${{ secrets.SPEAK_TENANT_ID }}
        run: npm run test:speak

      - name: Run connectivity check
        env:
          SPEAK_API_KEY: ${{ secrets.SPEAK_API_KEY }}
        run: python3 scripts/speak-health-check.py
```

## Python Health Check Script

```python
#!/usr/bin/env python3
"""Speak API connectivity and health check for CI."""

import os
import sys
import json
import urllib.request
import urllib.error

SPEAK_API_KEY = os.environ.get("SPEAK_API_KEY", "")
SPEAK_BASE_URL = os.environ.get("SPEAK_BASE_URL", "https://api.speak.com")


def speak_request(method: str, path: str, payload: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {SPEAK_API_KEY}",
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f"{SPEAK_BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def check_api_key() -> bool:
    if not SPEAK_API_KEY:
        print("[FAIL] SPEAK_API_KEY is not set")
        return False
    print(f"[PASS] SPEAK_API_KEY present ({len(SPEAK_API_KEY)} chars)")
    return True


def check_api_connectivity() -> bool:
    try:
        data = speak_request("GET", "/v1/health")
        status = data.get("status", "unknown")
        print(f"[PASS] API health: {status}")
        return status == "ok"
    except urllib.error.HTTPError as e:
        print(f"[FAIL] API returned HTTP {e.code}")
        return False
    except Exception as e:
        print(f"[FAIL] API unreachable: {e}")
        return False


def check_content_availability() -> bool:
    try:
        data = speak_request("GET", "/v1/lessons?limit=1")
        lessons = data.get("lessons", [])
        print(f"[PASS] Lessons accessible ({len(lessons)} returned)")
        return True
    except Exception as e:
        print(f"[FAIL] Could not fetch lessons: {e}")
        return False


def run_all_checks() -> bool:
    checks = [
        check_api_key,
        check_api_connectivity,
        check_content_availability,
    ]
    results = [check() for check in checks]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    return all(results)


if __name__ == "__main__":
    ok = run_all_checks()
    sys.exit(0 if ok else 1)
```

## Jest Integration Test Example

```typescript
// tests/speak.integration.test.ts
import { describe, it, expect, beforeAll } from 'vitest';

const BASE_URL = process.env.SPEAK_BASE_URL || 'https://api.speak.com';
const API_KEY = process.env.SPEAK_API_KEY!;

async function speakFetch(path: string) {
    const resp = await fetch(`${BASE_URL}${path}`, {
        headers: { Authorization: `Bearer ${API_KEY}` },
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${path}`);
    return resp.json();
}

describe('Speak API Integration', () => {
    beforeAll(() => {
        if (!API_KEY) throw new Error('SPEAK_API_KEY not set');
    });

    it('should return health status ok', async () => {
        const data = await speakFetch('/v1/health');
        expect(data.status).toBe('ok');
    });

    it('should list lessons', async () => {
        const data = await speakFetch('/v1/lessons?limit=5');
        expect(Array.isArray(data.lessons)).toBe(true);
        expect(data.lessons.length).toBeGreaterThan(0);
    });

    it('should retrieve lesson by ID', async () => {
        const { lessons } = await speakFetch('/v1/lessons?limit=1');
        const lessonId = lessons[0]?.id;
        expect(lessonId).toBeTruthy();
        const lesson = await speakFetch(`/v1/lessons/${lessonId}`);
        expect(lesson.id).toBe(lessonId);
    });
});
```

## Local Development Setup

```bash
# .env.local
SPEAK_API_KEY=sk-speak-your-key-here
SPEAK_TENANT_ID=your-tenant-id
SPEAK_BASE_URL=https://api.speak.com

# Run integration tests locally
SPEAK_API_KEY=$SPEAK_API_KEY npm run test:speak

# Run health check
python3 scripts/speak-health-check.py
```

## Resources

- [Speak API Docs](https://developers.speak.com)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest](https://vitest.dev/)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
