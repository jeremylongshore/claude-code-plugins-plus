# Groq Core Workflow B — Full Implementation Walkthrough

Complete, runnable code for every Groq audio, vision, and speech workflow. All
snippets use the same `groq-sdk` client (`const groq = new Groq()`), which reads
`GROQ_API_KEY` from the environment automatically.

## Step 1: Audio Transcription (Whisper)

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

## Step 2: Audio Translation (to English)

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

## Step 3: Vision (Image Understanding)

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

### Vision Model Limits

- Maximum 5 images per request
- Supported formats: JPEG, PNG, GIF, WebP
- Images fetched from URL or embedded as base64
- Vision models also support tool use, JSON mode, and streaming

## Step 4: Text-to-Speech

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
