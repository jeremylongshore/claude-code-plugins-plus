---
name: assemblyai-reference-architecture
description: |
  Implement AssemblyAI reference architecture with best-practice project layout.
  Use when designing new AssemblyAI transcription services, reviewing project structure,
  or building production-grade speech-to-text applications.
  Trigger with phrases like "assemblyai architecture", "assemblyai best practices",
  "assemblyai project structure", "how to organize assemblyai", "assemblyai design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, architecture]
compatible-with: claude-code
---

# AssemblyAI Reference Architecture

## Overview
Production-ready architecture for AssemblyAI-powered transcription services with layered design, webhook-driven processing, and LeMUR analysis pipelines.

## Prerequisites
- Understanding of layered architecture
- `assemblyai` npm package
- TypeScript project setup
- Database for transcript storage

## Project Structure

```
my-transcription-service/
├── src/
│   ├── assemblyai/
│   │   ├── client.ts              # Singleton client
│   │   ├── transcription.ts       # Transcription service
│   │   ├── streaming.ts           # Streaming service
│   │   ├── lemur.ts               # LeMUR analysis service
│   │   └── types.ts               # Domain types
│   ├── api/
│   │   ├── transcribe.ts          # POST /api/transcribe
│   │   ├── transcripts.ts         # GET /api/transcripts/:id
│   │   ├── streaming-token.ts     # GET /api/streaming-token
│   │   └── webhooks/
│   │       └── assemblyai.ts      # POST /webhooks/assemblyai
│   ├── services/
│   │   ├── audio-processor.ts     # Audio validation & preprocessing
│   │   └── transcript-store.ts    # Database storage
│   ├── jobs/
│   │   └── batch-transcriber.ts   # Background batch processing
│   └── config.ts
├── tests/
│   ├── unit/
│   │   ├── transcription.test.ts
│   │   └── lemur.test.ts
│   └── integration/
│       └── assemblyai.test.ts
└── package.json
```

## Architecture Layers

```
┌──────────────────────────────────────────────────────┐
│                    API Layer                          │
│  Transcribe endpoint, Webhook handler, Stream token  │
├──────────────────────────────────────────────────────┤
│                  Service Layer                        │
│  TranscriptionService, LeMURService, AudioProcessor  │
├──────────────────────────────────────────────────────┤
│                AssemblyAI SDK Layer                   │
│  client.transcripts, client.streaming, client.lemur  │
├──────────────────────────────────────────────────────┤
│               Infrastructure Layer                    │
│  Database, Redis Cache, Job Queue, Monitoring        │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Client Layer

```typescript
// src/assemblyai/client.ts
import { AssemblyAI } from 'assemblyai';

let client: AssemblyAI | null = null;

export function getClient(): AssemblyAI {
  if (!client) {
    client = new AssemblyAI({
      apiKey: process.env.ASSEMBLYAI_API_KEY!,
    });
  }
  return client;
}
```

### Step 2: Transcription Service

```typescript
// src/assemblyai/transcription.ts
import { type Transcript, type TranscriptParams } from 'assemblyai';
import { getClient } from './client';

export interface TranscriptionOptions {
  speakerLabels?: boolean;
  sentimentAnalysis?: boolean;
  entityDetection?: boolean;
  piiRedaction?: boolean;
  webhookUrl?: string;
  model?: 'best' | 'nano';
}

export class TranscriptionService {
  private client = getClient();

  // Async transcription with webhook (production pattern)
  async submitForTranscription(
    audio: string,
    options: TranscriptionOptions = {}
  ): Promise<{ transcriptId: string; status: string }> {
    const params: TranscriptParams = {
      audio,
      speech_model: options.model ?? 'best',
      speaker_labels: options.speakerLabels ?? false,
      sentiment_analysis: options.sentimentAnalysis ?? false,
      entity_detection: options.entityDetection ?? false,
      redact_pii: options.piiRedaction ?? false,
    };

    if (options.webhookUrl) {
      params.webhook_url = options.webhookUrl;
      params.webhook_auth_header_name = 'X-Webhook-Secret';
      params.webhook_auth_header_value = process.env.ASSEMBLYAI_WEBHOOK_SECRET!;
    }

    const transcript = options.webhookUrl
      ? await this.client.transcripts.submit(params)
      : await this.client.transcripts.transcribe(params);

    return { transcriptId: transcript.id, status: transcript.status };
  }

  // Get completed transcript with all data
  async getTranscript(id: string): Promise<Transcript> {
    return this.client.transcripts.get(id);
  }

  // Delete for GDPR compliance
  async deleteTranscript(id: string): Promise<void> {
    await this.client.transcripts.delete(id);
  }

  // Batch processing
  async batchTranscribe(audioUrls: string[], options: TranscriptionOptions = {}) {
    const PQueue = (await import('p-queue')).default;
    const queue = new PQueue({ concurrency: 5 });

    return Promise.all(
      audioUrls.map(url =>
        queue.add(() => this.submitForTranscription(url, options))
      )
    );
  }
}
```

### Step 3: LeMUR Analysis Service

```typescript
// src/assemblyai/lemur.ts
import { getClient } from './client';

