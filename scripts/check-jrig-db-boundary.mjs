#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { resolvePluginProvenance } from './plugin-provenance.mjs';

const ROOT_FILES = new Set(['AGENTS.md', 'CLAUDE.md', 'README.md', 'STANDARDS.md']);
const ACTIVE_ROOTS = ['.github/', 'plugins/', 'scripts/'];
const ACTIVE_EXTENSIONS = new Set(['.md', '.sh', '.yaml', '.yml']);
const DIRECT_REASON = 'DIRECT_JRIG_FRESHIE_DB';
const DIRECTIVE_REASON = 'JRIG_FRESHIE_DB_DIRECTIVE';
const JRIG_EVAL_RE = /\b(?:(?:pnpm\s+(?:exec|dlx)|npx)\s+)?j-rig\s+eval\b/;
const FRESHIE_DB_FLAG_RE = /[`'"]?--db[`'"]?(?:\s*=\s*|\s+)[`'"]?\S*freshie\/inventory\.sqlite\b/i;

function lineNumber(text, offset) {
  return text.slice(0, offset).split('\n').length;
}

function commandBlocks(text) {
  const lines = text.split('\n');
  const blocks = [];
  let offset = 0;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (JRIG_EVAL_RE.test(line)) {
      const start = offset;
      const commandLines = [line];
      let cursor = index;
      while (cursor + 1 < lines.length && commandLines.at(-1).trimEnd().endsWith('\\')) {
        cursor += 1;
        commandLines.push(lines[cursor]);
      }
      blocks.push({ text: commandLines.join('\n'), offset: start });
    }
    offset += line.length + 1;
  }
  return blocks;
}

// YAML folds `run: >` lines into one shell command. A line-oriented scan would
// otherwise miss a forbidden --db flag placed on the next indented line.
function foldedRunBlocks(text) {
  const lines = text.split('\n');
  const blocks = [];
  let offset = 0;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const match = /^(\s*)(?:-\s*)?run:\s*>[-+]?\s*(?:#.*)?$/.exec(line);
    if (!match) {
      offset += line.length + 1;
      continue;
    }

    const parentIndent = match[1].length;
    const content = [];
    let firstOffset = null;
    let cursor = index + 1;
    let cursorOffset = offset + line.length + 1;
    while (cursor < lines.length) {
      const candidate = lines[cursor];
      if (candidate.trim() === '') {
        content.push('');
      } else {
        const indent = candidate.match(/^\s*/)[0].length;
        if (indent <= parentIndent) break;
        if (firstOffset === null) firstOffset = cursorOffset;
        content.push(candidate.trim());
      }
      cursorOffset += candidate.length + 1;
      cursor += 1;
    }
    const folded = content.join(' ');
    if (firstOffset !== null && JRIG_EVAL_RE.test(folded)) {
      blocks.push({ text: folded, offset: firstOffset });
    }
    offset += line.length + 1;
  }
  return blocks;
}

export function inspectJrigDbBoundary(text, filePath) {
  const findings = [];
  const seen = new Set();
  for (const command of [...commandBlocks(text), ...foldedRunBlocks(text)]) {
    const normalized = command.text.replace(/\\\s*\n\s*/g, ' ');
    if (FRESHIE_DB_FLAG_RE.test(normalized)) {
      const finding = {
        path: filePath,
        line: lineNumber(text, command.offset),
        reasonCode: DIRECT_REASON,
      };
      const key = `${finding.line}:${finding.reasonCode}`;
      if (!seen.has(key)) findings.push(finding);
      seen.add(key);
    }
  }

  const directive =
    /\b(?:point|pass|set|use|give|feed|supply|target)\b[^\n]{0,120}?`?--db`?(?:\s*=\s*|\s+(?:(?:at|to)\s+)?)`?[^`\n]{0,120}?freshie\/inventory\.sqlite\b/gi;
  for (const match of text.matchAll(directive)) {
    findings.push({
      path: filePath,
      line: lineNumber(text, match.index),
      reasonCode: DIRECTIVE_REASON,
    });
  }
  return findings;
}

function isActiveSurface(filePath) {
  if (ROOT_FILES.has(filePath)) return true;
  if (!ACTIVE_ROOTS.some((root) => filePath.startsWith(root))) return false;
  return ACTIVE_EXTENSIONS.has(path.extname(filePath));
}

export function auditJrigDbBoundary({
  root = process.cwd(),
  paths,
  readFile = fs.readFileSync,
  lstat = fs.lstatSync,
  provenance = resolvePluginProvenance,
} = {}) {
  const findings = [];
  let scanned = 0;
  let mirrorsSkipped = 0;

  for (const filePath of [...paths].filter(isActiveSurface).sort()) {
    const absolute = path.join(root, filePath);
    let metadata;
    try {
      metadata = lstat(absolute);
    } catch (error) {
      findings.push({
        path: filePath,
        line: 0,
        reasonCode: 'UNREADABLE_ACTIVE_SURFACE',
        detail: error instanceof Error ? error.message : String(error),
      });
      continue;
    }
    if (!metadata.isFile() || metadata.isSymbolicLink()) {
      findings.push({ path: filePath, line: 0, reasonCode: 'NON_REGULAR_ACTIVE_SURFACE' });
      continue;
    }

    if (filePath.startsWith('plugins/')) {
      const result = provenance(path.dirname(filePath), { root });
      if (result.status === 'mirror') {
        mirrorsSkipped += 1;
        continue;
      }
      if (result.status !== 'first-party') {
        findings.push({
          path: filePath,
          line: 0,
          reasonCode: result.reasonCode ?? 'UNRESOLVED_PROVENANCE',
        });
        continue;
      }
    }

    let text;
    try {
      text = readFile(absolute, 'utf8');
    } catch (error) {
      findings.push({
        path: filePath,
        line: 0,
        reasonCode: 'UNREADABLE_ACTIVE_SURFACE',
        detail: error instanceof Error ? error.message : String(error),
      });
      continue;
    }
    scanned += 1;
    findings.push(...inspectJrigDbBoundary(text, filePath));
  }

  return { findings, scanned, mirrorsSkipped };
}

function trackedPaths(root) {
  const output = execFileSync(
    'git',
    [
      'ls-files',
      '-z',
      '--',
      'AGENTS.md',
      'CLAUDE.md',
      'README.md',
      'STANDARDS.md',
      '.github',
      'plugins',
      'scripts',
    ],
    { cwd: root, maxBuffer: 32 * 1024 * 1024 },
  );
  return output.toString('utf8').split('\0').filter(Boolean);
}

export function main(root = process.cwd()) {
  let paths;
  try {
    paths = trackedPaths(root);
  } catch (error) {
    console.error(`jrig-db-boundary: REFUSED (Git inventory unavailable: ${error.message})`);
    return 1;
  }
  const report = auditJrigDbBoundary({ root, paths });
  if (report.findings.length > 0) {
    for (const finding of report.findings.slice(0, 50)) {
      const location = finding.line > 0 ? `${finding.path}:${finding.line}` : finding.path;
      console.error(
        `${location}: ${finding.reasonCode}${finding.detail ? ` (${finding.detail})` : ''}`,
      );
    }
    console.error(
      `jrig-db-boundary: REFUSED (${report.findings.length} finding(s); use scripts/run-jrig-eval.sh so j-rig receives only a scratch DB)`,
    );
    return 1;
  }
  console.log(
    `jrig-db-boundary: OK (${report.scanned} active first-party surfaces; ${report.mirrorsSkipped} mirror surfaces skipped by provenance)`,
  );
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main();
}
