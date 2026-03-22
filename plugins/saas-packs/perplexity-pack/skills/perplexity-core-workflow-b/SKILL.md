---
name: perplexity-core-workflow-b
description: |
  Execute Perplexity multi-turn research sessions and batch query pipelines.
  Use when conducting in-depth investigations, generating research briefs,
  or processing multiple related search queries.
  Trigger with phrases like "perplexity research", "perplexity batch search",
  "multi-query perplexity", "perplexity deep dive", "perplexity report".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, workflow]

---
# Perplexity Core Workflow B: Multi-Query Research

## Overview
Multi-turn research workflow using Perplexity Sonar API. Decomposes a broad topic into focused sub-queries, runs them with context continuity, deduplicates citations, and synthesizes a structured research document. Use `sonar` for fast passes and `sonar-pro` for deep dives.

## Prerequisites
- Completed `perplexity-install-auth` setup
- Familiarity with `perplexity-core-workflow-a`
- `PERPLEXITY_API_KEY` set

## Instructions

### Step 1: Conversational Research Session
```typescript
import OpenAI from "openai";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});

type Message = OpenAI.ChatCompletionMessageParam;

class ResearchSession {
  private messages: Message[] = [];
  private allCitations: Set<string> = new Set();

  constructor(systemPrompt: string = "You are a research assistant. Provide thorough, cited answers.") {
    this.messages.push({ role: "system", content: systemPrompt });
  }

  async ask(question: string, model: "sonar" | "sonar-pro" = "sonar"): Promise<{
    answer: string;
    citations: string[];
  }> {
    this.messages.push({ role: "user", content: question });

    const response = await perplexity.chat.completions.create({
      model,
      messages: this.messages,
    } as any);

    const answer = response.choices[0].message.content || "";
    const citations = (response as any).citations || [];

    // Maintain conversation context
    this.messages.push({ role: "assistant", content: answer });

    // Accumulate all citations across the session
    citations.forEach((url: string) => this.allCitations.add(url));

    return { answer, citations };
  }

  getAllCitations(): string[] {
    return [...this.allCitations];
  }

  // Keep context manageable (Perplexity searches per turn)
  trimHistory(keepLast: number = 6) {
    const system = this.messages[0];
    const recent = this.messages.slice(-(keepLast * 2));
    this.messages = [system, ...recent];
  }
}
```

### Step 2: Batch Query Pipeline
```typescript
interface ResearchPlan {
  topic: string;
  questions: string[];
}

interface ResearchReport {
  topic: string;
  sections: Array<{ question: string; answer: string; citations: string[] }>;
  allCitations: string[];
  totalTokens: number;
}

async function conductResearch(plan: ResearchPlan): Promise<ResearchReport> {
  const sections: ResearchReport["sections"] = [];
  const allCitations = new Set<string>();
  let totalTokens = 0;

  for (const question of plan.questions) {
    const response = await perplexity.chat.completions.create({
      model: "sonar-pro",  // deeper research for each sub-question
      messages: [
        { role: "system", content: `Research context: ${plan.topic}` },
        { role: "user", content: question },
      ],
    } as any);

    const answer = response.choices[0].message.content || "";
    const citations = (response as any).citations || [];

    sections.push({ question, answer, citations });
    citations.forEach((url: string) => allCitations.add(url));
    totalTokens += response.usage?.total_tokens || 0;

    // Rate limit protection: 50 RPM for most tiers
    await new Promise((r) => setTimeout(r, 1500));
  }

  return {
    topic: plan.topic,
    sections,
    allCitations: [...allCitations],
    totalTokens,
  };
}
```

### Step 3: Topic Decomposition
```typescript
async function decomposeTopic(topic: string): Promise<string[]> {
  const response = await perplexity.chat.completions.create({
    model: "sonar",
    messages: [
      {
        role: "system",
        content: "Break this research topic into 4-6 specific, focused questions. Return one question per line, no numbering.",
      },
      { role: "user", content: topic },
    ],
    max_tokens: 500,
  });

  return (response.choices[0].message.content || "")
    .split("\n")
    .map((q) => q.trim())
    .filter((q) => q.length > 10);
}
```

### Step 4: Compile Research Report
```typescript
function compileReport(report: ResearchReport): string {
  let md = `# Research: ${report.topic}\n\n`;

  for (const section of report.sections) {
    md += `## ${section.question}\n\n`;
    md += `${section.answer}\n\n`;
  }

  md += `## Bibliography\n\n`;
  report.allCitations.forEach((url, i) => {
    md += `${i + 1}. ${url}\n`;
  });

  md += `\n---\n`;
  md += `*${report.sections.length} queries | ${report.allCitations.length} unique sources | ${report.totalTokens} tokens*\n`;

  return md;
}
```

### Step 5: Full Pipeline
```typescript
async function researchTopic(topic: string): Promise<string> {
  console.log(`Decomposing: ${topic}`);
  const questions = await decomposeTopic(topic);
  console.log(`Generated ${questions.length} sub-questions`);

  const report = await conductResearch({ topic, questions });
  console.log(`Found ${report.allCitations.length} unique sources`);

  return compileReport(report);
}

// Usage
const markdown = await researchTopic("Impact of AI on drug discovery in 2025");
console.log(markdown);
```

### Step 6: Python Multi-Query Research
```python
import asyncio, os
from openai import OpenAI

client = OpenAI(api_key=os.environ["PERPLEXITY_API_KEY"], base_url="https://api.perplexity.ai")

def research_topic(topic: str, questions: list[str]) -> dict:
    sections = []
    all_citations = set()

    for q in questions:
        r = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": f"Research context: {topic}"},
                {"role": "user", "content": q},
            ],
        )
        raw = r.model_dump()
        citations = raw.get("citations", [])
        sections.append({"question": q, "answer": r.choices[0].message.content, "citations": citations})
        all_citations.update(citations)

    return {"topic": topic, "sections": sections, "citations": list(all_citations)}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Batch queries too fast | Add 1-2s delay between queries |
| Context overflow | Too many conversation turns | Call `trimHistory()` to keep last 6 turns |
| Contradictory answers | Different sources disagree | Flag contradictions for manual review |
| High cost | Using sonar-pro for all queries | Use sonar for decomposition, sonar-pro for deep dives |

## Output
- Structured research document with multiple sections
- Consolidated bibliography of all cited sources
- Token usage for cost tracking
- Conversation session with context continuity

## Resources
- [Perplexity API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)
- [Model Selection Guide](https://docs.perplexity.ai/getting-started/models)

## Next Steps
For common errors, see `perplexity-common-errors`.
