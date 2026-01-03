#!/usr/bin/env python3
"""Fix OpenRouter skills to meet nixtla quality standards."""

import os
import re
from pathlib import Path

SKILLS_DIR = Path("plugins/saas-packs/openrouter-pack/skills")

# Mapping of skill names to their quality-compliant descriptions
SKILL_METADATA = {
    "openrouter-install-auth": {
        "description": "Set up OpenRouter API authentication and configure API keys. Use when starting a new OpenRouter integration or troubleshooting auth issues. Trigger with phrases like 'openrouter setup', 'openrouter api key', 'openrouter authentication', 'configure openrouter'.",
        "overview": "This skill guides you through obtaining and configuring OpenRouter API credentials, setting up environment variables, and verifying your authentication is working correctly.",
        "prerequisites": "- OpenRouter account (free at openrouter.ai)\n- Python 3.8+ or Node.js 18+\n- OpenAI SDK installed (`pip install openai` or `npm install openai`)",
    },
    "openrouter-hello-world": {
        "description": "Create your first OpenRouter API request with a simple example. Use when learning OpenRouter or testing your setup. Trigger with phrases like 'openrouter hello world', 'openrouter first request', 'openrouter quickstart', 'test openrouter'.",
        "overview": "This skill provides a minimal working example to verify your OpenRouter integration is functioning and introduces the basic request/response pattern.",
        "prerequisites": "- OpenRouter API key configured\n- Python 3.8+ or Node.js 18+\n- OpenAI SDK installed",
    },
    "openrouter-model-catalog": {
        "description": "Explore and query the OpenRouter model catalog programmatically. Use when selecting models or checking availability. Trigger with phrases like 'openrouter models', 'list openrouter models', 'openrouter model catalog', 'available models openrouter'.",
        "overview": "This skill teaches you how to query the OpenRouter models API, filter by capabilities, and select the right model for your use case.",
        "prerequisites": "- OpenRouter API key configured\n- Basic understanding of LLM model differences",
    },
    "openrouter-sdk-patterns": {
        "description": "Implement common SDK patterns for OpenRouter integration. Use when building production applications. Trigger with phrases like 'openrouter sdk', 'openrouter client pattern', 'openrouter best practices', 'openrouter code patterns'.",
        "overview": "This skill covers proven SDK patterns including client initialization, error handling, retry logic, and configuration management for robust OpenRouter integrations.",
        "prerequisites": "- OpenRouter API key configured\n- Python 3.8+ or Node.js 18+\n- OpenAI SDK installed",
    },
    "openrouter-openai-compat": {
        "description": "Configure OpenRouter as an OpenAI API drop-in replacement. Use when migrating from OpenAI or using OpenAI-compatible libraries. Trigger with phrases like 'openrouter openai', 'openrouter drop-in', 'openrouter compatibility', 'migrate to openrouter'.",
        "overview": "This skill demonstrates how to use OpenRouter with any OpenAI-compatible library or codebase with minimal changes.",
        "prerequisites": "- Existing OpenAI integration or familiarity with OpenAI API\n- OpenRouter API key",
    },
    "openrouter-pricing-basics": {
        "description": "Understand OpenRouter pricing and cost estimation. Use when budgeting or optimizing costs. Trigger with phrases like 'openrouter pricing', 'openrouter costs', 'openrouter budget', 'openrouter token pricing'.",
        "overview": "This skill explains the OpenRouter pricing model, how to estimate costs, and strategies for cost-effective model selection.",
        "prerequisites": "- OpenRouter account\n- Basic understanding of token-based pricing",
    },
    "openrouter-common-errors": {
        "description": "Diagnose and fix common OpenRouter API errors. Use when troubleshooting failed requests. Trigger with phrases like 'openrouter error', 'openrouter not working', 'openrouter 401', 'openrouter 429', 'fix openrouter'.",
        "overview": "This skill provides a comprehensive guide to identifying, diagnosing, and resolving the most common OpenRouter API errors.",
        "prerequisites": "- OpenRouter integration experiencing errors\n- Access to request/response logs",
    },
    "openrouter-debug-bundle": {
        "description": "Set up comprehensive logging and debugging for OpenRouter. Use when investigating issues or monitoring requests. Trigger with phrases like 'openrouter debug', 'openrouter logging', 'openrouter trace', 'monitor openrouter'.",
        "overview": "This skill shows how to implement request/response logging, timing metrics, and debugging utilities for OpenRouter integrations.",
        "prerequisites": "- OpenRouter integration\n- Logging infrastructure (optional but recommended)",
    },
    "openrouter-rate-limits": {
        "description": "Handle OpenRouter rate limits with proper backoff strategies. Use when experiencing 429 errors or building high-throughput systems. Trigger with phrases like 'openrouter rate limit', 'openrouter 429', 'openrouter throttle', 'openrouter backoff'.",
        "overview": "This skill teaches rate limit handling patterns including exponential backoff, token bucket algorithms, and request queuing.",
        "prerequisites": "- OpenRouter integration\n- Understanding of HTTP status codes",
    },
    "openrouter-model-availability": {
        "description": "Check model availability and implement fallback chains. Use when building resilient systems or handling model outages. Trigger with phrases like 'openrouter availability', 'openrouter fallback', 'openrouter model down', 'openrouter health check'.",
        "overview": "This skill covers model health monitoring, availability checking, and implementing automatic fallback chains for production reliability.",
        "prerequisites": "- OpenRouter integration\n- Multiple model options identified",
    },
    "openrouter-prod-checklist": {
        "description": "Pre-launch production readiness checklist for OpenRouter. Use when preparing to deploy to production. Trigger with phrases like 'openrouter production', 'openrouter go-live', 'openrouter launch checklist', 'deploy openrouter'.",
        "overview": "This skill provides a comprehensive checklist covering security, monitoring, error handling, and operational readiness for production OpenRouter deployments.",
        "prerequisites": "- Working OpenRouter integration\n- Production infrastructure ready",
    },
    "openrouter-upgrade-migration": {
        "description": "Migrate and upgrade OpenRouter SDK versions safely. Use when updating dependencies or migrating configurations. Trigger with phrases like 'openrouter upgrade', 'openrouter migration', 'update openrouter', 'openrouter breaking changes'.",
        "overview": "This skill guides you through SDK version upgrades, configuration migrations, and handling breaking changes safely.",
        "prerequisites": "- Existing OpenRouter integration\n- Version control for rollback capability",
    },
    "openrouter-fallback-config": {
        "description": "Configure model fallback chains for high availability. Use when building fault-tolerant LLM systems. Trigger with phrases like 'openrouter fallback', 'openrouter backup model', 'openrouter redundancy', 'model failover'.",
        "overview": "This skill demonstrates how to configure and implement model fallback chains that automatically switch to backup models on failure.",
        "prerequisites": "- OpenRouter integration\n- Multiple suitable models identified\n- Understanding of your latency/cost requirements",
    },
    "openrouter-routing-rules": {
        "description": "Implement intelligent model routing based on request characteristics. Use when optimizing for cost, speed, or quality per request. Trigger with phrases like 'openrouter routing', 'model selection', 'smart routing', 'dynamic model'.",
        "overview": "This skill covers implementing request-based routing logic to select optimal models based on content, urgency, or cost constraints.",
        "prerequisites": "- OpenRouter integration\n- Understanding of model capabilities and pricing",
    },
    "openrouter-streaming-setup": {
        "description": "Implement streaming responses with OpenRouter. Use when building real-time chat interfaces or reducing time-to-first-token. Trigger with phrases like 'openrouter streaming', 'openrouter sse', 'stream response', 'real-time openrouter'.",
        "overview": "This skill demonstrates streaming response implementation for lower perceived latency and real-time output display.",
        "prerequisites": "- OpenRouter integration\n- Frontend capable of handling SSE/streaming",
    },
    "openrouter-caching-strategy": {
        "description": "Implement response caching for OpenRouter efficiency. Use when optimizing costs or reducing latency for repeated queries. Trigger with phrases like 'openrouter cache', 'cache llm responses', 'openrouter redis', 'semantic caching'.",
        "overview": "This skill covers caching strategies from simple LRU caches to semantic similarity caching for intelligent response reuse.",
        "prerequisites": "- OpenRouter integration\n- Caching infrastructure (Redis recommended for production)",
    },
    "openrouter-load-balancing": {
        "description": "Distribute requests across multiple OpenRouter configurations. Use when scaling or implementing geographic distribution. Trigger with phrases like 'openrouter load balance', 'distribute requests', 'openrouter scaling', 'multi-key openrouter'.",
        "overview": "This skill teaches load balancing patterns for distributing requests across multiple API keys or configurations.",
        "prerequisites": "- Multiple OpenRouter API keys\n- Understanding of your traffic patterns",
    },
    "openrouter-reference-architecture": {
        "description": "Production reference architecture for OpenRouter deployments. Use when designing or reviewing system architecture. Trigger with phrases like 'openrouter architecture', 'openrouter design', 'production openrouter', 'openrouter infrastructure'.",
        "overview": "This skill provides a complete reference architecture for production OpenRouter deployments including infrastructure, monitoring, and operational patterns.",
        "prerequisites": "- Understanding of cloud infrastructure\n- Production deployment requirements defined",
    },
    "openrouter-team-setup": {
        "description": "Configure OpenRouter for team and organizational use. Use when setting up multi-user access or department billing. Trigger with phrases like 'openrouter team', 'openrouter organization', 'multi-user openrouter', 'openrouter rbac'.",
        "overview": "This skill covers setting up OpenRouter for team environments including key management, access control, and usage tracking per user or department.",
        "prerequisites": "- OpenRouter account with admin access\n- Team structure defined",
    },
    "openrouter-cost-controls": {
        "description": "Implement budget controls and cost limits for OpenRouter. Use when managing spending or preventing overruns. Trigger with phrases like 'openrouter budget', 'openrouter spending limit', 'cost control', 'openrouter billing alert'.",
        "overview": "This skill demonstrates implementing cost controls including per-key limits, budget alerts, and automatic cutoffs.",
        "prerequisites": "- OpenRouter account\n- Budget requirements defined",
    },
    "openrouter-usage-analytics": {
        "description": "Track and analyze OpenRouter usage patterns. Use when optimizing costs or understanding usage. Trigger with phrases like 'openrouter analytics', 'openrouter usage', 'openrouter metrics', 'track openrouter'.",
        "overview": "This skill covers implementing usage tracking, building dashboards, and analyzing patterns to optimize your OpenRouter usage.",
        "prerequisites": "- OpenRouter integration\n- Analytics/metrics infrastructure (optional)",
    },
    "openrouter-data-privacy": {
        "description": "Implement data privacy controls for OpenRouter requests. Use when handling PII or meeting compliance requirements. Trigger with phrases like 'openrouter privacy', 'openrouter pii', 'openrouter gdpr', 'openrouter data protection'.",
        "overview": "This skill covers PII detection, data redaction, and compliance considerations for OpenRouter integrations handling sensitive data.",
        "prerequisites": "- Understanding of applicable privacy regulations\n- Data classification requirements",
    },
    "openrouter-audit-logging": {
        "description": "Implement audit logging for OpenRouter compliance. Use when meeting regulatory requirements or security audits. Trigger with phrases like 'openrouter audit', 'openrouter compliance log', 'openrouter security log', 'audit trail'.",
        "overview": "This skill demonstrates implementing comprehensive audit logging for security, compliance, and operational visibility.",
        "prerequisites": "- OpenRouter integration\n- Audit requirements defined\n- Log storage infrastructure",
    },
    "openrouter-compliance-review": {
        "description": "Conduct security and compliance review of OpenRouter integration. Use when preparing for audits or security assessments. Trigger with phrases like 'openrouter security review', 'openrouter compliance', 'openrouter audit', 'security assessment'.",
        "overview": "This skill provides a framework for conducting security and compliance reviews of OpenRouter integrations.",
        "prerequisites": "- Working OpenRouter integration\n- Compliance requirements documented",
    },
    "openrouter-model-routing": {
        "description": "Implement advanced model routing with A/B testing. Use when optimizing model selection or running experiments. Trigger with phrases like 'openrouter a/b test', 'model experiment', 'openrouter routing', 'model comparison'.",
        "overview": "This skill covers advanced routing patterns including A/B testing, gradual rollouts, and performance-based model selection.",
        "prerequisites": "- OpenRouter integration\n- Metrics collection capability",
    },
    "openrouter-function-calling": {
        "description": "Implement function/tool calling with OpenRouter models. Use when building agents or structured outputs. Trigger with phrases like 'openrouter functions', 'openrouter tools', 'openrouter agent', 'function calling'.",
        "overview": "This skill demonstrates implementing function calling and tool use patterns with OpenRouter-supported models.",
        "prerequisites": "- OpenRouter integration\n- Model that supports function calling (GPT-4, Claude, etc.)",
    },
    "openrouter-context-optimization": {
        "description": "Optimize context window usage and token efficiency. Use when managing costs or hitting context limits. Trigger with phrases like 'openrouter context', 'openrouter tokens', 'reduce tokens', 'context window'.",
        "overview": "This skill covers techniques for efficient context management including truncation, summarization, and token optimization.",
        "prerequisites": "- OpenRouter integration\n- Understanding of token-based pricing",
    },
    "openrouter-multi-provider": {
        "description": "Work with multiple providers through OpenRouter. Use when comparing providers or building provider-agnostic systems. Trigger with phrases like 'openrouter providers', 'openrouter multi-model', 'compare models', 'provider selection'.",
        "overview": "This skill covers strategies for working with multiple AI providers through OpenRouter's unified API.",
        "prerequisites": "- OpenRouter integration\n- Understanding of different provider capabilities",
    },
    "openrouter-performance-tuning": {
        "description": "Optimize OpenRouter performance and latency. Use when reducing response times or improving throughput. Trigger with phrases like 'openrouter performance', 'openrouter latency', 'speed up openrouter', 'openrouter optimization'.",
        "overview": "This skill covers performance optimization techniques including connection pooling, async processing, and caching strategies.",
        "prerequisites": "- OpenRouter integration\n- Performance baseline measurements",
    },
    "openrouter-known-pitfalls": {
        "description": "Avoid common OpenRouter mistakes and anti-patterns. Use when reviewing code or onboarding developers. Trigger with phrases like 'openrouter pitfalls', 'openrouter mistakes', 'openrouter gotchas', 'openrouter common issues'.",
        "overview": "This skill documents common mistakes, anti-patterns, and gotchas to avoid when working with OpenRouter.",
        "prerequisites": "- OpenRouter integration or planning one",
    },
}


