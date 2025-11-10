# Firebase Genkit Pro

**Production-grade Firebase Genkit specialist with expert agents for AI flows, RAG systems, monitoring, and multi-language deployment across Node.js, Python, and Go.**

## Overview

Firebase Genkit Pro is a comprehensive Claude Code plugin providing expert guidance for building production-ready AI applications using Firebase Genkit 1.0+. This plugin includes specialized agents and auto-activating skills for the complete development lifecycle from initialization to production deployment.

## What's Included

### 🤖 Specialized Agents

- **genkit-flow-architect**: Expert in designing multi-step AI workflows, RAG systems, and tool calling patterns

### 📋 Slash Commands

- `/init-genkit-project`: Initialize new Genkit projects with best practices for Node.js, Python, or Go

### ✨ Agent Skills (Auto-Activating)

- **genkit-production-expert**: Automatically activates for Genkit-related tasks
  - **Trigger phrases**: "create genkit flow", "implement RAG", "deploy genkit", "gemini integration"
  - **Allowed tools**: Read, Write, Edit, Grep, Glob, Bash
  - **Version**: 1.0.0 (2025 schema compliant)

## Latest Genkit Versions Supported

- **Node.js**: 1.0 (Stable, Feb 2025)
- **Python**: Alpha (April 2025)
- **Go**: 1.0 (Stable, Sep 2025)

## Features

✅ Multi-language support (TypeScript/JavaScript, Python, Go)
✅ RAG implementation with vector search
✅ Tool calling and function integration
✅ Gemini 2.5 Pro/Flash integration
✅ AI monitoring with Firebase Console
✅ Production deployment to Firebase Functions or Cloud Run
✅ OpenTelemetry tracing
✅ Cost optimization strategies
✅ Auto-activating skills with clear trigger phrases

## Installation

```bash
/plugin install firebase-genkit-pro@claude-code-plugins-plus
```

## Quick Start

### Initialize a New Project

```bash
/init-genkit-project
```

Then follow the prompts to:
1. Select your language (Node.js/Python/Go)
2. Configure project structure
3. Set up environment variables
4. Install dependencies

### Natural Language Usage

The skill auto-activates when you mention Genkit tasks:

```
"Create a Genkit flow for question answering with Gemini 2.5 Flash"
"Implement RAG with vector search for our documentation"
"Deploy this Genkit app to Firebase with AI monitoring enabled"
"Add tool calling to my Genkit agent for weather and calendar"
```

## Architecture

### Genkit Flow Pattern

```typescript
const myFlow = ai.defineFlow(
  {
    name: 'myFlow',
    inputSchema: z.object({ input: z.string() }),
    outputSchema: z.object({ output: z.string() }),
  },
  async (input) => {
    const { text } = await ai.generate({
      model: gemini25Flash,
      prompt: `Process: ${input.input}`,
    });
    return { output: text };
  }
);
```

### RAG Implementation

```typescript
const ragFlow = ai.defineFlow(async (query) => {
  // 1. Retrieve relevant documents
  const docs = await retrieve({
    retriever: myRetriever,
    query,
    config: { k: 5 },
  });

  // 2. Generate answer with context
  const { text } = await ai.generate({
    model: gemini25Flash,
    prompt: `Context: ${docs}\n\nQuestion: ${query}`,
  });

  return text;
});
```

## Use Cases

- **Customer Support**: RAG-based Q&A systems
- **Content Generation**: Multi-step content workflows
- **Data Processing**: Extract, transform, and analyze with AI
- **Agent Systems**: Tool-calling agents for complex tasks
- **Search Enhancement**: Semantic search with embeddings

## Integration with Other Plugins

### Works with ADK Plugin

For complex multi-agent orchestration:
- Use Genkit for specialized AI flows
- Use ADK for orchestrating multiple flows
- Communication via A2A protocol

### Works with Vertex AI Validator

For production deployment:
- Genkit implements the flows
- Validator ensures production readiness
- Validates monitoring and security

## Best Practices

1. **Always use typed schemas** (Zod/Pydantic/structs)
2. **Enable AI monitoring** for production deployments
3. **Implement error handling** for all flows
4. **Use context caching** for repeated prompts
5. **Monitor token usage** to control costs
6. **Test locally** with Genkit Developer UI
7. **Version control** flow definitions

## Monitoring & Debugging

Access Genkit Developer UI during development:

```bash
npm run genkit:dev
# Opens http://localhost:4000
```

View production monitoring in Firebase Console:
- Token consumption
- Latency metrics
- Error rates
- Custom traces

## Production Deployment

### Firebase Functions

```bash
firebase deploy --only functions
```

### Google Cloud Run

```bash
gcloud run deploy genkit-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Requirements

- Node.js 18+ (for TypeScript/JavaScript)
- Python 3.9+ (for Python)
- Go 1.21+ (for Go)
- Google Cloud Project
- Firebase account (for Firebase deployment)
- Google API Key or Vertex AI credentials

## License

MIT

## Support

- Documentation: https://genkit.dev/
- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.0 (2025) - Initial release with Genkit 1.0 support
