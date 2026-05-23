# Frontend Integration

## Frontend Integration

### React Hook for Streaming

```typescript
import { useState, useCallback } from 'react';

function useStreamingChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [response, setResponse] = useState('');
  const [error, setError] = useState<Error | null>(null);

  const streamChat = useCallback(async (prompt: string) => {
    setIsStreaming(true);
    setResponse('');
    setError(null);

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        setResponse((prev) => prev + text);
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  return { streamChat, response, isStreaming, error };
}

// Usage
function ChatComponent() {
  const { streamChat, response, isStreaming } = useStreamingChat();

  return (
    <div>
      <button onClick={() => streamChat('Hello')} disabled={isStreaming}>
        Send
      </button>
      <pre>{response}</pre>
    </div>
  );
}
```

### SSE Client

```javascript
function streamSSE(prompt, onChunk, onComplete, onError) {
  const eventSource = new EventSource(
    `/api/chat/stream?prompt=${encodeURIComponent(prompt)}`
  );

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close();
      onComplete?.();
    } else {
      onChunk(event.data);
    }
  };

  eventSource.onerror = (error) => {
    eventSource.close();
    onError?.(error);
  };

  return () => eventSource.close();
}

// Usage
const cleanup = streamSSE(
  'Hello',
  (chunk) => console.log(chunk),
  () => console.log('Done'),
  (err) => console.error(err)
);
```
