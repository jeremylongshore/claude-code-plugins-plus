---
name: search-to-slack
description: |
  Takes web search results and formats them as polished Slack messages, digests,
  or thread summaries ready to post to channels. Use when the user wants to
  research a topic and share findings on Slack. Trigger with phrases like
  "research and post to Slack", "create a Slack digest", "summarize and share
  in #channel", or "format search results for Slack".
allowed-tools: Read, Write, Edit, Bash(curl:*), Glob, Grep, WebSearch, WebFetch
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex
tags: [slack, web-search, automation, team-communication, digest]
---

# Search to Slack

Research topics and format findings as Slack-ready messages, digests, and threaded summaries.

## Overview

This skill automates the workflow of researching a topic via web search and formatting the results into a well-structured Slack message. Instead of manually searching, reading articles, summarizing key points, and formatting them with Slack's Block Kit syntax, this skill handles the entire pipeline. It produces messages that use Slack-native formatting -- bold headers, bulleted lists, linked sources, dividers, and emoji markers -- so the output can be pasted directly into a Slack channel or sent via the Slack API.

The skill is designed for recurring team communication patterns: weekly technology digests, security vulnerability alerts, competitive intelligence updates, and ad-hoc research sharing. It supports single-message summaries, multi-part thread formats for longer research, and scheduled digest templates that can be reused each week.

## Instructions

1. **Specify the research topic and target channel:**
   - "Research React Server Components news this week and format for #frontend"
   - "Find CVEs related to OpenSSL from the last 30 days, post to #security"
   - "Create a weekly AI digest for #engineering"

2. **Choose the output format** (optional -- defaults to single message):
   - "Single message" -- one well-formatted Slack message with all findings
   - "Thread" -- a parent message with key takeaways, followed by individual replies for each source
   - "Digest" -- a structured weekly/daily digest format with sections and categories

3. **Customize the output** (optional):
   - Tone: "keep it casual" or "formal for leadership"
   - Length: "brief, 3-5 bullet points" or "comprehensive with full summaries"
   - Sections: "include a TL;DR at the top" or "add an action items section"

4. **Review and post** the output:
   - Copy and paste the formatted message directly into Slack
   - Or use the generated `curl` command to post via Slack webhook
   - Or save the Block Kit JSON for use with the Slack API

## Output

The skill generates Slack-formatted content in one or more of these forms:

- **Formatted Message** (Markdown with Slack syntax): A message using Slack's mrkdwn format with `*bold*`, `_italic_`, `>` blockquotes, bullet lists, and `<url|link text>` hyperlinks. Ready to paste directly into Slack.
- **Block Kit JSON**: For programmatic posting, a JSON payload using Slack's Block Kit with sections, dividers, context blocks, and action buttons. Compatible with Slack's `chat.postMessage` API.
- **Webhook Command**: A ready-to-run `curl` command that posts the message to a Slack incoming webhook URL (the user provides the webhook URL).
- **Thread Structure**: When thread format is selected, generates a parent message and numbered reply messages that form a cohesive research thread.

## Examples

### Example 1: Weekly AI Research Digest

**User:** "Research AI coding assistant news from this week and create a digest for #engineering."

The skill will:
1. Search for recent news about AI coding tools, LLM updates, and developer productivity research.
2. Categorize findings into sections: "New Releases", "Research Papers", "Industry Analysis".
3. Format each finding with a bold title, 1-2 sentence summary, source link, and relevance indicator.
4. Produce a complete Slack message with a header, TL;DR section, categorized findings, and a footer with the date range and source count.

Output format:
```
*Weekly AI Coding Digest* -- March 10-17, 2026

*TL;DR:* Claude 4.5 launched with 1M context, GitHub Copilot added workspace agents, and new research shows 40% productivity gains with AI pair programming.

---

*New Releases*
- *Claude 4.5 Opus* -- Anthropic's latest model with extended thinking and 1M context window. <https://anthropic.com/news|Read more>
- *Copilot Workspace Agents* -- GitHub introduced autonomous coding agents. <https://github.blog|Read more>

*Research*
- *AI Pair Programming Study* -- Stanford study shows 40% completion time reduction. <https://arxiv.org/...|Paper>

_5 sources | Compiled March 17, 2026_
```

### Example 2: Security Vulnerability Alert

**User:** "Search for critical CVEs in Node.js from the last week, format as a Slack alert for #security."

The skill will:
1. Search for recent Node.js CVEs and security advisories.
2. Extract severity ratings, affected versions, and remediation steps.
3. Format as an urgent Slack message with warning emoji, severity badges, and action items.
4. Include a checklist of remediation steps the team should follow.

### Example 3: Competitive Intelligence Thread

**User:** "Research what our competitors shipped this month and create a Slack thread for #product."

The skill will:
1. Search for product launches, blog posts, and changelog entries from specified competitors.
2. Create a parent message summarizing the competitive landscape.
3. Generate individual thread replies for each competitor, covering new features, pricing changes, and strategic implications.
4. End the thread with a "What This Means For Us" summary with recommended actions.

## Error Handling

- **No search results:** Reports that no recent results were found for the query and suggests broadening the search terms or time range.
- **Slack formatting issues:** Validates the output against Slack's mrkdwn spec, escaping special characters (`&`, `<`, `>`) that could break rendering.
- **No webhook URL provided:** Outputs the formatted message as text for manual pasting and explains how to set up a Slack incoming webhook for automated posting.
- **Rate limiting:** If web search returns limited results, clearly notes the coverage gap and suggests running the search again later.

## Prerequisites

- WebSearch and WebFetch tools enabled for research queries
- Slack incoming webhook URL (for automated posting) or manual copy-paste workflow
- Familiarity with target Slack channel naming conventions

## Resources

- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder) — visual message designer
- [Slack mrkdwn reference](https://api.slack.com/reference/surfaces/formatting) — formatting syntax
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks) — setup guide for automated posting
