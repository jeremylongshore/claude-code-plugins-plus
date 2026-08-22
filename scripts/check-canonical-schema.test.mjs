import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import Ajv2020 from 'ajv/dist/2020.js';

const schema = JSON.parse(
  readFileSync(
    new URL('../schemas/canonical/v0/skill-contract.schema.json', import.meta.url),
    'utf-8',
  ),
);
const ajv = new Ajv2020.default({ strict: true, allErrors: true });
const validate = ajv.compile(schema);

// The blueprint § 5.2 example, expressed as the JSON the YAML parses to.
const EXAMPLE = {
  id: 'plane',
  version: '0.3.0',
  intent: 'Synthesize project-tracker data into observations about team behavior.',
  inputs: [{ name: 'project', type: 'string', required: true }],
  outputs: [{ name: 'report', type: 'markdown', schema: './schemas/report.json' }],
  capabilities: [
    'filesystem.read',
    { 'filesystem.write': { paths: ['./out/**'] } },
    { 'shell.exec': { commands: ['jq', 'date'] } },
    { 'network.http': { hosts: ['api.plane.so'] } },
    'user.prompt',
  ],
  constraints: {
    forbid: ['filesystem.write.dotenv', 'shell.exec.rm', 'network.exfil'],
    bounded: { max_steps: 40 },
    risk_tier: 'medium',
  },
  side_effects: {
    writes: [{ path: './out/**', approx_mb_max: 5 }],
    network: ['api.plane.so'],
    env: ['PLANE_API_KEY'],
  },
  requires: { services: [{ kind: 'mcp', name: 'plane', env: ['PLANE_API_KEY'] }] },
  model_class: 'balanced',
  evaluation: './eval-spec.yaml',
  not_for: ['plane-admin-migration'],
  lifecycle: 'active',
  superseded_by: null,
  sunset_on: null,
  provenance: {
    author: 'Name <email>',
    license: 'MIT',
    spdx: 'MIT',
    source: null,
    source_commit: null,
    upstream_license: null,
  },
  adapters: ['claude-code'],
  unsupported: [
    {
      capability: 'user.prompt',
      adapter: 'codex',
      reason: 'no interactive-confirmation primitive',
      degradation: 'fail-closed',
    },
  ],
};

const withPatch = (patch) => JSON.parse(JSON.stringify({ ...EXAMPLE, ...patch }));

test('the blueprint § 5.2 example validates', () => {
  const ok = validate(EXAMPLE);
  assert.ok(ok, JSON.stringify(validate.errors, null, 2));
});

test('red run — an unknown top-level key is rejected (closed schema)', () => {
  assert.equal(validate(withPatch({ compatibility: 'Claude Code only' })), false);
  assert.equal(validate(withPatch({ metadata: {} })), false);
});

test('red run — a vendor literal cannot be a model class', () => {
  for (const literal of ['claude-sonnet-4', 'claude-fable-5', 'gpt-5', 'sonnet']) {
    assert.equal(validate(withPatch({ model_class: literal })), false, literal);
  }
});

test('red run — a harness with no registered adapter artifact is rejected', () => {
  for (const bogus of [['codex'], ['claude-code', 'openclaw'], []]) {
    assert.equal(validate(withPatch({ adapters: bogus })), false, JSON.stringify(bogus));
  }
});

test('red run — a branch name is not a mirror pin', () => {
  const p = withPatch({});
  p.provenance.source = 'https://github.com/x/y';
  p.provenance.upstream_license = 'MIT';
  p.provenance.source_commit = 'main';
  assert.equal(validate(p), false);
  p.provenance.source_commit = 'a'.repeat(40);
  assert.ok(validate(p), JSON.stringify(validate.errors));
});

test('red run — a mirrored contract cannot omit its pin or upstream license', () => {
  const p = withPatch({});
  p.provenance.source = 'https://github.com/x/y';
  p.provenance.source_commit = null;
  p.provenance.upstream_license = 'MIT';
  assert.equal(validate(p), false, 'null source_commit with non-null source must fail');
  p.provenance.source_commit = 'a'.repeat(40);
  p.provenance.upstream_license = null;
  assert.equal(validate(p), false, 'null upstream_license with non-null source must fail');
  // and a non-mirrored contract (null source) keeps nulls legal
  p.provenance.source = null;
  p.provenance.source_commit = null;
  assert.ok(validate(p), JSON.stringify(validate.errors));
});

test('red run — an invented token-shaped SPDX id is rejected', () => {
  const p = withPatch({});
  p.provenance.spdx = 'MadeUpLicense';
  assert.equal(validate(p), false);
  p.provenance.spdx = 'LicenseRef-IntentSolutions-Proprietary';
  assert.ok(validate(p), JSON.stringify(validate.errors));
  p.provenance.spdx = 'Apache-2.0 WITH LLVM-exception';
  assert.ok(validate(p), JSON.stringify(validate.errors));
});

test('an omitted degradation is legal and means fail-closed', () => {
  const p = withPatch({});
  p.unsupported = [{ capability: 'user.prompt', adapter: 'codex', reason: 'no primitive' }];
  assert.ok(validate(p), JSON.stringify(validate.errors));
});

test('red run — harness tool spellings are not capabilities', () => {
  for (const notACapability of ['Bash(jq:*)', 'mcp__plane__query', 'Read']) {
    assert.equal(validate(withPatch({ capabilities: [notACapability] })), false, notACapability);
  }
});

test('red run — unsupported entries require a reason', () => {
  const p = withPatch({});
  p.unsupported = [{ capability: 'user.prompt', adapter: 'codex' }];
  assert.equal(validate(p), false);
});

test('minimal contract: only the required seven fields', () => {
  const minimal = {
    id: 'tiny',
    version: '1.0.0',
    intent: 'Do one small portable thing.',
    capabilities: ['filesystem.read'],
    model_class: 'fast',
    lifecycle: 'active',
    provenance: { author: 'A <a@b.c>', license: 'MIT', spdx: 'MIT' },
    adapters: ['claude-code'],
  };
  assert.ok(validate(minimal), JSON.stringify(validate.errors, null, 2));
});
