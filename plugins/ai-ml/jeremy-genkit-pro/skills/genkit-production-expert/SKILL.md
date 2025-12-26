---
name: genkit-production-expert
description: |
  Build production Firebase Genkit applications including RAG systems, multi-step flows, and tool calling for Node.js/Python/Go. Deploy to Firebase Functions or Cloud Run with AI monitoring. Use when asked to "create genkit flow" or "implement RAG". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## What This Skill Does

This skill provides comprehensive expertise in building production-ready Firebase Genkit applications across Node.js (1.0), Python (Alpha), and Go (1.0). It handles the complete lifecycle from initialization to deployment with AI monitoring.

### Core Capabilities

1. **Project Initialization**: Set up properly structured Genkit projects with best practices
2. **Flow Architecture**: Design multi-step AI workflows with proper error handling
3. **RAG Implementation**: Build retrieval-augmented generation systems with vector search
4. **Tool Integration**: Implement function calling and custom tools
5. **Monitoring Setup**: Configure AI monitoring for Firebase Console
6. **Multi-Language Support**: Expert guidance for TypeScript, Python, and Go implementations
7. **Production Deployment**: Deploy to Firebase Functions or Google Cloud Run

## When This Skill Activates

This skill automatically activates when you mention:

### Trigger Phrases
- "Create a Genkit flow"
- "Implement RAG with Genkit"
- "Deploy Genkit to Firebase"
- "Set up Gemini integration"
- "Configure AI monitoring"
- "Build Genkit application"
- "Design AI workflow"
- "Genkit tool calling"
- "Vector search with Genkit"
- "Genkit production deployment"

### Use Case Patterns
- Setting up new Genkit projects
- Implementing RAG systems with embedding models
- Integrating Gemini 2.5 Pro/Flash models
- Creating multi-step AI workflows
- Deploying to production with monitoring
- Debugging Genkit flows
- Optimizing token usage and costs

## How It Works

### Phase 1: Requirements Analysis
```
User Request → Analyze needs → Determine:
- Target language (Node.js/Python/Go)
- Flow complexity (simple/multi-step/RAG)
- Model requirements (Gemini version, custom models)
- Deployment target (Firebase/Cloud Run/local)
```

### Phase 2: Project Setup
```
Check existing project → If new:
  - Initialize project structure
  - Install dependencies
  - Configure environment variables
  - Set up TypeScript/Python/Go config

If existing:
  - Analyze current structure
  - Identify integration points
  - Preserve existing code
```

### Phase 3: Implementation
```
Design flow architecture → Implement:
  - Input/output schemas (Zod/Pydantic/Go structs)
  - Model configuration
  - Tool definitions (if needed)
  - Retriever setup (for RAG)
  - Error handling
  - Tracing configuration
```

### Phase 4: Testing & Validation
```
Create test cases → Run locally:
  - Genkit Developer UI
  - Unit tests
  - Integration tests
  - Token usage analysis
```

### Phase 5: Production Deployment
```
Configure deployment → Deploy:
  - Firebase Functions (with AI monitoring)
  - Cloud Run (with auto-scaling)
  - Set up monitoring dashboards
  - Configure alerting
```

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
3. Sets up local testing
4. Provides deployment instructions

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
      embedder: textEmbeddingGecko,
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
3. Creates RAG flow combining retrieval + generation
4. Sets up vector database connection
5. Implements caching for efficiency

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
2. Creates agent flow with tool access:
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
3. Implements proper error handling
4. Sets up tool execution tracing

## Production Best Practices Applied

### 1. Schema Validation
- All inputs/outputs use Zod (TS), Pydantic (Python), or structs (Go)
- Prevents runtime errors from malformed data

### 2. Error Handling
```typescript
try {
  const result = await ai.generate({...});
  return result;
} catch (error) {
  if (error.code === 'SAFETY_BLOCK') {
    // Handle safety filters
  } else if (error.code === 'QUOTA_EXCEEDED') {
    // Handle rate limits
  }
  throw error;
}
```

### 3. Cost Optimization
- Context caching for repeated prompts
- Token usage monitoring
- Temperature tuning for use case
- Model selection (Flash vs Pro)

### 4. Monitoring
- OpenTelemetry tracing enabled
- Custom span attributes
- Firebase Console integration
- Alert configuration

### 5. Security
- Environment variable management
- API key rotation support
- Input sanitization
- Output filtering

## Integration with Other Tools

### Works With ADK Plugin
When complex multi-agent orchestration is needed:
- Use Genkit for individual specialized flows
- Use ADK for orchestrating multiple Genkit flows
- Pass results via A2A protocol

### Works With Vertex AI Validator
For production deployment:
- Genkit implements the flows
- Validator ensures production readiness
- Validates monitoring configuration
- Checks security compliance

## Tool Permissions

This skill uses the following tools:
- **Read**: Analyze existing code and configuration
- **Write**: Create new flow files and configs
- **Edit**: Modify existing Genkit implementations
- **Grep**: Search for integration points
- **Glob**: Find related files
- **Bash**: Install dependencies, run tests, deploy

## Troubleshooting Guide

### Common Issue 1: API Key Not Found
**Symptoms**: Error "API key not provided"
**Solution**:
1. Check `.env` file exists
2. Verify `GOOGLE_API_KEY` is set
3. Ensure `dotenv` is loaded

### Common Issue 2: Flow Not Appearing in UI
**Symptoms**: Flow not visible in Genkit Developer UI
**Solution**:
1. Ensure flow is exported
2. Restart Genkit server
3. Check console for errors

### Common Issue 3: High Token Usage
**Symptoms**: Unexpected costs
**Solution**:
1. Implement context caching
2. Use Gemini 2.5 Flash instead of Pro
3. Lower temperature
4. Compress prompts

## Version History

- **1.0.0** (2025): Initial release with Node.js 1.0, Python Alpha, Go 1.0 support
- Supports Gemini 2.5 Pro/Flash
- AI monitoring integration
- Production deployment patterns

## References

- Official Docs: https://genkit.dev/
- Node.js 1.0 Announcement: https://firebase.blog/posts/2025/02/announcing-genkit/
- Go 1.0 Announcement: https://developers.googleblog.com/en/announcing-genkit-go-10/
- Vertex AI Plugin: https://genkit.dev/docs/integrations/vertex-ai/

## Overview


This skill provides automated assistance for genkit production expert tasks.
This skill provides automated assistance for the described functionality.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Examples

Example usage patterns will be demonstrated in context.

## Resources

- Project documentation
- Related skills and commands