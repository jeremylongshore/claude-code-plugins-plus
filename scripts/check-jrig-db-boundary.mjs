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
  const events = [];
  const record = (index, name, rawValue) => {
    events.push({ index, name, value: rawValue.trim() });
  };

  // Match every assignment token, not only the first token in declarations
  // such as `local -r SAFE=x DB=...`.
  const assignment = /(?:^|[;\n]|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s;\n]+)/g;
  for (const match of text.matchAll(assignment)) {
    record(match.index, match[1], match[2]);
  }
  const unset = /(?:^|[;\n])\s*unset\s+([A-Za-z_][A-Za-z0-9_]*)\b/g;
  for (const match of text.matchAll(unset)) {
    events.push({ index: match.index, name: match[1], unset: true });
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
    record(
      match.index,
      match[1],
      alias && anchors.has(alias[1]) ? anchors.get(alias[1]) : rawValue,
    );
  }
  const yamlFlowEnv = /^\s*env\s*:\s*\{([^}\n]*)\}\s*(?:#.*)?$/gm;
  for (const flow of text.matchAll(yamlFlowEnv)) {
    const entry =
      /(?:^|,)\s*[`'"]?([A-Za-z_][A-Za-z0-9_]*)[`'"]?\s*:\s*("(?:\\.|[^"])*"|'(?:\\.|[^'])*'|[^,}]+)/g;
    for (const match of flow[1].matchAll(entry)) {
      record(flow.index + match.index, match[1], match[2]);
    }
  }

  const assignments = new Map();
  for (const event of events.sort((left, right) => left.index - right.index)) {
    if (event.unset) assignments.delete(event.name);
    else assignments.set(event.name, event.value);
  }
  return assignments;
}

function expandKnownVariables(value, assignments, stack = new Set()) {
  const resolve = (name, nextStack = stack) => {
    if (nextStack.has(name) || !assignments.has(name)) return null;
    const nestedStack = new Set(nextStack).add(name);
    return expandKnownVariables(assignments.get(name), assignments, nestedStack);
  };

  const variable =
    /\$\{!([A-Za-z_][A-Za-z0-9_]*)\}|\$\{([A-Za-z_][A-Za-z0-9_]*)(?:(:-|:\+|:)([^}]*))?\}|\$([A-Za-z_][A-Za-z0-9_]*)/g;
  return value.replace(variable, (token, indirectName, bracedName, operator, operand, bareName) => {
    if (indirectName) {
      const pointer = resolve(indirectName);
      return pointer === null ? token : (resolve(shellLiteralView(pointer)) ?? token);
    }

    const name = bracedName ?? bareName;
    const resolved = resolve(name);
    if (operator === ':-') {
      return resolved ? resolved : expandKnownVariables(operand, assignments, stack);
    }
    if (operator === ':+') {
      return resolved ? expandKnownVariables(operand, assignments, stack) : '';
    }
    if (operator === ':') {
      if (resolved === null || !/^-?\d+$/.test(operand)) return token;
      return resolved.slice(Number.parseInt(operand, 10));
    }
    return resolved ?? token;
  });
}

function shellWordPattern(value) {
  let literal = '';
  let regex = '^';
  let quote = null;
  let activeGlob = false;
  const appendLiteral = (character) => {
    literal += character;
    regex += character.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&');
  };

  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (character === '\\' && quote !== "'") {
      if (index + 1 < value.length) appendLiteral(value[(index += 1)]);
      continue;
    }
    if (quote) {
      if (character === quote) quote = null;
      else appendLiteral(character);
      continue;
    }
    if (character === '$' && (value[index + 1] === "'" || value[index + 1] === '"')) {
      quote = value[(index += 1)];
      continue;
    }
    if (character === "'" || character === '"') {
      quote = character;
      continue;
    }
    if (character === '*' || character === '?') {
      activeGlob = true;
      literal += character;
      regex += character === '*' ? '.*' : '.';
      continue;
    }
    if (character === '[') {
      const closing = value.indexOf(']', index + 1);
      if (closing > index + 1) {
        const body = value.slice(index + 1, closing).replace(/\\/g, '\\\\');
        activeGlob = true;
        literal += value.slice(index, closing + 1);
        regex += `[${body}]`;
        index = closing;
        continue;
      }
    }
    appendLiteral(character);
  }
  return { literal, regex: `${regex}$`, activeGlob };
}

