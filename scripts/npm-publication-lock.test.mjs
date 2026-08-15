import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { evaluateCheckEvidence, runPreflight } from './npm-publication-preflight.mjs';
import { evaluateWorkflowRun } from './publication-trigger-guard.mjs';

const SHA = 'a'.repeat(40);
const OTHER_SHA = 'b'.repeat(40);
const REPO = 'jeremylongshore/claude-code-plugins-plus-skills';

function fixture({
  context,
  workflowName,
  workflowPath,
  conclusion = 'success',
  status = 'completed',
  runId,
  sha = SHA,
  app = 'github-actions',
  runStatus = 'completed',
  runConclusion = 'success',
  runAttempt = 1,
}) {
  return {
    checkRun: {
      id: runId * 10,
      name: context,
      head_sha: sha,
      status,
      conclusion,
      details_url: `https://github.com/${REPO}/actions/runs/${runId}/job/${runId * 10}`,
      app: { slug: app },
    },
    workflowRun: {
      id: runId,
      name: workflowName,
      path: workflowPath,
      event: 'push',
      head_branch: 'main',
      head_sha: sha,
      status: runStatus,
      conclusion: runConclusion,
      run_attempt: runAttempt,
      repository: { full_name: REPO },
    },
  };
}

const all = [
  fixture({
    context: 'ci-required',
    workflowName: 'Validate Plugins',
    workflowPath: '.github/workflows/validate-plugins.yml',
    runId: 1,
  }),
  fixture({
    context: 'gitleaks',
    workflowName: 'Secret Scan',
    workflowPath: '.github/workflows/secret-scan.yml',
    runId: 2,
  }),
  fixture({
    context: 'skill-conform',
    workflowName: 'Skill Conform',
    workflowPath: '.github/workflows/skill-conform.yml',
    runId: 3,
  }),
];

function evaluate(items = all) {
  return evaluateCheckEvidence({
    repository: REPO,
    sha: SHA,
    checkRuns: items.map((item) => item.checkRun),
    workflowRuns: items.map((item) => item.workflowRun),
  });
}

function fixtureFetch(items = all) {
  return async (url) => {
    const body = url.includes('/commits/main')
      ? { sha: SHA }
      : url.includes('/compare/')
        ? { status: 'identical' }
        : url.includes('/check-runs')
          ? { check_runs: items.map((item) => item.checkRun) }
          : url.includes('/actions/runs')
            ? { workflow_runs: items.map((item) => item.workflowRun) }
            : url.includes('/status')
              ? { statuses: [] }
              : { full_name: REPO };
    return { ok: true, status: 200, json: async () => body };
  };
}

test('all trusted contexts succeed for the exact SHA', () => {
  assert.equal(evaluate().allow, true);
});

test('missing, failed, cancelled, skipped, and pending contexts refuse', () => {
  for (const mutate of [
    (items) => items.slice(1),
    (items) =>
      items.map((item) =>
        item.checkRun.name === 'gitleaks'
          ? { ...item, checkRun: { ...item.checkRun, conclusion: 'failure' } }
          : item,
      ),
    (items) =>
      items.map((item) =>
        item.checkRun.name === 'gitleaks'
          ? { ...item, checkRun: { ...item.checkRun, conclusion: 'cancelled' } }
          : item,
      ),
    (items) =>
      items.map((item) =>
        item.checkRun.name === 'gitleaks'
          ? { ...item, checkRun: { ...item.checkRun, conclusion: 'skipped' } }
          : item,
      ),
    (items) =>
      items.map((item) =>
        item.checkRun.name === 'gitleaks'
          ? {
              ...item,
              checkRun: { ...item.checkRun, status: 'queued', conclusion: null },
              workflowRun: { ...item.workflowRun, status: 'queued', conclusion: null },
            }
          : item,
      ),
  ]) {
    assert.equal(evaluate(mutate(all)).allow, false);
  }
});

