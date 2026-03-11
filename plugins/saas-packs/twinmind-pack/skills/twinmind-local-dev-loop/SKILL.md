---
name: twinmind-local-dev-loop
description: |
  Set up local development workflow with TwinMind API integration.
  Use when building applications that integrate TwinMind transcription,
  testing API calls locally, or developing meeting automation tools.
  Trigger with phrases like "twinmind dev setup", "twinmind local development",
  "twinmind API testing", "build with twinmind".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Local Dev Loop

## Overview
Configure a productive local development environment for TwinMind API integration.

## Prerequisites
- TwinMind Pro or Enterprise account (API access)
- Node.js 18+ or Python 3.10+
- API key from TwinMind dashboard
- Local development environment

## Instructions

### Step 1: Project Setup

```bash
set -euo pipefail
# Create project directory
mkdir twinmind-integration && cd twinmind-integration

# Initialize Node.js project
npm init -y

# Install dependencies
npm install dotenv axios zod typescript ts-node @types/node

# Initialize TypeScript
npx tsc --init
```

### Step 2: Configure Environment

```bash
# Create environment file
cat > .env << 'EOF'
TWINMIND_API_KEY=your-api-key-here
TWINMIND_API_URL=https://api.twinmind.com/v1
TWINMIND_WEBHOOK_SECRET=your-webhook-secret
NODE_ENV=development
EOF

# Add to .gitignore
echo ".env" >> .gitignore
echo "node_modules" >> .gitignore
```

### Step 3: Create TwinMind Client

```typescript
// src/twinmind/client.ts
import axios, { AxiosInstance } from 'axios';
import { z } from 'zod';

// Response schemas
const TranscriptSchema = z.object({
  id: z.string(),
  text: z.string(),
  duration_seconds: z.number(),
  language: z.string(),
  speakers: z.array(z.object({
    id: z.string(),
    name: z.string().optional(),
    segments: z.array(z.object({
      start: z.number(),
      end: z.number(),
      text: z.string(),
      confidence: z.number(),
    })),
  })),
  created_at: z.string(),
});

const SummarySchema = z.object({
  id: z.string(),
  transcript_id: z.string(),
  summary: z.string(),
  action_items: z.array(z.object({
    text: z.string(),
    assignee: z.string().optional(),
    due_date: z.string().optional(),
  })),
  key_points: z.array(z.string()),
});

export type Transcript = z.infer<typeof TranscriptSchema>;
export type Summary = z.infer<typeof SummarySchema>;

export class TwinMindClient {
  private client: AxiosInstance;

  constructor(apiKey: string, baseUrl?: string) {
    this.client = axios.create({
      baseURL: baseUrl || 'https://api.twinmind.com/v1',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      timeout: 30000,  # 30000: 30 seconds in ms
    });
  }

  async healthCheck(): Promise<boolean> {
    const response = await this.client.get('/health');
    return response.status === 200;  # HTTP 200 OK
  }

  async transcribe(audioUrl: string, options?: {
    language?: string;
    diarization?: boolean;
    model?: 'ear-3' | 'ear-2';
  }): Promise<Transcript> {
    const response = await this.client.post('/transcribe', {
      audio_url: audioUrl,
      language: options?.language || 'auto',
      diarization: options?.diarization ?? true,
      model: options?.model || 'ear-3',
    });
    return TranscriptSchema.parse(response.data);
  }

  async summarize(transcriptId: string): Promise<Summary> {
    const response = await this.client.post('/summarize', {
      transcript_id: transcriptId,
    });
    return SummarySchema.parse(response.data);
  }

  async search(query: string, options?: {
    limit?: number;
    date_from?: string;
    date_to?: string;
  }): Promise<Transcript[]> {
    const response = await this.client.get('/search', {
      params: {
        q: query,
        limit: options?.limit || 10,
        date_from: options?.date_from,
        date_to: options?.date_to,
      },
    });
    return z.array(TranscriptSchema).parse(response.data.results);
  }
}
```

