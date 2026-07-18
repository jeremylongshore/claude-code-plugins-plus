# Groq Models & Response Structure Reference

The full model catalog and the complete chat-completion response shape, moved out
of `SKILL.md` for progressive disclosure. Always confirm the live model list at
[console.groq.com/docs/models](https://console.groq.com/docs/models) — Groq
deprecates and adds models frequently.

## Available Models (Current)

| Model ID | Params | Context | Speed | Best For |
|----------|--------|---------|-------|----------|
| `llama-3.1-8b-instant` | 8B | 128K | ~560 tok/s | Classification, extraction, fast tasks |
| `llama-3.3-70b-versatile` | 70B | 128K | ~280 tok/s | General purpose, reasoning, code |
| `llama-3.3-70b-specdec` | 70B | 128K | Faster | Same quality, speculative decoding |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 17Bx16E | 128K | ~460 tok/s | Vision, multimodal |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | 17Bx128E | 128K | — | Best multimodal quality |

## Response Structure

Groq returns the OpenAI-compatible completion shape plus four Groq-specific timing
fields inside `usage` (`queue_time`, `prompt_time`, `completion_time`,
`total_time`) that let you measure LPU latency precisely.

```typescript
interface ChatCompletion {
  id: string;                    // "chatcmpl-xxx"
  object: "chat.completion";
  created: number;               // Unix timestamp
  model: string;                 // Actual model used
  choices: [{
    index: number;
    message: { role: "assistant"; content: string };
    finish_reason: "stop" | "length" | "tool_calls";
  }];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    queue_time: number;          // Groq-specific: seconds in queue
    prompt_time: number;         // Groq-specific: seconds for prompt
    completion_time: number;     // Groq-specific: seconds for completion
    total_time: number;          // Groq-specific: total processing seconds
  };
}
```
