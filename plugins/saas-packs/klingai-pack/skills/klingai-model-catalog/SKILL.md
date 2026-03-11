---
name: klingai-model-catalog
description: |
  Build explore Kling AI models and their capabilities for video generation. Use when selecting models
  or understanding features. Trigger with phrases like 'kling ai models', 'klingai capabilities',
  'kling video models', 'klingai features'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Model Catalog

## Overview

This skill provides a comprehensive guide to Kling AI's video generation models, their capabilities, recommended use cases, and how to select the right model for your needs.

## Prerequisites

- Kling AI API key configured
- Understanding of video generation concepts
- Knowledge of your use case requirements

## Instructions

Follow these steps to understand and select Kling AI models:

1. **Review Available Models**: Understand the model options
2. **Compare Capabilities**: Evaluate features vs requirements
3. **Test with Samples**: Try each model with your prompts
4. **Optimize Selection**: Choose based on quality/speed/cost tradeoffs
5. **Monitor Performance**: Track results and adjust as needed

## Output

Successful execution produces:
- List of available models with capabilities
- Model recommendation based on requirements
- Understanding of pricing and tradeoffs

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Models Documentation](https://docs.klingai.com/models)
- [Pricing Calculator](https://klingai.com/pricing)
- [Feature Comparison](https://docs.klingai.com/features)