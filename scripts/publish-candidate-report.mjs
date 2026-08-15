import fs from 'node:fs';
import path from 'node:path';
import { isPathInside, resolvePluginProvenance } from './plugin-provenance.mjs';

const ROOT = process.cwd();

function parseArgs(argv) {
  const args = { all: false, changedFiles: null, scope: null };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--all') args.all = true;
    else if (arg === '--changed-files') args.changedFiles = argv[++index];
    else if (arg === '--scope') args.scope = argv[++index];
    else if (arg === '--json') args.json = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if ((args.all ? 1 : 0) + (args.changedFiles ? 1 : 0) !== 1) {
    throw new Error('Choose exactly one of --all or --changed-files <file>.');
  }
  return args;
}

function walkPackageDirs(root) {
  const result = [];
  const walk = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (entry.name === 'node_modules' || entry.name === '.git') continue;
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(fullPath);
      else if (entry.name === 'package.json') {
        const packageDir = path.dirname(fullPath);
        if (
          fs.existsSync(path.join(packageDir, '.claude-plugin')) ||
          fs.existsSync(path.join(packageDir, 'plugin.json'))
        ) {
          result.push(packageDir);
        }
      }
    }
  };
  walk(path.join(root, 'plugins'));
  return result.sort();
}

function readPackage(directory) {
  try {
    const value = JSON.parse(fs.readFileSync(path.join(directory, 'package.json'), 'utf8'));
    if (!value || typeof value !== 'object' || typeof value.name !== 'string') return null;
    return value;
  } catch {
    return null;
  }
}

function changedFilesFrom(filePath) {
  return fs
    .readFileSync(filePath, 'utf8')
    .split(/\r?\n/)
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value) => path.resolve(ROOT, value));
}

export function buildPublishCandidateReport({
  root = ROOT,
  all = false,
  changedFiles = [],
  scope = null,
} = {}) {
  const rootPath = path.resolve(root);
  const packageDirs = walkPackageDirs(rootPath).filter((directory) => {
    if (all) return true;
    return changedFiles.some(
      (file) => isPathInside(rootPath, file) && isPathInside(directory, file),
    );
  });

  const report = {
    firstPartyCandidates: [],
    mirrorSkipped: [],
    refused: [],
    privateSkipped: [],
    nonPackageIgnored: [],
  };

  for (const directory of packageDirs) {
    const packageJson = readPackage(directory);
    const relativeDir = path.relative(rootPath, directory);
    if (!packageJson || (scope && !packageJson.name.startsWith(scope))) {
      report.nonPackageIgnored.push(relativeDir);
      continue;
    }

    const provenance = resolvePluginProvenance(relativeDir, { root: rootPath });
    const row = {
      name: packageJson.name,
      version: packageJson.version ?? '0.0.0',
      dir: relativeDir,
    };
    if (provenance.status === 'refused') {
      report.refused.push({ ...row, reasonCode: provenance.reasonCode });
    } else if (provenance.status === 'mirror') {
      report.mirrorSkipped.push({ ...row, reasonCode: provenance.reasonCode });
    } else if (packageJson.private === true) {
      report.privateSkipped.push({ ...row, reasonCode: 'PRIVATE_PACKAGE' });
    } else {
      report.firstPartyCandidates.push({ ...row, reasonCode: 'FIRST_PARTY_CANDIDATE' });
    }
  }

  return report;
}

function main() {
  const args = parseArgs(process.argv);
  const report = buildPublishCandidateReport({
    all: args.all,
    changedFiles: args.changedFiles ? changedFilesFrom(args.changedFiles) : [],
    scope: args.scope,
  });
  process.stdout.write(`${JSON.stringify(report)}\n`);
  if (report.refused.length > 0) process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) main();