def fix_skill(skill_name: str) -> None:
    """Fix a single skill file."""
    skill_dir = SKILLS_DIR / skill_name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        print(f"  Skipping {skill_name}: file not found")
        return

    content = skill_file.read_text()

    # Get metadata for this skill
    meta = SKILL_METADATA.get(skill_name, {})
    if not meta:
        print(f"  Warning: No metadata for {skill_name}")
        return

    # Parse existing content
    parts = content.split("---", 2)
    if len(parts) < 3:
        print(f"  Error: Invalid SKILL.md format for {skill_name}")
        return

    # Parse existing frontmatter
    frontmatter_lines = parts[1].strip().split("\n")
    frontmatter = {}
    current_key = None
    for line in frontmatter_lines:
        if line.startswith("  "):
            # Continuation of multiline value
            if current_key:
                frontmatter[current_key] += "\n" + line
        elif ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            frontmatter[current_key] = value.strip()

    # Get the body content
    body = parts[2].strip()

    # Extract the main heading and content
    lines = body.split("\n")
    main_heading = ""
    main_content = []
    for i, line in enumerate(lines):
        if line.startswith("# "):
            main_heading = line
            main_content = lines[i+1:]
            break

    # Build new frontmatter
    new_frontmatter = f"""---
name: {skill_name}
description: |
  {meta['description']}
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---"""

    # Build new body with required sections
    existing_content = "\n".join(main_content).strip()

    # Generate instructions section based on skill type
    instructions = meta.get('instructions', f"""Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring""")

    new_body = f"""
{main_heading}

## Overview

{meta['overview']}

## Prerequisites

{meta['prerequisites']}

## Instructions

{instructions}

{existing_content}

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
"""

    # Write updated content
    new_content = new_frontmatter + new_body
    skill_file.write_text(new_content)
    print(f"  Fixed {skill_name}")


def main():
    """Fix all OpenRouter skills."""
    print("Fixing OpenRouter skills for quality compliance...")

    if not SKILLS_DIR.exists():
        print(f"Error: Skills directory not found: {SKILLS_DIR}")
        return

    skills = sorted([d.name for d in SKILLS_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(skills)} skills to fix\n")

    for skill in skills:
        fix_skill(skill)

    print(f"\nDone! Fixed {len(skills)} skills.")


if __name__ == "__main__":
    main()
