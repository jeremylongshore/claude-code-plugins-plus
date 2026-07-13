# Deepgram Hello World Extended Examples

## TypeScript - Transcribe Local File

```typescript
import { createClient } from '@deepgram/sdk';
import { readFileSync } from 'fs';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

async function transcribeFile(filePath: string) {
  const audio = readFileSync(filePath);

  const { result, error } = await deepgram.listen.prerecorded.transcribeFile(
    audio,
    { model: 'nova-2', smart_format: true, mimetype: 'audio/wav' }
  );

  if (error) throw error;
  console.log('Transcript:', result.results.channels[0].alternatives[0].transcript);
}

transcribeFile('./audio.wav');
```

## Python Example

```python
from deepgram import DeepgramClient, PrerecordedOptions
import os

deepgram = DeepgramClient(os.environ.get('DEEPGRAM_API_KEY'))

options = PrerecordedOptions(
    model="nova-2",
    smart_format=True,
)

url = {"url": "https://static.deepgram.com/examples/nasa-podcast.wav"}
response = deepgram.listen.rest.v("1").transcribe_url(url, options)

print(response.results.channels[0].alternatives[0].transcript)
```

## Customization Options

- Change `model` to `nova`, `enhanced`, or `base` for different accuracy/speed trade-offs
- Set `language` to process non-English audio (e.g., `es`, `fr`, `de`)
- Enable `diarize: true` to identify different speakers
- Enable `paragraphs: true` for structured paragraph output
