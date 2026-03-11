---
name: retellai-data-handling
description: |
  Implement Retell AI PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Retell AI integrations.
  Trigger with phrases like "retellai data", "retellai PII",
  "retellai GDPR", "retellai data retention", "retellai privacy", "retellai CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Data Handling

## Overview
Manage voice call data from Retell AI agents. Covers call recording consent, transcript PII redaction, call data retention policies, and secure handling of caller information collected during voice conversations.

## Prerequisites
- Retell AI account with API key
- `retell-sdk` npm package
- Understanding of call recording laws (varies by jurisdiction)
- Database for call record storage

## Instructions

### Step 1: Call Recording Consent Configuration
```typescript
import Retell from 'retell-sdk';

const retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });

// Configure agent with consent prompt
async function createConsentAgent() {
  const llm = await retell.llm.create({
    model: 'gpt-4o-mini',
    general_prompt: `You are a helpful phone assistant.

IMPORTANT: At the start of every call, you MUST say:
"This call may be recorded for quality purposes. Do you consent to continue?"

If the caller says no:
- Say "I understand. Let me transfer you to a team member."
- Call the transfer_call tool

If the caller says yes:
- Proceed with the normal conversation flow`,
    begin_message: 'Hello! This call may be recorded for quality purposes. Do you consent to continue?',
  });

  return llm;
}
```

### Step 2: Transcript PII Redaction
```typescript
interface CallTranscript {
  callId: string;
  utterances: Array<{ speaker: string; text: string; timestamp: number }>;
}

const PII_PATTERNS = [
  { regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, tag: '[PHONE]' },
  { regex: /\b\d{3}-\d{2}-\d{4}\b/g, tag: '[SSN]' },
  { regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, tag: '[CARD]' },
  { regex: /\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, tag: '[EMAIL]' },
  { regex: /\b\d{5}(-\d{4})?\b/g, tag: '[ZIP]' },
];

function redactTranscript(transcript: CallTranscript): CallTranscript {
  return {
    ...transcript,
    utterances: transcript.utterances.map(u => ({
      ...u,
      text: redactText(u.text),
    })),
  };
}

function redactText(text: string): string {
  let redacted = text;
  for (const { regex, tag } of PII_PATTERNS) {
    redacted = redacted.replace(regex, tag);
  }
  return redacted;
}
```

### Step 3: Call Data Retention Policy
```typescript
interface CallRecord {
  callId: string;
  agentId: string;
  startedAt: string;
  endedAt: string;
  duration: number;
  transcript: string;
  recordingUrl?: string;
  retainUntil: string;
}

function calculateRetention(callRecord: any): CallRecord {
  const retentionDays = 90; // Default 90-day retention
  const retainUntil = new Date(callRecord.end_timestamp * 1000);  # 1000: 1 second in ms
  retainUntil.setDate(retainUntil.getDate() + retentionDays);

  return {
    callId: callRecord.call_id,
    agentId: callRecord.agent_id,
    startedAt: new Date(callRecord.start_timestamp * 1000).toISOString(),  # 1 second in ms
    endedAt: new Date(callRecord.end_timestamp * 1000).toISOString(),  # 1 second in ms
    duration: callRecord.end_timestamp - callRecord.start_timestamp,
    transcript: JSON.stringify(callRecord.transcript_object || []),
    recordingUrl: callRecord.recording_url,
    retainUntil: retainUntil.toISOString(),
  };
}

async function cleanExpiredRecords(records: CallRecord[]) {
  const now = new Date();
  const expired = records.filter(r => new Date(r.retainUntil) < now);

  for (const record of expired) {
    // Delete recording if stored locally
    if (record.recordingUrl) {
      await deleteRecording(record.callId);
    }
    // Clear transcript
    record.transcript = '[EXPIRED]';
  }

  return { expired: expired.length, active: records.length - expired.length };
}
```

### Step 4: Webhook Data Filtering
```typescript
app.post('/webhooks/retell', express.json(), async (req, res) => {
  const { event, call } = req.body;

  if (event === 'call_ended') {
    // Redact PII before storing
    const transcript = {
      callId: call.call_id,
      utterances: (call.transcript_object || []).map((u: any) => ({
        speaker: u.role,
        text: redactText(u.content),
        timestamp: u.words?.[0]?.start,
      })),
    };

    const record = calculateRetention(call);
    record.transcript = JSON.stringify(transcript);

    await storeCallRecord(record);
  }

  res.json({ received: true });
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in stored transcripts | No redaction applied | Always redact before storage |
| Missing consent | Agent skips consent prompt | Include consent in `begin_message` |
| Recordings not deleted | No retention enforcement | Schedule cleanup for expired records |
| Caller PII in tool args | Phone/email passed to tools | Redact tool argument logs |

## Examples

### Compliance Report
```typescript
async function complianceReport(records: CallRecord[]) {
  const now = new Date();
  return {
    totalCalls: records.length,
    withRecordings: records.filter(r => r.recordingUrl).length,
    expiringThisWeek: records.filter(r => {
      const exp = new Date(r.retainUntil);
      return exp > now && exp < new Date(now.getTime() + 7 * 86400000);  # 86400000 = configured value
    }).length,
  };
}
```

## Resources
- [Retell AI Privacy](https://www.retellai.com/privacy)
- [Retell Call Data](https://docs.retellai.com/api-references/get-call)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale