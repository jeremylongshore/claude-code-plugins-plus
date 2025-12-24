#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '../..');
const playbooksDir = join(projectRoot, 'playbooks');
const pagesDir = join(projectRoot, 'marketplace/src/pages/playbooks');

const playbooks = [
  {
    slug: '01-multi-agent-rate-limits',
    title: 'Multi-Agent Rate Limits',
    description: 'Prevent API throttling in concurrent multi-agent systems. Token bucket algorithms, sliding windows, priority queues, and backpressure handling for Claude API rate limits.',
    category: 'Cost',
    wordCount: 2800
  },
  {
    slug: '02-cost-caps',
    title: 'Cost Caps & Budget Management',
    description: 'Hard budget controls for AI spending. Real-time spend tracking, automatic shutoffs, team quotas, and financial safeguards to prevent runaway costs.',
    category: 'Cost',
    wordCount: 3200
  },
  {
    slug: '03-mcp-reliability',
    title: 'MCP Server Reliability',
    description: 'Self-healing MCP servers with circuit breakers, exponential backoff, health checks, and automatic recovery. Production-grade Model Context Protocol implementations.',
    category: 'Infrastructure',
    wordCount: 3500
  },
  {
    slug: '04-ollama-migration',
    title: 'Ollama Migration Guide',
    description: 'Switch from OpenAI/Anthropic to self-hosted LLMs. Complete migration path: local setup, prompt translation, performance benchmarks, and cost analysis.',
    category: 'Infrastructure',
    wordCount: 4500
  },
  {
    slug: '05-incident-debugging',
    title: 'Incident Debugging Playbook',
    description: 'SEV-1/2/3/4 incident response protocols. Log analysis, root cause investigation (5 Whys, Fishbone), postmortem templates, and on-call procedures.',
    category: 'Operations',
    wordCount: 5000
  },
  {
    slug: '06-self-hosted-stack',
    title: 'Self-Hosted Stack Setup',
    description: 'Full infrastructure deployment with Docker/Kubernetes. Ollama, PostgreSQL, Redis, Prometheus, Grafana, Nginx - complete production stack with monitoring and backups.',
    category: 'Infrastructure',
    wordCount: 5500
  },
  {
    slug: '07-compliance-audit',
    title: 'Compliance & Audit Guide',
    description: 'SOC 2, GDPR, HIPAA, PCI DSS implementation. Audit logging with immutable signatures, RBAC, data privacy (PII redaction), and regulatory compliance.',
    category: 'Security',
    wordCount: 6000
  },
  {
    slug: '08-team-presets',
    title: 'Team Presets & Workflows',
    description: 'Team standardization and collaboration. Plugin bundles, workflow templates, automated onboarding, and multi-layer configuration hierarchy (org/team/project/individual).',
    category: 'Operations',
    wordCount: 5000
  },
  {
    slug: '09-cost-attribution',
    title: 'Cost Attribution System',
    description: 'Multi-dimensional cost tracking (team/project/user/workflow). Automatic tagging, chargeback models, budget enforcement, and usage analytics for AI operations.',
    category: 'Cost',
    wordCount: 5500
  },
  {
    slug: '10-progressive-enhancement',
    title: 'Progressive Enhancement Patterns',
    description: 'Safe AI feature rollout strategies. Feature flags (0% → 100%), A/B testing, canary deployments, graceful degradation, and automated rollback on failures.',
    category: 'Operations',
    wordCount: 5500
  },
  {
    slug: '11-advanced-tool-use',
    title: 'Advanced Tool Use',
    description: 'Dynamic tool discovery, programmatic orchestration, and parameter guidance. Tool Search Tool (85% token reduction), Programmatic Tool Calling (37% efficiency gains), and Tool Use Examples (90% parameter accuracy). Enterprise-scale agent architecture.',
    category: 'AI Architecture',
    wordCount: 6500
  }
];

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function markdownToHtml(markdown) {
  let html = markdown;

  // Remove the first H1 title (we'll use it from metadata)
  html = html.replace(/^# .+\n\n/, '');

  // Remove "Production Playbook for Claude Code Plugin Developers" line
  html = html.replace(/\*\*Production Playbook for Claude Code Plugin Developers\*\*\n\n/, '');

  // Remove manual TOC section (we generate it with JS)
  html = html.replace(/## Table of Contents\n\n[\s\S]*?\n---\n\n/, '');

  // Convert headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');

  // Convert code blocks with language
  html = html.replace(/```(\w+)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
  });

  // Convert inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Convert bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Convert italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Convert links
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>');

  // Convert lists
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n)+/g, (match) => `<ul>\n${match}</ul>\n`);

  // Convert tables
  html = html.replace(/(\|.+\|\n)+/g, (match) => {
    const rows = match.trim().split('\n');
    const header = rows[0];
    const divider = rows[1];
    const body = rows.slice(2);

    const headerCells = header.split('|').slice(1, -1).map(cell => cell.trim());
    const bodyRows = body.map(row =>
      row.split('|').slice(1, -1).map(cell => cell.trim())
    );

    let table = '<table>\n<thead>\n<tr>\n';
    headerCells.forEach(cell => {
      table += `<th>${cell}</th>\n`;
    });
    table += '</tr>\n</thead>\n<tbody>\n';

    bodyRows.forEach(row => {
      table += '<tr>\n';
      row.forEach(cell => {
        table += `<td>${cell}</td>\n`;
      });
      table += '</tr>\n';
    });

    table += '</tbody>\n</table>\n';
    return table;
  });

  // Convert horizontal rules
  html = html.replace(/^---$/gm, '<hr>');

  // Convert blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

  // Convert paragraphs (anything not already wrapped)
  const lines = html.split('\n');
  const processedLines = [];
  let inBlock = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.startsWith('<h') || line.startsWith('<ul') || line.startsWith('<ol') ||
        line.startsWith('<pre') || line.startsWith('<table') || line.startsWith('<hr') ||
        line.startsWith('<blockquote') || line.startsWith('</') || line.startsWith('<li') ||
        line === '') {
      inBlock = line.startsWith('<pre') || line.startsWith('<table') || line.startsWith('<ul') || line.startsWith('<ol');
      processedLines.push(lines[i]);
    } else if (!inBlock && line.length > 0) {
      processedLines.push(`<p>${lines[i].trim()}</p>`);
    } else {
      processedLines.push(lines[i]);
    }
  }

  return processedLines.join('\n');
}

function generatePlaybookPage(playbook) {
  const markdownPath = join(playbooksDir, `${playbook.slug}.md`);
  const markdown = readFileSync(markdownPath, 'utf-8');
  const htmlContent = markdownToHtml(markdown);

  return `---
import PlaybookTemplate from '../../components/PlaybookTemplate.astro';

const meta = {
  title: "${playbook.title}",
  description: "${playbook.description}",
  category: "${playbook.category}",
  wordCount: ${playbook.wordCount},
  slug: "${playbook.slug}"
};
---

<PlaybookTemplate {...meta}>
  <div set:html={\`${htmlContent.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`} />
</PlaybookTemplate>
`;
}

// Generate all playbook pages
playbooks.forEach(playbook => {
  const content = generatePlaybookPage(playbook);
  const outputPath = join(pagesDir, `${playbook.slug}.astro`);
  writeFileSync(outputPath, content, 'utf-8');
  console.log(`✅ Generated ${playbook.slug}.astro`);
});

console.log(`\n🎉 All ${playbooks.length} playbook pages generated successfully!`);
