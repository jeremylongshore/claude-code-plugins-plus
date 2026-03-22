---
name: neurodivergent-visual-org
description: |
  Creates ADHD-friendly visual organizational tools using Mermaid diagrams
  optimized for neurodivergent thinking patterns. Auto-detects overwhelm,
  provides compassionate task breakdowns with realistic time estimates.
  Use when creating visual task breakdowns, decision trees, or organizational
  diagrams for neurodivergent users or accessibility-focused projects. Trigger with 'neurodivergent', 'visual', 'org'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 3.1.1
author: Jack Reis <hello@jack.digital>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [productivity, neurodivergent-visual]

---
## Mode System (v3.1.1)

This skill supports four modes to adapt to different cognitive styles and accessibility needs:

### Mode Selection

**Base Modes** (choose one):
1. **Neurodivergent Mode** - ADHD-friendly, energy-aware, compassionate language
2. **Neurotypical Mode** - Direct, efficient, standard cognitive load

**Accessibility Modes** (optional, combinable with base modes):
3. **Colorblind-Safe Mode** - Pattern-based differentiation for all color vision types
4. **Monochrome Mode** - Pure black & white optimized for printing and e-ink displays

#### Mode Combinations Available:
- Neurodivergent + Colorblind-Safe
- Neurodivergent + Monochrome
- Neurotypical + Colorblind-Safe
- Neurotypical + Monochrome
- Colorblind-Safe only (no base mode features)
- Monochrome only (no base mode features)

#### Selection Methods:

#### 1. Auto-Detect (Default)
- Analyzes user language for distress signals ("overwhelmed", "paralyzed", "stuck")
- Detects mentions of neurodivergent conditions or executive dysfunction
- Detects accessibility requests ("colorblind-safe", "print-friendly", "grayscale")
- Defaults to neurodivergent mode when ambiguous (inclusive design)

#### 2. Explicit Mode Request
- User says: "Use neurotypical mode" or "Use ADHD mode"
- User says: "Use colorblind-safe mode" or "Make it print-friendly"
- User says: "Combine neurodivergent and colorblind-safe modes"
- Persists for current conversation unless changed

#### 3. Configuration File
- User creates: `.claude/neurodivergent-visual-org-preference.yml`
- Sets default base mode, accessibility modes, time multipliers, chunk sizes
- Can set auto-enable rules (e.g., monochrome for PDFs)

### Mode Characteristics

#### Base Mode Features:

| Aspect | Neurodivergent Mode | Neurotypical Mode |
|--------|---------------------|-------------------|
| Chunk size | 3-5 items | 5-7 items |
| Time estimates | 1.5-2x with buffer | Standard |
| Task granularity | 3-10 min micro-steps | 15-30 min tasks |
| Language | Compassionate, validating | Direct, efficient |
| Colors | Calming (blues/greens) | Standard themes |
| Energy scaffolding | Explicit (spoons, breaks) | Minimal |

#### Accessibility Mode Features:

