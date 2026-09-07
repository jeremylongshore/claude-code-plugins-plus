# Groq Core Workflow A — Full Implementation

Deep implementation detail for the tool-use, JSON-mode, and structured-output
patterns. The lean SKILL.md summarizes each; this file carries the complete,
copy-paste-ready code.

## Tool Use / Function Calling

The three-phase pattern: (A) send the message with tool definitions, (B) if the
model returns `tool_calls`, execute them, (C) send the results back for the
final natural-language response.

```typescript
// Define tools with JSON Schema
const tools: Groq.Chat.ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "Get current weather for a location",
      parameters: {
        type: "object",
        properties: {
          location: { type: "string", description: "City name" },
          unit: { type: "string", enum: ["celsius", "fahrenheit"] },
        },
        required: ["location"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "search_docs",
      description: "Search internal documentation",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string" },
          limit: { type: "number", description: "Max results" },
        },
        required: ["query"],
      },
    },
  },
];

async function chatWithTools(userMessage: string) {
  // Step A: Send message with tool definitions
  const response = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: userMessage }],
    tools,
    tool_choice: "auto",
  });

  const message = response.choices[0].message;

  // Step B: If model wants to call tools, execute them
  if (message.tool_calls) {
    const toolResults = await Promise.all(
      message.tool_calls.map(async (tc) => {
        const args = JSON.parse(tc.function.arguments);
        const result = await executeFunction(tc.function.name, args);
        return {
          role: "tool" as const,
          tool_call_id: tc.id,
          content: JSON.stringify(result),
        };
      })
    );

    // Step C: Send tool results back for final response
    const finalResponse = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: [
        { role: "user", content: userMessage },
        message,         // includes tool_calls
        ...toolResults,  // tool execution results
      ],
      tools,
    });

    return finalResponse.choices[0].message.content;
  }

  return message.content;
}

// Implement your actual tool functions
async function executeFunction(name: string, args: any): Promise<any> {
  switch (name) {
    case "get_weather":
      return { temperature: 72, conditions: "sunny", location: args.location };
    case "search_docs":
      return { results: [`Doc about ${args.query}`], count: 1 };
    default:
      throw new Error(`Unknown function: ${name}`);
  }
}
```

## JSON Mode

Force the model to return syntactically valid JSON. The system prompt MUST
describe the JSON shape you want, or the model has nothing to key on.

```typescript
// Force model to return valid JSON
async function extractJSON(text: string) {
  const completion = await groq.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      {
        role: "system",
        content: "Extract entities from the text. Respond with JSON: {entities: [{name, type, confidence}]}",
      },
      { role: "user", content: text },
    ],
    response_format: { type: "json_object" },
    temperature: 0,
  });

  return JSON.parse(completion.choices[0].message.content!);
}
```

## Structured Outputs (Strict Schema)

When you need a *guaranteed* schema match (no post-hoc validation), use
`json_schema` with `strict: true`.

```typescript
// Guaranteed schema compliance -- no validation needed
async function extractStructured(text: string) {
  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "system", content: "Extract contact information from the text." },
      { role: "user", content: text },
    ],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "contact_info",
        strict: true,
        schema: {
          type: "object",
          properties: {
            name: { type: "string" },
            email: { type: "string" },
            phone: { type: "string" },
            company: { type: "string" },
          },
          required: ["name", "email"],
          additionalProperties: false,
        },
      },
    },
  });

  // With strict: true, output is guaranteed to match schema
  return JSON.parse(completion.choices[0].message.content!);
}
```

**Limitation**: Streaming and tool use are not supported with Structured
Outputs. Use non-streaming mode when using `response_format` with `json_schema`.
