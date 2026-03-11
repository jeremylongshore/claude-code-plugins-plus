---
name: granola-performance-tuning
description: |
  Optimize Granola transcription quality and note performance.
  Use when improving transcription accuracy, reducing processing time,
  or enhancing note quality.
  Trigger with phrases like "granola performance", "granola accuracy",
  "granola quality", "improve granola", "granola optimization".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Granola Performance Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Granola for best transcription accuracy and note quality through audio setup, meeting practices, and template design.

## Prerequisites
- Working Granola installation
- Active meetings to optimize
- Willingness to invest in audio quality

## Instructions

### Step 1: Optimize Audio Setup
| Factor | Impact | Optimization |
|--------|--------|--------------|
| Background noise | High | Use quiet room, noise cancellation |
| Echo/reverb | High | Soft furnishings, smaller room |
| Distance from mic | Medium | Within 12 inches |
| Multiple speakers | Medium | Use identification phrases |

### Step 2: Improve Meeting Practices
- State names when addressing people
- Summarize decisions verbally
- Spell out technical terms and acronyms
- One person speaking at a time
- Use explicit action item language

### Step 3: Optimize Templates
Use structured templates with headers (AI parses better), pre-filled context, standard action item format (`- [ ] What (@who, by when)`).

### Step 4: Post-Meeting Review (5 min)
- [ ] Correct transcription errors
- [ ] Add context AI missed
- [ ] Verify action items complete
- [ ] Add document links
- [ ] Tag key decisions

### Step 5: Optimize Integrations
Use instant Zapier triggers, batch updates to Notion/CRM, minimize Zap steps.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for microphone recommendations, room checklist, template examples, processing speed expectations, and accuracy improvement techniques.

## Output
- Audio setup optimized for transcription
- Meeting practices improving accuracy
- Templates structured for AI parsing
- Integration latency minimized

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Low accuracy (<85%) | Poor microphone | Upgrade to quality headset or USB mic |
| Missing action items | Unclear language | Use explicit "Action item:" prefix |
| Slow processing | Large meeting | Normal: expect 1 min per 10 min meeting |
| Wrong speaker attribution | Crosstalk | State names, avoid overlapping speech |

## Examples

### Performance Metrics to Track
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Transcription accuracy | >95% | Sample review |
| Action item detection | >90% | Compare to meeting |
| Processing time | <5 min | Timestamp comparison |
| Note usefulness | 4+/5 | Team survey |

## Resources
- [Granola Quality Tips](https://granola.ai/tips)
- [Audio Equipment Guide](https://granola.ai/help/audio)

## Next Steps
Proceed to `granola-cost-tuning` for cost optimization strategies.
