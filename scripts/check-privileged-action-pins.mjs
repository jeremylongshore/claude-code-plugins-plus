#!/usr/bin/env node

import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const WORKFLOW_DIRECTORY = '.github/workflows';
const FULL_SHA = /^[0-9a-f]{40}$/;

export function isPrivilegedWorkflowText(text) {
  return (
    /\bid-token:\s*write\b/.test(text) ||
    /\bsecrets\.NPM_TOKEN\b/.test(text) ||
    /\bsigstore\/cosign-installer@/.test(text)
  );
}

export function externalActionUses(path, text) {
  const uses = [];
  for (const [index, line] of text.split('\n').entries()) {
    const match = line.match(/\buses:\s*([^\s#]+)/);
    if (!match || match[1].startsWith('./') || match[1].startsWith('docker://')) continue;
    const at = match[1].lastIndexOf('@');
    if (at <= 0) {
      uses.push({ action: match[1], line: index + 1, path, ref: '' });
      continue;
    }
    uses.push({
      action: match[1].slice(0, at),
      line: index + 1,
      path,
      ref: match[1].slice(at + 1),
    });
  }
  return uses;
}

export function inspectWorkflowEntries(entries) {
  const privileged = entries.filter((entry) => isPrivilegedWorkflowText(entry.text));
  const uses = privileged.flatMap((entry) => externalActionUses(entry.path, entry.text));
  return {
    distinctActions: [...new Set(uses.map((entry) => entry.action))].sort(),
    privilegedWorkflows: privileged.map((entry) => entry.path).sort(),
    unpinned: uses.filter((entry) => !FULL_SHA.test(entry.ref)),
    uses,
  };
}

export function inspectPrivilegedActionPins(root = ROOT) {
  const directory = join(root, WORKFLOW_DIRECTORY);
  const entries = readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && /\.ya?ml$/.test(entry.name))
    .map((entry) => {
      const absolute = join(directory, entry.name);
      return {
        path: relative(root, absolute).replaceAll('\\', '/'),
        text: readFileSync(absolute, 'utf8'),
      };
    });
  return inspectWorkflowEntries(entries);
}

function main() {
  const report = inspectPrivilegedActionPins();
  if (report.unpinned.length > 0) {
    console.error('privileged-action-pins: FAIL — mutable external action references found');
    for (const entry of report.unpinned) {
      console.error(`  ${entry.path}:${entry.line} ${entry.action}@${entry.ref || '<missing>'}`);
    }
    process.exitCode = 1;
    return;
  }
  console.log(
    `privileged-action-pins: OK (${report.privilegedWorkflows.length} workflows, ${report.uses.length} uses, ${report.distinctActions.length} distinct actions)`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
