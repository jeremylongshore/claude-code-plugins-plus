---
name: gamma-core-workflow-a
description: |
  Implement core Gamma workflow for AI presentation generation.
  Use when creating presentations from prompts, documents,
  or structured content with AI assistance.
  Trigger with phrases like "gamma generate presentation", "gamma AI slides",
  "gamma from prompt", "gamma content to slides", "gamma automation".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Core Workflow A: AI Presentation Generation

## Overview
Implement the core workflow for generating presentations using Gamma's AI capabilities from various input sources.

## Prerequisites
- Completed `gamma-sdk-patterns` setup
- Understanding of async patterns
- Content ready for presentation

## Instructions

### Step 1: Prompt-Based Generation
```typescript
import { GammaClient } from '@gamma/sdk';

const gamma = new GammaClient({ apiKey: process.env.GAMMA_API_KEY });

async function generateFromPrompt(topic: string, slides: number = 10) {
  const presentation = await gamma.presentations.generate({
    prompt: topic,
    slideCount: slides,
    style: 'professional',
    includeImages: true,
    includeSpeakerNotes: true,
  });

  return presentation;
}

// Usage
const deck = await generateFromPrompt('Introduction to Machine Learning', 8);
console.log('Generated:', deck.url);
```

### Step 2: Document-Based Generation
```typescript
async function generateFromDocument(filePath: string) {
  const document = await fs.readFile(filePath, 'utf-8');

  const presentation = await gamma.presentations.generate({
    sourceDocument: document,
    sourceType: 'markdown', // or 'pdf', 'docx', 'text'
    extractKeyPoints: true,
    maxSlides: 15,
  });

  return presentation;
}
```

### Step 3: Structured Content Generation
```typescript
interface SlideOutline {
  title: string;
  points: string[];
  imagePrompt?: string;
}

async function generateFromOutline(outline: SlideOutline[]) {
  const presentation = await gamma.presentations.generate({
    slides: outline.map(slide => ({
      title: slide.title,
      content: slide.points.join('\n'),
      generateImage: slide.imagePrompt,
    })),
    style: 'modern',
  });

  return presentation;
}
```

### Step 4: Batch Generation Pipeline
```typescript
async function batchGenerate(topics: string[]) {
  const results = await Promise.allSettled(
    topics.map(topic =>
      gamma.presentations.generate({
        prompt: topic,
        slideCount: 5,
      })
    )
  );

  return results.map((r, i) => ({
    topic: topics[i],
    status: r.status,
    url: r.status === 'fulfilled' ? r.value.url : null,
    error: r.status === 'rejected' ? r.reason.message : null,
  }));
}
```

## Output
- AI-generated presentations from prompts
- Document-to-presentation conversion
- Structured content transformation
- Batch processing capability

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Generation Timeout | Complex prompt | Reduce slide count or simplify |
| Content Too Long | Document exceeds limit | Split into sections |
| Rate Limit | Too many requests | Implement queue system |
| Style Not Found | Invalid style name | Check available styles |

## Resources
- [Gamma AI Generation](https://gamma.app/docs/ai-generation)
- [Prompt Best Practices](https://gamma.app/docs/prompts)

## Next Steps
Proceed to `gamma-core-workflow-b` for presentation editing and export workflows.

## Examples

**Basic usage**: Apply gamma core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma core workflow a for production environments with multiple constraints and team-specific requirements.