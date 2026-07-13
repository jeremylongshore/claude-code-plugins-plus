# Typescript Client Pattern

## TypeScript Client Pattern

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

interface VideoResult {
  jobId: string;
  status: JobStatus;
  videoUrl?: string;
  thumbnailUrl?: string;
  error?: string;
  duration?: number;
  metadata?: Record<string, any>;
}

interface KlingAIConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

class KlingAIClient {
  private client: AxiosInstance;
  private static DEFAULT_BASE_URL = 'https://api.klingai.com/v1';
  private static DEFAULT_TIMEOUT = 30000;
  private static DEFAULT_POLL_INTERVAL = 5000;
  private static DEFAULT_MAX_WAIT = 600000;

  constructor(config: KlingAIConfig = {}) {
    const apiKey = config.apiKey || process.env.KLINGAI_API_KEY;
    if (!apiKey) {
      throw new Error('KLINGAI_API_KEY required');
    }

    this.client = axios.create({
      baseURL: config.baseUrl || KlingAIClient.DEFAULT_BASE_URL,
      timeout: config.timeout || KlingAIClient.DEFAULT_TIMEOUT,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    // Add retry interceptor
    this.client.interceptors.response.use(
      response => response,
      async (error: AxiosError) => {
        const config = error.config as any;
        config.retryCount = config.retryCount || 0;

        if (config.retryCount < (config.maxRetries || 3) &&
            [429, 500, 502, 503, 504].includes(error.response?.status || 0)) {
          config.retryCount++;
          await this.delay(Math.pow(2, config.retryCount) * 1000);
          return this.client.request(config);
        }

        throw error;
      }
    );
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async textToVideo(params: {
    prompt: string;
    duration?: number;
    model?: string;
    aspectRatio?: string;
  }): Promise<string> {
    const response = await this.client.post('/videos/text2video', {
      model: params.model || 'kling-v1.5',
      prompt: params.prompt,
      duration: params.duration || 5,
      aspect_ratio: params.aspectRatio || '16:9'
    });
    return response.data.job_id;
  }

  async getJobStatus(jobId: string): Promise<VideoResult> {
    const response = await this.client.get(`/videos/${jobId}`);
    return {
      jobId,
      status: response.data.status as JobStatus,
      videoUrl: response.data.video_url,
      thumbnailUrl: response.data.thumbnail_url,
      error: response.data.error,
      duration: response.data.duration,
      metadata: response.data
    };
  }

  async waitForCompletion(
    jobId: string,
    options: { pollInterval?: number; maxWait?: number; callback?: (result: VideoResult) => void } = {}
  ): Promise<VideoResult> {
    const pollInterval = options.pollInterval || KlingAIClient.DEFAULT_POLL_INTERVAL;
    const maxWait = options.maxWait || KlingAIClient.DEFAULT_MAX_WAIT;
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const result = await this.getJobStatus(jobId);

      if (options.callback) {
        options.callback(result);
      }

      if (result.status === JobStatus.COMPLETED) {
        return result;
      } else if (result.status === JobStatus.FAILED) {
        throw new Error(`Generation failed: ${result.error}`);
      }

      await this.delay(pollInterval);
    }

    throw new Error(`Job ${jobId} timed out after ${maxWait}ms`);
  }

  async generateVideo(params: {
    prompt: string;
    wait?: boolean;
    duration?: number;
    model?: string;
  }): Promise<VideoResult> {
    const jobId = await this.textToVideo(params);

    if (params.wait !== false) {
      return this.waitForCompletion(jobId);
    }

    return { jobId, status: JobStatus.PENDING };
  }
}

// Usage
const client = new KlingAIClient();
const result = await client.generateVideo({
  prompt: 'A cat playing piano in a jazz club',
  duration: 10
});
console.log(`Video URL: ${result.videoUrl}`);
```
