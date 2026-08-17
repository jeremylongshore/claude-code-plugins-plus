#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

export const CANONICAL_REPOSITORY = 'jeremylongshore/claude-code-plugins-plus-skills';

export function evaluateWorkflowRun(event, repository = CANONICAL_REPOSITORY) {
  const run = event?.workflow_run ?? {};
  const reasons = [];

  if (run.name !== 'Validate Plugins') reasons.push('WORKFLOW_NAME_MISMATCH');
  if (run.conclusion !== 'success') reasons.push('WORKFLOW_NOT_SUCCESS');
  if (run.event !== 'push') reasons.push('TRIGGER_EVENT_NOT_PUSH');
  if (run.head_branch !== 'main') reasons.push('HEAD_BRANCH_NOT_MAIN');
  if (run.head_repository?.full_name !== repository) reasons.push('HEAD_REPOSITORY_NOT_CANONICAL');
  if (!/^[0-9a-f]{40}$/i.test(run.head_sha ?? '')) reasons.push('HEAD_SHA_MISSING_OR_INVALID');

  return {
    eligible: reasons.length === 0,
    reasons,
    workflowRunId: run.id ?? null,
    headSha: run.head_sha ?? null,
    repository: run.head_repository?.full_name ?? null,
  };
}

async function main() {
  const [, , eventPath, repository = CANONICAL_REPOSITORY] = process.argv;
  if (!eventPath) {
    console.error('usage: publication-trigger-guard.mjs <event-json> [repository]');
    process.exitCode = 2;
    return;
  }

  const result = evaluateWorkflowRun(JSON.parse(await readFile(eventPath, 'utf8')), repository);
  console.log(JSON.stringify(result));
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) await main();
