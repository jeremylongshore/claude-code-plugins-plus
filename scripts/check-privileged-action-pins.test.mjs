import assert from 'node:assert/strict';
import test from 'node:test';

import {
  inspectPrivilegedActionPins,
  inspectWorkflowEntries,
} from './check-privileged-action-pins.mjs';

test('all current privileged and signing workflows use immutable action SHAs', () => {
  const report = inspectPrivilegedActionPins();
  assert.deepEqual(report.unpinned, []);
  assert.ok(report.privilegedWorkflows.length >= 8);
  assert.ok(report.uses.length >= 13);
  assert.ok(report.distinctActions.length >= 6);
});

test('a mutable tag in an OIDC-capable workflow fails the policy', () => {
  const report = inspectWorkflowEntries([
    {
      path: '.github/workflows/publish.yml',
      text: 'permissions:\n  id-token: write\nsteps:\n  - uses: actions/checkout@v6\n',
    },
  ]);
  assert.deepEqual(report.unpinned, [
    {
      action: 'actions/checkout',
      line: 4,
      path: '.github/workflows/publish.yml',
      ref: 'v6',
    },
  ]);
});

test('local reusable workflows are outside the third-party pin rule', () => {
  const report = inspectWorkflowEntries([
    {
      path: '.github/workflows/publish.yml',
      text: 'permissions:\n  id-token: write\njobs:\n  sign:\n    uses: ./.github/workflows/sign.yml\n',
    },
  ]);
  assert.deepEqual(report.unpinned, []);
  assert.deepEqual(report.uses, []);
});
