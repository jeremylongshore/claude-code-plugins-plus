---
name: groq-core-workflow-b
description: |
  Execute Groq secondary workflows: audio transcription (Whisper), vision,
  text-to-speech, and batch model evaluation.
  Trigger with phrases like "groq whisper", "groq transcription",
  "groq audio", "groq vision", "groq TTS", "groq speech".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, workflow, audio, vision]

---
# Groq Core Workflow B: Audio, Vision & Speech

## Overview
Beyond chat completions, Groq provides ultra-fast audio transcription (Whisper at 216x real-time), multimodal vision (Llama 4 Scout/Maverick), and text-to-speech. These endpoints use the same `groq-sdk` client.

## Prerequisites
- `groq-sdk` installed, `GROQ_API_KEY` set
- For audio: audio files in supported formats
- For vision: image URLs or base64 images

## Audio Models

| Model ID | Languages | Speed | Best For |
|----------|-----------|-------|----------|
| `whisper-large-v3` | 100+ | 164x real-time | Best accuracy, multilingual |
| `whisper-large-v3-turbo` | 100+ | 216x real-time | Best speed/accuracy balance |

**Supported audio formats**: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm

## Instructions

### Step 1: Audio Transcription (Whisper)
```typescript
import Groq from "groq-sdk";
import fs from "fs";

const groq = new Groq();

// Transcribe audio file
async function transcribe(filePath: string): Promise<string> {
  const transcription = await groq.audio.transcriptions.create({
    file: fs.createReadStream(filePath),
    model: "whisper-large-v3-turbo",
    response_format: "json",        // or "text" or "verbose_json"
    language: "en",                  // Optional: ISO 639-1 code
  });

  return transcription.text;
}

// With timestamps (verbose mode)
async function transcribeWithTimestamps(filePath: string) {
  const transcription = await groq.audio.transcriptions.create({
    file: fs.createReadStream(filePath),
    model: "whisper-large-v3-turbo",
    response_format: "verbose_json",
    timestamp_granularities: ["segment"],
  });

  return transcription;
  // Returns segments with start/end times
}
```

### Step 2: Audio Translation (to English)
```typescript
// Translate any language audio to English text
async function translateAudio(filePath: string): Promise<string> {
  const translation = await groq.audio.translations.create({
    file: fs.createReadStream(filePath),
    model: "whisper-large-v3",
  });

  return translation.text;
}
```

### Step 3: Vision (Image Understanding)
```typescript
// Analyze images with Llama 4 Scout (up to 5 images per request)
async function analyzeImage(imageUrl: string, question: string) {
  const completion = await groq.chat.completions.create({
    model: "meta-llama/llama-4-scout-17b-16e-instruct",
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: question },
          { type: "image_url", image_url: { url: imageUrl } },
        ],
      },
    ],
    max_tokens: 1024,
  });

  return completion.choices[0].message.content;
}

// Multiple images
async function compareImages(urls: string[], prompt: string) {
  const imageContent = urls.map((url) => ({
    type: "image_url" as const,
    image_url: { url },
  }));

  const completion = await groq.chat.completions.create({
    model: "meta-llama/llama-4-scout-17b-16e-instruct",
    messages: [{
      role: "user",
      content: [{ type: "text", text: prompt }, ...imageContent],
    }],
    max_tokens: 2048,
  });

  return completion.choices[0].message.content;
}

// Base64 image input
async function analyzeBase64Image(base64Data: string) {
  return groq.chat.completions.create({
    model: "meta-llama/llama-4-scout-17b-16e-instruct",
    messages: [{
      role: "user",
      content: [
        { type: "text", text: "Describe this image in detail." },
        {
          type: "image_url",
          image_url: { url: `data:image/jpeg;base64,${base64Data}` },
        },
      ],
    }],
  });
}
```

### Step 4: Text-to-Speech
```typescript
// Generate speech from text
async function textToSpeech(text: string, outputPath: string) {
  const response = await groq.audio.speech.create({
    model: "playai-tts",          // or "playai-tts-arabic"
    input: text,
    voice: "Arista-PlayAI",      // See Groq docs for voice options
    response_format: "wav",       // wav, mp3, flac, opus, aac
  });

  const buffer = Buffer.from(await response.arrayBuffer());
  fs.writeFileSync(outputPath, buffer);
  console.log(`Audio saved to ${outputPath}`);
}
```

### Step 5: Python Audio Transcription
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

### Step 6: Model Benchmarking
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

## Vision Model Limits
- Maximum 5 images per request
- Supported formats: JPEG, PNG, GIF, WebP
- Images fetched from URL or embedded as base64
- Vision models also support tool use, JSON mode, and streaming

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid file format` | Unsupported audio type | Convert to mp3/wav/flac first |
| `File too large` | Audio exceeds 25MB | Split into smaller chunks |
| `model_not_found` | Vision model ID wrong | Use full path: `meta-llama/llama-4-scout-17b-16e-instruct` |
| `max_images_exceeded` | >5 images in request | Reduce to 5 or fewer images |
| `429` on Whisper | Audio RPM limit hit | Queue transcription requests |

## Resources
- [Groq Speech-to-Text](https://console.groq.com/docs/speech-to-text)
- [Groq Text-to-Speech](https://console.groq.com/docs/text-to-speech)
- [Groq Vision](https://console.groq.com/docs/vision)
- [Groq Models](https://console.groq.com/docs/models)

## Next Steps
For common errors and troubleshooting, see `groq-common-errors`.