export class LeMURService {
  private client = getClient();

  async summarize(transcriptIds: string[], context?: string) {
    const { response } = await this.client.lemur.summary({
      transcript_ids: transcriptIds,
      context,
      answer_format: 'bullet points',
    });
    return response;
  }

  async extractActionItems(transcriptIds: string[]) {
    const { response } = await this.client.lemur.actionItems({
      transcript_ids: transcriptIds,
    });
    return response;
  }

  async askQuestions(transcriptIds: string[], questions: string[]) {
    const { response } = await this.client.lemur.questionAnswer({
      transcript_ids: transcriptIds,
      questions: questions.map(q => ({ question: q })),
    });
    return response;
  }

  async customTask(transcriptIds: string[], prompt: string) {
    const { response } = await this.client.lemur.task({
      transcript_ids: transcriptIds,
      prompt,
    });
    return response;
  }
}
```

### Step 4: Streaming Service

```typescript
// src/assemblyai/streaming.ts
import { getClient } from './client';

export class StreamingService {
  private client = getClient();

  async createToken(expiresInSeconds = 300) {
    return this.client.streaming.createTemporaryToken({
      expires_in_seconds: expiresInSeconds,
    });
  }

  createTranscriber(options: {
    sampleRate?: number;
    model?: string;
    wordBoost?: string[];
  } = {}) {
    return this.client.streaming.createService({
      speech_model: (options.model as any) ?? 'nova-3',
      sample_rate: options.sampleRate ?? 16000,
      word_boost: options.wordBoost,
    });
  }
}
```

### Step 5: Webhook Handler

```typescript
// src/api/webhooks/assemblyai.ts
import { TranscriptionService } from '../../assemblyai/transcription';
import { LeMURService } from '../../assemblyai/lemur';

const transcription = new TranscriptionService();
const lemur = new LeMURService();

export async function handleWebhook(req: Request): Promise<Response> {
  // Verify auth
  const secret = req.headers.get('x-webhook-secret');
  if (secret !== process.env.ASSEMBLYAI_WEBHOOK_SECRET) {
    return new Response('Unauthorized', { status: 401 });
  }

  const { transcript_id, status } = await req.json();

  // Respond immediately
  const response = new Response(JSON.stringify({ received: true }), { status: 200 });

  // Process asynchronously
  if (status === 'completed') {
    const transcript = await transcription.getTranscript(transcript_id);

    // Auto-analyze with LeMUR
    const summary = await lemur.summarize([transcript_id]);
    const actionItems = await lemur.extractActionItems([transcript_id]);

    // Store results in your database
    await storeResults(transcript, summary, actionItems);
  }

  return response;
}
```

### Step 6: Data Flow

```
User uploads audio
        │
        ▼
┌─────────────────┐
│  API: /transcribe│
│  submit() + URL  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AssemblyAI API  │  ← Processes audio (seconds to minutes)
│  (async queue)   │
└────────┬────────┘
         │ webhook POST
         ▼
┌─────────────────┐
│ Webhook Handler  │
│ get() transcript │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Store  │ │ LeMUR  │  ← Auto-summarize, extract action items
│ in DB  │ │ Analyze│
└────────┘ └────────┘
```

## Configuration

```typescript
// src/config.ts
export const config = {
  assemblyai: {
    model: (process.env.ASSEMBLYAI_MODEL ?? 'best') as 'best' | 'nano',
    webhookUrl: process.env.ASSEMBLYAI_WEBHOOK_URL,
    webhookSecret: process.env.ASSEMBLYAI_WEBHOOK_SECRET,
    defaultFeatures: {
      speakerLabels: true,
      sentimentAnalysis: false,
      entityDetection: false,
      piiRedaction: process.env.NODE_ENV === 'production',
    },
    streaming: {
      tokenExpiry: 300,
      sampleRate: 16000,
      model: 'nova-3',
    },
    batch: {
      concurrency: 5,
      retries: 3,
    },
  },
};
```

## Output
- Layered architecture with clear separation of concerns
- Transcription service with webhook-based async processing
- LeMUR analysis pipeline auto-triggered on completion
- Streaming service with temporary token management
- Batch processing with concurrency control

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layer boundaries | Services depend on SDK layer, never on API layer |
| Webhook missed | Processing took too long | Return 200 immediately, process async |
| LeMUR timeout | Too many transcripts | Batch transcript_ids in groups of 10 |
| Streaming disconnect | Network interruption | Implement reconnection in StreamingService |

## Resources
- [AssemblyAI Documentation](https://www.assemblyai.com/docs)
- [AssemblyAI Node SDK](https://github.com/AssemblyAI/assemblyai-node-sdk)
- [AssemblyAI API Reference](https://www.assemblyai.com/docs/api-reference/overview)
- [AssemblyAI Blog — Best Practices](https://www.assemblyai.com/blog)

## Next Steps
For getting started quickly, see `assemblyai-hello-world`.
