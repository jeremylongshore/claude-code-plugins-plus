import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { auditJrigDbBoundary, inspectJrigDbBoundary } from './check-jrig-db-boundary.mjs';

function fixture() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'jrig-db-boundary-'));
}

function write(root, relative, contents) {
  const target = path.join(root, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, contents);
}

test('safe scratch wrapper and non-persisting direct eval remain allowed', () => {
  const text = `
\`\`\`bash
j-rig eval skills/example --json
scripts/run-jrig-eval.sh --skill-dir skills/example --inventory-db freshie/inventory.sqlite
\`\`\`
Never pass the tracked inventory as j-rig's --db value.
`;
  assert.deepEqual(inspectJrigDbBoundary(text, 'plugins/example/README.md'), []);
});

test('red proof: direct, continued, npx, quoted, and folded-YAML writes are refused', () => {
  const text = `
j-rig eval skills/plain --db freshie/inventory.sqlite --json
\`\`\`bash
j-rig eval skills/one --db freshie/inventory.sqlite --json
pnpm exec j-rig eval skills/two \\
  --models fast,slow \\
  --db ~/000-projects/claude-code-plugins/freshie/inventory.sqlite
j-rig eval skills/three \\
  --db \\
  freshie/inventory.sqlite
\`\`\`
npx j-rig eval skills/four '--db=freshie/inventory.sqlite'
run: >-
  j-rig eval skills/five
  --models fast,slow
  --db freshie/inventory.sqlite
`;
  assert.deepEqual(
    inspectJrigDbBoundary(text, 'plugins/example/README.md').map((row) => row.reasonCode),
    [
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
    ],
  );
});

test('prose directives using distinct operator verbs are refused', () => {
  const findings = inspectJrigDbBoundary(
    [
      'To persist results, point `--db` at `freshie/inventory.sqlite`.',
      'Use `--db freshie/inventory.sqlite` for the durable run.',
      'Feed `--db=freshie/inventory.sqlite` into j-rig.',
    ].join('\n'),
    'plugins/example/README.md',
  );
  assert.deepEqual(
    findings.map((row) => row.reasonCode),
    ['JRIG_FRESHIE_DB_DIRECTIVE', 'JRIG_FRESHIE_DB_DIRECTIVE', 'JRIG_FRESHIE_DB_DIRECTIVE'],
  );
});

test('copyable forbidden commands remain refused even when labeled as negative examples', () => {
  const findings = inspectJrigDbBoundary(
    'Do not run `j-rig eval skills/example --db freshie/inventory.sqlite`.',
    'plugins/example/README.md',
  );
  assert.deepEqual(
    findings.map((row) => row.reasonCode),
    ['DIRECT_JRIG_FRESHIE_DB'],
  );
});

test('mirror surfaces are skipped from first-party policy by source ancestry', () => {
  const root = fixture();
  write(
    root,
    'plugins/mirror/README.md',
    '```bash\nj-rig eval x --db freshie/inventory.sqlite\n```',
  );
  const report = auditJrigDbBoundary({
    root,
    paths: ['plugins/mirror/README.md'],
    provenance: () => ({ status: 'mirror', reasonCode: 'UPSTREAM_SOURCE_RECORD' }),
  });
  assert.equal(report.mirrorsSkipped, 1);
  assert.deepEqual(report.findings, []);
});

test('malformed provenance and unreadable active files fail closed', () => {
  const root = fixture();
  write(root, 'plugins/bad/README.md', '# fixture');
  write(root, 'scripts/check.sh', '#!/bin/sh');
  const report = auditJrigDbBoundary({
    root,
    paths: ['plugins/bad/README.md', 'scripts/check.sh'],
    provenance: () => ({ status: 'refused', reasonCode: 'MALFORMED_SOURCE_RECORD' }),
    readFile: (filePath, encoding) => {
      if (filePath.endsWith('check.sh')) throw new Error('fixture EACCES');
      return fs.readFileSync(filePath, encoding);
    },
  });
  assert.deepEqual(report.findings.map((row) => row.reasonCode).sort(), [
    'MALFORMED_SOURCE_RECORD',
    'UNREADABLE_ACTIVE_SURFACE',
  ]);
});
