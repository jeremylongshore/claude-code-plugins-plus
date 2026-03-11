---
name: klingai-style-transfer
description: |
  Manage apply artistic styles to Kling AI video generation. Use when creating stylized videos,
  matching brand aesthetics, or artistic effects. Trigger with phrases like 'klingai style',
  'kling ai artistic', 'klingai video style', 'stylize klingai video'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Style Transfer

## Overview

This skill demonstrates applying artistic styles, visual effects, and aesthetic modifications to Kling AI video generation for unique creative outputs.

## Prerequisites

- Kling AI API key configured
- Reference images for style (optional)
- Python 3.8+

## Instructions

Follow these steps for style transfer:

1. **Define Style**: Choose or describe target aesthetic
2. **Prepare Reference**: Gather style reference images
3. **Craft Prompt**: Include style descriptors
4. **Generate Video**: Submit with style parameters
5. **Refine Output**: Iterate on style settings

## Output

Successful execution produces:
- Stylized video content
- Consistent brand aesthetics
- Artistic transformations
- Style variation comparisons

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Styles](https://docs.klingai.com/styles)
- [Color Theory](https://www.colormatters.com/color-and-design/basic-color-theory)
- [Visual Style Guide](https://www.canva.com/learn/visual-identity/)