### Step 4: Create Dev Runner Script

```typescript
// src/dev.ts
import 'dotenv/config';
import { TwinMindClient } from './twinmind/client';

async function main() {
  const client = new TwinMindClient(process.env.TWINMIND_API_KEY!);

  // Health check
  console.log('Checking TwinMind API health...');
  const healthy = await client.healthCheck();
  console.log(`API Status: ${healthy ? 'Healthy' : 'Unhealthy'}`);

  // Example: Transcribe audio file
  // const transcript = await client.transcribe('https://example.com/meeting.mp3');
  // console.log('Transcript:', transcript);

  // Example: Generate summary
  // const summary = await client.summarize(transcript.id);
  // console.log('Summary:', summary);

  // Example: Search memory vault
  // const results = await client.search('budget review');
  // console.log('Search results:', results);
}

main().catch(console.error);
```

### Step 5: Configure Dev Scripts

```json
// package.json scripts
{
  "scripts": {
    "dev": "ts-node src/dev.ts",
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src/**/*.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

### Step 6: Create Test Fixtures

```typescript
// tests/fixtures/mock-responses.ts
export const mockTranscript = {
  id: 'tr_test_123',
  text: 'Welcome to the meeting. Today we discuss the project timeline.',
  duration_seconds: 45,
  language: 'en',
  speakers: [
    {
      id: 'spk_1',
      name: 'Host',
      segments: [
        {
          start: 0,
          end: 5.2,
          text: 'Welcome to the meeting.',
          confidence: 0.97,
        },
        {
          start: 5.5,
          end: 12.1,
          text: 'Today we discuss the project timeline.',
          confidence: 0.95,
        },
      ],
    },
  ],
  created_at: '2025-01-15T10:00:00Z',  # 2025 year
};

export const mockSummary = {
  id: 'sum_test_456',
  transcript_id: 'tr_test_123',
  summary: 'Brief meeting to discuss project timeline and milestones.',
  action_items: [
    {
      text: 'Review timeline document',
      assignee: 'John',
      due_date: '2025-01-20',
    },
  ],
  key_points: [
    'Project kickoff confirmed',
    'Timeline review scheduled',
  ],
};
```

### Step 7: Run Development Loop

```bash
set -euo pipefail
# Start development
npm run dev

# Watch mode (requires nodemon)
npm install -D nodemon
npx nodemon --exec ts-node src/dev.ts

# Run with debug logging
DEBUG=twinmind:* npm run dev
```

## Output
- Project structure with TypeScript configuration
- TwinMind client with type-safe schemas
- Environment configuration
- Development scripts
- Test fixtures for offline development

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| API key missing | .env not loaded | Check dotenv import |
| Connection refused | Wrong API URL | Verify TWINMIND_API_URL |
| Rate limited | Too many requests | Add delay between calls |
| Schema validation failed | API response changed | Update Zod schemas |
| Timeout | Large audio file | Increase timeout value |

## Project Structure

```
twinmind-integration/
├── src/
│   ├── twinmind/
│   │   ├── client.ts       # API client
│   │   ├── types.ts        # TypeScript types
│   │   └── errors.ts       # Error classes
│   ├── services/
│   │   └── meeting.ts      # Business logic
│   └── dev.ts              # Development entry
├── tests/
│   ├── fixtures/
│   │   └── mock-responses.ts
│   └── twinmind.test.ts
├── .env                    # Environment (gitignored)
├── .env.example            # Template
├── package.json
└── tsconfig.json
```

## Resources
- [TwinMind API Documentation](https://twinmind.com/docs/api)
- [Ear-3 Model Specification](https://twinmind.com/ear-3)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `twinmind-sdk-patterns` for production-ready code.

## Examples

**Basic usage**: Apply twinmind local dev loop to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind local dev loop for production environments with multiple constraints and team-specific requirements.