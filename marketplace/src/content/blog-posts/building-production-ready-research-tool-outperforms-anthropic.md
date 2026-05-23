---
title: "How I Built a Production-Ready Research Tool That Outperforms Anthropic's Solution"
description: "How I Built a Production-Ready Research Tool That Outperforms Anthropic's Solution"
date: "2025-10-20"
tags: ["typescript", "mcp", "open-source", "product-development", "api-design"]
featured: false
---
On October 20, 2025, Anthropic announced Claude for Life Sciences - a suite of research tools for scientific literature. That same evening, I built something better: a production-ready PubMed research toolkit with 10 MCP tools, comprehensive test coverage, and zero security vulnerabilities.

This is how I approached the problem, the critical decisions I made, and why simpler solutions often win.

## The Challenge: Build Better, Not Compete

When I saw Anthropic's announcement, I didn't think about competition. I thought about **user value**:

- What do researchers actually need?
- What's missing from existing solutions?
- How can we make it better while keeping it simple?

The answer: **Build a complete toolkit that users can actually own and customize.**

## Problem-Solving Under Constraint

The first major challenge was technical: I needed to use Vertex AI Gemini 2.0 Flash for code generation, but **it was trained before the Model Context Protocol existed**.

### The Wrong Approach

My initial attempt assumed the AI understood MCP. Result: Incomplete code, missing critical components, failed implementation.

### The Right Approach

I created a 480-line context document explaining:

- What MCP is and how it works
- Complete JSON-RPC 2.0 protocol specification
- TypeScript implementation patterns
- Working examples with full code

**Lesson: When working with constraints, invest time in setup to save time in execution.**

Second attempt with comprehensive context: Complete success.

## Critical Design Decision: Simplicity vs. Features

The AI-generated code included SQLite caching - impressive, feature-rich, complex.

Then came user feedback: "What's the SQLite database have to do with anything?"

This triggered a decision matrix:

| Option | Pros | Cons |
|--------|------|------|
| **Keep SQLite** | Offline caching, comprehensive features | Complex setup, more dependencies, harder to maintain |
| **Remove SQLite** | Simple, clean, easy to understand | No offline access by default |

I chose simplicity. Here's the business reasoning:

1. **Free version should be simple** - Lower barrier to entry
2. **Premium upgrades for complexity** - Monetization path
3. **User ownership** - They can add features themselves (open source)

This decision reduced dependencies from 5 packages to 3, eliminated database management, and created a clear product differentiation strategy.

## Technical Architecture: 10 Specialized Tools

Rather than one monolithic tool, I designed a modular system:

### Research Discovery (Tools 1-4)

- Advanced search with filters
- Article metadata retrieval
- Full-text access (when available)
- Medical subject heading taxonomy

### Network Expansion (Tools 5-7)

- Citation network mapping
- Multiple export formats (BibTeX/RIS/EndNote)
- Publication trend analysis

### Analysis & Comparison (Tools 8-10)

- Side-by-side study comparison
- MeSH term extraction
- Advanced Boolean queries

Each tool has a single, well-defined purpose. No feature creep.

## Quality Assurance: Test-Driven Validation

I built 16 comprehensive tests covering:

1. **Server initialization** - Proper startup and configuration
2. **Tool registration** - All 10 tools available
3. **Rate limiting** - Actual timing tests with NCBI compliance
4. **Input validation** - Parameter checking and error handling
5. **Error scenarios** - Network failures, invalid inputs, API limits

**Result: 16/16 tests passing, 0 security vulnerabilities, 0 TypeScript errors.**

This wasn't about checking boxes - it was about **confidence in deployment**.

## Compliance & Best Practices

NCBI E-utilities has strict rate limits:

- 3 requests/second without API key
- 10 requests/second with API key

I implemented automatic enforcement with proper timing logic:

```typescript
private async enforceRateLimit() {
  const now = Date.now();
  const timeSinceLastRequest = now - this.lastRequestTime;

  if (this.apiKey) {
    // 10 req/s = 100ms minimum delay
    if (timeSinceLastRequest < 100) {
      await new Promise(resolve =>
        setTimeout(resolve, 100 - timeSinceLastRequest)
      );
    }
  } else {
    // 3 req/s = track counter within 1-second window
    if (this.requestCounter >= 3 && timeSinceLastRequest < 1000) {
      await new Promise(resolve =>
        setTimeout(resolve, 1000 - timeSinceLastRequest)
      );
    }
    this.requestCounter = (timeSinceLastRequest < 1000)
      ? this.requestCounter + 1 : 1;
  }

  this.lastRequestTime = Date.now();
}
```

Every API call goes through rate limiting. No exceptions. **Compliance isn't optional.**

## Intelligent Automation: The 9.6 KB Agent Skill

While Anthropic uses 500-byte Agent Skills, I built a 9,600-byte Literature Review Automator (17x larger) that runs complete research workflows automatically.

When a user says "Review the literature on X," it:

1. **Constructs optimized queries** - Analyzes topic, identifies synonyms
2. **Retrieves comprehensive data** - Articles, abstracts, metadata
3. **Analyzes patterns** - Trends, key researchers, citation networks
4. **Synthesizes findings** - Themed grouping, structured summaries

This isn't just bigger - it's **systematically better** because it guides Claude through a proven research methodology.

## Product Positioning: Better Than Anthropic

I'm not claiming superiority out of ego. Here's the objective comparison:

| Metric | Anthropic | My Solution | Advantage |
|--------|-----------|-------------|-----------|
| Cost | Paid tier | Free (MIT) | 100% savings |
| Tools | 1 basic tool | 10 specialized tools | 10x functionality |
| Agent Skills | 500 bytes | 9,600 bytes | 17x more guidance |
| Customization | Proprietary | Open source | Full control |
| Data Privacy | Cloud-hosted | Self-hosted | User ownership |

**This isn't competition - it's a different product philosophy.**

## Execution Timeline: 4 Hours

- **Hour 1**: Research Anthropic's announcement, identify gaps
- **Hour 2**: Create comprehensive AI context, first generation attempt (failed)
- **Hour 3**: Refine context, second attempt (success), implement simplifications
- **Hour 4**: Build test suite, validate functionality, deploy to marketplace

**From concept to production in one evening.**

## What This Demonstrates

### Technical Skills

- TypeScript/Node.js development
- API integration and rate limiting
- Test-driven development
- MCP protocol implementation

### Product Skills

- User-centered design decisions
- Feature prioritization (simplicity over complexity)
- Competitive analysis and differentiation
- Open-source business models

### Process Skills

- Rapid prototyping under constraints
- Iterative problem-solving
- Quality assurance practices
- Documentation and deployment

## Try It Yourself

The plugin is live in the Claude Code marketplace:

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install pubmed-research-master@claude-code-plugins-plus
```

Or just ask Claude: "Review the literature on CRISPR gene editing"

## The Source Code

Everything is open source:

- Repository: https://github.com/jeremylongshore/claude-code-plugins
- Plugin directory: `/plugins/life-sciences/pubmed-research-master/`
- Full test suite included
- MIT License

Fork it. Examine it. Learn from it.

## Related Work

- [Building Multi-Platform Developer Tools](https://jeremylongshore.com/posts/building-multi-platform-developer-tools/) - My approach to cross-platform development
- [Automating Developer Workflows: Custom AI Commands](https://jeremylongshore.com/posts/automating-developer-workflows-custom-ai-commands/) - How I build development automation

---

**Building better solutions means understanding user needs, making thoughtful trade-offs, and executing with quality. This project demonstrates all three.**
