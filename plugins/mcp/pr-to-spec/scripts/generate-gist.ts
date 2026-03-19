#!/usr/bin/env node
/**
 * Generates gist markdown from README.md, CHANGELOG.md, and VERSION.
 * Output goes to stdout. Run: npx tsx scripts/generate-gist.ts
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const ROOT = resolve(import.meta.dirname, '..');
const readme = readFileSync(resolve(ROOT, 'README.md'), 'utf-8');
const changelog = readFileSync(resolve(ROOT, 'CHANGELOG.md'), 'utf-8');
const version = readFileSync(resolve(ROOT, 'VERSION'), 'utf-8').trim();

// ── Helpers ──

function extractSection(content: string, heading: string, level = 2): string {
  const prefix = '#'.repeat(level);
  const lines = content.split('\n');
  let start = -1;
  let end = lines.length;

  for (let i = 0; i < lines.length; i++) {
    if (start === -1) {
      if (lines[i].match(new RegExp(`^${prefix}\\s+${heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`))) {
        start = i + 1;
      }
    } else if (lines[i].match(new RegExp(`^#{1,${level}}\\s`))) {
      end = i;
      break;
    }
  }

  if (start === -1) return '';
  return lines.slice(start, end).join('\n').trim();
}

function extractCodeBlock(content: string, lang?: string): string {
  const pattern = lang
    ? new RegExp(`\`\`\`${lang}\\n([\\s\\S]*?)\`\`\``, 'm')
    : /```[\w]*\n([\s\S]*?)```/m;
  const match = content.match(pattern);
  return match ? match[1].trim() : '';
}

// ── Extract sections from README ──

const whatItDoes = extractSection(readme, 'What It Does');
const quickStart = extractSection(readme, 'Quick Start');
const mcpServer = extractSection(readme, 'MCP Server');
const agentProtocol = extractSection(readme, 'Agent Protocol');
const cliReference = extractSection(readme, 'CLI Reference');
const riskClassification = extractSection(readme, 'Risk Classification');
const architecture = extractSection(readme, 'Architecture');
const envVars = extractSection(readme, 'Environment Variables');
const githubAction = extractSection(readme, 'GitHub Action');

// ── Build the gist ──

const output = `# pr-to-spec v${version}

**The flight envelope for agentic coding.**

Turn any code change — a GitHub PR, a local branch, staged edits — into a structured, agent-consumable spec with intent drift detection. CLI *and* MCP server.

[![CI](https://github.com/jeremylongshore/pr-to-prompt/actions/workflows/ci.yml/badge.svg)](https://github.com/jeremylongshore/pr-to-prompt/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![npm](https://img.shields.io/npm/v/pr-to-spec)](https://www.npmjs.com/package/pr-to-spec)

**Links:** [GitHub](https://github.com/jeremylongshore/pr-to-prompt) · [npm](https://www.npmjs.com/package/pr-to-spec) · [Docs](https://jeremylongshore.github.io/pr-to-prompt/)

---

## One-Pager

### What It Does

${whatItDoes}

### Quick Start

${quickStart}

### MCP Server

${mcpServer}

### Agent Protocol

${agentProtocol}

### Environment Variables

${envVars}

---

## Operator Audit

### CLI Reference

${cliReference}

### Risk Classification

${riskClassification}

### Architecture

${architecture}

### GitHub Action

${githubAction}

---

## Changelog

${changelog.split('\n').slice(6).join('\n').trim()}
`;

process.stdout.write(output);
