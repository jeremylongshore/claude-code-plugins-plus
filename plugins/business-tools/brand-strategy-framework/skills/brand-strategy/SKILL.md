---
name: brand-strategy
description: 'A 7-part brand strategy framework for building comprehensive brand foundations.

  Trigger with phrases like "create brand strategy", "build brand brief", "define
  brand positioning",

  "brand messaging", "audience architecture", "brand truth", or "go-to-market brand
  plan". Use when working with brand strategy.

  '
version: 1.0.0
author: Rowan Brooks <rowanbrooks100@github.com>
license: MIT
allowed-tools: Read, Write, Edit, Glob, Grep
tags:
- business
- brand-strategy
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Brand Strategy Framework

A systematic 7-part methodology for building brand foundations — the same process top agencies use with Fortune 500 clients.

## Overview

This skill guides users through a comprehensive brand strategy process, from core identity through measurement. Each phase builds on the previous, creating a cohesive strategic foundation.

Walk the user through each phase sequentially. Ask discovery questions, synthesize their answers, and produce structured outputs for each section before moving to the next.

## The 7-Part Framework

### Phase 1: Brand Truth

The foundation. Define who the brand authentically is before anything else.

**Discovery Questions:**
- What problem does this brand exist to solve?
- What would be lost if this brand disappeared tomorrow?
- What does this brand believe that competitors don't?
- What's the origin story? Why was it created?
- What are the non-negotiable values?

**Output:** A Brand Truth statement (2-3 sentences) capturing the brand's reason for being, core belief, and authentic identity.

---

### Phase 2: Audience Architecture

Define who the brand serves — not demographics, but motivations.

**Discovery Questions:**
- Who benefits most from what this brand offers?
- What are they trying to achieve or avoid?
- What do they currently believe about this category?
- What would make them switch from their current solution?
- Who is explicitly NOT the target?

**Output:** 2-4 audience personas, each with:
- Name/archetype
- Core motivation (what they want)
- Current belief (what they think now)
- Tension point (what's holding them back)
- Success state (what winning looks like for them)

---

### Phase 3: Cultural Context

Position the brand within the broader landscape.

**Discovery Questions:**
- What's happening in culture that makes this brand relevant now?
- Who are the real competitors (including non-obvious ones)?
- What category conventions should be challenged?
- What cultural tension does this brand resolve?
- Where is the white space?

**Output:** A positioning statement that captures competitive differentiation and cultural relevance. Include a simple competitive landscape map.

---

### Phase 4: Messaging Framework

Translate strategy into language.

**Discovery Questions:**
- What's the one thing people should remember?
- What proof points support the core claim?
- What objections need to be overcome?
- What emotional territory does the brand own?
- What words should never be used?

**Output:** A messaging framework including:
- Core message (1 sentence)
- Supporting messages (3-5 proof points)
- Tone attributes (3-5 adjectives with definitions)
- Language do's and don'ts

---

### Phase 5: Visual Language

Define the principles (not the executions) for visual identity.

**Discovery Questions:**
- What should people feel when they see the brand?
- What visual references resonate with the brand truth?
- What does the category typically look like — and how should this differ?
- What's the balance of minimal vs. expressive?
- What elements are sacred vs. flexible?

**Output:** Visual principles document including:
- Mood/feeling descriptors
- Reference directions (with rationale)
- Typography philosophy
- Color meaning/intent
- Photography/illustration approach
- What to avoid

---

### Phase 6: Channel Strategy

Define where and how the brand shows up.

**Discovery Questions:**
- Where does the audience already spend attention?
- What channels align with the brand personality?
- What's the role of each channel (awareness, conversion, retention)?
- What channels should be deprioritized or avoided?
- What's the owned vs. earned vs. paid balance?

**Output:** Channel matrix with:
- Priority channels (ranked)
- Role of each channel
- Content themes per channel
- Frequency/cadence guidelines
- Channel-specific tone adjustments

---

### Phase 7: Measurement Framework

Define what success looks like.

**Discovery Questions:**
- What business outcomes matter most?
- What leading indicators predict those outcomes?
- What's the current baseline?
- What's a realistic 6/12/24 month target?
- What will you NOT measure (to stay focused)?

**Output:** Measurement dashboard including:
- North star metric
- 3-5 supporting KPIs
- Tracking cadence
- Baseline and targets
- What's explicitly out of scope

---

## Workflow Guidelines

1. **Sequential, not parallel**: Complete each phase before moving to the next
2. **Discovery before prescription**: Always ask questions before providing recommendations
3. **Synthesize, don't summarize**: Transform user inputs into strategic outputs
4. **Challenge assumptions**: Push back on generic or undifferentiated answers
5. **Document as you go**: Produce a clear output artifact for each phase

## Final Deliverable

After completing all 7 phases, compile a Brand Strategy Document containing:

1. Executive Summary (1 page)
2. Brand Truth
3. Audience Architecture
4. Cultural Context & Positioning
5. Messaging Framework
6. Visual Language Principles
7. Channel Strategy
8. Measurement Framework

Format as a professional strategy document suitable for stakeholder presentation.

## Examples

**User:** "Help me create a brand strategy for my new coffee subscription service"
→ Begin with Phase 1 (Brand Truth) discovery questions

**User:** "I need to define our target audience"
→ Jump to Phase 2 (Audience Architecture) but note that Brand Truth should come first if not already defined

**User:** "Can you write our brand messaging?"
→ Jump to Phase 4 (Messaging Framework) but confirm Phases 1-3 are complete or gather that context first

**User:** "Review my brand strategy"
→ Evaluate against the 7-part framework, identify gaps, suggest improvements

## Prerequisites

- Access to the branding environment or API
- Required CLI tools installed and authenticated
- Familiarity with branding concepts and terminology

## Instructions

1. Assess the current state of the branding configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with branding |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Resources

- Official branding documentation
- Community best practices and patterns
- Related skills in this plugin pack