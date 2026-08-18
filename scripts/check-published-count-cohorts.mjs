#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REGISTRY_PATH = 'scripts/published-count-cohorts.json';
const DISCOVERY_ROOTS = Object.freeze(['marketplace/src/pages', 'marketplace/src/components']);
const DISCOVERY_DYNAMIC_TERMS = Object.freeze(['count', 'length', 'shown', 'total']);
const DISCOVERY_IGNORED_PHRASES = Object.freeze(['Tons of Skills']);
const LABEL_LINE_WINDOW = 4;
const CANONICAL_COHORTS = Object.freeze([
  'marketplace-visible',
  'graded',
  'first-party',
  'curated-mirror',
  'curriculum',
]);

class CohortCheckError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'CohortCheckError';
    this.code = code;
  }
}

function refuse(code, message) {
  throw new CohortCheckError(code, message);
}

function nonemptyString(value, field) {
  if (typeof value !== 'string' || value.trim() === '') {
    refuse('INVALID_REGISTRY', `${field} must be a nonempty string`);
  }
  return value;
}

function foldedPath(value) {
  return value.normalize('NFC').toLocaleLowerCase('en-US');
}

function foldedText(value) {
  return value.normalize('NFC').toLocaleLowerCase('en-US');
}

function stripComments(source) {
  return source
    .replace(/<!--[\s\S]*?-->/g, (comment) => comment.replace(/[^\n]/g, ' '))
    .replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/[^\n]/g, ' '))
    .replace(/(?<!:)\/\/.*$/gm, '');
}

function maskText(value) {
  return value.replace(/[^\r\n]/g, ' ');
}

function maskNonRenderedAstroRegions(source) {
  let visible = source;
  const opening = /^(?:\uFEFF)?---[ \t]*(?:\r?\n|$)/.exec(visible);
  if (opening) {
    const closing = /^---[ \t]*\r?$/gm;
    closing.lastIndex = opening[0].length;
    const match = closing.exec(visible);
    if (!match)
      refuse('MALFORMED_ASTRO_FRONTMATTER', 'Astro frontmatter lacks a closing delimiter');
    const end = match.index + match[0].length;
    visible = `${maskText(visible.slice(0, end))}${visible.slice(end)}`;
  }
  return visible
    .replace(/<script\b(?![^>]*\/\s*>)[^>]*>[\s\S]*?<\/script\s*>/gi, maskText)
    .replace(/<style\b(?![^>]*\/\s*>)[^>]*>[\s\S]*?<\/style\s*>/gi, maskText);
}

const OTHER_POPULATION_NOUN =
  /\b(?:plugins?|categor(?:y|ies)|items?|commands?|agents?|bundles?|packs?)\b/i;

function namesOtherPopulation(intervening) {
  const skillModifiersRemoved = intervening.replace(/\b(?:agent|plugin)\s+skills\b/gi, 'skills');
  return OTHER_POPULATION_NOUN.test(skillModifiersRemoved);
}

