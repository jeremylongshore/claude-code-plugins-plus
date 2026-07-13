# Langfuse SDK Patterns - Implementation Details

## Singleton Client Instance

```typescript
import { Langfuse } from "langfuse";

let langfuseInstance: Langfuse | null = null;

export function getLangfuse(): Langfuse {
  if (!langfuseInstance) {
    langfuseInstance = new Langfuse({
      publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
      secretKey: process.env.LANGFUSE_SECRET_KEY!,
      baseUrl: process.env.LANGFUSE_HOST,
    });
  }
  return langfuseInstance;
}

export async function shutdownLangfuse(): Promise<void> {
  if (langfuseInstance) {
    await langfuseInstance.shutdownAsync();
    langfuseInstance = null;
  }
}
```

## Proper Trace Lifecycle

```typescript
async function handleRequest(request: Request) {
  const langfuse = getLangfuse();
  const trace = langfuse.trace({
    name: "api/chat",
    userId: request.userId,
    sessionId: request.sessionId,
    input: request.body,
  });

  try {
    const result = await processRequest(trace, request);
    trace.update({ output: result, metadata: { status: "success" } });
    return result;
  } catch (error) {
    trace.update({ output: { error: String(error) }, level: "ERROR", statusMessage: String(error) });
    throw error;
  }
}
```

## Nested Spans for Complex Operations

```typescript
async function processRequest(trace, request) {
  const processSpan = trace.span({ name: "process-request", input: request.body });

  const validateSpan = processSpan.span({ name: "validate-input", input: request.body });
  const validatedInput = await validateInput(request.body);
  validateSpan.end({ output: validatedInput });

  const retrieveSpan = processSpan.span({ name: "retrieve-context" });
  const context = await retrieveContext(validatedInput.query);
  retrieveSpan.end({ output: { documentCount: context.length } });

  const generation = processSpan.generation({ name: "generate-response", model: "gpt-4", input: { messages: buildMessages(validatedInput, context) } });
  const response = await callLLM(validatedInput, context);
  generation.end({ output: response.content, usage: { promptTokens: response.usage.prompt_tokens, completionTokens: response.usage.completion_tokens } });

  processSpan.end({ output: response });
  return response;
}
```

## Python Decorators

```python
from langfuse.decorators import observe, langfuse_context

@observe()
def process_request(user_input: str) -> str:
    langfuse_context.update_current_observation(metadata={"input_length": len(user_input)})
    validated = validate_input(user_input)
    context = retrieve_context(validated)
    return generate_response(validated, context)

@observe()
def validate_input(user_input: str) -> dict:
    return {"query": user_input.strip(), "valid": True}

@observe(as_type="generation")
def generate_response(query: dict, context: list) -> str:
    langfuse_context.update_current_observation(model="gpt-4", usage={"prompt_tokens": 100, "completion_tokens": 50})
    return "Generated response"
```

## Session and User Tracking

```typescript
function createConversationTrace(userId: string, sessionId: string, turn: number) {
  return langfuse.trace({
    name: "conversation-turn",
    userId,
    sessionId,
    metadata: { turn, timestamp: new Date().toISOString() },
    tags: ["conversation"],
  });
}
```

## Scores and Evaluation

```typescript
const trace = langfuse.trace({ name: "scored-operation" });

langfuse.score({ traceId: trace.id, name: "accuracy", value: 0.95, comment: "High accuracy response" });
langfuse.score({ traceId: trace.id, name: "user-feedback", value: 1, comment: "User thumbs up" });
langfuse.score({ traceId: trace.id, observationId: generation.id, name: "relevance", value: 0.8 });
```

## Complete TypeScript Pattern

```typescript
async function chat(request: { userId: string; sessionId: string; message: string }) {
  const trace = langfuse.trace({ name: "chat", userId: request.userId, sessionId: request.sessionId, input: { message: request.message } });
  const span = trace.span({ name: "process" });

  try {
    const generation = span.generation({ name: "llm-call", model: "gpt-4", input: [{ role: "user", content: request.message }] });
    const response = await callOpenAI(request.message);
    generation.end({ output: response.content, usage: response.usage });
    span.end({ output: { response: response.content } });
    trace.update({ output: { response: response.content } });
    return response.content;
  } catch (error) {
    span.end({ level: "ERROR", statusMessage: String(error) });
    trace.update({ level: "ERROR", output: { error: String(error) } });
    throw error;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
