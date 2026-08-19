import test from 'node:test';
import assert from 'node:assert/strict';
import {
  adapterFiles,
  canonicalCounterpart,
  checkAdapters,
  isWaived,
  loadWaivers,
} from './check-adapter-thinness.mjs';

const FILES = [
  '.gemini/config.yaml',
  'plugins/x/p/skills/a/SKILL.md',
  'plugins/x/p/.codex/skills/a/SKILL.md',
  'plugins/x/p/.codex/skills/a/references/deep.md',
  'plugins/x/p/.codex/LICENSE',
  'plugins/x/p/adapters/openclaw/skills/a/SKILL.md',
  'plugins/x/p/README.md',
];

test('adapter subtrees are recognized, canonical files are not', () => {
  const a = adapterFiles(FILES);
  assert.deepEqual(a, [
    'plugins/x/p/.codex/skills/a/SKILL.md',
    'plugins/x/p/.codex/skills/a/references/deep.md',
    'plugins/x/p/.codex/LICENSE',
    'plugins/x/p/adapters/openclaw/skills/a/SKILL.md',
  ]);
});

test('the canonical counterpart strips exactly the adapter segment', () => {
  assert.equal(
    canonicalCounterpart('plugins/x/p/.codex/skills/a/SKILL.md'),
    'plugins/x/p/skills/a/SKILL.md',
  );
  assert.equal(
    canonicalCounterpart('plugins/x/p/adapters/openclaw/skills/a/SKILL.md'),
    'plugins/x/p/skills/a/SKILL.md',
  );
});

test('red run — a byte-identical fork fails; a genuinely thin file passes', () => {
  const content = {
    'plugins/x/p/skills/a/SKILL.md': 'SAME',
    'plugins/x/p/.codex/skills/a/SKILL.md': 'SAME',
  };
  const read = (f) => content[f] ?? 'other';
  const violations = checkAdapters(
    ['plugins/x/p/skills/a/SKILL.md', 'plugins/x/p/.codex/skills/a/SKILL.md'],
    read,
    { waivers: [] },
  );
  assert.equal(violations.length, 1);
  assert.equal(violations[0].kind, 'byte-identical');

  content['plugins/x/p/.codex/skills/a/SKILL.md'] = 'THIN MAPPING ONLY';
  assert.deepEqual(
    checkAdapters(['plugins/x/p/skills/a/SKILL.md', 'plugins/x/p/.codex/skills/a/SKILL.md'], read, {
      waivers: [],
    }),
    [],
  );
});

test('red run — forbidden content classes inside an adapter fail', () => {
  const read = () => 'unique';
  const violations = checkAdapters(
    ['plugins/x/p/.codex/skills/a/references/deep.md', 'plugins/x/p/.codex/LICENSE'],
    read,
    { waivers: [] },
  );
  assert.deepEqual(
    violations.map((v) => v.kind),
    ['forbidden-class', 'forbidden-class'],
  );
});

test('a dated waiver suppresses its prefix and nothing else', () => {
  const waivers = { waivers: [{ path_prefix: 'plugins/x/p/.codex/', dated: '2026-08-18' }] };
  assert.ok(isWaived('plugins/x/p/.codex/LICENSE', waivers));
  assert.ok(!isWaived('plugins/x/q/.codex/LICENSE', waivers));
  const read = () => 'SAME';
  assert.deepEqual(
    checkAdapters(
      ['plugins/x/p/skills/a/SKILL.md', 'plugins/x/p/.codex/skills/a/SKILL.md'],
      read,
      waivers,
    ),
    [],
  );
});

test('the live waiver file names its removal owner', () => {
  const live = loadWaivers();
  assert.ok(live.waivers.length >= 1);
  for (const w of live.waivers) {
    assert.ok(w.dated, 'every waiver is dated');
    assert.ok(w.removed_by, 'every waiver names the bead that deletes it');
  }
});
