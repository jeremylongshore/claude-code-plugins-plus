# Examples — Genkit Production Expert

## Example 1: Question-Answering Flow with Zod Schemas

A simple Genkit flow with typed input/output, temperature tuning, and token monitoring.

### Setup

```bash
npm install genkit @genkit-ai/googleai zod
npm install -D typescript tsx
```

### Flow Implementation

```typescript
// src/qa-flow.ts
import { genkit, z } from "genkit";
import { googleAI, gemini25Flash } from "@genkit-ai/googleai";

const ai = genkit({
  plugins: [googleAI()],
});

// Strict input/output schemas
const QuestionInput = z.object({
  question: z.string().min(3).describe("The user question"),
  context: z.string().optional().describe("Optional context to ground the answer"),
  maxWords: z.number().min(10).max(500).default(150),
});

const AnswerOutput = z.object({
  answer: z.string(),
  confidence: z.enum(["high", "medium", "low"]),
  tokenUsage: z.object({
    input: z.number(),
    output: z.number(),
  }),
});

export const qaFlow = ai.defineFlow(
  {
    name: "question-answer",
    inputSchema: QuestionInput,
    outputSchema: AnswerOutput,
  },
  async (input) => {
    const contextBlock = input.context
      ? `\n\nContext:\n${input.context}`
      : "";

    const { text, usage } = await ai.generate({
      model: gemini25Flash,
      prompt: `Answer the following question in at most ${input.maxWords} words.
If you are unsure, say so and rate your confidence as "low".${contextBlock}

Question: ${input.question}

Respond in JSON format:
{"answer": "...", "confidence": "high|medium|low"}`,
      config: {
        temperature: 0.3,
        maxOutputTokens: 1024,
      },
    });

    const parsed = JSON.parse(text);

    return {
      answer: parsed.answer,
      confidence: parsed.confidence,
      tokenUsage: {
        input: usage?.inputTokens ?? 0,
        output: usage?.outputTokens ?? 0,
      },
    };
  }
);

// Start local server for testing with Genkit Developer UI
ai.startFlowServer({ flows: [qaFlow] });
```

### Local Testing

```bash
# Start the Genkit dev server
npx genkit start -- tsx src/qa-flow.ts

# Test with curl
curl -X POST http://localhost:3400/question-answer \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Firebase Genkit?", "maxWords": 100}'
```

### Expected Output

```json
{
  "answer": "Firebase Genkit is an open-source framework for building AI-powered applications. It provides a unified API for defining flows (multi-step AI pipelines), tools (external capabilities), and retrievers (document search). Genkit supports multiple model providers including Google Gemini, has built-in observability via OpenTelemetry, and deploys to Firebase Functions or Cloud Run. It is available for Node.js, Python, and Go.",
  "confidence": "high",
  "tokenUsage": {
    "input": 82,
    "output": 94
  }
}
```

### Deploy to Firebase Functions

```typescript
// src/index.ts — Firebase Functions entry point
import { onFlow } from "@genkit-ai/firebase/functions";
import { qaFlow } from "./qa-flow";

export const questionAnswer = onFlow(
  {
    name: "question-answer",
    httpsOptions: {
      cors: true,
      memory: "512MiB",
      minInstances: 1,
    },
  },
  qaFlow
);
```

```bash
firebase deploy --only functions
# Function URL: https://us-central1-my-project.cloudfunctions.net/questionAnswer
```

---

## Example 2: RAG Flow with Firestore Vector Search

Retrieve documents, inject as context, and generate grounded answers with source citations.

