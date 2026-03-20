---
name: speak-sdk-patterns
description: |
  Apply production-ready Speak SDK patterns for TypeScript and Python.
  Use when implementing Speak integrations, refactoring SDK usage,
  or establishing team coding standards for language learning features.
  Trigger with phrases like "speak SDK patterns", "speak best practices",
  "speak code patterns", "idiomatic speak".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak SDK Patterns

## Overview
Production patterns for Speak's language learning REST API. Speak provides pronunciation assessment, conversation practice, and language proficiency evaluation through audio analysis endpoints.

## Prerequisites
- Speak API key configured
- Audio recording capability (WAV/MP3 format)
- Understanding of language learning assessment concepts

## Instructions

### Step 1: Client Setup with Audio Handling

```python
import requests
import os

class SpeakClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["SPEAK_API_KEY"]
        self.base_url = "https://api.speak.com/v1"
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def _post(self, path: str, **kwargs):
        r = self.session.post(f"{self.base_url}{path}", **kwargs)
        r.raise_for_status()
        return r.json()
```

### Step 2: Pronunciation Assessment

```python
    def assess_pronunciation(self, audio_path: str, target_text: str, language: str = "en") -> dict:
        with open(audio_path, 'rb') as f:
            return self._post("/pronunciation/assess", files={
                "audio": (os.path.basename(audio_path), f, "audio/wav")
            }, data={
                "text": target_text,
                "language": language,
                "detail_level": "phoneme"  # word, sentence, or phoneme
            })

# Usage
client = SpeakClient()
result = client.assess_pronunciation("recording.wav", "Hello, how are you?")
print(f"Overall score: {result['score']}/100")
for word in result.get("words", []):
    print(f"  {word['text']}: {word['score']}/100")
```

### Step 3: Conversation Practice Session

```python
    def start_conversation(self, scenario: str, language: str = "en", level: str = "intermediate") -> dict:
        return self._post("/conversation/start", json={
            "scenario": scenario,
            "language": language,
            "proficiency_level": level
        })

    def send_turn(self, session_id: str, audio_path: str) -> dict:
        with open(audio_path, 'rb') as f:
            return self._post(f"/conversation/{session_id}/turn", files={
                "audio": (os.path.basename(audio_path), f, "audio/wav")
            })
```

### Step 4: Batch Assessment with Rate Limiting

```python
import time

def batch_assess(client: SpeakClient, recordings: list[dict], delay: float = 1.0):
    results = []
    for rec in recordings:
        try:
            result = client.assess_pronunciation(rec["audio"], rec["text"], rec.get("lang", "en"))
            results.append({"file": rec["audio"], "score": result["score"]})
        except requests.HTTPError as e:
            if e.response.status_code == 429:  # HTTP 429 Too Many Requests
                time.sleep(float(e.response.headers.get("Retry-After", 10)))
                result = client.assess_pronunciation(rec["audio"], rec["text"])
                results.append({"file": rec["audio"], "score": result["score"]})
            else:
                results.append({"file": rec["audio"], "error": str(e)})
        time.sleep(delay)
    return results
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad audio format` | Unsupported codec | Convert to WAV 16kHz mono |
| `413 Payload too large` | Audio file > 25MB | Trim or compress audio |
| `429 Rate limited` | Too many assessments | Add delay between requests |
| Low confidence score | Background noise | Record in quiet environment |

## Examples

### Audio Preprocessing
```python
import subprocess
def convert_to_wav(input_path: str, output_path: str):
    subprocess.run([
        "ffmpeg", "-i", input_path, "-ar", "16000",  # 16000 = configured value
        "-ac", "1", "-f", "wav", output_path
    ], check=True)
```

## Resources
- [Speak API Docs](https://docs.speak.com)

## Output

- Production-ready Speak client class with typed methods
- Audio preprocessing pipeline (format conversion, quality validation)
- Batch assessment runner with rate-limit-aware scheduling