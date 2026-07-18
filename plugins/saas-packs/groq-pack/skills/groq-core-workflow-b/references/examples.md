# Groq Core Workflow B — Worked Examples

End-to-end examples that combine the primitives from
[implementation.md](implementation.md) into complete, copy-pasteable scripts.

## Example 1: Python Audio Transcription with Segment Timestamps

Transcribe a local MP3 and print each segment with its start/end time.

```python
from groq import Groq

client = Groq()

# Transcribe
with open("audio.mp3", "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=("audio.mp3", file),
        model="whisper-large-v3-turbo",
        response_format="verbose_json",
    )
    print(transcription.text)
    for segment in transcription.segments:
        print(f"[{segment.start:.1f}s - {segment.end:.1f}s] {segment.text}")
```

Expected output shape:

```
Full transcript text here...
[0.0s - 3.2s] First segment of speech
[3.2s - 7.8s] Second segment of speech
```

## Example 2: Model Benchmarking (Speed vs Quality)

Run the same prompt across several chat models and print latency and
throughput for each, so you can pick the right speed/quality tradeoff.

```typescript
// Compare models on same prompt for speed vs quality
async function benchmarkModels(prompt: string) {
  const models = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
  ];

  for (const model of models) {
    const start = performance.now();
    const result = await groq.chat.completions.create({
      model,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 200,
    });
    const elapsed = performance.now() - start;
    const tps = result.usage!.completion_tokens / ((result.usage as any).completion_time || 1);

    console.log(
      `${model.padEnd(45)} | ${elapsed.toFixed(0)}ms | ${tps.toFixed(0)} tok/s | ${result.usage!.total_tokens} tokens`
    );
  }
}
```

Expected output shape (one line per model):

```
llama-3.1-8b-instant                          | 210ms | 840 tok/s | 245 tokens
llama-3.3-70b-versatile                       | 480ms | 310 tok/s | 251 tokens
llama-3.3-70b-specdec                         | 300ms | 520 tok/s | 248 tokens
```
