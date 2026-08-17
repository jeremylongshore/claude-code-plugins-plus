#!/usr/bin/env node

/** Enforce the publication boundary for externally mirrored plugins. */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function sourceMarkers(directory) {
  const found = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.isSymbolicLink()) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) found.push(...sourceMarkers(path));
    else if (entry.name === '.source.json') found.push(path);
  }
  return found;
}

export function scanMirrorPackages(root) {
  const pluginsRoot = join(root, 'plugins');
  const markers = existsSync(pluginsRoot) ? sourceMarkers(pluginsRoot) : [];
  const packages = [];
  const violations = [];

  for (const marker of markers) {
    const directory = dirname(marker);
    const packagePath = join(directory, 'package.json');
    if (!existsSync(packagePath)) continue;
    const packageData = JSON.parse(readFileSync(packagePath, 'utf8'));
    const item = {
      marker: relative(root, marker),
      packagePath: relative(root, packagePath),
      name: packageData.name ?? '(unnamed)',
      private: packageData.private === true,
    };
    packages.push(item);
    if (!item.private) violations.push(item);
  }

  return { markerCount: markers.length, packageCount: packages.length, packages, violations };
}

export function formatReport(result) {
  const lines = [
    `Machine-provenance mirror markers: ${result.markerCount}`,
    `Mirror packages with package.json: ${result.packageCount}`,
    `Private mirror packages: ${result.packageCount - result.violations.length}`,
  ];
  if (result.violations.length) {
    lines.push('Publishability violations:');
    for (const violation of result.violations)
      lines.push(`  ${violation.packagePath} (${violation.name})`);
  } else {
    lines.push('Publishability violations: 0');
  }
  return lines.join('\n');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = process.argv[2] ? resolve(process.argv[2]) : repositoryRoot;
  const result = scanMirrorPackages(root);
  console.log(formatReport(result));
  if (result.violations.length) process.exitCode = 1;
}
