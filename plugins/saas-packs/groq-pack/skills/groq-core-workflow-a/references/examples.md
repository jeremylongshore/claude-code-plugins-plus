# Groq Core Workflow A — Worked Examples

Two runnable examples: a single-turn chat completion and a stateful multi-turn
conversation. Both assume `const groq = new Groq();` with `GROQ_API_KEY` set.

## Example 1: Chat Completion with System Prompt

Single request/response with an optional rolling `history` array. Returns the
reply text plus token `usage` so callers can meter cost.

```typescript
import Groq from "groq-sdk";

const groq = new Groq();

async function chat(userMessage: string, history: any[] = []) {
  const messages = [
    { role: "system" as const, content: "You are a concise technical assistant." },
    ...history,
    { role: "user" as const, content: userMessage },
  ];

  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages,
    temperature: 0.7,
    max_tokens: 1024,
  });

  return {
    reply: completion.choices[0].message.content,
    usage: completion.usage,
  };
}
```

## Example 2: Multi-Turn Conversation

A small class that accumulates the message history so each turn keeps context.
Push the assistant's returned message back onto the stack so the next turn sees
it.

```typescript
class GroqConversation {
  private messages: Groq.Chat.ChatCompletionMessageParam[] = [];

  constructor(private systemPrompt: string) {
    this.messages.push({ role: "system", content: systemPrompt });
  }

  async send(userMessage: string): Promise<string> {
    this.messages.push({ role: "user", content: userMessage });

    const completion = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: this.messages,
      max_tokens: 1024,
    });

    const reply = completion.choices[0].message;
    this.messages.push(reply);
    return reply.content || "";
  }
}
```