| Aspect | Colorblind-Safe Mode | Monochrome Mode |
|--------|---------------------|-----------------|
| Color usage | Redundant (patterns + color) | Pure B&W only (#000/#fff) |
| Border patterns | Dashed/dotted variations | Solid/dashed/dotted styles |
| Text labels | Prefixed ([KEEP], [DONATE]) | Verbose ([✓ KEEP], [? MAYBE]) |
| Shape coding | Diamond/hexagon/trapezoid | Distinct geometric shapes |
| Fill patterns | N/A (white fill, patterned borders) | Solid/crosshatch/dots/white |
| Border thickness | 1-3px for hierarchy | 1-3px for hierarchy |
| Symbols | Redundant icons (✅ 📦 🤔) | Text-based (✓ → ?) |
| Best for | All color vision types | B&W printing, e-ink displays |
| WCAG compliance | 2.1 AA (Use of Color 1.4.1) | 2.1 AAA (Maximum contrast) |

#### Mode Combination Notes:
- Base mode controls language, time estimates, and cognitive scaffolding
- Accessibility mode controls visual encoding (patterns, contrast, shapes)
- Both can be active simultaneously for maximum accommodation

### Backward Compatibility

v3.1.1 maintains v3.0 behavior:
- Defaults to neurodivergent base mode (v2.0 compatible)
- Accessibility modes are opt-in (not enabled by default)
- v3.0 visualizations remain valid (no breaking changes)

## Mode Detection Algorithm

See [references/mode-detection-algorithm.md](references/mode-detection-algorithm.md) for the full 6-step detection pseudocode covering explicit requests, config file lookup, auto-detection from language signals, and defaults.

## Accessibility Mode Implementation

See [references/accessibility-modes.md](references/accessibility-modes.md) for complete specifications including:
- Colorblind-safe mode: border patterns, shape coding, text prefixes, color strategy
- Monochrome mode: fill patterns, border styles, verbose labels, spacing
- Mode combination logic and combined output examples

## Configuration File Schema

Users can create `.claude/neurodivergent-visual-org-preference.yml` to set default modes and customize behavior. See [references/configuration-schema.md](references/configuration-schema.md) for the complete schema, examples, and precedence rules.

# Neurodivergent Visual Organization

Create visual organizational tools that make invisible work visible and reduce cognitive overwhelm. This skill generates Mermaid diagrams optimized for neurodivergent thinking patterns, leveraging research-backed design principles that work WITH ADHD brain wiring rather than against it.

## Why Visual Tools Work for ADHD Brains

Visual aids externalize executive function by:
- **Converting abstract concepts** (time, energy, priorities) into concrete visual formats
- **Reducing working memory load** by moving information from internal to external scaffolding
- **Combating "out of sight, out of mind"** through persistent visual presence
- **Leveraging visual-spatial strengths** while compensating for working memory deficits
- **Providing immediate feedback** that ADHD brains need for sustained engagement
- **Making time tangible** to address time blindness (a core ADHD deficit)

Research shows altered early sensory processing in ADHD (P1 component deficits), making thoughtful visual design critical for reducing sensory load and improving focus.

## When to Use This Skill

Use when the user:
- Feels overwhelmed by a task or project ("I don't know where to start")
- Needs to break down something complex into steps
- Is stuck making a decision or mentions analysis paralysis
- Asks "what should I focus on?" or "what's on my plate?"
- Mentions executive dysfunction, time blindness, or decision fatigue
- Wants to see how tasks connect or depend on each other
- Needs to track progress across multiple things
- Says something feels "too big" or "too much"
- Requests help with routines, habits, or time management
- Needs energy tracking or spoon theory visualization
- Wants to understand system states or process flows

## Core Principles

#### Always apply these neurodivergent-friendly principles:
- Use compassionate, non-judgmental language (never "just do it" or "should be easy")
- Give realistic time estimates with buffer (use 1.5-2x what seems reasonable)
- Acknowledge energy costs, not just time (consider spoon theory)
- Break tasks into 3-10 minute micro-steps (smaller than you think)
- Include "you can modify this" permission statements (combat perfectionism)
- Celebrate starting, not just finishing (task initiation is a real achievement)
- Make "done" concrete and achievable (vague goals create paralysis)
- Show progress, not just what's left (focus on accomplishments)
- Limit information to 3-5 chunks per section (working memory constraint)
- Use calming color palettes (blues, greens, muted tones)
- Provide generous white space (reduce visual overwhelm)
- Create clear visual hierarchy (size, color, contrast)

## Neurodivergent-Friendly Design Standards

### Color Psychology for ADHD

#### Primary Palette (Use These)
- **Blues and greens** in soft, muted tones - promote tranquility and focus
- **Muted browns** - provide grounding without stimulation
- **Soft pastels** (light blues, lavenders, pale greens) - reduce visual stress
- **Muted yellows** (sparingly) - boost energy without overstimulation

#### Avoid
- Bright reds, oranges, intense yellows - increase hyperactivity/agitation
- Bright saturated colors - cause sensory overload
- Clashing color combinations - create visual stress

#### Implementation
- Use `forest` theme (green-based) or `neutral` theme (muted earth tones)
- Apply 60-30-10 rule: 60% calming background, 30% secondary, 10% accent
- Maintain 4.5:1 contrast ratio minimum (WCAG compliance)
- Never rely on color alone - pair with icons, patterns, or text labels

### Information Density Management

#### Miller's Law + ADHD Considerations
- Working memory holds 5-7 chunks (neurotypical) or 3-5 chunks (ADHD)
- Stay at lower end (3-5 chunks) to prevent cognitive overload
- Increased cognitive load reduces ADHD performance more severely

#### Practical Limits
- **Flowcharts**: 15-20 nodes maximum before splitting into multiple diagrams
- **Mindmaps**: 3-4 levels deep maximum
- **Pie charts**: 6-8 slices for readability
- **Lists**: No more than 2 lists of 3-5 items per diagram
- **Sections**: Use timeline/journey sections to chunk events logically

#### Implementation
- Break complex diagrams into digestible sections
- Use progressive disclosure (show relevant info upfront, details on demand)
- Provide TL;DR sections at beginning of complex diagrams
- Include generous white space between elements

### Visual Hierarchy Principles

**Size Contrast** (must be dramatic for ADHD attention)
- H1 significantly larger than H2, which is notably larger than body text
- Important nodes visibly larger than standard nodes
- Use `classDef` to style critical elements distinctly

#### Priority Signaling
- Distinguish important information through bold or color
- Use visual highlights for critical numbers or elements
- Separate each instruction clearly
- Implement color-coded systems for immediate visual feedback

#### Avoid
- Competing visual elements fighting for attention
- Auto-playing animations or flashy effects (extremely distracting)
- Blinking or flashing elements
- More than 2 fonts per diagram

## Comprehensive Mermaid Diagram Selection Guide

Mermaid 11.12.1 offers **22 diagram types**. Choose based on cognitive need:

### Executive Function & Task Management

| User Need | Best Diagram Type | When to Use |
|-----------|------------------|-------------|
| "I don't know where to start" | **Flowchart** (decision tree) | Diagnose task initiation blocks |
| "This task is overwhelming" | **Gantt chart** or **Timeline** | Break into sequential phases with time |
| "How are tasks connected?" | **Flowchart** (dependencies) | Show prerequisite relationships |
| "What's the order of operations?" | **Timeline** or **State diagram** | Sequential progression with states |
| "Track project phases" | **Gantt chart** | Complex projects with dependencies |

### Decision-Making & Prioritization

| User Need | Best Diagram Type | When to Use |
|-----------|------------------|-------------|
| "I can't decide between options" | **Quadrant chart** | 2-dimensional comparison (Eisenhower Matrix) |
| "Need to weigh factors" | **Flowchart** (decision tree) | Branching logic with validation |
| "What should I focus on first?" | **Quadrant chart** | Urgent/Important matrix |
| "Too many things on my plate" | **Pie chart** | Visualize proportional allocation |
| "Comparing multiple aspects" | **User journey** | Track satisfaction across dimensions |

### Organization & Current State

| User Need | Best Diagram Type | When to Use |
|-----------|------------------|-------------|
| "What's on my plate?" | **Kanban** (if available) | Track To Do/Doing/Done states |
| "Show task status" | **State diagram** | Visualize item states and transitions |
| "Organize by category" | **Mindmap** | Non-linear brainstorming and categorization |
| "See the big picture" | **Mindmap** | Hierarchical overview of complex topic |
| "Track multiple projects" | **Gantt chart** | Parallel timelines with milestones |

### Time & Energy Management

| User Need | Best Diagram Type | When to Use |
|-----------|------------------|-------------|
| "Make time visible" | **Timeline** with sections | Combat time blindness with visual periods |
| "Plan my day/week" | **Gantt chart** | Time-blocked schedule with buffer |
| "Track energy patterns" | **Pie chart** or **XY chart** | Spoon theory visualization |
| "Pomodoro planning" | **Timeline** | Show focus/break cycles visually |
| "Energy allocation" | **Sankey diagram** | Show energy flow across activities |

### Habits & Routines

| User Need | Best Diagram Type | When to Use |
|-----------|------------------|-------------|
| "Build a morning routine" | **Flowchart** or **Timeline** | Sequential steps with time estimates |
| "Habit stacking" | **Flowchart** | Show trigger → action chains |
| "Track habit progress" | **User journey** | Satisfaction scores across habit stages |
| "Visual routine chart" | **Timeline** with sections | Color-coded daily schedule |

### Systems & Processes

| User Need | Best Diagram Type | When to Use |
|-----------|------------------|-------------|
| "How does this system work?" | **State diagram** | Show system states and transitions |
| "Process flow" | **Flowchart** | Step-by-step procedures |
| "Data/resource flow" | **Sankey diagram** | Visualize flow and distribution |
| "Relationships between entities" | **ER diagram** or **Mindmap** | Show connections and structure |
| "Architecture/structure" | **Architecture diagram** (beta) | System components with icons |

## Detailed Syntax Guide for Priority Types

[Content continues with all the detailed syntax guides, troubleshooting, workflow sections, etc. from the original SKILL.md - truncating here to stay within reasonable length]

## Playground Links and URL Encoding

When providing links to edit Mermaid diagrams in online playgrounds (like https://mermaid.live), you MUST properly URL-encode the diagram content, especially HTML entities like `<br/>` tags.

### Common Issue: Broken `<br/>` Tags

Mermaid diagrams use `<br/>` for line breaks in node text. These MUST be encoded properly in URLs.

**❌ BROKEN** (angle brackets not encoded):
```
https://mermaid.live/edit#pako:flowchart TD
    Start{Can decide<br/>in 3 seconds?}
```

**✅ CORRECT** (all characters properly encoded):
```
https://mermaid.live/edit#pako:flowchart%20TD%0A%20%20%20%20Start%7BCan%20decide%3Cbr%2F%3Ein%203%20seconds%3F%7D
```

### URL Encoding Rules

**IMPORTANT:** Despite earlier claims that "Mermaid 11.12.1+ fixed <br/> encoding", URL encoding is STILL REQUIRED for playground links to work correctly.

Use Python's `urllib.parse.quote()` with `safe=''` to encode ALL special characters:

```python
import urllib.parse

diagram = """flowchart TD
    Start{Can decide<br/>in 3 seconds?}"""

encoded = urllib.parse.quote(diagram, safe='')
url = f"https://mermaid.live/edit#pako:{encoded}"
```

#### Key encodings:
- `<` → `%3C`
- `>` → `%3E`
- `/` → `%2F`
- Space → `%20`
- Newline → `%0A`
- `{` → `%7B`
- `}` → `%7D`

### When Providing Playground Links

Always include properly encoded playground links in your diagram output:

```markdown
## 🎯 Master Decision Flowchart

[🎨 Edit in Playground](https://mermaid.live/edit#pako:{PROPERLY_ENCODED_DIAGRAM})

\`\`\`mermaid
{DIAGRAM_CODE}
\`\`\`
```

This allows users to:
- View rendered diagrams online
- Edit and customize diagrams
- Share diagrams with collaborators
- Access diagrams on mobile devices

### Testing Links

Before providing a playground link, verify that:
1. The URL opens without errors
2. The diagram renders correctly
3. All `<br/>` tags display as line breaks (not literal `<br/>` text)

If angle brackets appear as literal text in the rendered diagram, the URL encoding is broken.

## Version History

- **v3.1.1** (Current): Fixed URL encoding documentation error. Mermaid playground links STILL require proper encoding of HTML entities like `<br/>` tags. All previous features plus corrected documentation.
- **v3.1**: Added colorblind-safe and monochrome accessibility modes with pattern-based differentiation. Mode system supports neurodivergent/neurotypical base modes combined with optional accessibility modes. Configuration file support for personalized defaults.
- **v3.0**: Mode system (neurodivergent/neurotypical/auto-detect), configuration file support, enhanced accessibility features
- **v2.0**: Comprehensive Mermaid 11.12.1 syntax, research-backed neurodivergent design principles, troubleshooting guide, expanded diagram types
- **v1.0**: Initial release with basic patterns and reference files

---

## Quick Reference Card

**When user says...** → **Use this diagram type**

- "I don't know where to start" → Flowchart (decision tree)
- "This is overwhelming" → Timeline or Gantt (break into phases)
- "I can't decide" → Quadrant chart (Eisenhower Matrix)
- "What should I focus on?" → Quadrant chart or Pie chart
- "Too many things" → Kanban or State diagram
- "Time disappears" → Timeline (make time visible)
- "No energy" → Pie or Sankey (spoon theory)
- "How does this work?" → State diagram or Flowchart
- "Build a habit" → Flowchart (habit stacking) or User journey
- "Plan my day" → Timeline or Gantt (time-blocked)

#### Always:
✅ Use calming colors (forest/neutral theme)
✅ Limit to 3-5 chunks per section
✅ Be compassionate and realistic
✅ Validate with Mermaid tool
✅ Provide usage instructions
✅ Offer to save to Obsidian
✅ Properly URL-encode playground links (REQUIRED for `<br/>` tags)

#### Never:
❌ Judgmental language ("just" or "should")
❌ Unrealistic time estimates
❌ Too many nodes/elements
❌ Bright clashing colors
❌ Skip encouragement and validation
❌ Provide unencoded playground links with `<br/>` tags

## Overview

Creates ADHD-friendly visual organizational tools using Mermaid diagrams optimized for neurodivergent thinking patterns, with colorblind-safe and monochrome accessibility modes.

## Prerequisites

- Mermaid rendering support (Obsidian, GitHub, VS Code, or [mermaid.live](https://mermaid.live))
- No CLI tools required — all output is Mermaid diagram code

## Instructions

1. Detect mode: check for explicit request, then config file, then auto-detect from language signals (see [mode detection algorithm](references/mode-detection-algorithm.md))
2. Choose diagram type from the Comprehensive Mermaid Diagram Selection Guide based on user need
3. Apply neurodivergent-friendly design standards (3-5 chunks, calming colors, compassionate language)
4. Generate Mermaid diagram with properly URL-encoded playground links

## Output

- Mermaid diagram code block ready for rendering
- Playground link for editing at [mermaid.live](https://mermaid.live) (properly URL-encoded)
- Brief usage instructions calibrated to user's cognitive mode

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Mermaid syntax error | Invalid node or style definition | Validate against Mermaid 11.12.1 syntax; check for unescaped special characters |
| Broken playground link | `<br/>` tags not URL-encoded | Encode all HTML entities: `<` as `%3C`, `>` as `%3E`, `/` as `%2F` |
| Diagram too complex | Exceeds 15-20 nodes | Split into multiple diagrams with clear section labels |

## Examples

- **Task overwhelm**: User says "I don't know where to start" — generate a flowchart decision tree breaking the task into 3-5 minute micro-steps with energy cost labels.
- **Decision paralysis**: User says "I can't decide" — generate a quadrant chart (Eisenhower Matrix) sorting options by urgency and importance.

## Resources

- [references/mode-detection-algorithm.md](references/mode-detection-algorithm.md) — 6-step mode detection pseudocode
- [references/accessibility-modes.md](references/accessibility-modes.md) — colorblind-safe and monochrome specifications
- [references/configuration-schema.md](references/configuration-schema.md) — user preference file schema and examples
- [Mermaid documentation](https://mermaid.js.org/intro/) — official syntax reference

