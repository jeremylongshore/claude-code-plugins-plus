# TwinMind Core Workflow A - Detailed Implementation

## Meeting Capture

```typescript
import { getTwinMindClient } from '../twinmind/client';

export class MeetingCapture {
  private client = getTwinMindClient();

  async startLiveCapture(options: MeetingOptions = {}): Promise<string> {
    const response = await this.client.post('/meetings/live/start', {
      title: options.title || `Meeting ${new Date().toISOString()}`,
      calendar_event_id: options.calendarEventId,
      language: options.language || 'auto',
      diarization: options.enableDiarization ?? true,
      model: 'ear-3',
    });
    return response.data.session_id;
  }

  async stopCapture(sessionId: string): Promise<Transcript> {
    const response = await this.client.post(`/meetings/live/${sessionId}/stop`);
    return response.data.transcript;
  }

  async transcribeRecording(audioUrl: string, options: MeetingOptions = {}): Promise<Transcript> {
    const response = await this.client.post('/transcribe', {
      audio_url: audioUrl,
      title: options.title,
      language: options.language || 'auto',
      diarization: options.enableDiarization ?? true,
      model: 'ear-3',
    });
    return this.waitForTranscript(response.data.transcript_id);
  }

  private async waitForTranscript(transcriptId: string, maxWaitMs = 300000): Promise<Transcript> {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitMs) {
      const response = await this.client.get(`/transcripts/${transcriptId}`);
      if (response.data.status === 'completed') return response.data;
      if (response.data.status === 'failed') throw new Error(`Transcription failed: ${response.data.error}`);
      await new Promise(r => setTimeout(r, 2000));
    }
    throw new Error('Transcription timeout');
  }
}
```

## Summary Generator

```typescript
export class SummaryGenerator {
  private client = getTwinMindClient();

  async generateSummary(transcriptId: string, options: SummaryOptions = {}): Promise<Summary> {
    const response = await this.client.post('/summarize', {
      transcript_id: transcriptId,
      format: options.format || 'detailed',
      include_action_items: options.includeActionItems ?? true,
      include_key_points: options.includeKeyPoints ?? true,
      max_length: options.maxLength || 500,
    });
    return response.data;
  }

  async generateFollowUpEmail(transcriptId: string): Promise<string> {
    const response = await this.client.post('/generate/follow-up-email', { transcript_id: transcriptId });
    return response.data.email_content;
  }

  async generateMeetingNotes(transcriptId: string): Promise<string> {
    const response = await this.client.post('/generate/meeting-notes', { transcript_id: transcriptId, format: 'markdown' });
    return response.data.notes;
  }
}
```

## Speaker Manager

```typescript
export class SpeakerManager {
  async identifySpeakers(transcript: Transcript, attendees?: string[]): Promise<Speaker[]> {
    const speakers = new Map<string, Speaker>();
    for (const segment of transcript.segments) {
      const speakerId = segment.speaker_id || 'unknown';
      const existing = speakers.get(speakerId);
      if (existing) {
        existing.speakingTime += segment.end - segment.start;
        existing.segments += 1;
      } else {
        speakers.set(speakerId, { id: speakerId, speakingTime: segment.end - segment.start, segments: 1 });
      }
    }
    if (attendees?.length) {
      return this.matchToAttendees(Array.from(speakers.values()), attendees);
    }
    return Array.from(speakers.values());
  }

  private async matchToAttendees(speakers: Speaker[], attendees: string[]): Promise<Speaker[]> {
    const client = getTwinMindClient();
    const response = await client.post('/speakers/match', { speakers: speakers.map(s => s.id), attendees });
    return speakers.map((speaker, idx) => ({
      ...speaker,
      name: response.data.matches[idx]?.name,
      email: response.data.matches[idx]?.email,
    }));
  }
}
```

## Complete Workflow Orchestration

```typescript
export async function processMeeting(audioUrl: string, options = {}): Promise<MeetingResult> {
  const capture = new MeetingCapture();
  const summaryGen = new SummaryGenerator();
  const speakerMgr = new SpeakerManager();

  // Step 1: Transcribe
  const transcript = await capture.transcribeRecording(audioUrl, { title: options.title, enableDiarization: true });

  // Step 2: Summary + speakers in parallel
  const [summary, speakers] = await Promise.all([
    summaryGen.generateSummary(transcript.id, { format: 'detailed', includeActionItems: true, includeKeyPoints: true }),
    speakerMgr.identifySpeakers(transcript, options.attendees),
  ]);

  const result: MeetingResult = { transcriptId: transcript.id, transcript, summary, speakers };

  // Step 3: Optional outputs
  if (options.generateEmail) result.followUpEmail = await summaryGen.generateFollowUpEmail(transcript.id);
  if (options.generateNotes) result.meetingNotes = await summaryGen.generateMeetingNotes(transcript.id);

  return result;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
