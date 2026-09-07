#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, resolve } from 'node:path';
import { main as generateSbom } from './generate-publication-sbom.mjs';

export function buildReport(completed, { sbomDir }) {
  if (!Array.isArray(completed) || completed.length === 0)
    throw new Error('completed publications must be a non-empty array');
  mkdirSync(sbomDir, { recursive: true });
  const names = new Set();
  return {
    schema_version: 'publication-report/v1',
    publications: completed.map((publication, index) => {
      if (!publication || typeof publication !== 'object')
        throw new Error(`publication ${index} is invalid`);
      const { channel, name, package_path: packagePath, ...facts } = publication;
      if (
        !['npm', 'mcp-registry', 'github-release'].includes(channel) ||
        typeof name !== 'string' ||
        !name
      )
        throw new Error(`publication ${index} has invalid channel or name`);
      if (typeof packagePath !== 'string' || !packagePath)
        throw new Error(`publication ${name} missing package_path`);
      const manifestPath = resolve(packagePath, 'package.json');
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
      if (manifest.name !== name && channel === 'npm')
        throw new Error(
          `publication name ${name} does not match ${packagePath} (${manifest.name})`,
        );
      if (names.has(name)) throw new Error(`duplicate completed publication ${name}`);
      names.add(name);
      const sbomPath = resolve(
        sbomDir,
        `${String(index + 1).padStart(3, '0')}-${basename(packagePath)}.cdx.json`,
      );
      return {
        channel,
        name,
        ...(channel === 'npm' ? {} : { package_name: manifest.name }),
        ...facts,
        sbom_digest: generateSbom(['--package', manifestPath, '--out', sbomPath]),
        sbom_format: 'CycloneDX',
      };
    }),
  };
}

export function main(argv = process.argv.slice(2)) {
  const completedAt = argv.indexOf('--completed');
  const outAt = argv.indexOf('--out');
  const sbomAt = argv.indexOf('--sbom-dir');
  if ([completedAt, outAt, sbomAt].some((at) => at < 0))
    throw new Error('usage: --completed <json> --out <json> --sbom-dir <dir>');
  const report = buildReport(JSON.parse(readFileSync(argv[completedAt + 1], 'utf8')), {
    sbomDir: resolve(argv[sbomAt + 1]),
  });
  const output = `${JSON.stringify(report)}\n`;
  writeFileSync(resolve(argv[outAt + 1]), output);
  return `sha256:${createHash('sha256').update(output).digest('hex')}`;
}
if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
