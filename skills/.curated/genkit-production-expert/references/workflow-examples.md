# Workflow Examples

## Workflow Examples

### Example 1: Simple Question-Answering Flow

**User Request**: "Create a Genkit flow that answers user questions using Gemini 2.5 Flash"

**Skill Response**:

1. Creates TypeScript project (default)
2. Implements flow with input validation:

```typescript
const qaFlow = ai.defineFlow(
  {
    name: 'qaFlow',
    inputSchema: z.object({ question: z.string() }),
    outputSchema: z.object({ answer: z.string() }),
  },
  async (input) => {
    const { text } = await ai.generate({
      model: gemini25Flash,
      prompt: `Answer this question: ${input.question}`,
      config: { temperature: 0.3 }, // Lower for factual answers
    });
    return { answer: text };
  }
);
```

1. Sets up local testing
2. Provides deployment instructions

### Example 2: RAG System with Vector Search

**User Request**: "Implement RAG with Genkit for our documentation search"

**Skill Response**:

1. Analyzes document storage needs
2. Implements retriever with embeddings:

```typescript
const docRetriever = ai.defineRetriever(
  {
    name: 'docRetriever',
    configSchema: z.object({ k: z.number().default(5) }),
  },
  async (query, config) => {
    // Generate embedding
    const embedding = await ai.embed({
      embedder: textEmbedding004,
      content: query,
    });

    // Search vector database
    const results = await vectorDB.search(embedding, config.k);
    return results.map(doc => ({
      content: doc.text,
      metadata: { source: doc.source },
    }));
  }
);
```

1. Creates RAG flow combining retrieval + generation
2. Sets up vector database connection
3. Implements caching for efficiency

### Example 3: Multi-Agent Tool Calling

**User Request**: "Create a Genkit agent with weather and calendar tools"

**Skill Response**:

1. Defines tools with proper schemas:

```typescript
const weatherTool = ai.defineTool({
  name: 'getWeather',
  description: 'Get current weather for a location',
  inputSchema: z.object({ location: z.string() }),
  outputSchema: z.object({
    temp: z.number(),
    conditions: z.string(),
  }),
}, async ({ location }) => {
  // Call weather API
});

const calendarTool = ai.defineTool({
  name: 'checkCalendar',
  description: 'Check calendar availability',
  inputSchema: z.object({ date: z.string() }),
  outputSchema: z.object({ available: z.boolean() }),
}, async ({ date }) => {
  // Check calendar API
});
```

1. Creates agent flow with tool access:

```typescript
const agentFlow = ai.defineFlow(async (userQuery) => {
  const { text } = await ai.generate({
    model: gemini25Flash,
    prompt: userQuery,
    tools: [weatherTool, calendarTool],
  });
  return text;
});
```

1. Implements proper error handling
2. Sets up tool execution tracing