function blocksSkillAssociation(intervening, adjacentNoun = '') {
  const combined = `${intervening}${adjacentNoun}`;
  return namesOtherPopulation(combined) || /(?:^|\s)(?:const|let|var)\s|[;`]/i.test(intervening);
}

function validateRepositoryPath(value, field) {
  nonemptyString(value, field);
  if (
    value.includes('\0') ||
    value.includes('\\') ||
    path.posix.isAbsolute(value) ||
    path.win32.isAbsolute(value) ||
    path.posix.normalize(value) !== value ||
    value
      .split('/')
      .some((component) => component === '' || component === '.' || component === '..')
  ) {
    refuse(
      'UNSAFE_PATH',
      `${field} is not a safe repository-relative path: ${JSON.stringify(value)}`,
    );
  }
  return value;
}

function safeRepositoryEntry(root, relativePath, expectedType, io) {
  validateRepositoryPath(relativePath, 'path');
  let current = root;
  const components = relativePath.split('/');

  for (const [index, component] of components.entries()) {
    current = path.join(current, component);
    let metadata;
    try {
      metadata = io.lstatSync(current);
    } catch (error) {
      refuse(
        'UNREADABLE_PATH',
        `cannot inspect ${relativePath}: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
    if (metadata.isSymbolicLink())
      refuse('SYMLINK_PATH', `${relativePath} traverses a symbolic link`);

    const final = index === components.length - 1;
    if (!final && !metadata.isDirectory()) {
      refuse('NON_DIRECTORY_PATH', `${relativePath} has a non-directory ancestor`);
    }
    if (final && expectedType === 'file' && !metadata.isFile()) {
      refuse('NON_REGULAR_FILE', `${relativePath} is not a regular file`);
    }
    if (final && expectedType === 'directory' && !metadata.isDirectory()) {
      refuse('NON_DIRECTORY_PATH', `${relativePath} is not a directory`);
    }
  }

  let physical;
  try {
    physical = io.realpathSync(current);
  } catch (error) {
    refuse(
      'UNREADABLE_PATH',
      `cannot resolve ${relativePath}: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
  const relative = path.relative(root, physical);
  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    refuse('PATH_ESCAPE', `${relativePath} resolves outside the repository`);
  }
  return current;
}

function safeRead(root, relativePath, io) {
  const absolute = safeRepositoryEntry(root, relativePath, 'file', io);
  try {
    return io.readFileSync(absolute, 'utf8');
  } catch (error) {
    refuse(
      'UNREADABLE_FILE',
      `cannot read ${relativePath}: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

function parseRegistry(root, io) {
  const contents = safeRead(root, REGISTRY_PATH, io);
  try {
    return JSON.parse(contents);
  } catch (error) {
    refuse(
      'MALFORMED_JSON',
      `${REGISTRY_PATH} is not valid JSON: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

function validateCohorts(registry) {
  if (!registry || typeof registry !== 'object' || Array.isArray(registry)) {
    refuse('INVALID_REGISTRY', 'registry root must be an object');
  }
  if (registry.schemaVersion !== 1) refuse('INVALID_SCHEMA_VERSION', 'schemaVersion must equal 1');
  if (
    !registry.cohorts ||
    typeof registry.cohorts !== 'object' ||
    Array.isArray(registry.cohorts)
  ) {
    refuse('INVALID_REGISTRY', 'cohorts must be an object');
  }

  const actualKeys = Object.keys(registry.cohorts).sort();
  const expectedKeys = [...CANONICAL_COHORTS].sort();
  if (JSON.stringify(actualKeys) !== JSON.stringify(expectedKeys)) {
    refuse('INVALID_COHORT_KEYS', `cohorts must contain exactly: ${CANONICAL_COHORTS.join(', ')}`);
  }

  for (const cohort of CANONICAL_COHORTS) {
    const entry = registry.cohorts[cohort];
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
      refuse('INVALID_COHORT', `cohorts.${cohort} must be an object`);
    }
    if (entry.label !== cohort) {
      refuse('INVALID_COHORT', `cohorts.${cohort}.label must equal ${JSON.stringify(cohort)}`);
    }
    nonemptyString(entry.description, `cohorts.${cohort}.description`);
    if (entry.resolver !== 'scripts/corpus-resolver.mjs') {
      refuse(
        'INVALID_COHORT_RESOLVER',
        `cohorts.${cohort}.resolver must equal "scripts/corpus-resolver.mjs"`,
      );
    }
    const command = `node scripts/corpus-resolver.mjs --cohort ${cohort} --json`;
    if (entry.command !== command) {
      refuse(
        'INVALID_COHORT_COMMAND',
        `cohorts.${cohort}.command must equal ${JSON.stringify(command)}`,
      );
    }
  }
}

function literalOccurrences(source, literal) {
  const occurrences = [];
  let offset = 0;
  while (offset <= source.length) {
    const found = source.indexOf(literal, offset);
    if (found === -1) break;
    occurrences.push(found);
    offset = found + Math.max(literal.length, 1);
  }
  return occurrences;
}

function lineAtOffset(source, offset) {
  return source.slice(0, offset).split('\n').length;
}

function hasLabelNearLine(lines, label, line) {
  const start = Math.max(0, line - 1 - LABEL_LINE_WINDOW);
  const end = Math.min(lines.length, line + LABEL_LINE_WINDOW);
  const expected = foldedText(label);
  return lines.slice(start, end).some((candidate) => foldedText(candidate).includes(expected));
}

function validateDiscovery(registry) {
  if (
    !registry.discovery ||
    typeof registry.discovery !== 'object' ||
    Array.isArray(registry.discovery)
  ) {
    refuse('INVALID_DISCOVERY', 'discovery must be an object');
  }
  const expected = {
    roots: DISCOVERY_ROOTS,
    extension: '.astro',
    noun: 'skills',
    dynamicTerms: DISCOVERY_DYNAMIC_TERMS,
    ignoredPhrases: DISCOVERY_IGNORED_PHRASES,
  };
  if (JSON.stringify(registry.discovery) !== JSON.stringify(expected)) {
    refuse('INVALID_DISCOVERY', `discovery must equal ${JSON.stringify(expected)}`);
  }
  return expected;
}

function validateSurfaces(registry, root, io) {
  if (!Array.isArray(registry.surfaces)) refuse('INVALID_REGISTRY', 'surfaces must be an array');

  const knownCohorts = new Set(CANONICAL_COHORTS);
  const exactPaths = new Set();
  const foldedPaths = new Map();
  const registeredPaths = new Set();
  const registeredExpressions = new Map();
  let enforced = 0;
  let deferred = 0;

  function registerSurfacePath(surfacePath) {
    if (exactPaths.has(surfacePath))
      refuse('DUPLICATE_SURFACE_PATH', `duplicate surface path: ${surfacePath}`);
    exactPaths.add(surfacePath);
    const folded = foldedPath(surfacePath);
    if (foldedPaths.has(folded)) {
      refuse(
        'CASEFOLD_SURFACE_COLLISION',
        `surface paths collide after NFC/case folding: ${foldedPaths.get(folded)} and ${surfacePath}`,
      );
    }
    foldedPaths.set(folded, surfacePath);
    registeredPaths.add(surfacePath);
  }

  for (const [index, surface] of registry.surfaces.entries()) {
    const field = `surfaces[${index}]`;
    if (!surface || typeof surface !== 'object' || Array.isArray(surface)) {
      refuse('INVALID_SURFACE', `${field} must be an object`);
    }
    const surfacePath = validateRepositoryPath(surface.path, `${field}.path`);
    nonemptyString(surface.classification, `${field}.classification`);

    registerSurfacePath(surfacePath);

    if (surface.status === 'deferred') {
      nonemptyString(surface.owner, `${field}.owner`);
      nonemptyString(surface.reason, `${field}.reason`);
      if (surface.cohort !== undefined && !knownCohorts.has(surface.cohort)) {
        refuse('UNKNOWN_COHORT', `${field}.cohort is unknown: ${JSON.stringify(surface.cohort)}`);
      }
      safeRead(root, surfacePath, io);
      registeredExpressions.set(surfacePath, null);
      deferred += 1;
      continue;
    }

    if (surface.status !== 'enforced') {
      refuse('INVALID_SURFACE_STATUS', `${field}.status must be "enforced" or "deferred"`);
    }
    if (!knownCohorts.has(surface.cohort)) {
      refuse('UNKNOWN_COHORT', `${field}.cohort is unknown: ${JSON.stringify(surface.cohort)}`);
    }
    const expression = nonemptyString(surface.expression, `${field}.expression`);
    const label = nonemptyString(surface.label, `${field}.label`);
    const provenance = nonemptyString(surface.provenance, `${field}.provenance`);
    if (!foldedText(label).includes(foldedText(surface.cohort))) {
      refuse(
        'COHORT_LABEL_MISMATCH',
        `${field}.label must name cohort ${JSON.stringify(surface.cohort)}`,
      );
    }
    if (!provenance.includes(surface.cohort)) {
      refuse(
        'COHORT_PROVENANCE_MISMATCH',
        `${field}.provenance must name cohort ${JSON.stringify(surface.cohort)}`,
      );
    }

    const rawSource = safeRead(root, surfacePath, io);
    const source = stripComments(rawSource);
    const visibleSource = stripComments(maskNonRenderedAstroRegions(rawSource));
    const expressions = [expression];
    if (surface.deferredExpressions !== undefined) {
      if (!Array.isArray(surface.deferredExpressions)) {
        refuse('INVALID_DEFERRED_EXPRESSION', `${field}.deferredExpressions must be an array`);
      }
      for (const [claimIndex, claim] of surface.deferredExpressions.entries()) {
        const claimField = `${field}.deferredExpressions[${claimIndex}]`;
        if (!claim || typeof claim !== 'object' || Array.isArray(claim)) {
          refuse('INVALID_DEFERRED_EXPRESSION', `${claimField} must be an object`);
        }
        const claimExpression = nonemptyString(claim.expression, `${claimField}.expression`);
        nonemptyString(claim.classification, `${claimField}.classification`);
        nonemptyString(claim.owner, `${claimField}.owner`);
        nonemptyString(claim.reason, `${claimField}.reason`);
        if (expressions.includes(claimExpression)) {
          refuse(
            'DUPLICATE_SURFACE_EXPRESSION',
            `${surfacePath} registers expression more than once: ${JSON.stringify(claimExpression)}`,
          );
        }
        if (literalOccurrences(source, claimExpression).length === 0) {
          refuse(
            'MISSING_EXPRESSION',
            `${surfacePath} does not contain deferred expression ${JSON.stringify(claimExpression)}`,
          );
        }
        expressions.push(claimExpression);
        deferred += 1;
      }
    }
    registeredExpressions.set(surfacePath, expressions);
    const expressionOffsets = literalOccurrences(visibleSource, expression);
    if (expressionOffsets.length === 0) {
      refuse(
        'MISSING_EXPRESSION',
        `${surfacePath} does not contain expression ${JSON.stringify(expression)}`,
      );
    }
    const lines = visibleSource.split(/\r?\n/);
    for (const offset of expressionOffsets) {
      const line = lineAtOffset(visibleSource, offset);
      if (!hasLabelNearLine(lines, label, line)) {
        refuse(
          'MISSING_COHORT_LABEL',
          `${surfacePath}:${line} lacks label ${JSON.stringify(label)} within ${LABEL_LINE_WINDOW} lines`,
        );
      }
    }

    const provenanceCount = literalOccurrences(visibleSource, provenance).length;
    if (provenanceCount !== 1) {
      refuse(
        'INVALID_PROVENANCE_COUNT',
        `${surfacePath} must contain provenance marker exactly once (found ${provenanceCount})`,
      );
    }
    enforced += 1;
  }

  if (!Array.isArray(registry.deferredGroups)) {
    refuse('INVALID_REGISTRY', 'deferredGroups must be an array');
  }
  for (const [groupIndex, group] of registry.deferredGroups.entries()) {
    const field = `deferredGroups[${groupIndex}]`;
    if (!group || typeof group !== 'object' || Array.isArray(group)) {
      refuse('INVALID_DEFERRED_GROUP', `${field} must be an object`);
    }
    nonemptyString(group.classification, `${field}.classification`);
    nonemptyString(group.owner, `${field}.owner`);
    nonemptyString(group.reason, `${field}.reason`);
    if (!Array.isArray(group.paths) || group.paths.length === 0) {
      refuse('INVALID_DEFERRED_GROUP', `${field}.paths must be a nonempty array`);
    }
    for (const [pathIndex, candidate] of group.paths.entries()) {
      const surfacePath = validateRepositoryPath(candidate, `${field}.paths[${pathIndex}]`);
      registerSurfacePath(surfacePath);
      safeRead(root, surfacePath, io);
      registeredExpressions.set(surfacePath, null);
      deferred += 1;
    }
  }

  return { enforced, deferred, registeredExpressions, registeredPaths };
}

export function findPublishedSkillCountEvidence(source, discovery) {
  let searchable = stripComments(source);
  for (const phrase of discovery.ignoredPhrases) {
    searchable = searchable.replaceAll(phrase, ' '.repeat(phrase.length));
  }
  const terms = discovery.dynamicTerms.join('|');
  const dynamicExpressionSource = String.raw`\$?\{[^}\n]{0,200}(?:${terms})[^}\n]{0,200}\}`;
  const evidence = [];
  const numericBefore = /\b\d[\d,]*(?:\.\d+)?\+?(?:-\d+)?\b[^\n]{0,100}$/i;
  const folded = searchable.toLocaleLowerCase('en-US');
  const noun = discovery.noun.toLocaleLowerCase('en-US');
  let offset = 0;
  while (offset < folded.length) {
    const found = folded.indexOf(noun, offset);
    if (found === -1) break;
    offset = found + noun.length;
    const previous = folded[found - 1] ?? '';
    const next = folded[offset] ?? '';
    if (/[a-z0-9_]/i.test(previous) || /[a-z0-9_]/i.test(next)) continue;
    const beforeStart = Math.max(0, found - 240);
    const before = searchable.slice(beforeStart, found);
    const after = searchable.slice(offset, Math.min(searchable.length, offset + 120));
    const beforeCandidates = [];
    const afterCandidates = [];

    for (const match of before.matchAll(new RegExp(dynamicExpressionSource, 'gi'))) {
      const absolute = beforeStart + match.index;
      const intervening = searchable.slice(absolute + match[0].length, found);
      beforeCandidates.push({
        distance: found - (absolute + match[0].length),
        // Include the noun itself so modifiers such as "Agent Skills" are
        // treated as one skill label rather than an intervening agent count.
        interveningOtherPopulation: blocksSkillAssociation(intervening, noun),
        kind: 'dynamic',
        line: lineAtOffset(searchable, found),
        nounOffset: found,
        offset: absolute,
        sameLine: !intervening.includes('\n'),
        text: match[0],
      });
    }
    for (const match of after.matchAll(new RegExp(dynamicExpressionSource, 'gi'))) {
      const intervening = searchable.slice(offset, offset + match.index);
      afterCandidates.push({
        distance: match.index,
        interveningOtherPopulation: blocksSkillAssociation(intervening),
        kind: 'dynamic',
        line: lineAtOffset(searchable, found),
        nounOffset: found,
        offset: offset + match.index,
        sameLine: !intervening.includes('\n'),
        text: match[0],
      });
    }
    const numeric = numericBefore.exec(before);
    if (numeric) {
      const absolute = beforeStart + numeric.index;
      const intervening = searchable.slice(absolute + numeric[0].length, found);
      beforeCandidates.push({
        distance: found - (absolute + numeric[0].length),
        interveningOtherPopulation: blocksSkillAssociation(intervening, noun),
        kind: 'numeric',
        line: lineAtOffset(searchable, found),
        nounOffset: found,
        offset: absolute,
        sameLine: !intervening.includes('\n'),
        text: numeric[0],
      });
    }

    beforeCandidates.sort(
      (left, right) => left.distance - right.distance || left.offset - right.offset,
    );
    afterCandidates.sort(
      (left, right) => left.distance - right.distance || left.offset - right.offset,
    );
    const sameLineBefore = beforeCandidates.filter(
      (candidate) => candidate.sameLine && !candidate.interveningOtherPopulation,
    );
    const sameLineAfter = afterCandidates.filter(
      (candidate) => candidate.sameLine && !candidate.interveningOtherPopulation,
    );
    if (sameLineBefore.length > 0) {
      evidence.push(...sameLineBefore);
      continue;
    }
    if (sameLineAfter.length > 0) {
      evidence.push(...sameLineAfter);
      continue;
    }

    const crossLine = [...beforeCandidates, ...afterCandidates].filter(
      (candidate) => !candidate.interveningOtherPopulation,
    );
    const skillNamed = crossLine.filter((candidate) =>
      foldedText(candidate.text).includes('skill'),
    );
    const nearest =
      (skillNamed.length === 1 ? skillNamed[0] : undefined) ??
      crossLine.sort(
        (left, right) => left.distance - right.distance || left.offset - right.offset,
      )[0];
    if (nearest) {
      evidence.push(nearest);
    }
  }
  return evidence;
}

export function containsPublishedSkillCount(source, discovery) {
  return findPublishedSkillCountEvidence(source, discovery).length > 0;
}

function evidenceMatchesExpression(candidateText, expression) {
  let offset = 0;
  while (offset <= candidateText.length) {
    const found = candidateText.indexOf(expression, offset);
    if (found === -1) return false;
    const before = candidateText[found - 1] ?? '';
    const after = candidateText[found + expression.length] ?? '';
    if (!/[A-Za-z0-9_$]/.test(before) && !/[A-Za-z0-9_$]/.test(after)) return true;
    offset = found + Math.max(expression.length, 1);
  }
  return false;
}

function discoverPublicCountSources(root, registeredPaths, registeredExpressions, discovery, io) {
  let discovered = 0;
  const pending = [...discovery.roots];

  while (pending.length > 0) {
    const directory = pending.shift();
    const absolute = safeRepositoryEntry(root, directory, 'directory', io);
    let entries;
    try {
      entries = io.readdirSync(absolute, { withFileTypes: true });
    } catch (error) {
      refuse(
        'UNREADABLE_DISCOVERY_ROOT',
        `cannot inspect ${directory}: ${error instanceof Error ? error.message : String(error)}`,
      );
    }

    for (const entry of [...entries].sort((left, right) =>
      left.name.localeCompare(right.name, 'en'),
    )) {
      const relativePath = `${directory}/${entry.name}`;
      if (entry.isSymbolicLink()) {
        refuse('SYMLINK_PATH', `${relativePath} is a symbolic link inside the discovery tree`);
      }
      if (entry.isDirectory()) {
        safeRepositoryEntry(root, relativePath, 'directory', io);
        pending.push(relativePath);
        continue;
      }
      if (!entry.name.endsWith(discovery.extension)) continue;
      const source = safeRead(root, relativePath, io);
      const countEvidence = findPublishedSkillCountEvidence(source, discovery);
      if (countEvidence.length === 0) continue;
      discovered += 1;
      if (!registeredPaths.has(relativePath)) {
        refuse(
          'UNREGISTERED_PUBLIC_COUNT',
          `${relativePath} contains a published skill count but is not registered`,
        );
      }
      const allowedExpressions = registeredExpressions.get(relativePath);
      if (allowedExpressions === null) continue;
      const unregistered = countEvidence.find(
        (candidate) =>
          !allowedExpressions.some((expression) =>
            evidenceMatchesExpression(candidate.text, expression),
          ),
      );
      if (unregistered) {
        refuse(
          'UNREGISTERED_PUBLIC_COUNT_EXPRESSION',
          `${relativePath}:${lineAtOffset(source, unregistered.offset)} contains an unregistered published skill-count expression`,
        );
      }
    }
  }
  return discovered;
}

function defaultReport() {
  return {
    schemaVersion: 1,
    cohorts: 0,
    enforced: 0,
    deferred: 0,
    discovered: 0,
    allow: false,
    decision: 'REFUSE',
    findings: [],
  };
}

export function checkPublishedCountCohorts({ root = process.cwd(), io = fs } = {}) {
  const report = defaultReport();
  try {
    let repositoryRoot;
    try {
      repositoryRoot = io.realpathSync(path.resolve(root));
      if (!io.lstatSync(repositoryRoot).isDirectory())
        refuse('INVALID_ROOT', 'repository root is not a directory');
    } catch (error) {
      if (error instanceof CohortCheckError) throw error;
      refuse(
        'INVALID_ROOT',
        `cannot resolve repository root: ${error instanceof Error ? error.message : String(error)}`,
      );
    }

    const registry = parseRegistry(repositoryRoot, io);
    validateCohorts(registry);
    const discovery = validateDiscovery(registry);
    report.cohorts = CANONICAL_COHORTS.length;
    const surfaces = validateSurfaces(registry, repositoryRoot, io);
    report.enforced = surfaces.enforced;
    report.deferred = surfaces.deferred;
    report.discovered = discoverPublicCountSources(
      repositoryRoot,
      surfaces.registeredPaths,
      surfaces.registeredExpressions,
      discovery,
      io,
    );
    report.allow = true;
    report.decision = 'ALLOW';
  } catch (error) {
    report.findings.push({
      code: error instanceof CohortCheckError ? error.code : 'UNEXPECTED_ERROR',
      message: error instanceof Error ? error.message : String(error),
    });
  }
  return report;
}

export function parseArguments(argv) {
  let root = process.cwd();
  let json = false;
  let sawRoot = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--json') {
      if (json) refuse('UNKNOWN_ARGUMENT', '--json may be provided only once');
      json = true;
      continue;
    }
    if (argument === '--root') {
      if (sawRoot || index + 1 >= argv.length) {
        refuse('UNKNOWN_ARGUMENT', '--root requires exactly one value');
      }
      root = argv[index + 1];
      sawRoot = true;
      index += 1;
      continue;
    }
    refuse('UNKNOWN_ARGUMENT', `unknown argument: ${argument}`);
  }
  return { root, json };
}

function formatReport(report) {
  const summary = `published-count-cohorts: ${report.decision} cohorts=${report.cohorts} enforced=${report.enforced} deferred=${report.deferred} discovered=${report.discovered}`;
  if (report.findings.length === 0) return summary;
  return `${summary}\n${report.findings.map((finding) => `${finding.code}: ${finding.message}`).join('\n')}`;
}

function main() {
  let options;
  try {
    options = parseArguments(process.argv.slice(2));
  } catch (error) {
    const report = defaultReport();
    report.findings.push({
      code: error instanceof CohortCheckError ? error.code : 'UNKNOWN_ARGUMENT',
      message: error instanceof Error ? error.message : String(error),
    });
    process.stderr.write(`${formatReport(report)}\n`);
    process.exitCode = 1;
    return;
  }

  const report = checkPublishedCountCohorts({ root: options.root });
  const output = options.json ? JSON.stringify(report, null, 2) : formatReport(report);
  (report.allow ? process.stdout : process.stderr).write(`${output}\n`);
  if (!report.allow) process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
