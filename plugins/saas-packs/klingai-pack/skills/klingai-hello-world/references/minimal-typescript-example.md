# Minimal Typescript Example

## Minimal TypeScript Example

```typescript
import axios from 'axios';

const KLINGAI_API_KEY = process.env.KLINGAI_API_KEY!;
const BASE_URL = 'https://api.klingai.com/v1';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${KLINGAI_API_KEY}`,
    'Content-Type': 'application/json'
  }
});

async function createVideo(prompt: string): Promise<string> {
  const response = await client.post('/videos/text2video', {
    prompt,
    duration: 5,
    aspect_ratio: '16:9'
  });
  return response.data.job_id;
}

async function waitForVideo(jobId: string, timeout = 300000): Promise<any> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const response = await client.get(`/videos/${jobId}`);
    const { status, video_url, error } = response.data;

    console.log(`Status: ${status}`);

    if (status === 'completed') {
      return response.data;
    } else if (status === 'failed') {
      throw new Error(`Generation failed: ${error}`);
    }

    await new Promise(r => setTimeout(r, 5000));
  }

  throw new Error('Video generation timed out');
}

async function main() {
  console.log('🎬 Kling AI Hello World');
  console.log('='.repeat(40));

  const prompt = 'A golden retriever running through a sunny meadow, cinematic quality';

  console.log(`Prompt: ${prompt}`);
  console.log('Submitting generation request...');

  const jobId = await createVideo(prompt);
  console.log(`Job ID: ${jobId}`);

  console.log('Waiting for completion...');
  const result = await waitForVideo(jobId);

  console.log('\n✅ Video generated successfully!');
  console.log(`Video URL: ${result.video_url}`);
}

main().catch(console.error);
```
