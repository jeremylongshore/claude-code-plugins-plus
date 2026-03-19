import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// process.cwd() is `site/` during build; CHANGELOG is one level up at project root
const CHANGELOG_PATH = resolve(process.cwd(), '..', 'CHANGELOG.md');

export interface ChangelogSection {
  added?: string[];
  changed?: string[];
  fixed?: string[];
  security?: string[];
  'backwards compatible'?: string[];
}

export interface ChangelogEntry {
  version: string;
  date: string;
  sections: ChangelogSection;
}

export function parseChangelog(): ChangelogEntry[] {
  const content = readFileSync(CHANGELOG_PATH, 'utf-8');
  const entries: ChangelogEntry[] = [];

  // Split by version headings: ## [x.y.z] - YYYY-MM-DD or ## [Unreleased]
  const versionPattern = /^## \[([^\]]+)\](?:\s*-\s*(\S+))?/gm;
  const matches = [...content.matchAll(versionPattern)];

  for (let i = 0; i < matches.length; i++) {
    const version = matches[i][1];
    const date = matches[i][2] || '';

    // Skip unreleased if empty
    if (version === 'Unreleased') {
      const nextStart = matches[i + 1]?.index ?? content.length;
      const body = content.slice(matches[i].index! + matches[i][0].length, nextStart).trim();
      if (!body) continue;
    }

    const start = matches[i].index! + matches[i][0].length;
    const end = matches[i + 1]?.index ?? content.length;
    const body = content.slice(start, end);

    const sections: ChangelogSection = {};
    const sectionPattern = /^### (\w[\w\s]*)/gm;
    const sectionMatches = [...body.matchAll(sectionPattern)];

    for (let j = 0; j < sectionMatches.length; j++) {
      const sectionName = sectionMatches[j][1].trim().toLowerCase() as keyof ChangelogSection;
      const sectionStart = sectionMatches[j].index! + sectionMatches[j][0].length;
      const sectionEnd = sectionMatches[j + 1]?.index ?? body.length;
      const sectionBody = body.slice(sectionStart, sectionEnd);

      const items = sectionBody
        .split('\n')
        .filter(line => line.trimStart().startsWith('- '))
        .map(line => line.trimStart().replace(/^- /, ''));

      if (items.length > 0) {
        sections[sectionName] = items;
      }
    }

    entries.push({ version, date, sections });
  }

  return entries;
}
