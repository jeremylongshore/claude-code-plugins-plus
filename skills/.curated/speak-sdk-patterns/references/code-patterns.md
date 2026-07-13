# Speak SDK Code Patterns

## Full Client Class

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

    def assess_pronunciation(self, audio_path: str, target_text: str,
                              language: str = "en") -> dict:
        with open(audio_path, 'rb') as f:
            return self._post("/pronunciation/assess", files={
                "audio": (os.path.basename(audio_path), f, "audio/wav")
            }, data={
                "text": target_text,
                "language": language,
                "detail_level": "phoneme"
            })

    def start_conversation(self, scenario: str, language: str = "en",
                           level: str = "intermediate") -> dict:
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

## Batch Assessment with Rate Limiting

```python
import time

def batch_assess(client: SpeakClient, recordings: list[dict], delay: float = 1.0):
    results = []
    for rec in recordings:
        try:
            result = client.assess_pronunciation(
                rec["audio"], rec["text"], rec.get("lang", "en"))
            results.append({"file": rec["audio"], "score": result["score"]})
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                time.sleep(float(e.response.headers.get("Retry-After", 10)))
                result = client.assess_pronunciation(rec["audio"], rec["text"])
                results.append({"file": rec["audio"], "score": result["score"]})
            else:
                results.append({"file": rec["audio"], "error": str(e)})
        time.sleep(delay)
    return results
```

## Audio Preprocessing

```python
import subprocess

def convert_to_wav(input_path: str, output_path: str):
    subprocess.run([
        "ffmpeg", "-i", input_path, "-ar", "16000",
        "-ac", "1", "-f", "wav", output_path
    ], check=True)
```

## Usage Examples

```python
# Pronunciation assessment
client = SpeakClient()
result = client.assess_pronunciation("recording.wav", "Hello, how are you?")
print(f"Overall score: {result['score']}/100")
for word in result.get("words", []):
    print(f"  {word['text']}: {word['score']}/100")

# Conversation practice
session = client.start_conversation("ordering at a restaurant", language="es")
response = client.send_turn(session["session_id"], "reply.wav")
print(f"AI response: {response['text']}")
```
