#!/usr/bin/env node

/**
 * README Section Extraction Script
 *
 * Reads plugin READMEs, splits on ## headings into named sections,
 * converts markdown to HTML, and outputs readme-sections.json.
 * Runs between discover-skills.mjs and sync-catalog.mjs in the build pipeline.
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { createRequire } from 'node:module';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { mdToHtml } from './md-to-html.mjs';

const require = createRequire(import.meta.url);
const { publishedPlugins } = require('../../scripts/publication-policy.cjs');

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = join(__dirname, '..', '..');
const CATALOG_PATH = join(ROOT_DIR, '.claude-plugin', 'marketplace.extended.json');
const OUTPUT_FILE = join(__dirname, '..', 'src', 'data', 'readme-sections.json');

const MAX_SECTION_CHARS = 3000;

/** Flexible heading matchers for canonical section keys */
const SECTION_MATCHERS = {
  features: /^(features|key features|capabilities)$/i,
  usage: /^(usage|how to use|how it works|quick start)$/i,
  overview: /^(overview|what it does|about)$/i,
  useCases: /^(use cases|example scenarios|example workflow|examples?)$/i,
  troubleshooting: /^(troubleshooting|faq|common issues)$/i,
};

/**
 * Split README content into named sections based on ## headings.
 * Content before the first ## is treated as potential "overview".
 */
function extractSections(content) {
  const lines = content.split('\n');
  const sections = {};
  let currentHeading = null;
  let currentLines = [];
  let preHeadingLines = [];
  let foundFirstH2 = false;

  for (const line of lines) {
    const h2Match = line.match(/^##\s+(.+)$/);
    if (h2Match) {
      // Save previous section
      if (currentHeading !== null) {
        saveSection(sections, currentHeading, currentLines);
      } else if (!foundFirstH2 && preHeadingLines.length > 0) {
        // Content before first H2 — candidate for overview
        sections._preHeading = preHeadingLines.join('\n').trim();
      }
      currentHeading = h2Match[1].trim();
      currentLines = [];
      foundFirstH2 = true;
      continue;
    }

    // Skip H1 titles
    if (line.match(/^#\s+/)) continue;

    if (!foundFirstH2) {
      preHeadingLines.push(line);
    } else {
      currentLines.push(line);
    }
  }

  // Save last section
  if (currentHeading !== null) {
    saveSection(sections, currentHeading, currentLines);
  }

  return sections;
}

function saveSection(sections, heading, lines) {
  const text = lines.join('\n').trim();
  if (!text) return;

  for (const [key, regex] of Object.entries(SECTION_MATCHERS)) {
    if (regex.test(heading)) {
      sections[key] = text;
      return;
    }
  }
  // Unmatched sections are stored by original heading for possible future use
  sections[`_raw:${heading}`] = text;
}

/**
 * Parse troubleshooting sections into Q&A format from H3 subheadings.
 */
function parseTroubleshooting(md) {
  const items = [];
  const parts = md.split(/^###\s+/m);

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    const nlIdx = trimmed.indexOf('\n');
    if (nlIdx === -1) continue;

    const question = trimmed.slice(0, nlIdx).trim().replace(/^["']|["']$/g, '');
    const answer = trimmed.slice(nlIdx + 1).trim();

    if (question && answer) {
      items.push({
        question,
        answer: mdToHtml(answer),
      });
    }
  }

  return items.length > 0 ? items : null;
}

function truncate(html, max) {
  if (html.length <= max) return html;
  // Truncate at last complete tag before limit
  const cut = html.slice(0, max);
  const lastClose = cut.lastIndexOf('>');
  return (lastClose > max * 0.5 ? cut.slice(0, lastClose + 1) : cut) + '...';
}

// ── Main ──

const catalog = JSON.parse(readFileSync(CATALOG_PATH, 'utf-8'));
const result = {};
let found = 0;
let skipped = 0;

for (const plugin of publishedPlugins(catalog.plugins, 'extended catalog')) {
  const readmePath = join(ROOT_DIR, 'plugins', plugin.category, plugin.name, 'README.md');

  if (!existsSync(readmePath)) {
    skipped++;
    continue;
  }

  const raw = readFileSync(readmePath, 'utf-8');
  const sections = extractSections(raw);

  const entry = {};

  // Overview: explicit section or pre-heading content
  const overviewMd = sections.overview || sections._preHeading;
  if (overviewMd) {
    entry.overview = truncate(mdToHtml(overviewMd), MAX_SECTION_CHARS);
  }

  // Features
  if (sections.features) {
    entry.features = truncate(mdToHtml(sections.features), MAX_SECTION_CHARS);
  }

  // Usage
  if (sections.usage) {
    entry.usage = truncate(mdToHtml(sections.usage), MAX_SECTION_CHARS);
  }

  // Use Cases
  if (sections.useCases) {
    entry.useCases = truncate(mdToHtml(sections.useCases), MAX_SECTION_CHARS);
  }

  // Troubleshooting — parsed as Q&A
  if (sections.troubleshooting) {
    const faqItems = parseTroubleshooting(sections.troubleshooting);
    if (faqItems) {
      entry.troubleshooting = faqItems;
    }
  }

  // Only include plugins that have at least one section
  if (Object.keys(entry).length > 0) {
    result[plugin.name] = entry;
    found++;
  }
}

writeFileSync(OUTPUT_FILE, JSON.stringify(result, null, 2));
console.log(`[readme:extract] Extracted sections for ${found} plugins (${skipped} skipped, no README)`);
