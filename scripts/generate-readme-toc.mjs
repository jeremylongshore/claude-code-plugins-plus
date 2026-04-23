#!/usr/bin/env node
/**
 * generate-readme-toc.mjs
 *
 * Reads .claude-plugin/marketplace.extended.json and emits an awesome-list-style
 * Table of Contents into README.md, bounded by HTML comment sentinels. CI fails
 * if the bounded block is out of sync with the catalog.
 *
 * Structure:
 *   - Quick navigation table (category + emoji + count)
 *   - Per-category section with a plugin table (name, description, tags)
 *   - Back-to-top links
 *
 * Anchors use GitHub's auto-slug algorithm on plain (no-emoji) headers for
 * stability. Emojis live in the TOC display text only.
 *
 * Usage:
 *   node scripts/generate-readme-toc.mjs           # write README
 *   node scripts/generate-readme-toc.mjs --check   # CI: exit 1 if out of sync
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const EXTENDED = join(ROOT, '.claude-plugin', 'marketplace.extended.json');
const README = join(ROOT, 'README.md');

const TOC_START = '<!-- AUTO-TOC:START — do not edit; run `node scripts/generate-readme-toc.mjs` -->';
const TOC_END = '<!-- AUTO-TOC:END -->';

// Display metadata for each category: emoji + human-friendly label.
// Categories not listed fall back to auto-title and a default emoji.
const CATEGORIES = {
  'ai-ml':           { emoji: '🤖', label: 'AI & Machine Learning' },
  'ai-agency':       { emoji: '🎭', label: 'AI Agents & Agency' },
  'api-development': { emoji: '🔌', label: 'API Development' },
  'business-tools':  { emoji: '💼', label: 'Business Tools' },
  'community':       { emoji: '👥', label: 'Community' },
  'crypto':          { emoji: '₿',  label: 'Crypto & Web3' },
  'database':        { emoji: '💾', label: 'Database' },
  'design':          { emoji: '🎨', label: 'Design' },
  'devops':          { emoji: '🔧', label: 'DevOps & Infrastructure' },
  'examples':        { emoji: '📚', label: 'Examples & Templates' },
  'mcp':             { emoji: '🧩', label: 'MCP Servers' },
  'packages':        { emoji: '📦', label: 'Packages' },
  'performance':     { emoji: '⚡', label: 'Performance' },
  'productivity':    { emoji: '✅', label: 'Productivity' },
  'saas-packs':      { emoji: '🎁', label: 'SaaS Skill Packs' },
  'security':        { emoji: '🔐', label: 'Security' },
  'skill-enhancers': { emoji: '✨', label: 'Skill Enhancers' },
  'testing':         { emoji: '🧪', label: 'Testing' },
};

function metaFor(slug) {
  if (CATEGORIES[slug]) return CATEGORIES[slug];
  const label = slug
    .split(/[-_]/)
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : ''))
    .join(' ');
  return { emoji: '📁', label };
}

// GitHub auto-slug algorithm (matches @primer/slug / GFM TableOfContentsFilter):
//   1. lowercase
//   2. strip characters that aren't word-chars, hyphens, or plain spaces
//      (so "&" becomes nothing, "AI & ML" becomes "ai  ml" with two spaces)
//   3. replace each space with a hyphen (DO NOT collapse — "ai  ml" → "ai--ml")
// Unicode emojis fall into the "stripped" bucket, so leading emojis produce a
// leading hyphen; avoid by keeping display emojis out of the actual header text.
function githubSlug(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\- ]/g, '')
    .replace(/ /g, '-');
}

function escapeTable(text) {
  if (!text) return '';
  return text
    .replace(/\|/g, '\\|')
    .replace(/\r?\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function truncate(text, max = 120) {
  if (!text) return '';
  const clean = text.trim();
  if (clean.length <= max) return clean;
  return clean.slice(0, max - 1).replace(/\s+\S*$/, '') + '…';
}

function buildBlock(catalog) {
  const plugins = catalog.plugins || [];
  const byCategory = new Map();
  for (const p of plugins) {
    const cat = p.category || 'uncategorized';
    if (!byCategory.has(cat)) byCategory.set(cat, []);
    byCategory.get(cat).push(p);
  }

  // Stable ordering: CATEGORIES definition order first, then unknowns alpha.
  const known = Object.keys(CATEGORIES).filter((k) => byCategory.has(k));
  const unknown = Array.from(byCategory.keys())
    .filter((k) => !(k in CATEGORIES))
    .sort();
  const ordered = [...known, ...unknown];

  const lines = [];
  lines.push(TOC_START);
  lines.push('');
  lines.push('## Browse Plugins by Category');
  lines.push('');
  lines.push(`Jump to any of the ${ordered.length} categories below. Plugin counts are catalog totals — auto-generated from \`marketplace.extended.json\`.`);
  lines.push('');

  // Quick navigation table
  lines.push('|   | Category | Plugins |');
  lines.push('|---|----------|--------:|');
  for (const slug of ordered) {
    const meta = metaFor(slug);
    const count = byCategory.get(slug).length;
    const anchor = '#' + githubSlug(meta.label);
    lines.push(`| ${meta.emoji} | [${meta.label}](${anchor}) | ${count} |`);
  }
  lines.push('');

  // Per-category sections with plugin tables
  for (const slug of ordered) {
    const meta = metaFor(slug);
    const items = [...byCategory.get(slug)].sort((a, b) =>
      (a.name || '').localeCompare(b.name || '')
    );
    lines.push(`### ${meta.label}`);
    lines.push('');
    lines.push(`${meta.emoji} **${items.length} plugins** · category slug: \`${slug}\``);
    lines.push('');
    lines.push('| Plugin | Description |');
    lines.push('|--------|-------------|');
    for (const p of items) {
      const name = escapeTable(p.name);
      const desc = escapeTable(truncate(p.description, 140));
      lines.push(`| \`${name}\` | ${desc} |`);
    }
    lines.push('');
    lines.push('<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>');
    lines.push('');
  }

  lines.push(TOC_END);
  return lines.join('\n');
}

function replaceBlock(readme, newBlock) {
  const startIdx = readme.indexOf(TOC_START);
  const endIdx = readme.indexOf(TOC_END);

  if (startIdx === -1 || endIdx === -1) {
    throw new Error(
      `README.md is missing the TOC sentinels. Add:\n${TOC_START}\n${TOC_END}\nwhere the TOC should live.`
    );
  }
  if (endIdx < startIdx) {
    throw new Error('README TOC sentinels are in the wrong order.');
  }

  const before = readme.slice(0, startIdx);
  const after = readme.slice(endIdx + TOC_END.length);
  return before + newBlock + after;
}

function main() {
  const args = process.argv.slice(2);
  const checkMode = args.includes('--check');

  const catalog = JSON.parse(readFileSync(EXTENDED, 'utf-8'));
  const block = buildBlock(catalog);
  const current = readFileSync(README, 'utf-8');
  const updated = replaceBlock(current, block);

  if (checkMode) {
    if (current !== updated) {
      console.error(
        'README.md TOC is out of sync with marketplace.extended.json.\n' +
        'Run: node scripts/generate-readme-toc.mjs'
      );
      process.exit(1);
    }
    console.log('README TOC in sync.');
    return;
  }

  if (current === updated) {
    console.log('README TOC already up to date.');
    return;
  }

  writeFileSync(README, updated);
  const newBytes = Buffer.byteLength(updated, 'utf-8');
  console.log(`README updated (${(newBytes / 1024).toFixed(1)} KB).`);
}

main();
