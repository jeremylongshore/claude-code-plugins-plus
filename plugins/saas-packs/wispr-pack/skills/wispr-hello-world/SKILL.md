---
name: wispr-hello-world
description: |
  Wispr Flow hello world for voice-to-text API integration.
  Use when integrating Wispr Flow dictation, WebSocket streaming,
  or building voice-powered applications.
  Trigger: "wispr hello world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, dictation, wispr]
compatible-with: claude-code
---

# Wispr Flow Hello World

## Overview

Stream audio to Wispr Flow and receive real-time transcription. Wispr specializes in developer-context-aware dictation -- it understands code terms, CLI commands, and technical jargon.

## Instructions

### Step 1: Record and Transcribe (REST)

```python
import requests, os

# Transcribe an audio file
with open("voice-memo.wav", "rb") as audio:
    response = requests.post(
        "https://api.wisprflow.ai/api/v1/transcribe",
        headers={"Authorization": f"Bearer {os.environ['WISPR_API_KEY']}"},
        files={"audio": audio},
        data={"language": "en", "context": "programming"},
    )

result = response.json()
print(f"Text: {result['text']}")
print(f"Confidence: {result.get('confidence', 'N/A')}")
```

### Step 2: Real-Time Streaming (WebSocket)

```typescript
// Stream microphone audio to Wispr Flow
const ws = new WebSocket('wss://api.wisprflow.ai/api/v1/ws');

// Browser audio capture
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const context = new AudioContext({ sampleRate: 16000 });
const source = context.createMediaStreamSource(stream);

const processor = context.createScriptProcessor(4096, 1, 1);
source.connect(processor);
processor.connect(context.destination);

processor.onaudioprocess = (event) => {
  const audioData = event.inputBuffer.getChannelData(0);
  // Convert Float32Array to Int16Array for transmission
  const int16 = new Int16Array(audioData.length);
  for (let i = 0; i < audioData.length; i++) {
    int16[i] = Math.max(-32768, Math.min(32767, audioData[i] * 32768));
  }
  ws.send(int16.buffer);
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'partial') {
    console.log(`Partial: ${data.text}`);
  } else if (data.type === 'final') {
    console.log(`Final: ${data.text}`);
  }
};
```

## Output

```
Partial: implement a function that
Final: Implement a function that calculates the Fibonacci sequence using dynamic programming.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Garbled text | Wrong sample rate | Use 16kHz mono PCM |
| No results | Silence or noise | Check microphone input |
| High latency | REST endpoint | Use WebSocket for streaming |

## Resources

- [WebSocket Quickstart](https://api-docs.wisprflow.ai/websocket_quickstart)
- [Wispr Flow for Developers](https://wisprflow.ai/developers)

## Next Steps

Proceed to `wispr-local-dev-loop` for development workflow.
