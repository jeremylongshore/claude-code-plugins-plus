---
name: speak-ci-integration
description: |
  Configure Speak CI/CD integration with GitHub Actions and automated testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Speak language learning tests into your build process.
  Trigger with phrases like "speak CI", "speak GitHub Actions",
  "speak automated tests", "CI speak".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Speak CI Integration

## Overview
Integrate Speak language learning API validation into CI/CD pipelines. Covers pronunciation analysis endpoint testing, lesson content validation, API response format verification, and regression testing for language assessment accuracy.

## Prerequisites
- Speak API key stored as GitHub secret
- GitHub Actions configured
- Test framework (Vitest or Jest)
- Audio test fixtures for pronunciation tests

## Instructions

### Step 1: API Validation Workflow
```yaml
# .github/workflows/speak-tests.yml
name: Speak API Tests

on:
  pull_request:
    paths:
      - 'src/speak/**'
      - 'src/lessons/**'
      - 'tests/speak/**'

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci

      - name: Run Speak API tests
        env:
          SPEAK_API_KEY: ${{ secrets.SPEAK_API_KEY }}
        run: npm test -- tests/speak/ --reporter=verbose

      - name: Validate lesson content
        run: node scripts/validate-lessons.js
```

### Step 2: API Response Regression Tests
```typescript
// tests/speak/api-regression.test.ts
import { describe, it, expect } from 'vitest';

const SPEAK_API = 'https://api.speak.com/v1';
const headers = {
  'Authorization': `Bearer ${process.env.SPEAK_API_KEY}`,
  'Content-Type': 'application/json',
};

describe('Speak API Regression', () => {
  it('pronunciation analysis returns valid scores', async () => {
    const response = await fetch(`${SPEAK_API}/pronunciation/analyze`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        text: 'Hello, how are you?',
        language: 'en',
        audio_url: 'https://test-fixtures.example.com/hello-en.wav',
      }),
    });

    expect(response.ok).toBe(true);
    const data = await response.json();

    expect(data).toHaveProperty('overall_score');
    expect(data.overall_score).toBeGreaterThanOrEqual(0);
    expect(data.overall_score).toBeLessThanOrEqual(100);
    expect(data).toHaveProperty('word_scores');
  });

  it('lesson generation returns valid structure', async () => {
    const response = await fetch(`${SPEAK_API}/lessons/generate`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        topic: 'ordering food at a restaurant',
        language: 'en',
        level: 'beginner',
      }),
    });

    expect(response.ok).toBe(true);
    const data = await response.json();

    expect(data).toHaveProperty('title');
    expect(data).toHaveProperty('phrases');
    expect(data.phrases.length).toBeGreaterThan(0);
    expect(data.phrases[0]).toHaveProperty('text');
    expect(data.phrases[0]).toHaveProperty('translation');
  });

  it('supported languages endpoint returns valid list', async () => {
    const response = await fetch(`${SPEAK_API}/languages`, { headers });

    expect(response.ok).toBe(true);
    const data = await response.json();

    expect(data.languages).toBeInstanceOf(Array);
    expect(data.languages.length).toBeGreaterThan(0);
    expect(data.languages).toContain('en');
  });
});
```

### Step 3: Lesson Content Validation Script
```typescript
// scripts/validate-lessons.ts
import { readdirSync, readFileSync } from 'fs';
import { join } from 'path';
import { z } from 'zod';

const LessonSchema = z.object({
  id: z.string(),
  title: z.string().min(3),
  language: z.string().length(2),
  level: z.enum(['beginner', 'intermediate', 'advanced']),
  phrases: z.array(z.object({
    text: z.string().min(1),
    translation: z.string().min(1),
    pronunciation_guide: z.string().optional(),
  })).min(1),
});

const lessonsDir = join(process.cwd(), 'src/lessons');
let errors = 0;

for (const file of readdirSync(lessonsDir)) {
  if (!file.endsWith('.json')) continue;

  const content = JSON.parse(readFileSync(join(lessonsDir, file), 'utf-8'));
  const result = LessonSchema.safeParse(content);

  if (!result.success) {
    console.error(`INVALID: ${file}`);
    console.error(result.error.flatten().fieldErrors);
    errors++;
  } else {
    console.log(`VALID: ${file} (${result.data.phrases.length} phrases)`);
  }
}

if (errors > 0) {
  console.error(`\n${errors} lesson files have validation errors`);
  process.exit(1);
}
```

### Step 4: Audio Test Fixture Management
```yaml
# .github/workflows/speak-fixtures.yml
name: Validate Test Fixtures

on:
  pull_request:
    paths:
      - 'tests/fixtures/audio/**'

jobs:
  validate-fixtures:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate audio fixtures
        run: |
          for file in tests/fixtures/audio/*.wav; do
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
            if [ "$size" -lt 1000 ]; then
              echo "WARNING: $file is too small ($size bytes)"
            fi
            if [ "$size" -gt 5000000 ]; then
              echo "ERROR: $file exceeds 5MB limit ($size bytes)"
              exit 1
            fi
            echo "OK: $file ($size bytes)"
          done
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key invalid | Secret not set | Add `SPEAK_API_KEY` to repo secrets |
| Audio fixture too large | Uncompressed WAV | Compress to 16-bit mono |
| Lesson validation fails | Missing required field | Check schema and fix JSON files |
| Flaky pronunciation test | Audio quality varies | Use consistent test recordings |

## Examples

### Minimal Smoke Test
```yaml
- name: Speak API health check
  env:
    SPEAK_API_KEY: ${{ secrets.SPEAK_API_KEY }}
  run: |
    curl -s -H "Authorization: Bearer $SPEAK_API_KEY" \
      https://api.speak.com/v1/languages | jq '.languages | length'
```

## Resources
- [Speak API Documentation](https://docs.speak.com)
- [Speak Developer Guide](https://speak.com/developers)
