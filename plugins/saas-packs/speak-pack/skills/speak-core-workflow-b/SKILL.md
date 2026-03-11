---
name: speak-core-workflow-b
description: |
  Execute Speak secondary workflow: Pronunciation Training with detailed phoneme analysis.
  Use when implementing pronunciation drills, speech scoring,
  or targeted pronunciation improvement features.
  Trigger with phrases like "speak pronunciation training",
  "speak speech scoring", "secondary speak workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Core Workflow B

## Overview
Secondary workflow for Speak: Detailed pronunciation training with phoneme-level analysis and targeted practice.

## Prerequisites
- Completed `speak-install-auth` setup
- Familiarity with `speak-core-workflow-a`
- Valid API credentials configured
- High-quality audio input capabilities

## Instructions
1. **Complete Workflow Example**
2. **Workflow Comparison**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Detailed phoneme-level scores
- Visual pronunciation guides
- Adaptive practice recommendations
- Progress tracking over time
- Weakness identification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Audio Too Short | Brief recording | Minimum 0.5s audio |
| Background Noise | Poor recording conditions | Prompt for quieter environment |
| Phoneme Not Detected | Unclear speech | Slow down and articulate |
| Model Loading Failed | Network issue | Retry with fallback |

## Resources
- [Speak Pronunciation API](https://developer.speak.com/api/pronunciation)
- [Phoneme Reference](https://developer.speak.com/docs/phonemes)
- [Audio Recording Best Practices](https://developer.speak.com/docs/audio-quality)

## Next Steps
For common errors, see `speak-common-errors`.

## Examples

**Basic usage**: Apply speak core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize speak core workflow b for production environments with multiple constraints and team-specific requirements.