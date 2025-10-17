---
name: Analyzing Text Sentiment
description: |
  This skill enables Claude to analyze the sentiment of text data. It identifies the emotional tone expressed in text, classifying it as positive, negative, or neutral. Use this skill when a user requests sentiment analysis, opinion mining, or emotion detection on any text, such as customer reviews, social media posts, or survey responses. Trigger words include "sentiment analysis", "analyze sentiment", "opinion mining", "emotion detection", and "polarity".
---

## Overview

This skill empowers Claude to perform sentiment analysis on text, providing insights into the emotional content and polarity of the provided data. By leveraging AI/ML techniques, it helps understand public opinion, customer feedback, and overall emotional tone in written communication.

## How It Works

1. **Text Input**: The skill receives text data as input from the user.
2. **Sentiment Analysis**: The skill processes the text using a pre-trained sentiment analysis model to determine the sentiment polarity (positive, negative, or neutral).
3. **Result Output**: The skill provides a sentiment score and classification, indicating the overall sentiment expressed in the text.

## When to Use This Skill

This skill activates when you need to:
- Determine the overall sentiment of customer reviews.
- Analyze the emotional tone of social media posts.
- Gauge public opinion on a particular topic.
- Identify positive and negative feedback in survey responses.

## Examples

### Example 1: Analyzing Customer Reviews

User request: "Analyze the sentiment of these customer reviews: 'The product is amazing!', 'The service was terrible.', 'It was okay.'"

The skill will:
1. Process the provided customer reviews.
2. Classify each review as positive, negative, or neutral and provide sentiment scores.

### Example 2: Monitoring Social Media Sentiment

User request: "Perform sentiment analysis on the following tweet: 'I love this new feature!'"

The skill will:
1. Analyze the provided tweet.
2. Identify the sentiment as positive and provide a corresponding sentiment score.

## Best Practices

- **Data Quality**: Ensure the input text is clear and free from ambiguous language for accurate sentiment analysis.
- **Context Awareness**: Consider the context of the text when interpreting sentiment scores, as sarcasm or irony can affect results.
- **Model Selection**: Use appropriate sentiment analysis models based on the type of text being analyzed (e.g., social media, customer reviews).

## Integration

This skill can be integrated with other Claude Code plugins to automate workflows, such as summarizing feedback alongside sentiment scores or triggering actions based on sentiment polarity (e.g., escalating negative feedback).