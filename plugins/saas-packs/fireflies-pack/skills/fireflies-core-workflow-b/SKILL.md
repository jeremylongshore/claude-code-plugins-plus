---
name: fireflies-core-workflow-b
description: |
  Search across Fireflies.ai transcripts, use AskFred AI, and build meeting analytics.
  Use when searching meeting history, querying Fred AI assistant,
  or aggregating meeting data for reports.
  Trigger with phrases like "fireflies search", "ask fred", "fireflies analytics",
  "search meetings", "fireflies AskFred".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, workflow, search, analytics]

---
# Fireflies.ai Core Workflow B -- Search, AskFred & Analytics

## Overview
Secondary workflow: search across transcripts with keyword and date filters, use AskFred AI for natural language Q&A over meetings, and aggregate meeting analytics for reporting.

## Prerequisites
- Completed `fireflies-install-auth` setup
- Familiarity with `fireflies-core-workflow-a`
- AI credits for AskFred queries (check Fireflies dashboard)

## Instructions

### Step 1: Search Transcripts by Keyword
```typescript
const SEARCH_TRANSCRIPTS = `
  query SearchMeetings(
    $keyword: String,
    $fromDate: DateTime,
    $toDate: DateTime,
    $participants: [String],
    $limit: Int
  ) {
    transcripts(
      keyword: $keyword
      fromDate: $fromDate
      toDate: $toDate
      participants: $participants
      limit: $limit
    ) {
      id title date duration
      organizer_email
      participants
      summary { overview action_items keywords }
    }
  }
`;

// Search for "quarterly review" in the last 30 days
const results = await firefliesQuery(SEARCH_TRANSCRIPTS, {
  keyword: "quarterly review",
  fromDate: new Date(Date.now() - 30 * 86400000).toISOString(),
  limit: 20,
});

console.log(`Found ${results.transcripts.length} matching meetings`);
for (const t of results.transcripts) {
  console.log(`  ${t.title} (${t.date}) - ${t.duration}min`);
}
```

### Step 2: AskFred -- AI Q&A Over a Single Meeting
```typescript
// Create a new AskFred thread tied to a transcript
const CREATE_THREAD = `
  mutation CreateThread($input: CreateAskFredThreadInput!) {
    createAskFredThread(input: $input) {
      id
      title
      messages {
        id
        answer
        suggested_queries
      }
    }
  }
`;

const thread = await firefliesQuery(CREATE_THREAD, {
  input: {
    query: "What were the key decisions made in this meeting?",
    transcript_id: "your-transcript-id",
  },
});

console.log("Fred says:", thread.createAskFredThread.messages[0].answer);
console.log("Suggested follow-ups:", thread.createAskFredThread.messages[0].suggested_queries);
```

### Step 3: AskFred -- Continue a Conversation
```typescript
const CONTINUE_THREAD = `
  mutation ContinueThread($thread_id: String!, $query: String!) {
    continueAskFredThread(thread_id: $thread_id, query: $query) {
      id
      answer
      suggested_queries
    }
  }
`;

const followUp = await firefliesQuery(CONTINUE_THREAD, {
  thread_id: thread.createAskFredThread.id,
  query: "Who is responsible for the action items?",
});

console.log("Follow-up:", followUp.continueAskFredThread.answer);
```

### Step 4: AskFred -- Cross-Meeting Analysis
```typescript
// Query across multiple meetings (no transcript_id = searches all)
const crossMeeting = await firefliesQuery(CREATE_THREAD, {
  input: {
    query: "What topics came up repeatedly across our sprint planning meetings?",
    // filters can narrow scope without tying to a single transcript
  },
});
```

### Step 5: Meeting Analytics Aggregation
```typescript
async function meetingAnalytics(days: number = 30) {
  const since = new Date(Date.now() - days * 86400000).toISOString();

  const data = await firefliesQuery(`
    query Analytics($fromDate: DateTime) {
      transcripts(fromDate: $fromDate, limit: 100) {
        id title date duration
        organizer_email participants
        summary { action_items keywords }
        analytics {
          speakers { name duration word_count questions }
          sentiments { positive_pct negative_pct }
        }
      }
    }
  `, { fromDate: since });

  const meetings = data.transcripts;
  const totalMinutes = meetings.reduce((s: number, m: any) => s + (m.duration || 0), 0);
  const totalActions = meetings.reduce(
    (s: number, m: any) => s + (m.summary?.action_items?.length || 0), 0
  );

  // Top keywords across all meetings
  const keywordCounts: Record<string, number> = {};
  for (const m of meetings) {
    for (const kw of m.summary?.keywords || []) {
      keywordCounts[kw] = (keywordCounts[kw] || 0) + 1;
    }
  }
  const topKeywords = Object.entries(keywordCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  return {
    period: `${days} days`,
    totalMeetings: meetings.length,
    totalHours: (totalMinutes / 60).toFixed(1),
    totalActionItems: totalActions,
    avgDuration: Math.round(totalMinutes / meetings.length),
    topKeywords,
  };
}
```

### Step 6: List and Manage AskFred Threads
```typescript
// List all threads
const threads = await firefliesQuery(`{
  askfred_threads {
    id title transcript_id created_at
  }
}`);

// Delete a thread (cleanup)
await firefliesQuery(`
  mutation DeleteThread($id: String!) {
    deleteAskFredThread(thread_id: $id)
  }
`, { id: "thread-id-to-delete" });
```

## AskFred Credits
AskFred API calls consume AI credits. If you receive `require_ai_credits`, visit the Upgrade section in your Fireflies dashboard to add credits. Budget accordingly for production use.

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `require_ai_credits` | No AI credits remaining | Purchase credits in Fireflies dashboard |
| Empty search results | No matching transcripts | Broaden keyword or date range |
| Thread not found | Invalid thread ID | List threads first to get valid IDs |
| Rate limit 429 | Too many requests | Implement backoff per `fireflies-rate-limits` |

## Output
- Keyword search results across transcript history
- AskFred AI-powered Q&A threads with suggested follow-ups
- Cross-meeting analytics report with keyword trends

## Resources
- [AskFred API Overview](https://docs.fireflies.ai/askfred/overview)
- [Transcripts Query](https://docs.fireflies.ai/graphql-api/query/transcript)

## Next Steps
For common errors, see `fireflies-common-errors`.
