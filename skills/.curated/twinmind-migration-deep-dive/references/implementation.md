# TwinMind Migration Deep Dive - Detailed Implementation

## Migration Assessment

```typescript
async function assessMigration(source: string, dataPath: string): Promise<MigrationAssessment> {
  const files = fs.readdirSync(dataPath);
  const issues: string[] = [];
  let totalTranscripts = 0, totalDuration = 0;
  let earliest = new Date(), latest = new Date(0);
  const formats = new Set<string>();

  for (const file of files) {
    formats.add(path.extname(file).toLowerCase());
    if (path.extname(file) === '.json') {
      try {
        const content = JSON.parse(fs.readFileSync(path.join(dataPath, file), 'utf-8'));
        totalTranscripts++;
        if (content.duration) totalDuration += content.duration;
        const date = new Date(content.created_at || content.date);
        if (date < earliest) earliest = date;
        if (date > latest) latest = date;
      } catch { issues.push(`Failed to parse: ${file}`); }
    }
  }

  return {
    source, totalTranscripts,
    totalDurationHours: totalDuration / 3600,
    dateRange: { earliest, latest },
    dataFormats: Array.from(formats),
    estimatedMigrationTime: `${Math.ceil(totalTranscripts / 60 + totalDuration / 3600 * 10)} minutes`,
    potentialIssues: issues,
  };
}
```

## Fireflies.ai Export

```typescript
async function exportFromFireflies(apiKey: string): Promise<any[]> {
  const response = await fetch('https://api.fireflies.ai/graphql', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: `{ transcripts { id title date duration transcript_text summary action_items { text assignee } speakers { name id } sentences { text speaker_id start_time end_time } } }` }),
  });
  return (await response.json()).data.transcripts;
}
```

## Rev.ai Export

```typescript
async function exportFromRev(apiKey: string): Promise<any[]> {
  const jobs = await (await fetch('https://api.rev.ai/speechtotext/v1/jobs', { headers: { 'Authorization': `Bearer ${apiKey}` } })).json();
  const transcripts = [];
  for (const job of jobs.filter((j: any) => j.status === 'transcribed')) {
    const transcript = await (await fetch(`https://api.rev.ai/speechtotext/v1/jobs/${job.id}/transcript`, {
      headers: { 'Authorization': `Bearer ${apiKey}`, 'Accept': 'application/vnd.rev.transcript.v1.0+json' },
    })).json();
    transcripts.push({ id: job.id, name: job.name, created_on: job.created_on, duration_seconds: job.duration_seconds, transcript });
  }
  return transcripts;
}
```

## Data Transformers

```typescript
// Otter.ai to TwinMind
export function transformOtterToTwinMind(otterData: any): Transcript {
  return {
    id: `tm_imported_${otterData.id}`,
    text: otterData.text || otterData.transcript_text,
    duration_seconds: otterData.duration || 0,
    language: otterData.language || 'en',
    created_at: otterData.created_at || new Date().toISOString(),
    metadata: { imported_from: 'otter.ai', original_id: otterData.id },
    speakers: otterData.speakers?.map((s: any, i: number) => ({ id: `spk_${i}`, name: s.name || `Speaker ${i + 1}` })),
    segments: otterData.segments?.map((seg: any) => ({ start: seg.start_time, end: seg.end_time, text: seg.text, speaker_id: seg.speaker_id, confidence: 0.95 })),
  };
}

// Fireflies.ai to TwinMind
export function transformFirefliesToTwinMind(ffData: any): Transcript {
  return {
    id: `tm_imported_${ffData.id}`,
    title: ffData.title,
    text: ffData.transcript_text,
    duration_seconds: ffData.duration,
    language: 'en',
    created_at: ffData.date,
    metadata: { imported_from: 'fireflies.ai', original_id: ffData.id, summary: ffData.summary },
    speakers: ffData.speakers?.map((s: any) => ({ id: s.id, name: s.name })),
    segments: ffData.sentences?.map((sent: any) => ({ start: sent.start_time, end: sent.end_time, text: sent.text, speaker_id: sent.speaker_id, confidence: 0.95 })),
  };
}

// Zoom VTT to TwinMind
export function transformZoomVTTToTwinMind(vttContent: string, metadata: { title: string; date: string; duration: number }): Transcript {
  const segments: Segment[] = [];
  const lines = vttContent.split('\n');
  let current: Partial<Segment> = {};
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.includes('-->')) {
      const [start, end] = trimmed.split('-->').map(t => parseVTTTimestamp(t.trim()));
      current = { start, end };
    } else if (trimmed && !trimmed.match(/^\d+$/) && current.start !== undefined) {
      const match = trimmed.match(/^(.+?):\s*(.*)$/);
      if (match) { current.speaker_id = match[1]; current.text = match[2]; }
      else current.text = trimmed;
      if (current.text) { segments.push(current as Segment); current = {}; }
    }
  }
  return { id: `tm_imported_zoom_${Date.now()}`, title: metadata.title, text: segments.map(s => s.text).join(' '), duration_seconds: metadata.duration, language: 'en', created_at: metadata.date, metadata: { imported_from: 'zoom' }, segments };
}
```

## Batch Importer

```typescript
export async function importToTwinMind(transcripts: Transcript[], options = {}): Promise<ImportResult> {
  const client = getTwinMindClient();
  const batchSize = options.batchSize || 10;
  const result = { successful: 0, failed: 0, errors: [] };

  for (let i = 0; i < transcripts.length; i += batchSize) {
    for (const transcript of transcripts.slice(i, i + batchSize)) {
      try {
        // Check for duplicates
        const existing = await client.get('/transcripts', { params: { 'metadata.original_id': transcript.metadata?.original_id } });
        if (existing.data.length > 0) continue;

        await client.post('/transcripts/import', transcript);
        result.successful++;
      } catch (error: any) {
        result.failed++;
        result.errors.push({ id: transcript.id, error: error.message });
      }
    }
    if (i + batchSize < transcripts.length) await new Promise(r => setTimeout(r, options.delayMs || 1000));
  }
  return result;
}
```

## Migration Verification

```typescript
export async function verifyMigration(sourceTranscripts: Transcript[]): Promise<VerificationResult> {
  const client = getTwinMindClient();
  const missing: string[] = [];
  const mismatches: Array<{ id: string; issue: string }> = [];

  for (const source of sourceTranscripts) {
    const imported = await client.get('/transcripts', { params: { 'metadata.original_id': source.metadata?.original_id } });
    if (imported.data.length === 0) { missing.push(source.id); continue; }

    const imp = imported.data[0];
    const srcWords = source.text.split(/\s+/).length;
    const impWords = imp.text.split(/\s+/).length;
    if (Math.abs(srcWords - impWords) > srcWords * 0.1) {
      mismatches.push({ id: source.id, issue: `Word count: ${srcWords} vs ${impWords}` });
    }
  }

  return { sourceCount: sourceTranscripts.length, importedCount: sourceTranscripts.length - missing.length, matchRate: (sourceTranscripts.length - missing.length) / sourceTranscripts.length, missing, mismatches };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
