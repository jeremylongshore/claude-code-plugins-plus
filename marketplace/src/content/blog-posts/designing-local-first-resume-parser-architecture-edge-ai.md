---
title: "Designing a Local-First Resume Parser: Architecture Decisions for Edge AI"
description: "Documenting the architecture decisions for Resume Realtime - a planned Chrome extension for local resume parsing. This post covers the technical choices made before writing production code."
date: "2025-12-11"
tags: ["rust", "leptos", "wasm", "webgpu", "ai", "architecture", "planning"]
featured: false
---
## The Problem I Want to Solve

Recruiters pay $0.05-$0.20 per document to cloud parsing services like DaXtra, RChilli, and Affinda. Beyond cost, there's a privacy issue: candidate data leaves the device and travels to vendor servers.

I want to explore whether browser-based AI can eliminate both problems.

## Project Status: Planning Complete, Build Starting

I've completed the architecture planning phase:

- PRD defining MVP scope
- 6 Architecture Decision Records (ADRs)
- 89-task implementation plan across 8 weeks

No production code yet. This post documents the *planned* architecture, not a working system.

## Planned Technical Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| UI Framework | Leptos 0.6 (Rust) | SSR + hydration, single-language codebase |
| Inference | transformers.js + Phi-3-mini | WebGPU acceleration, browser-native |
| PDF Extraction | pdf.js | Mozilla-maintained, client-side |
| Storage | IndexedDB + SubtleCrypto | AES-256-GCM encryption at rest |
| Extension | Manifest V3 | Chrome Web Store requirement |

## Key Architecture Decisions

### ADR-001: Leptos Over React

**Decision:** Use Leptos with SSR + hydration for the extension UI.

**Tradeoffs:**

- Pro: Single Rust codebase (UI + inference bridge + storage)
- Pro: Direct WASM memory access, no serialization overhead
- Con: ~500KB bundle vs ~100KB React
- Con: Smaller ecosystem, fewer examples

I'm betting that unified language benefits outweigh ecosystem maturity for this use case.

### ADR-002: transformers.js + Phi-3-mini

**Decision:** Use transformers.js with Phi-3-mini q4 (~1.5GB quantized).

**Why Phi-3:**

- Optimized for instruction following
- 1.3B parameters fits browser cache
- WebGPU support in transformers.js

**Risk:** 1.5GB initial download. First-time UX will require patience.

### ADR-006: WebGPU Primary, WASM Fallback

**Detection logic:**

```typescript
async function selectBackend(): Promise<'webgpu' | 'wasm'> {
  if (navigator.gpu) {
    const adapter = await navigator.gpu.requestAdapter();
    if (adapter) return 'webgpu';
  }
  return 'wasm';
}
```

**Expected performance:**

- WebGPU: Target < 5s parse latency
- WASM SIMD: Target < 30s parse latency

These are targets, not measurements. Actual performance unknown until implementation.

## MVP Scope

What I'm planning to build first:

- PDF drag-drop upload
- Client-side text extraction
- Local LLM inference with confidence scores
- Human-in-the-loop field correction
- Encrypted local storage
- JSON export

**Not in MVP:** LinkedIn overlays, ATS integration, team features.

## Open Questions

| Question | Status |
|----------|--------|
| Phi-3 vs Llama-3.2-1B accuracy | Need to benchmark |
| Safari fallback strategy | CPU-only, need to test UX |
| Actual parse latency | Unknown until built |

## Next Steps

Week 1: Extension scaffold with Leptos popup rendering. I'll document what actually works vs. what was planned.

*Documenting the build at Intent Solutions. jeremy@intentsolutions.io*