```typescript
// src/rag-flow.ts
import { genkit, z } from "genkit";
import { googleAI, gemini25Flash, textEmbedding004 } from "@genkit-ai/googleai";
import { Firestore, FieldValue } from "firebase-admin/firestore";
import { initializeApp } from "firebase-admin/app";

initializeApp();
const db = new Firestore();

const ai = genkit({
  plugins: [googleAI()],
});

// Retriever: query Firestore vector index
const docRetriever = ai.defineRetriever(
  { name: "firestore-knowledge-base" },
  async (query: string, options?: { k?: number }) => {
    const k = options?.k ?? 5;

    // Generate query embedding
    const { embedding } = await ai.embed({
      embedder: textEmbedding004,
      content: query,
    });

    // Vector similarity search in Firestore
    const snapshot = await db
      .collection("knowledge_base")
      .findNearest("embedding", embedding, {
        limit: k,
        distanceMeasure: "COSINE",
      })
      .get();

    return snapshot.docs.map((doc) => ({
      content: doc.data().text as string,
      metadata: {
        id: doc.id,
        title: doc.data().title as string,
        category: doc.data().category as string,
        lastUpdated: doc.data().updatedAt?.toDate()?.toISOString() ?? "",
      },
    }));
  }
);

// Indexer: add documents to the vector store
const docIndexer = ai.defineIndexer(
  { name: "firestore-indexer" },
  async (docs) => {
    const batch = db.batch();
    for (const doc of docs) {
      const { embedding } = await ai.embed({
        embedder: textEmbedding004,
        content: doc.content,
      });
      const ref = db.collection("knowledge_base").doc();
      batch.set(ref, {
        text: doc.content,
        title: doc.metadata?.title ?? "Untitled",
        category: doc.metadata?.category ?? "general",
        embedding,
        updatedAt: FieldValue.serverTimestamp(),
      });
    }
    await batch.commit();
  }
);

// RAG flow
const RagInput = z.object({
  question: z.string().min(1),
  topK: z.number().min(1).max(20).default(5),
});

const RagOutput = z.object({
  answer: z.string(),
  sources: z.array(z.object({
    title: z.string(),
    category: z.string(),
    snippet: z.string(),
  })),
  cached: z.boolean(),
});

// Simple in-memory cache for repeated queries
const queryCache = new Map<string, { result: z.infer<typeof RagOutput>; expiry: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

export const ragFlow = ai.defineFlow(
  {
    name: "rag-search",
    inputSchema: RagInput,
    outputSchema: RagOutput,
  },
  async (input) => {
    // Check cache
    const cacheKey = `${input.question}:${input.topK}`;
    const cached = queryCache.get(cacheKey);
    if (cached && cached.expiry > Date.now()) {
      return { ...cached.result, cached: true };
    }

    // Retrieve relevant documents
    const docs = await ai.retrieve({
      retriever: docRetriever,
      query: input.question,
      options: { k: input.topK },
    });

    if (docs.length === 0) {
      return {
        answer: "I could not find any relevant documents to answer your question.",
        sources: [],
        cached: false,
      };
    }

    // Build numbered context
    const context = docs
      .map((d, i) => `[${i + 1}] (${d.metadata?.category}) ${d.metadata?.title}\n${d.content}`)
      .join("\n\n---\n\n");

    // Generate grounded answer
    const { text } = await ai.generate({
      model: gemini25Flash,
      prompt: `You are a knowledge base assistant. Answer ONLY using the provided sources.
Cite sources using [1], [2], etc. If the sources don't cover the question, say so.

Sources:
${context}

Question: ${input.question}`,
      config: { temperature: 0.2, maxOutputTokens: 1024 },
    });

    const result: z.infer<typeof RagOutput> = {
      answer: text,
      sources: docs.map((d) => ({
        title: d.metadata?.title ?? "Unknown",
        category: d.metadata?.category ?? "general",
        snippet: d.content.substring(0, 150) + "...",
      })),
      cached: false,
    };

    // Cache the result
    queryCache.set(cacheKey, { result, expiry: Date.now() + CACHE_TTL_MS });

    return result;
  }
);

ai.startFlowServer({ flows: [ragFlow] });
```

### Expected Output

```json
{
  "answer": "To set up VPC Service Controls for Vertex AI, you need to: 1) Create an access policy and service perimeter in Access Context Manager [1], 2) Add aiplatform.googleapis.com to the restricted services list [1], 3) Configure access levels for your CI/CD service accounts [2], and 4) Test access from both inside and outside the perimeter [3]. Changes propagate within 30 minutes.",
  "sources": [
    {
      "title": "VPC-SC Configuration Guide",
      "category": "security",
      "snippet": "VPC Service Controls create a security perimeter around GCP resources. To configure for Vertex AI..."
    },
    {
      "title": "CI/CD Pipeline Security",
      "category": "devops",
      "snippet": "Service accounts used in CI/CD pipelines need explicit access levels in the VPC-SC perimeter..."
    },
    {
      "title": "Agent Engine Deployment Checklist",
      "category": "deployment",
      "snippet": "Before deploying to production, verify that VPC-SC perimeters allow the agent service account..."
    }
  ],
  "cached": false
}
```

---

## Example 3: Multi-Tool Agent Flow

