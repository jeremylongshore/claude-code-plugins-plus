#!/usr/bin/env node
/**
 * Protect the model-neutral rename's deliberately frozen compatibility surface.
 *
 * The required CI lane runs the local contract only. `--live` additionally
 * follows the public redirects as an operator receipt; it is intentionally not
 * part of required CI because GitHub and skills.sh availability are external.
 */

import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = join(SCRIPT_DIR, '..');

export const IDENTITY = Object.freeze({
  canonicalRepository: 'jeremylongshore/tons-of-skills-marketplace',
  rootRepositoryUrl: 'git+https://github.com/jeremylongshore/tons-of-skills-marketplace.git',
  cliRepositoryUrl: 'https://github.com/jeremylongshore/tons-of-skills-marketplace.git',
  catalogUrl:
    'https://raw.githubusercontent.com/jeremylongshore/tons-of-skills-marketplace/main/.claude-plugin/marketplace.json',
  marketplaceSlug: 'claude-code-plugins-plus',
  packageName: '@intentsolutionsio/ccpi',
  cliEntry: './dist/index.js',
  installCommand: '/plugin marketplace add jeremylongshore/claude-code-plugins',
  skillsRoute: 'https://skills.sh/jeremylongshore/tons-of-skills-marketplace',
});

export const LIVE_REDIRECTS = Object.freeze([
  {
    label: 'legacy GitHub install repository',
    source: 'https://github.com/jeremylongshore/claude-code-plugins',
    destination: 'https://github.com/jeremylongshore/tons-of-skills-marketplace',
  },
  {
    label: 'legacy GitHub repository',
    source: 'https://github.com/jeremylongshore/claude-code-plugins-plus-skills',
    destination: 'https://github.com/jeremylongshore/tons-of-skills-marketplace',
  },
  {
    label: 'legacy GitHub clone endpoint',
    source: 'https://github.com/jeremylongshore/claude-code-plugins-plus-skills.git',
    destination: 'https://github.com/jeremylongshore/tons-of-skills-marketplace',
  },
  {
    label: 'legacy skills.sh discovery route',
    source: 'https://skills.sh/jeremylongshore/claude-code-plugins-plus-skills',
    destination: IDENTITY.skillsRoute,
  },
]);

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

export function loadIdentitySnapshot(root = DEFAULT_ROOT) {
  return {
    rootPackage: readJson(join(root, 'package.json')),
    cliPackage: readJson(join(root, 'packages/cli/package.json')),
    extendedCatalog: readJson(join(root, '.claude-plugin/marketplace.extended.json')),
    generatedCatalog: readJson(join(root, '.claude-plugin/marketplace.json')),
    readme: readFileSync(join(root, 'README.md'), 'utf8'),
    cliConstantsSource: readFileSync(join(root, 'packages/cli/src/utils/constants.ts'), 'utf8'),
    cliProgramSource: readFileSync(join(root, 'packages/cli/src/program.ts'), 'utf8'),
  };
}

function hasExportedString(source, name, value) {
  const escaped = value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`^\\s*export\\s+const\\s+${name}\\s*=\\s*['"]${escaped}['"]\\s*;`, 'm').test(
    source,
  );
}

