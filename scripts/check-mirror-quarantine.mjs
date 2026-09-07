#!/usr/bin/env node
/** Assert every external mirror has a non-publishable E8 disposition. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

import { resolvePluginProvenance } from './plugin-provenance.mjs';

function fail(message) {
  throw new Error(`check-mirror-quarantine: ${message}`);
}

function safeRepoPath(value, label) {
  if (typeof value !== 'string' || value.length === 0) fail(`${label} must be a non-empty path`);
  const normalized = value.replaceAll('\\', '/').replace(/^\.\//, '');
  if (
    path.posix.normalize(normalized) !== normalized ||
    normalized.startsWith('/') ||
    normalized.split('/').includes('..')
  ) {
    fail(`${label} escapes the repository: ${value}`);
  }
  return normalized;
}

function sameStrings(left, right) {
  const a = [...new Set(left)].sort();
  const b = [...new Set(right)].sort();
  return a.length === b.length && a.every((value, index) => value === b[index]);
}

function optionalJson(root, relativePath, fallback) {
  const absolute = path.join(root, relativePath);
  return fs.existsSync(absolute) ? JSON.parse(fs.readFileSync(absolute, 'utf8')) : fallback;
}

function markdownLinkTo(text, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`\\[${escaped}\\]\\(`, 'i').test(text);
}

export function checkMirrorQuarantine({ root = process.cwd() } = {}) {
  const ledger = JSON.parse(
    fs.readFileSync(path.join(root, 'freshie/disposition-ledger.json'), 'utf8'),
  );
  if (ledger?.schema_version !== 'disposition-ledger/v1' || !Array.isArray(ledger.artifacts)) {
    fail('disposition ledger is malformed');
  }
  const rows = new Map(ledger.artifacts.map((row) => [row.path, row]));
  const gradePaths = fs
    .readFileSync(path.join(root, 'freshie/grades.csv'), 'utf8')
    .trim()
    .split(/\r?\n/)
    .slice(1)
    .map((line) => `${line.split(',')[0]}/SKILL.md`);
  const mirrors = gradePaths.filter(
    (skill) => resolvePluginProvenance(path.posix.dirname(skill), { root }).status === 'mirror',
  );
  const bad = mirrors.filter(
    (skill) => !['QUARANTINE', 'CERTIFY-UPSTREAM'].includes(rows.get(skill)?.disposition),
  );
  if (bad.length) fail(`mirror without non-publishable disposition: ${bad.join(', ')}`);

  const manifestPath = path.join(root, 'skills/.curated/MANIFEST.json');
  const curated = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const curatedSources = new Set((curated.skills ?? []).map((row) => row.source_path));
  const leaked = mirrors.filter((skill) => curatedSources.has(skill));
  if (leaked.length)
    fail(`quarantined mirror appears in curated publication: ${leaked.join(', ')}`);

  const sourceDocument = yaml.load(fs.readFileSync(path.join(root, 'sources.yaml'), 'utf8'));
  if (!Array.isArray(sourceDocument?.sources)) fail('sources.yaml has no sources array');
  const catalogDocument = JSON.parse(
    fs.readFileSync(path.join(root, '.claude-plugin/marketplace.extended.json'), 'utf8'),
  );
  if (!Array.isArray(catalogDocument?.plugins)) fail('marketplace catalog has no plugins array');
  const catalogRows = new Map(catalogDocument.plugins.map((plugin) => [plugin?.name, plugin]));
  const installCatalog = JSON.parse(
    fs.readFileSync(path.join(root, '.claude-plugin/marketplace.json'), 'utf8'),
  );
  const siteCatalog = JSON.parse(
    fs.readFileSync(path.join(root, 'marketplace/src/data/catalog.json'), 'utf8'),
  );
  const skillsCatalog = JSON.parse(
    fs.readFileSync(path.join(root, 'marketplace/src/data/skills-catalog.json'), 'utf8'),
  );
  const skillsIndex = JSON.parse(
    fs.readFileSync(path.join(root, 'marketplace/src/data/skills-index.json'), 'utf8'),
  );
  const searchIndex = JSON.parse(
    fs.readFileSync(path.join(root, 'marketplace/src/data/unified-search-index.json'), 'utf8'),
  );
  const readmeSections = optionalJson(root, 'marketplace/src/data/readme-sections.json', {});
  const coworkManifest = optionalJson(root, 'marketplace/src/data/cowork-manifest.json', {
    plugins: [],
  });
  const spotlights = JSON.parse(
    fs.readFileSync(path.join(root, 'marketplace/src/data/spotlights.json'), 'utf8'),
  );
  const rootReadme = fs.readFileSync(path.join(root, 'README.md'), 'utf8');
  const declared = new Map();

  for (const source of sourceDocument.sources) {
    const dispositions = [source?.publication_disposition, source?.copyleft_disposition].filter(
      (value) => value !== undefined,
    );
    if (dispositions.length === 0) continue;
    if (dispositions.length > 1) fail(`${source.name} has multiple publication dispositions`);
    const disposition = dispositions[0];
    if (
      !disposition ||
      typeof disposition !== 'object' ||
      disposition.status !== 'quarantined' ||
      !Array.isArray(disposition.channels) ||
      disposition.channels.length !== 0 ||
      typeof disposition.rationale !== 'string' ||
      disposition.rationale.trim().length === 0
    ) {
      fail(`${source?.name ?? '<unnamed source>'} has malformed publication disposition`);
    }
    if (catalogRows.get(source.name)?.publication !== 'quarantined') {
      fail(`${source.name} must remain an explicitly quarantined extended-catalog record`);
    }
    const leakedSurfaces = [];
    if ((installCatalog.plugins ?? []).some((plugin) => plugin?.name === source.name)) {
      leakedSurfaces.push('CLI install catalog');
    }
    if (
      (siteCatalog.plugins ?? []).some(
        (plugin) => plugin?.name === source.name || plugin?.slug === source.name,
      )
    ) {
      leakedSurfaces.push('website catalog');
    }
    if (
      (skillsCatalog.skills ?? []).some(
        (skill) =>
          skill?.parentPlugin?.name === source.name ||
          safeRepoPath(skill?.filePath ?? 'missing', 'skills catalog filePath').startsWith(
            `${safeRepoPath(source.target_path, `${source.name}.target_path`)}/`,
          ),
      )
    ) {
      leakedSurfaces.push('website skills catalog');
    }
    if ((skillsIndex.skills ?? []).some((skill) => skill?.parentPlugin === source.name)) {
      leakedSurfaces.push('website skills index');
    }
    if (
      (searchIndex.items ?? []).some(
        (item) => item?.name === source.name || item?.parentPlugin?.name === source.name,
      )
    ) {
      leakedSurfaces.push('unified search');
    }
    if (Object.hasOwn(readmeSections, source.name)) {
      leakedSurfaces.push('website README sections');
    }
    if ((coworkManifest.plugins ?? []).some((plugin) => plugin?.name === source.name)) {
      leakedSurfaces.push('Cowork downloads');
    }
    if ((spotlights.hallOfFame ?? []).some((item) => item?.pluginSlug === source.name)) {
      leakedSurfaces.push('community spotlight');
    }
    if (markdownLinkTo(rootReadme, source.name)) {
      leakedSurfaces.push('root README recommendation');
    }
    if (leakedSurfaces.length > 0) {
      fail(`${source.name} quarantine leaks through ${leakedSurfaces.join(', ')}`);
    }
    if (source.publication_disposition === undefined) continue;
    if (!Array.isArray(disposition.artifacts) || disposition.artifacts.length === 0) {
      fail(`${source.name} publication_disposition has no governed artifacts`);
    }
    const target = safeRepoPath(source.target_path, `${source.name}.target_path`);
    for (const [index, artifact] of disposition.artifacts.entries()) {
      const artifactPath = safeRepoPath(
        artifact?.path,
        `${source.name}.publication_disposition.artifacts[${index}].path`,
      );
      if (artifactPath !== `${target}/SKILL.md` && !artifactPath.startsWith(`${target}/`)) {
        fail(`${source.name} disposition artifact is outside its mirror: ${artifactPath}`);
      }
      if (!fs.statSync(path.join(root, artifactPath)).isFile()) {
        fail(`${source.name} disposition artifact is missing: ${artifactPath}`);
      }
      if (
        !Array.isArray(artifact.reason_codes) ||
        artifact.reason_codes.length === 0 ||
        !artifact.reason_codes.every((code) => typeof code === 'string' && code.length > 0)
      ) {
        fail(`${source.name} disposition artifact has no reason_codes: ${artifactPath}`);
      }
      if (declared.has(artifactPath)) fail(`duplicate publication disposition: ${artifactPath}`);
      declared.set(artifactPath, artifact.reason_codes);
    }
  }

  const g0Mirrors = [];
  for (const row of ledger.artifacts.filter((artifact) => artifact?.gate === 'G0')) {
    const provenance = resolvePluginProvenance(path.posix.dirname(row.path), { root });
    if (provenance.status !== 'mirror') {
      fail(`first-party G0 finding must be remediated, not dispositioned: ${row.path}`);
    }
    g0Mirrors.push(row.path);
    const reasonCodes = declared.get(row.path);
    if (!reasonCodes) fail(`G0 mirror has no source publication disposition: ${row.path}`);
    if (
      row.disposition !== 'QUARANTINE' ||
      !Array.isArray(row.reason_codes) ||
      !sameStrings(reasonCodes, row.reason_codes)
    ) {
      fail(`G0 mirror disposition contradicts the ledger: ${row.path}`);
    }
  }
  const staleDeclarations = [...declared.keys()].filter(
    (artifact) => !g0Mirrors.includes(artifact),
  );
  if (staleDeclarations.length) {
    fail(`publication disposition has no live G0 finding: ${staleDeclarations.join(', ')}`);
  }

  return {
    mirrors: mirrors.length,
    quarantined: mirrors.filter((skill) => rows.get(skill)?.disposition === 'QUARANTINE').length,
    g0Quarantined: g0Mirrors.length,
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const result = checkMirrorQuarantine();
    console.log(
      `mirror quarantine: OK (${result.quarantined}/${result.mirrors} quarantined; ` +
        `${result.g0Quarantined} G0 findings have zero publication channels)`,
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