Define tools with typed schemas, route user queries, and trace tool execution.

```typescript
// src/agent-flow.ts
import { genkit, z } from "genkit";
import { googleAI, gemini25Flash } from "@genkit-ai/googleai";

const ai = genkit({
  plugins: [googleAI()],
});

// Tool 1: Weather lookup
const getWeather = ai.defineTool(
  {
    name: "getWeather",
    description: "Get current weather for a city",
    inputSchema: z.object({
      city: z.string().describe("City name, e.g. 'San Francisco'"),
    }),
    outputSchema: z.object({
      city: z.string(),
      tempF: z.number(),
      condition: z.string(),
      humidity: z.number(),
    }),
  },
  async ({ city }) => {
    // In production, call a real weather API
    const mockWeather: Record<string, { tempF: number; condition: string; humidity: number }> = {
      "san francisco": { tempF: 62, condition: "Foggy", humidity: 78 },
      "new york": { tempF: 45, condition: "Cloudy", humidity: 55 },
      "austin": { tempF: 85, condition: "Sunny", humidity: 40 },
    };
    const data = mockWeather[city.toLowerCase()] ?? { tempF: 70, condition: "Unknown", humidity: 50 };
    return { city, ...data };
  }
);

// Tool 2: Calendar event creation
const createEvent = ai.defineTool(
  {
    name: "createEvent",
    description: "Create a calendar event",
    inputSchema: z.object({
      title: z.string(),
      date: z.string().describe("ISO date string, e.g. 2025-03-20"),
      startTime: z.string().describe("Start time, e.g. 14:00"),
      durationMinutes: z.number().min(15).max(480),
    }),
    outputSchema: z.object({
      eventId: z.string(),
      title: z.string(),
      scheduledAt: z.string(),
      confirmed: z.boolean(),
    }),
  },
  async ({ title, date, startTime, durationMinutes }) => {
    const eventId = `evt_${Date.now().toString(36)}`;
    return {
      eventId,
      title,
      scheduledAt: `${date}T${startTime}:00`,
      confirmed: true,
    };
  }
);

// Agent flow with multi-turn tool usage
const AgentInput = z.object({
  message: z.string(),
  sessionId: z.string().optional(),
});

const AgentOutput = z.object({
  reply: z.string(),
  toolsUsed: z.array(z.string()),
});

export const agentFlow = ai.defineFlow(
  {
    name: "assistant-agent",
    inputSchema: AgentInput,
    outputSchema: AgentOutput,
  },
  async (input) => {
    const { text, toolRequests } = await ai.generate({
      model: gemini25Flash,
      tools: [getWeather, createEvent],
      prompt: input.message,
      system: `You are a helpful assistant with access to weather and calendar tools.
Use tools when the user asks about weather or wants to schedule something.
Be concise in your responses.`,
      config: { temperature: 0.5 },
    });

    const toolsUsed = (toolRequests ?? []).map((t) => t.toolName);

    return {
      reply: text,
      toolsUsed,
    };
  }
);

ai.startFlowServer({ flows: [agentFlow] });
```

### Testing

```bash
# Weather query
curl -X POST http://localhost:3400/assistant-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in San Francisco?"}'

# Calendar + weather combined
curl -X POST http://localhost:3400/assistant-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Schedule a picnic tomorrow at 2pm for 2 hours. Also check the weather in Austin."}'
```

### Expected Output

Weather query:

```json
{
  "reply": "The weather in San Francisco is currently 62F and foggy with 78% humidity. You might want to bring a jacket!",
  "toolsUsed": ["getWeather"]
}
```

Combined query:

```json
{
  "reply": "I've scheduled your picnic for tomorrow at 2:00 PM (2 hours). The weather in Austin looks great - 85F, sunny, and 40% humidity. Perfect picnic weather!",
  "toolsUsed": ["createEvent", "getWeather"]
}
```

### Cloud Run Deployment

```bash
# Dockerfile
cat > Dockerfile << 'DOCKERFILE'
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist/ ./dist/
ENV PORT=8080
EXPOSE 8080
CMD ["node", "dist/agent-flow.js"]
DOCKERFILE

# Deploy
gcloud run deploy genkit-agent \
  --source . \
  --region us-central1 \
  --memory 512Mi \
  --min-instances 2 \
  --max-instances 10 \
  --set-secrets "GOOGLE_GENAI_API_KEY=genai-api-key:latest" \
  --allow-unauthenticated
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