export function checkIdentityCompatibility(snapshot) {
  const violations = [];
  const {
    rootPackage,
    cliPackage,
    extendedCatalog,
    generatedCatalog,
    readme,
    cliConstantsSource,
    cliProgramSource,
  } = snapshot;

  if (rootPackage.repository?.url !== IDENTITY.rootRepositoryUrl) {
    violations.push('root package repository URL is not canonical');
  }
  if (
    cliPackage.repository?.url !== IDENTITY.cliRepositoryUrl ||
    cliPackage.repository?.directory !== 'packages/cli'
  ) {
    violations.push('CLI package repository metadata is not canonical');
  }
  if (cliPackage.name !== IDENTITY.packageName) {
    violations.push(`published CLI package identity must remain ${IDENTITY.packageName}`);
  }
  if (cliPackage.bin?.ccpi !== IDENTITY.cliEntry || cliPackage.bin?.tons !== IDENTITY.cliEntry) {
    violations.push('ccpi and tons binary aliases must both resolve to the same CLI entry point');
  }
  if (
    extendedCatalog.name !== IDENTITY.marketplaceSlug ||
    generatedCatalog.name !== IDENTITY.marketplaceSlug
  ) {
    violations.push(`marketplace install identity must remain ${IDENTITY.marketplaceSlug}`);
  }
  if (!readme.includes(IDENTITY.installCommand)) {
    violations.push(`frozen install command is missing: ${IDENTITY.installCommand}`);
  }
  if (!readme.includes(IDENTITY.skillsRoute)) {
    violations.push(`canonical skills.sh route is missing: ${IDENTITY.skillsRoute}`);
  }
  if (!hasExportedString(cliConstantsSource, 'MARKETPLACE_REPO', IDENTITY.canonicalRepository)) {
    violations.push('CLI marketplace repository constant is not canonical');
  }
  if (!hasExportedString(cliConstantsSource, 'MARKETPLACE_SLUG', IDENTITY.marketplaceSlug)) {
    violations.push('CLI marketplace slug no longer preserves the install identity');
  }
  if (!hasExportedString(cliConstantsSource, 'CATALOG_URL', IDENTITY.catalogUrl)) {
    violations.push('CLI catalog URL is not canonical');
  }
  if (!/^\s*\.name\(\s*['"]ccpi['"]\s*\)/m.test(cliProgramSource)) {
    violations.push('existing ccpi program identity is missing');
  }
  if (!/^\s*\.command\(\s*['"]skills['"]\s*\)/m.test(cliProgramSource)) {
    violations.push('portable capability is not exposed through the tons skills command family');
  }

  return violations;
}

function normalizedDestination(value) {
  const url = new URL(value);
  url.hostname = url.hostname.replace(/^www\./, '');
  url.hash = '';
  url.search = '';
  url.pathname = url.pathname.replace(/\.git\/?$/, '').replace(/\/$/, '');
  return url.toString().replace(/\/$/, '');
}

export function checkRedirectResult(contract, response) {
  const violations = [];
  if (response.status < 200 || response.status >= 300) {
    violations.push(`${contract.label} returned HTTP ${response.status}`);
  }
  if (normalizedDestination(response.url) !== normalizedDestination(contract.destination)) {
    violations.push(
      `${contract.label} resolved to ${response.url}, expected ${contract.destination}`,
    );
  }
  return violations;
}

export async function checkLiveRedirects(fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== 'function') {
    throw new TypeError('a fetch implementation is required for live redirect checks');
  }

  const results = [];
  for (const contract of LIVE_REDIRECTS) {
    const response = await fetchImpl(contract.source, {
      redirect: 'follow',
      headers: { 'user-agent': 'tons-of-skills-identity-check/1.0' },
    });
    const violations = checkRedirectResult(contract, response);
    results.push({
      ...contract,
      status: response.status,
      resolved: response.url,
      violations,
    });
    if (response.body && typeof response.body.cancel === 'function') await response.body.cancel();
  }
  return results;
}

async function main() {
  const args = process.argv.slice(2);
  const unknown = args.filter((arg) => arg !== '--live');
  if (unknown.length > 0) {
    console.error(`identity-compatibility: unknown argument(s): ${unknown.join(', ')}`);
    process.exitCode = 2;
    return;
  }

  const violations = checkIdentityCompatibility(loadIdentitySnapshot());
  for (const violation of violations) {
    console.error(`identity-compatibility: VIOLATION — ${violation}`);
  }
  if (violations.length > 0) {
    console.error(`identity-compatibility: FAIL — ${violations.length} local violation(s)`);
    process.exitCode = 1;
    return;
  }
  console.log(
    'identity-compatibility: OK (canonical repository + frozen install/package/CLI identities)',
  );

  if (args.includes('--live')) {
    const results = await checkLiveRedirects();
    const liveViolations = results.flatMap((result) => result.violations);
    for (const result of results) {
      console.log(
        `identity-compatibility: ${result.label}: HTTP ${result.status} -> ${result.resolved}`,
      );
    }
    for (const violation of liveViolations) {
      console.error(`identity-compatibility: LIVE VIOLATION — ${violation}`);
    }
    if (liveViolations.length > 0) {
      console.error(
        `identity-compatibility: LIVE FAIL — ${liveViolations.length} redirect violation(s)`,
      );
      process.exitCode = 1;
      return;
    }
    console.log('identity-compatibility: LIVE OK');
  }
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (isMain) await main();
