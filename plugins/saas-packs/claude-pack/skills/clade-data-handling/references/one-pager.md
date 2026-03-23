# clade-data-handling — One-Pager

Manage the 200K context window, redact PII, and handle data retention for Claude integrations.

## The Problem

Claude's 200K token context window is generous but not infinite. Long conversations overflow it and trigger `invalid_request_error`. Developers also need to handle sensitive data responsibly — sending raw PII (emails, phone numbers, SSNs, credit cards) to any external API is a compliance risk. And few teams understand Anthropic's default data retention policies or what they are responsible for on their end.

## The Solution

This skill provides three production patterns: token counting with `countTokens` before every request to prevent overflow, a conversation trimming strategy that preserves the first message and recent turns while dropping the middle, and regex-based PII redaction for emails, phone numbers, SSNs, and credit card numbers. It also documents Anthropic's data retention defaults (no training on API data, zero retention on Enterprise).

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers building Claude applications that handle user data or long conversations |
| **What** | Context window management, conversation trimming, PII redaction, and data retention policy guidance |
| **When** | When your application processes user-generated content, handles multi-turn conversations, or must comply with data privacy requirements |

## Key Features

1. **Token counting** — Use `client.messages.countTokens()` to measure input before sending, calculate available budget as `200K - max_tokens`
2. **Conversation trimming** — Keep the first message (key context) and the last 3 turns, drop the middle to fit within budget
3. **PII redaction** — Regex patterns to strip emails, phone numbers, SSNs, and credit card numbers before sending to the API
4. **Data retention awareness** — Anthropic does not train on API data by default; zero retention available on Enterprise plans; your responsibility to manage stored responses

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
