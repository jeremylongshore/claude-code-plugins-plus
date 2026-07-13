# Perplexity Reference Architecture - Implementation Details

## Search Service with Model Routing

```typescript
import OpenAI from 'openai';

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: 'https://api.perplexity.ai',
});

type SearchDepth = 'quick' | 'standard' | 'deep' | 'reasoning';

const MODEL_FOR_DEPTH: Record<SearchDepth, string> = {
  quick: 'sonar', standard: 'sonar', deep: 'sonar-pro', reasoning: 'sonar-reasoning',
};

async function search(query: string, depth: SearchDepth = 'standard') {
  return perplexity.chat.completions.create({
    model: MODEL_FOR_DEPTH[depth],
    messages: [
      { role: 'system', content: 'Provide accurate, well-sourced answers. Include citations.' },
      { role: 'user', content: query },
    ],
    max_tokens: depth === 'quick' ? 512 : 2048,
  });
}
```

## Citation Extraction Pipeline

```typescript
interface Citation { url: string; title?: string; snippet?: string; index: number; }

function extractCitations(responseText: string): Citation[] {
  const citations: Citation[] = [];
  const urlRegex = /\[(\d+)\]\s*(https?:\/\/[^\s\]]+)/g;
  let match;
  while ((match = urlRegex.exec(responseText)) !== null) {
    citations.push({ index: parseInt(match[1]), url: match[2] });
  }
  // Also extract inline URLs not already captured
  const inlineUrls = responseText.match(/https?:\/\/[^\s\])+/g) || [];
  for (const url of inlineUrls) {
    if (!citations.some(c => c.url === url)) {
      citations.push({ url, index: citations.length + 1 });
    }
  }
  return citations;
}

async function searchWithCitations(query: string, depth: SearchDepth = 'standard') {
  const result = await search(query, depth);
  const text = result.choices[0].message.content || '';
  return { answer: text, citations: extractCitations(text), model: MODEL_FOR_DEPTH[depth], usage: result.usage };
}
```

## Multi-Query Research Pipeline

```typescript
async function deepResearch(topic: string) {
  // Phase 1: Broad overview (fast model)
  const overview = await searchWithCitations(`What are the key aspects of ${topic}?`, 'quick');

  // Phase 2: Identify subtopics
  const subtopics = await search(`List 3-5 specific subtopics worth researching about: ${topic}`, 'quick');

  // Phase 3: Deep dive each subtopic
  const details = await Promise.all(
    parseSubtopics(subtopics.choices[0].message.content || '').map(
      sub => searchWithCitations(sub, 'deep')
    )
  );

  return {
    overview, details,
    allCitations: deduplicateCitations([
      ...overview.citations, ...details.flatMap(d => d.citations),
    ]),
  };
}

function deduplicateCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  return citations.filter(c => { if (seen.has(c.url)) return false; seen.add(c.url); return true; });
}
```

## Conversational Research Session

```typescript
class ResearchSession {
  private history: any[] = [];

  async ask(query: string, depth: SearchDepth = 'standard') {
    this.history.push({ role: 'user', content: query });
    const result = await perplexity.chat.completions.create({
      model: MODEL_FOR_DEPTH[depth],
      messages: [
        { role: 'system', content: 'You are a research assistant. Build on previous context.' },
        ...this.history,
      ],
    });
    const answer = result.choices[0].message.content || '';
    this.history.push({ role: 'assistant', content: answer });
    return { answer, citations: extractCitations(answer) };
  }

  reset() { this.history = []; }
}
```

## Fact-Check Service

```typescript
async function factCheck(claim: string) {
  const result = await searchWithCitations(
    `Is this claim accurate? Provide evidence: "${claim}"`, 'deep'
  );
  return { claim, verdict: result.answer, sources: result.citations };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
