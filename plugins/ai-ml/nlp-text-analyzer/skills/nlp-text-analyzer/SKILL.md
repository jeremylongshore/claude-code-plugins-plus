---
name: analyzing-text-with-nlp
description: |
  This skill enables Claude to perform natural language processing and text analysis using the nlp-text-analyzer plugin. It should be used when the user requests analysis of text, including sentiment analysis, keyword extraction, topic modeling, or other NLP tasks. The skill is triggered by requests involving "analyze text", "sentiment analysis", "keyword extraction", "topic modeling", or similar phrases related to text processing. It leverages AI/ML techniques to understand and extract insights from textual data.
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill empowers Claude to analyze text using the nlp-text-analyzer plugin, extracting meaningful information and insights. It facilitates tasks such as sentiment analysis, keyword extraction, and topic modeling, enabling a deeper understanding of textual data.

## How It Works

1. **Request Analysis**: Claude receives a user request to analyze text.
2. **Text Processing**: The nlp-text-analyzer plugin processes the text using NLP techniques.
3. **Insight Extraction**: The plugin extracts insights such as sentiment, keywords, and topics.

## When to Use This Skill

This skill activates when you need to:
- Perform sentiment analysis on a piece of text.
- Extract keywords from a document.
- Identify the main topics discussed in a text.

## Examples

### Example 1: Sentiment Analysis

User request: "Analyze the sentiment of this product review: 'I loved the product! It exceeded my expectations.'"

The skill will:
1. Process the review text using the nlp-text-analyzer plugin.
2. Determine the sentiment as positive and provide a confidence score.

### Example 2: Keyword Extraction

User request: "Extract the keywords from this news article about the latest AI advancements."

The skill will:
1. Process the article text using the nlp-text-analyzer plugin.
2. Identify and return a list of relevant keywords, such as "AI", "advancements", "machine learning", and "neural networks".

## Best Practices

- **Clarity**: Be specific in your requests to ensure accurate and relevant analysis.
- **Context**: Provide sufficient context to improve the quality of the analysis.
- **Iteration**: Refine your requests based on the initial results to achieve the desired outcome.

## Integration

This skill can be integrated with other tools to provide a comprehensive workflow, such as using the extracted keywords to perform further research or using sentiment analysis to categorize customer feedback.