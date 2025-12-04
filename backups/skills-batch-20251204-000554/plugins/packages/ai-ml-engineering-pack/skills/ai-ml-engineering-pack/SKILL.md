---
name: optimizing-prompts
description: |
  This skill optimizes prompts for Large Language Models (LLMs) to reduce token usage, lower costs, and improve performance. It analyzes the prompt, identifies areas for simplification and redundancy removal, and rewrites the prompt to be more concise and effective. It is used when the user wants to reduce LLM costs, improve response speed, or enhance the quality of LLM outputs by optimizing the prompt. Trigger terms include "optimize prompt", "reduce LLM cost", "improve prompt performance", "rewrite prompt", "prompt optimization".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to refine prompts for optimal LLM performance. It streamlines prompts to minimize token count, thereby reducing costs and enhancing response speed, all while maintaining or improving output quality.

## How It Works

1. **Analyzing Prompt**: The skill analyzes the input prompt to identify areas of redundancy, verbosity, and potential for simplification.
2. **Rewriting Prompt**: It rewrites the prompt using techniques like concise language, targeted instructions, and efficient phrasing.
3. **Suggesting Alternatives**: The skill provides the optimized prompt along with an explanation of the changes made and their expected impact.

## When to Use This Skill

This skill activates when you need to:
- Reduce the cost of using an LLM.
- Improve the speed of LLM responses.
- Enhance the quality or clarity of LLM outputs by refining the prompt.

## Examples

### Example 1: Reducing LLM Costs

User request: "Optimize this prompt for cost and quality: 'I would like you to create a detailed product description for a new ergonomic office chair, highlighting its features, benefits, and target audience, and also include information about its warranty and return policy.'"

The skill will:
1. Analyze the prompt for redundancies and areas for simplification.
2. Rewrite the prompt to be more concise: "Create a product description for an ergonomic office chair. Include features, benefits, target audience, warranty, and return policy."
3. Provide the optimized prompt and explain the token reduction achieved.

### Example 2: Improving Prompt Performance

User request: "Optimize this prompt for better summarization: 'Please read the following document and provide a comprehensive summary of all the key points, main arguments, supporting evidence, and overall conclusion, ensuring that the summary is accurate, concise, and easy to understand.'"

The skill will:
1. Identify areas for improvement in the prompt's clarity and focus.
2. Rewrite the prompt to be more direct: "Summarize this document, including key points, arguments, evidence, and the conclusion."
3. Present the optimized prompt and explain how it enhances summarization performance.

## Best Practices

- **Clarity**: Ensure the original prompt is clear and well-defined before optimization.
- **Context**: Provide sufficient context to the skill so it can understand the prompt's purpose.
- **Iteration**: Iterate on the optimized prompt based on the LLM's output to fine-tune performance.

## Integration

This skill integrates with the `prompt-architect` agent to leverage advanced prompt engineering techniques. It can also be used in conjunction with the `llm-integration-expert` to optimize prompts for specific LLM APIs.