test('wrong SHA, untrusted producer, and ambiguous duplicates refuse', () => {
  assert.equal(
    evaluate(
      all.map((item) =>
        item.checkRun.name === 'gitleaks'
          ? { ...item, checkRun: { ...item.checkRun, head_sha: OTHER_SHA } }
          : item,
      ),
    ).allow,
    false,
  );
  assert.equal(
    evaluate(
      all.map((item) =>
        item.checkRun.name === 'gitleaks'
          ? { ...item, checkRun: { ...item.checkRun, app: { slug: 'evil-app' } } }
          : item,
      ),
    ).allow,
    false,
  );
  const duplicate = [
    ...all,
    fixture({
      context: 'gitleaks',
      workflowName: 'Secret Scan',
      workflowPath: '.github/workflows/secret-scan.yml',
      runId: 4,
    }),
  ];
  assert.equal(evaluate(duplicate).allow, false);
});

test('workflow trigger accepts only successful canonical push-to-main validation', () => {
  const base = {
    workflow_run: {
      name: 'Validate Plugins',
      conclusion: 'success',
      event: 'push',
      head_branch: 'main',
      head_sha: SHA,
      head_repository: { full_name: REPO },
    },
  };
  assert.equal(evaluateWorkflowRun(base).eligible, true);
  assert.equal(
    evaluateWorkflowRun({ workflow_run: { ...base.workflow_run, event: 'pull_request' } }).eligible,
    false,
  );
  assert.equal(
    evaluateWorkflowRun({
      workflow_run: { ...base.workflow_run, head_repository: { full_name: 'fork/example' } },
    }).eligible,
    false,
  );
});

test('administrator/direct merge with absent or red checks cannot publish', () => {
  assert.equal(evaluate([]).allow, false);
  assert.equal(
    evaluate(
      all.map((item) =>
        item.checkRun.name === 'ci-required'
          ? { ...item, checkRun: { ...item.checkRun, conclusion: 'failure' } }
          : item,
      ),
    ).allow,
    false,
  );
});

test('zero candidates is a safe no-op decision', () => {
  const candidates = [];
  assert.deepEqual(candidates, []);
  assert.equal(evaluate().allow, true);
});

test('manual real-publish request without successful preflight refuses', () => {
  assert.equal(evaluate(all.slice(0, 2)).allow, false);
});

test('the shared preflight allows the exact live-shaped fixture and bounds pending polling', async () => {
  const allowed = await runPreflight({
    repository: REPO,
    sha: SHA,
    token: 'fixture-token',
    timeoutSeconds: 0,
    pollSeconds: 0,
    fetchImpl: fixtureFetch(),
  });
  assert.equal(allowed.allow, true);

  const pendingItems = all.map((item) =>
    item.checkRun.name === 'skill-conform'
      ? {
          ...item,
          checkRun: { ...item.checkRun, status: 'queued', conclusion: null },
          workflowRun: { ...item.workflowRun, status: 'queued', conclusion: null },
        }
      : item,
  );
  const pending = await runPreflight({
    repository: REPO,
    sha: SHA,
    token: 'fixture-token',
    timeoutSeconds: 0,
    pollSeconds: 0,
    fetchImpl: fixtureFetch(pendingItems),
  });
  assert.equal(pending.allow, false);
  assert.equal(
    pending.requiredContexts.find((context) => context.context === 'skill-conform').reason,
    'PENDING',
  );
});

test('legacy raw-push topology is rejected by the new workflow guard', () => {
  const rawPush = {
    workflow_run: {
      name: 'Validate Plugins',
      conclusion: 'success',
      event: 'push',
      head_branch: 'main',
      head_sha: SHA,
      head_repository: { full_name: REPO },
    },
  };
  assert.equal(evaluateWorkflowRun(rawPush).eligible, true);
  assert.equal(
    evaluateWorkflowRun({ workflow_run: { ...rawPush.workflow_run, conclusion: 'failure' } })
      .eligible,
    false,
  );
});

test('the old raw-push route is absent and the new publisher requires the preflight job', () => {
  const changedWorkflow = readFileSync(
    new URL('../.github/workflows/publish-changed-packages.yml', import.meta.url),
    'utf8',
  );
  assert.doesNotMatch(changedWorkflow, /\n\x20{2}push:\n/);
  assert.match(changedWorkflow, /\n\x20{2}workflow_run:\n/);
  assert.match(changedWorkflow, /needs: \[guard, preflight, detect\]/);
  assert.match(changedWorkflow, /environment: npm-production/);
});
