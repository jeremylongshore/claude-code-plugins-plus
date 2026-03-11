# Speak CI Integration - Implementation Guide

Detailed implementation reference for the speak-ci-integration skill.

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

