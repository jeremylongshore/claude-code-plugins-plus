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

test('red proof: direct, continued, quoted, variable, and folded-YAML writes are refused', () => {
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
"j-rig" eval skills/six --db "freshie"/inventory.sqlite
j-rig eval skills/seven --db freshie//inventory.sqlite
j-rig eval skills/eight --db freshie/./inventory.sqlite
db_path=freshie/inventory.sqlite
j-rig eval skills/nine --db "$db_path"
run : >-
  "j-rig" eval skills/ten
  --db freshie/../freshie/inventory.sqlite
readonly inventory_path="freshie/inventory.sqlite"
j-rig eval skills/eleven --db "\${inventory_path}"
env:
  JRIG_DB: freshie/inventory.sqlite
run : >
  j-rig eval skills/twelve --db "$JRIG_DB"
j\\-rig \\
  eval skills/thirteen \\
  --db freshie/inventory.sqlite
j-rig ev\\al skills/fourteen --db freshie/inventory.sqlite
j-rig eval skills/fifteen --d\\b freshie/inventory.sqlite
local -r local_db=freshie/inventory.sqlite
j-rig eval skills/sixteen --db "$local_db"
declare -r declared_db=freshie/inventory.sqlite
j-rig eval skills/seventeen --db "$declared_db"
typeset typed_db=freshie/inventory.sqlite
j-rig eval skills/eighteen --db "$typed_db"
env: { FLOW_DB: freshie/inventory.sqlite }
run: >2-
  j-rig eval skills/nineteen --db "$FLOW_DB"
`;
  const findings = inspectJrigDbBoundary(text, 'plugins/example/README.md');
  assert.deepEqual(
    findings.map((row) => row.reasonCode),
    [
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
      'DIRECT_JRIG_FRESHIE_DB',
    ],
    JSON.stringify(findings),
  );
});

test('hostile shell and YAML aliases resolve to the forbidden argv', () => {
  const cases = [
    [
      'multiple local assignments',
      `f(){
 local -r SAFE=x DB=freshie/inventory.sqlite
 j-rig eval skills/x --db "$DB"
}`,
    ],
    [
      'quote-concatenated assignment',
      `DB="freshie"/inventory.sqlite
j-rig eval skills/x --db "$DB"`,
    ],
    ['ANSI-C quoted path', "j-rig eval skills/x --db $'freshie/inventory.sqlite'"],
    [
      'static executable variable',
      `JRIG=j-rig
"$JRIG" eval skills/x --db freshie/inventory.sqlite`,
    ],
    [
      'static verb variable',
      `VERB=eval
j-rig "$VERB" skills/x --db freshie/inventory.sqlite`,
    ],
    [
      'static flag variable',
      `FLAG=--db
j-rig eval skills/x "$FLAG" freshie/inventory.sqlite`,
    ],
    [
      'indirect static variable',
      `DB=freshie/inventory.sqlite
NAME=DB
j-rig eval skills/x --db "\${!NAME}"`,
    ],
    [
      'quoted flow YAML key',
      `env: { "DB": freshie/inventory.sqlite }
run: >
  j-rig eval skills/x --db "$DB"`,
    ],
    [
      'quoted block YAML key',
      `env:
  "DB": freshie/inventory.sqlite
run: >
  j-rig eval skills/x --db "$DB"`,
    ],
    [
      'YAML anchor alias',
      `x-db: &freshie_db freshie/inventory.sqlite
env:
  DB: *freshie_db
run: >
  j-rig eval skills/x --db "$DB"`,
    ],
    [
      'anchored YAML run with indentation and chomping indicators',
      `env: { DB: freshie/inventory.sqlite }
run: &command >2-
  j-rig eval skills/x --db "$DB"`,
    ],
    [
      'folded YAML with static executable split from the flag',
      `env: { JRIG: j-rig }
run: >
  "$JRIG" eval skills/x
  --db freshie/inventory.sqlite`,
    ],
    ['route prose alias', 'Route `--db` to `freshie/inventory.sqlite` for persistence.'],
    ['persist prose alias', 'Persist JRig results with `--db freshie/inventory.sqlite`.'],
    ['glob-expanded path', 'j-rig eval skills/x --db freshie/inventory.sqli?e'],
  ];

  for (const [name, text] of cases) {
    const findings = inspectJrigDbBoundary(text, 'plugins/example/README.md');
    assert.equal(findings.length, 1, name);
  }
});

test('command-scoped state, parameter expansion, and parsed YAML preserve shell semantics', () => {
  const slash = String.fromCharCode(92);
  const chain = [
    'V17=freshie/inventory.sqlite',
    ...Array.from({ length: 16 }, (_, index) => `V${16 - index}=$V${17 - index}`),
    'j-rig eval x --db "$V1"',
  ].join('\n');
  const latestAssignment = [
    ...Array.from({ length: 65 }, (_, index) => `DB=/dev/shm/safe-${index}.sqlite`),
    'DB=freshie/inventory.sqlite',
    'j-rig eval x --db "$DB"',
  ].join('\n');
  const branchExplosion = [
    'DB=/dev/shm/safe.sqlite',
    ...Array.from({ length: 7 }, (_, index) => `unknown_${index} && V${index}=safe-${index}`),
    'j-rig eval x --db "$DB"',
  ].join('\n');
  const dangerous = [
    [
      'token continuations',
      [`j-${slash}`, `rig ev${slash}`, `al x --d${slash}`, 'b freshie/inventory.sqlite'].join('\n'),
    ],
    [
      'eval-prefixed token continuations',
      [`eval j-${slash}`, `rig ev${slash}`, `al x --d${slash}`, 'b freshie/inventory.sqlite'].join(
        '\n',
      ),
    ],
    ['bracket glob', 'j-rig eval x --db freshie/inventory.sqlit[e]'],
    ['default parameter value', 'unset DB\nj-rig eval x --db "${DB:-freshie/inventory.sqlite}"'],
    ['alternate parameter value', 'DB=on\nj-rig eval x --db "${DB:+freshie/inventory.sqlite}"'],
    ['substring parameter value', 'DB=freshie/inventory.sqlite\nj-rig eval x --db "${DB:0}"'],
    ['seventeen-assignment chain', chain],
    ['latest of sixty-six assignments', latestAssignment],
    [
      'same-line dangerous assignment precedes later safe value',
      'DB=freshie/inventory.sqlite; j-rig eval x --db "$DB"; DB=/dev/shm/safe.sqlite',
    ],
    [
      'and-chained assignment applies before command',
      'DB=freshie/inventory.sqlite && j-rig eval x --db "$DB"',
    ],
    ['tagged YAML run', 'run: !!str >-\n  j-rig eval x\n  --db freshie/inventory.sqlite\n'],
    ['escaped YAML run key', '"r\\u0075n": >-\n  j-rig eval x\n  --db freshie/inventory.sqlite\n'],
    ['assignment parameter', 'j-rig eval x --db "${DB:=freshie/inventory.sqlite}"'],
    ['brace-expanded path', 'j-rig eval x --db freshie/inventory.sql{ite,other}'],
    ['dynamic eval token', 'j-rig "$(printf eval)" x --db freshie/inventory.sqlite'],
    ['dynamic db flag', 'j-rig eval x "$(printf -- --db)" freshie/inventory.sqlite'],
    ['dynamic db path', 'j-rig eval x --db "$(printf %s freshie/inventory.sqlite)"'],
    [
      'subshell cannot overwrite parent Freshie assignment',
      'DB=freshie/inventory.sqlite\n( DB=/dev/shm/safe.sqlite )\nj-rig eval x --db "$DB"',
    ],
    [
      'current-shell group can set Freshie assignment',
      'DB=/dev/shm/safe.sqlite\n{ DB=freshie/inventory.sqlite; }\nj-rig eval x --db "$DB"',
    ],
    [
      'pipeline cannot overwrite parent Freshie assignment',
      'DB=freshie/inventory.sqlite\nDB=/dev/shm/safe.sqlite | cat\nj-rig eval x --db "$DB"',
    ],
    [
      'background assignment cannot overwrite parent Freshie assignment',
      'DB=freshie/inventory.sqlite\nDB=/dev/shm/safe.sqlite &\nj-rig eval x --db "$DB"',
    ],
    [
      'skipped and-branch cannot overwrite parent Freshie assignment',
      'DB=freshie/inventory.sqlite\nfalse && DB=/dev/shm/safe.sqlite\nj-rig eval x --db "$DB"',
    ],
    [
      'skipped or-branch cannot overwrite parent Freshie assignment',
      'DB=freshie/inventory.sqlite\ntrue || DB=/dev/shm/safe.sqlite\nj-rig eval x --db "$DB"',
    ],
    ['function alias invocation', 'jr() { j-rig "$@"; }\njr eval x --db freshie/inventory.sqlite'],
    ['ambiguous branch state fails closed', branchExplosion],
    [
      'comment does not discard later assignments',
      '# heading\nDB=freshie/inventory.sqlite\nj-rig eval x --db "$DB"',
    ],
    [
      'inline comment preserves the preceding assignment',
      'DB=freshie/inventory.sqlite # governed path\nj-rig eval x --db "$DB"',
    ],
    [
      'Markdown possessive does not absorb later shell',
      'This platform\'s integration is documented.\nDB=freshie/inventory.sqlite\nj-rig eval x --db "$DB"',
    ],
    [
      'parameter assignment side effect persists',
      ': "${DB:=freshie/inventory.sqlite}"\nj-rig eval x --db "$DB"',
    ],
    [
      'non-colon parameter assignment side effect persists',
      ': "${DB=freshie/inventory.sqlite}"\nj-rig eval x --db "$DB"',
    ],
    [
      'dynamic executable assignment preserves command substitution',
      'EXE=$(printf %s j-rig)\nDB=freshie/inventory.sqlite\n"$EXE" eval x --db "$DB"',
    ],
    [
      'composed command substitution cannot hide the database path',
      'DB=$(printf "freshie/%s" inventory.sqlite)\nj-rig eval x --db "$DB"',
    ],
    [
      'multi-placeholder command substitution cannot hide the database path',
      'DB=$(printf "%s/%s" freshie inventory.sqlite)\nj-rig eval x --db "$DB"',
    ],
    [
      'embedded-placeholder command substitution cannot hide the database path',
      'DB=$(printf "fresh%s/inventory.%s" ie sqlite)\nj-rig eval x --db "$DB"',
    ],
    [
      'non-static database substitution fails closed',
      'DB=$(resolve-runtime-db)\nj-rig eval x --db "$DB"',
    ],
    [
      'conditional assignment remains a possible state',
      'if test -n "${FLAG:-}"; then DB=freshie/inventory.sqlite; fi\nj-rig eval x --db "$DB"',
    ],
    [
      'GitHub env expression resolves parsed YAML env',
      'env:\n  DB: freshie/inventory.sqlite\nrun: j-rig eval x --db "${{ env.DB }}"',
    ],
  ];
  for (const [name, text] of dangerous) {
    const findings = inspectJrigDbBoundary(text, 'plugins/example/README.md');
    assert.equal(findings.length, 1, name);
  }

  const safe = [
    ['escaped question mark', `j-rig eval x --db freshie/inventory.sqli${slash}?e`],
    ['quoted question mark', 'j-rig eval x --db "freshie/inventory.sqli?e"'],
    ['escaped asterisk', `j-rig eval x --db freshie/inventory.sql${slash}*`],
    [
      'later wrapper-only Freshie assignment',
      `DB=/dev/shm/jrig.sqlite
j-rig eval x --db "$DB"
DB=freshie/inventory.sqlite
scripts/run-jrig-eval.sh --inventory-db "$DB"`,
    ],
    [
      'latest assignment is scratch',
      `DB=freshie/inventory.sqlite
DB=/dev/shm/safe.sqlite
j-rig eval x --db "$DB"`,
    ],
    [
      'same-line later assignment cannot taint earlier command',
      'DB=/dev/shm/safe.sqlite; j-rig eval x --db "$DB"; DB=freshie/inventory.sqlite',
    ],
    [
      'blank line separates folded shell commands',
      `run: >
  j-rig eval x

  --db freshie/inventory.sqlite`,
    ],
    [
      'subshell cannot overwrite parent scratch assignment',
      'DB=/dev/shm/safe.sqlite\n( DB=freshie/inventory.sqlite )\nj-rig eval x --db "$DB"',
    ],
    [
      'current-shell group can set scratch assignment',
      'DB=freshie/inventory.sqlite\n{ DB=/dev/shm/safe.sqlite; }\nj-rig eval x --db "$DB"',
    ],
    [
      'pipeline cannot overwrite parent scratch assignment',
      'DB=/dev/shm/safe.sqlite\nDB=freshie/inventory.sqlite | cat\nj-rig eval x --db "$DB"',
    ],
    [
      'background assignment cannot overwrite parent scratch assignment',
      'DB=/dev/shm/safe.sqlite\nDB=freshie/inventory.sqlite &\nj-rig eval x --db "$DB"',
    ],
    [
      'skipped and-branch cannot overwrite parent scratch assignment',
      'DB=/dev/shm/safe.sqlite\nfalse && DB=freshie/inventory.sqlite\nj-rig eval x --db "$DB"',
    ],
    [
      'skipped or-branch cannot overwrite parent scratch assignment',
      'DB=/dev/shm/safe.sqlite\ntrue || DB=freshie/inventory.sqlite\nj-rig eval x --db "$DB"',
    ],
    [
      'statically skipped direct command is unreachable',
      'false && j-rig eval x --db freshie/inventory.sqlite',
    ],
    ['non-JRig utility with db-shaped arguments', 'echo --db freshie/inventory.sqlite'],
    ['echo of a JRig command is not execution', 'echo j-rig eval x --db freshie/inventory.sqlite'],
    [
      'informational JRig prose is not an operator directive',
      'JRig documentation describes --db and freshie/inventory.sqlite without directing its use.',
    ],
    [
      'negative JRig prose is not an operator directive',
      'JRig must never use --db freshie/inventory.sqlite.',
    ],
    [
      'non-colon assignment preserves an existing empty value',
      'DB=\n: "${DB=freshie/inventory.sqlite}"\nj-rig eval x --db "$DB"',
    ],
    [
      'statically proven scratch substitution remains allowed',
      'DB=$(printf %s /dev/shm/jrig-safe.sqlite)\nj-rig eval x --db "$DB"',
    ],
  ];
  for (const [name, text] of safe) {
    assert.deepEqual(inspectJrigDbBoundary(text, 'plugins/example/README.md'), [], name);
  }
});

test('prose directives using distinct operator verbs are refused', () => {
  const findings = inspectJrigDbBoundary(
    [
      'To persist results, point `--db` at `freshie/inventory.sqlite`.',
      'Use `--db freshie/inventory.sqlite` for the durable run.',
      'Feed `--db=freshie/inventory.sqlite` into j-rig.',
      'Supply `freshie/./inventory.sqlite` to `--db` for persistence.',
      'Configure `freshie/inventory.sqlite` as the `--db` target.',
      "Choose Freshie's inventory.sqlite as the --db destination when evaluating with JRig.",
    ].join('\n'),
    'plugins/example/README.md',
  );
  assert.deepEqual(
    findings.map((row) => row.reasonCode),
    [
      'JRIG_FRESHIE_DB_DIRECTIVE',
      'JRIG_FRESHIE_DB_DIRECTIVE',
      'JRIG_FRESHIE_DB_DIRECTIVE',
      'JRIG_FRESHIE_DB_DIRECTIVE',
      'JRIG_FRESHIE_DB_DIRECTIVE',
      'JRIG_FRESHIE_DB_DIRECTIVE',
    ],
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
