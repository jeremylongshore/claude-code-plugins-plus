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

function shellLiteralView(text) {
  return text.replace(/[`'"]/g, '');
}

function containsJrigEval(text) {
  return JRIG_EVAL_RE.test(shellLiteralView(text));
}

function collectAssignments(text) {
  const assignments = new Map();
  const assignment =
    /(?:^|[;\n])\s*(?:(?:export|local|readonly)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*("(?:\\.|[^"\n])*"|'(?:\\.|[^'\n])*'|[^\s;\n]+)/g;
  for (const match of text.matchAll(assignment)) {
    const values = assignments.get(match[1]) ?? [];
    values.push(shellLiteralView(match[2]));
    assignments.set(match[1], values);
  }
  const yamlScalar = /^\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([`'"]?[^#\n]+?[`'"]?)\s*$/gm;
  for (const match of text.matchAll(yamlScalar)) {
    const values = assignments.get(match[1]) ?? [];
    values.push(shellLiteralView(match[2].trim()));
    assignments.set(match[1], values);
  }
  return assignments;
}

function expandKnownVariables(value, assignments, seen = new Set()) {
  const variable = /\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))/.exec(value);
  if (!variable) return [value];
  const name = variable[1] ?? variable[2];
  const replacements = assignments.get(name);
  if (!replacements || seen.has(name) || seen.size >= 16) return [value];

  const nextSeen = new Set(seen).add(name);
  return replacements.flatMap((replacement) =>
    expandKnownVariables(
      `${value.slice(0, variable.index)}${replacement}${value.slice(variable.index + variable[0].length)}`,
      assignments,
      nextSeen,
    ),
  );
}

function isFreshieInventoryPath(value) {
  const cleaned = value.replace(/[),.;]+$/, '');
  const normalized = path.posix.normalize(cleaned);
  return (
    normalized === 'freshie/inventory.sqlite' || normalized.endsWith('/freshie/inventory.sqlite')
  );
}

function commandTargetsFreshie(command, assignments) {
  const normalized = shellLiteralView(command.replace(/\\\s*\n\s*/g, ' '));
  const dbArgument = /(?:^|\s)--db(?:\s*=\s*|\s+)([^\s;&|]+)/g;
  for (const match of normalized.matchAll(dbArgument)) {
    const candidates = expandKnownVariables(match[1], assignments);
    if (candidates.some(isFreshieInventoryPath)) return true;
  }
  return false;
}

function lineNumber(text, offset) {
  return text.slice(0, offset).split('\n').length;
}

function commandBlocks(text) {
  const lines = text.split('\n');
  const blocks = [];
  let offset = 0;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (containsJrigEval(line)) {
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
    const match = /^(\s*)(?:-\s*)?[`'"]?run[`'"]?\s*:\s*>[-+]?\s*(?:#.*)?$/.exec(line);
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
    if (firstOffset !== null && containsJrigEval(folded)) {
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
    const assignments = collectAssignments(`${text.slice(0, command.offset)}\n${command.text}`);
    if (commandTargetsFreshie(command.text, assignments)) {
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

  const prose = shellLiteralView(text)
    .replace(/\/{2,}/g, '/')
    .replace(/\/\.\//g, '/');
  const verbs = '(?:point|pass|set|use|give|feed|supply|target)';
  const directives = [
    new RegExp(
      `\\b${verbs}\\b[^\\n]{0,160}?--db(?:\\s*=\\s*|\\s+(?:(?:at|to)\\s+)?)?[^\\n]{0,160}?freshie/inventory\\.sqlite\\b`,
      'gi',
    ),
    new RegExp(
      `\\b${verbs}\\b[^\\n]{0,160}?freshie/inventory\\.sqlite\\b[^\\n]{0,160}?--db\\b`,
      'gi',
    ),
  ];
  for (const directive of directives) {
    for (const match of prose.matchAll(directive)) {
      const finding = {
        path: filePath,
        line: lineNumber(prose, match.index),
        reasonCode: DIRECTIVE_REASON,
      };
      const key = `${finding.line}:${finding.reasonCode}`;
      if (!seen.has(key)) findings.push(finding);
      seen.add(key);
    }
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
