# Request Logging

## Request Logging

### Python Debug Wrapper

```python
import json
import time
from datetime import datetime
from openai import OpenAI

class DebugOpenRouterClient:
    def __init__(self, api_key: str, log_file: str = "openrouter_debug.log"):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.log_file = log_file

    def _log(self, data: dict):
        with open(self.log_file, "a") as f:
            f.write(json.dumps(data, indent=2) + "\n---\n")

    def chat(self, model: str, messages: list, **kwargs):
        request_id = datetime.now().isoformat()
        start_time = time.time()

        # Log request
        self._log({
            "type": "request",
            "id": request_id,
            "timestamp": request_id,
            "model": model,
            "messages": messages,
            "kwargs": kwargs
        })

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            elapsed = time.time() - start_time

            # Log success
            self._log({
                "type": "response",
                "id": request_id,
                "elapsed_seconds": elapsed,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason,
                "content_preview": response.choices[0].message.content[:200]
            })

            return response

        except Exception as e:
            elapsed = time.time() - start_time

            # Log error
            self._log({
                "type": "error",
                "id": request_id,
                "elapsed_seconds": elapsed,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise

# Usage
client = DebugOpenRouterClient(api_key=os.environ["OPENROUTER_API_KEY"])
response = client.chat("openai/gpt-4-turbo", [{"role": "user", "content": "Hello"}])
```

### TypeScript Debug Wrapper

```typescript
import OpenAI from 'openai';
import fs from 'fs';

class DebugOpenRouterClient {
  private client: OpenAI;
  private logFile: string;

  constructor(apiKey: string, logFile = 'openrouter_debug.log') {
    this.client = new OpenAI({
      baseURL: 'https://openrouter.ai/api/v1',
      apiKey,
    });
    this.logFile = logFile;
  }

  private log(data: object) {
    fs.appendFileSync(
      this.logFile,
      JSON.stringify(data, null, 2) + '\n---\n'
    );
  }

  async chat(
    model: string,
    messages: OpenAI.Chat.ChatCompletionMessageParam[],
    options: Partial<OpenAI.Chat.ChatCompletionCreateParams> = {}
  ) {
    const requestId = new Date().toISOString();
    const startTime = Date.now();

    this.log({
      type: 'request',
      id: requestId,
      timestamp: requestId,
      model,
      messages,
      options,
    });

    try {
      const response = await this.client.chat.completions.create({
        model,
        messages,
        ...options,
      });

      const elapsed = (Date.now() - startTime) / 1000;

      this.log({
        type: 'response',
        id: requestId,
        elapsed_seconds: elapsed,
        model: response.model,
        usage: response.usage,
        finish_reason: response.choices[0].finish_reason,
        content_preview: response.choices[0].message.content?.slice(0, 200),
      });

      return response;
    } catch (error) {
      const elapsed = (Date.now() - startTime) / 1000;

      this.log({
        type: 'error',
        id: requestId,
        elapsed_seconds: elapsed,
        error_type: error.constructor.name,
        error_message: String(error),
      });

      throw error;
    }
  }
}
```
