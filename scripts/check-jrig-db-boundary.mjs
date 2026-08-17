#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';
import { resolvePluginProvenance } from './plugin-provenance.mjs';

const ROOT_FILES = new Set(['AGENTS.md', 'CLAUDE.md', 'README.md', 'STANDARDS.md']);
const ACTIVE_ROOTS = ['.github/', 'plugins/', 'scripts/'];
const ACTIVE_EXTENSIONS = new Set(['.md', '.sh', '.yaml', '.yml']);
const DIRECT_REASON = 'DIRECT_JRIG_FRESHIE_DB';
const DIRECTIVE_REASON = 'JRIG_FRESHIE_DB_DIRECTIVE';
const JRIG_EVAL_RE = /\b(?:(?:pnpm\s+(?:exec|dlx)|npx)\s+)?j-rig\s+eval\b/;

function shellLiteralView(text) {
  return text
    .replace(/\$(['"])/g, '$1')
    .replace(/[`'"]/g, '')
    .replace(/\\([^\n])/g, '$1');
}

function containsJrigEval(text) {
  return JRIG_EVAL_RE.test(shellLiteralView(text));
}

function collectAssignments(text) {
  const assignments = new Map();
  const record = (name, rawValue) => {
    const values = assignments.get(name) ?? [];
    values.push(shellLiteralView(rawValue.trim()));
    assignments.set(name, values);
  };

  // Match every assignment token, not only the first token in declarations
  // such as `local -r SAFE=x DB=...`.
  const assignment = /(?:^|[;\n]|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s;\n]+)/g;
  for (const match of text.matchAll(assignment)) {
    record(match[1], match[2]);
  }

  const anchors = new Map();
  const yamlAnchor = /^\s*[^#\n:]+:\s*&([A-Za-z_][A-Za-z0-9_]*)\s+([^#\n]+?)\s*$/gm;
  for (const match of text.matchAll(yamlAnchor)) {
    anchors.set(match[1], shellLiteralView(match[2].trim()));
  }

  const yamlScalar = /^\s+[`'"]?([A-Za-z_][A-Za-z0-9_]*)[`'"]?\s*:\s*([`'"]?[^#\n]+?[`'"]?)\s*$/gm;
  for (const match of text.matchAll(yamlScalar)) {
    const rawValue = match[2].trim();
    const alias = /^\*([A-Za-z_][A-Za-z0-9_]*)$/.exec(rawValue);
    record(match[1], alias && anchors.has(alias[1]) ? anchors.get(alias[1]) : rawValue);
  }
  const yamlFlowEnv = /^\s*env\s*:\s*\{([^}\n]*)\}\s*(?:#.*)?$/gm;
  for (const flow of text.matchAll(yamlFlowEnv)) {
    const entry =
      /(?:^|,)\s*[`'"]?([A-Za-z_][A-Za-z0-9_]*)[`'"]?\s*:\s*("(?:\\.|[^"])*"|'(?:\\.|[^'])*'|[^,}]+)/g;
    for (const match of flow[1].matchAll(entry)) {
      record(match[1], match[2]);
    }
  }

  const yamlSources = /^\s*env\s*:/m.test(text) ? [text] : [];
  for (const fence of text.matchAll(/```ya?ml\s*\n([\s\S]*?)```/gi)) {
    if (/^\s*env\s*:/m.test(fence[1])) yamlSources.push(fence[1]);
  }
  for (const source of yamlSources) {
    try {
      yaml.loadAll(source, (document) => {
        const visited = new WeakSet();
        const visit = (value) => {
          if (!value || typeof value !== 'object') return;
          if (visited.has(value)) return;
          visited.add(value);
          if (!Array.isArray(value) && value.env && typeof value.env === 'object') {
            for (const [name, envValue] of Object.entries(value.env)) {
              if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) && typeof envValue === 'string') {
                record(name, envValue);
              }
            }
          }
          for (const child of Object.values(value)) visit(child);
        };
        visit(document);
      });
    } catch {
      // Markdown and shell surfaces are not YAML documents. The deterministic
      // token scanners above remain authoritative for those mixed surfaces.
    }
  }
  return assignments;
}

function expandKnownVariables(value, assignments, seen = new Set()) {
  const variable = /\$\{(!?)([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/.exec(value);
  if (!variable) return [value];
  const name = variable[2] ?? variable[3];
  const indirect = variable[1] === '!';
  const replacements = indirect
    ? (assignments.get(name) ?? []).flatMap(
        (pointer) => assignments.get(shellLiteralView(pointer)) ?? [],
      )
    : assignments.get(name);
  if (!replacements || seen.has(name) || seen.size >= 16) return [value];

  const nextSeen = new Set(seen).add(name);
  return replacements
    .flatMap((replacement) =>
      expandKnownVariables(
        `${value.slice(0, variable.index)}${replacement}${value.slice(variable.index + variable[0].length)}`,
        assignments,
        nextSeen,
      ),
    )
    .slice(0, 64);
}

function isFreshieInventoryPath(value) {
  const cleaned = value.replace(/[),.;]+$/, '');
  const normalized = path.posix.normalize(cleaned);
  const suffix = normalized.split('/').slice(-2).join('/');
  let pattern = '^';
  for (const character of suffix) {
    if (character === '*') pattern += '.*';
    else if (character === '?') pattern += '.';
    else pattern += character.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&');
  }
  pattern += '$';
  return new RegExp(pattern).test('freshie/inventory.sqlite');
}

function commandTargetsFreshie(command, assignments) {
  const dbArgument = /(?:^|\s)--db(?:\s*=\s*|\s+)([^\s;&|]+)/g;
  for (const expanded of expandKnownVariables(command, assignments)) {
    const normalized = shellLiteralView(expanded.replace(/\\\s*\n\s*/g, ' '));
    for (const match of normalized.matchAll(dbArgument)) {
      if (isFreshieInventoryPath(match[1])) return true;
    }
  }
  return false;
}

function lineNumber(text, offset) {
  return text.slice(0, offset).split('\n').length;
}

function commandBlocks(text, assignments) {
  const lines = text.split('\n');
  const blocks = [];
  const offsets = [];
  let runningOffset = 0;
  for (const line of lines) {
    offsets.push(runningOffset);
    runningOffset += line.length + 1;
  }

  for (let index = 0; index < lines.length; ) {
    const line = lines[index];
    const commandLines = [line];
    let cursor = index;
    while (cursor + 1 < lines.length && commandLines.at(-1).trimEnd().endsWith('\\')) {
      cursor += 1;
      commandLines.push(lines[cursor]);
    }
    const logicalCommand = commandLines.join('\n');
    const expandedCommands = expandKnownVariables(
      logicalCommand.replace(/\\\s*\n\s*/g, ' '),
      assignments,
    );
    if (expandedCommands.some(containsJrigEval)) {
      blocks.push({ text: logicalCommand, offset: offsets[index] });
    }
    index = cursor + 1;
  }
  return blocks;
}

// YAML folds `run: >` lines into one shell command. A line-oriented scan would
// otherwise miss a forbidden --db flag placed on the next indented line.
function foldedRunBlocks(text, assignments) {
  const lines = text.split('\n');
  const blocks = [];
  let offset = 0;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const match =
      /^(\s*)(?:-\s*)?[`'"]?run[`'"]?\s*:\s*(?:&[A-Za-z_][A-Za-z0-9_]*\s+)?>(?:[1-9][+-]?|[+-][1-9]?)?\s*(?:#.*)?$/.exec(
        line,
      );
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
    if (firstOffset !== null && expandKnownVariables(folded, assignments).some(containsJrigEval)) {
      blocks.push({ text: folded, offset: firstOffset });
    }
    offset += line.length + 1;
  }
  return blocks;
}

export function inspectJrigDbBoundary(text, filePath) {
  const findings = [];
  const seen = new Set();
  const assignments = collectAssignments(text);
  for (const command of [
    ...commandBlocks(text, assignments),
    ...foldedRunBlocks(text, assignments),
  ]) {
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
  const verbs = '(?:point|pass|set|use|give|feed|supply|target|configure|route|persist)';
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