function isFreshieInventoryPath(value) {
  const cleaned = value.replace(/[),.;`]+$/, '');
  const fullPattern = shellWordPattern(cleaned);
  const fullNormalized = path.posix.normalize(fullPattern.literal);
  if (
    fullNormalized === 'freshie/inventory.sqlite' ||
    fullNormalized.endsWith('/freshie/inventory.sqlite')
  ) {
    return true;
  }
  const suffix = cleaned.split('/').slice(-2).join('/');
  const pattern = shellWordPattern(suffix);
  return pattern.activeGlob && new RegExp(pattern.regex).test('freshie/inventory.sqlite');
}

function commandTargetsFreshie(command, assignments) {
  const dbArgument = /(?:^|\s)--db(?:\s*=\s*|\s+)([^\s;&|]+)/g;
  const expanded = expandKnownVariables(command, assignments)
    .replace(/\\\s*\n\s*/g, '')
    .replace(/\\([A-Za-z-])/g, '$1')
    .replace(/(["'])--db\1/g, '--db')
    .replace(/(["'])--db/g, '--db');
  for (const match of expanded.matchAll(dbArgument)) {
    if (isFreshieInventoryPath(match[1])) return true;
  }
  return false;
}

function lineNumber(text, offset) {
  return text.slice(0, offset).split('\n').length;
}

function logicalShellLines(text) {
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
    blocks.push({ text: commandLines.join('\n'), offset: offsets[index] });
    index = cursor + 1;
  }
  return blocks;
}

function commandBlocks(text) {
  const blocks = [];
  let assignments = new Map();
  for (const command of logicalShellLines(text)) {
    assignments = mergeAssignments(assignments, collectAssignments(command.text));
    const expanded = expandKnownVariables(command.text.replace(/\\\s*\n\s*/g, ''), assignments);
    if (containsJrigEval(expanded)) {
      blocks.push({ ...command, assignments: new Map(assignments) });
    }
  }
  return blocks;
}

function mergeAssignments(...maps) {
  const merged = new Map();
  for (const assignments of maps) {
    for (const [name, value] of assignments) merged.set(name, value);
  }
  return merged;
}

function structuredYamlBlocks(text, filePath) {
  const blocks = [];
  const sources = [];
  const yamlLike =
    /\.ya?ml$/i.test(filePath) ||
    /^\s*(?:[`'"]?(?:run|r\\u0075n)[`'"]?|env|jobs|steps)\s*:/im.test(text);
  if (yamlLike) sources.push({ text, offset: 0, wholeDocument: true });
  for (const fence of text.matchAll(/```ya?ml\s*\n([\s\S]*?)```/gi)) {
    sources.push({ text: fence[1], offset: fence.index, wholeDocument: false });
  }

  let wholeDocument = false;
  for (const source of sources) {
    try {
      yaml.loadAll(source.text, (document) => {
        if (!document || typeof document !== 'object') return;
        if (source.wholeDocument) wholeDocument = true;
        const visited = new WeakSet();
        const visit = (value, inheritedEnv = new Map()) => {
          if (!value || typeof value !== 'object' || visited.has(value)) return;
          visited.add(value);
          const localEnv = new Map(inheritedEnv);
          if (!Array.isArray(value) && value.env && typeof value.env === 'object') {
            for (const [name, envValue] of Object.entries(value.env)) {
              if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) && typeof envValue === 'string') {
                localEnv.set(name, envValue);
              }
            }
          }

          for (const [key, child] of Object.entries(value)) {
            if (key === 'run' && typeof child === 'string') {
              let runtimeEnv = new Map(localEnv);
              for (const command of logicalShellLines(child)) {
                runtimeEnv = mergeAssignments(runtimeEnv, collectAssignments(command.text));
                const expanded = expandKnownVariables(
                  command.text.replace(/\\\s*\n\s*/g, ''),
                  runtimeEnv,
                );
                if (containsJrigEval(expanded)) {
                  const needle = /j-rig|\$[A-Za-z_]/.exec(command.text)?.[0];
                  const relative = needle ? source.text.indexOf(needle) : 0;
                  blocks.push({
                    text: command.text,
                    offset: source.offset + Math.max(relative, 0),
                    assignments: new Map(runtimeEnv),
                  });
                }
              }
            } else if (key !== 'env') {
              visit(child, localEnv);
            }
          }
        };
        visit(document);
      });
    } catch {
      if (source.wholeDocument) wholeDocument = false;
    }
  }
  return { blocks, wholeDocument };
}

// YAML folds `run: >` lines into one shell command. A line-oriented scan would
// otherwise miss a forbidden --db flag placed on the next indented line.
function foldedRunBlocks(text) {
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
    for (const paragraph of content.join('\n').split(/\n\s*\n/)) {
      const folded = paragraph.replace(/\n/g, ' ').trim();
      if (!folded || firstOffset === null) continue;
      const assignments = collectAssignments(`${text.slice(0, firstOffset)}\n${folded}`);
      if (containsJrigEval(expandKnownVariables(folded, assignments))) {
        blocks.push({ text: folded, offset: firstOffset, assignments });
      }
    }
    offset += line.length + 1;
  }
  return blocks;
}

export function inspectJrigDbBoundary(text, filePath) {
  const findings = [];
  const seen = new Set();
  const structured = structuredYamlBlocks(text, filePath);
  const commands = structured.wholeDocument
    ? structured.blocks
    : [...commandBlocks(text), ...foldedRunBlocks(text), ...structured.blocks];
  for (const command of commands) {
    if (commandTargetsFreshie(command.text, command.assignments)) {
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
