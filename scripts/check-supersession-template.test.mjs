import { deepEqual, equal, match, throws } from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import {
  checkSupersessionCorpus,
  checkSupersessionTemplate,
  parseSupersessionRecords,
  readTrackedDocumentation,
  trackedDocumentationPaths,
} from './check-supersession-template.mjs';

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const fixtureRoot = join(repositoryRoot, 'tests', 'fixtures', 'supersession-template');
const fixture = (name) => readFileSync(join(fixtureRoot, `${name}.md`), 'utf8');
const codes = (name) => checkSupersessionTemplate(fixture(name)).findings.map((item) => item.code);

test('completed worked-example record passes with structured element evidence', () => {
  const result = checkSupersessionTemplate(fixture('valid'));
  equal(result.ok, true);
  equal(result.records.length, 1);
  deepEqual(result.records[0].elements, {
    frozenMarker: true,
    frozenBanner: true,
    dispositionRows: 2,
    canonicalPointerTask: 13,
    onePrAtomicity: 5,
  });
  deepEqual(result.findings, []);
});

test('each required record element fails with a stable reason code', () => {
  const cases = [
    ['missing-marker', 'SUPERSESSION_FROZEN_MARKER_MISSING'],
    ['missing-banner', 'SUPERSESSION_FROZEN_BANNER_MISSING'],
    ['missing-disposition', 'SUPERSESSION_DISPOSITION_TABLE_MISSING'],
    ['missing-pointer', 'SUPERSESSION_CANONICAL_POINTER_TASK_MISSING'],
    ['missing-one-pr', 'SUPERSESSION_ONE_PR_ATOMICITY_MISSING'],
  ];
  for (const [name, code] of cases) {
    const result = checkSupersessionTemplate(fixture(name));
    equal(result.ok, false, name);
    equal(
      result.findings.some((item) => item.code === code),
      true,
      name,
    );
  }
});

test('malformed and empty disposition tables fail closed', () => {
  equal(codes('malformed-table').includes('SUPERSESSION_DISPOSITION_TABLE_MALFORMED'), true);
  equal(codes('empty-table').includes('SUPERSESSION_DISPOSITION_ROW_MISSING'), true);
  equal(codes('placeholder-row').includes('SUPERSESSION_PLACEHOLDER_PRESENT'), true);
  equal(codes('placeholder-row').includes('SUPERSESSION_DISPOSITION_ROW_MISSING'), true);
  equal(codes('invalid-disposition').includes('SUPERSESSION_DISPOSITION_INVALID'), true);
});

test('comment-wrapped and negated requirements fail closed', () => {
  equal(codes('comment-wrapped-marker').includes('SUPERSESSION_FROZEN_MARKER_MISSING'), true);
  equal(codes('negated-pointer').includes('SUPERSESSION_CANONICAL_POINTER_TASK_MISSING'), true);
  equal(codes('negated-one-pr').includes('SUPERSESSION_ONE_PR_ATOMICITY_MISSING'), true);

  const negatedBanner = checkSupersessionTemplate(
    fixture('valid').replace(
      /^- \*\*Frozen header:\*\*.*$/m,
      '- **Frozen header:** `<!-- doc-class: frozen -->` is not a `SUPERSEDED–FROZEN` banner.',
    ),
  );
  equal(
    negatedBanner.findings.some((item) => item.code === 'SUPERSESSION_FROZEN_BANNER_MISSING'),
    true,
  );

  const contractedCases = [
    [
      'pointer',
      fixture('valid').replace(
        'Update the `STANDARDS.md` Canonical documents pointer to the new authority.',
        "The `STANDARDS.md` Canonical documents pointer isn't updated to the new authority.",
      ),
      'SUPERSESSION_CANONICAL_POINTER_TASK_MISSING',
    ],
    [
      'atomicity',
      fixture('valid').replace(
        '**Atomic PR:** This one pull request carries every checked item below.',
        "**Atomic PR:** This record isn't atomic in one pull request.",
      ),
      'SUPERSESSION_ONE_PR_ATOMICITY_MISSING',
    ],
    [
      'frozen header',
      fixture('valid').replace(
        /^- \*\*Frozen header:\*\*.*$/m,
        "- **Frozen header:** `<!-- doc-class: frozen -->` isn't a `SUPERSEDED–FROZEN` banner.",
      ),
      'SUPERSESSION_FROZEN_BANNER_MISSING',
    ],
  ];
  for (const [name, markdown, code] of contractedCases) {
    const result = checkSupersessionTemplate(markdown);
    equal(
      result.findings.some((item) => item.code === code),
      true,
      name,
    );
  }

  const invalidDirectBanners = [
    '> **SUPERSEDED–FROZEN (test).** This is not a valid supersession banner.',
    "> **SUPERSEDED–FROZEN (test).** This supersession banner isn't valid.",
    '> **SUPERSEDED–FROZEN (test).** This does not qualify as a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This supersession banner is invalid.',
    '> **SUPERSEDED–FROZEN (test).** This is not an effective supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This does not constitute a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This banner is not valid as a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This cannot serve as a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This is a purported supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This is no supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This does not amount to a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This supersession banner is void.',
    '> **SUPERSEDED–FROZEN (test).** This banner must not be treated as a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This is not really a supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This supersession banner lacks validity.',
    '> **SUPERSEDED–FROZEN (test).**\n> This is not a valid supersession banner.',
    '> **SUPERSEDED–FROZEN (test).**\nThis is not a valid supersession banner.',
    '> **SUPERSEDED–FROZEN (test).** This is not a supersession-banner.',
    '> **SUPERSEDED–FROZEN (test).** This is not one of the supersession banners.',
    '> **SUPERSEDED–FROZEN (test).** This is not a supersession **banner**.',
    '> **SUPERSEDED–FROZEN (test).** This is not a supersession&nbsp;banner.',
    '> **SUPERSEDED–FROZEN (test).** This is not a supersession notice.',
    '> **SUPERSEDED–FROZEN (test).** No supersession applies here.',
    '> **SUPERSEDED–FROZEN (test).** No super&#115;ession applies here.',
    '> **SUPERSEDED–FROZEN (test).** No super&#x73;ession applies here.',
    '> **SUPERSEDED–FROZEN (test).** No super<em>session</em> applies here.',
    '> **SUPERSEDED–FROZEN (test).** No super[session](https://example.invalid) applies here.',
    '> **SUPERSEDED–FROZEN (test).** No super­session applies here.',
    '> **SUPERSEDED–FROZEN (test).**\n\n> This is not a valid supersession banner.',
    '    > **SUPERSEDED–FROZEN.**',
    '> **SUPERSEDED–FROZEN (test **not controlled**).**',
    '> **SUPERSEDED–FROZEN (test _not controlled_).**',
    '> **SUPERSEDED–FROZEN (test __not controlled__).**',
    '> **SUPERSEDED–FROZEN (test <!-- hidden -->).**',
    '<!-- hidden --> > **SUPERSEDED–FROZEN.**',
    '<!-- hidden -->\n> **SUPERSEDED–FROZEN.**',
    '<!-- hidden -->\n\n> **SUPERSEDED–FROZEN.**',
    '> <!-- hidden -->\n> **SUPERSEDED–FROZEN.**',
  ];
  const directBanner = checkSupersessionTemplate(
    fixture('valid').replace(
      /^- \*\*Frozen header:\*\*.*$/m,
      '- **Frozen marker:** `<!-- doc-class: frozen -->`\n\n> **SUPERSEDED–FROZEN (test).**',
    ),
  );
  equal(
    directBanner.findings.some((item) => item.code === 'SUPERSESSION_FROZEN_BANNER_MISSING'),
    false,
    'controlled direct banner',
  );
  for (const banner of invalidDirectBanners) {
    const result = checkSupersessionTemplate(
      fixture('valid').replace(
        /^- \*\*Frozen header:\*\*.*$/m,
        `- **Frozen marker:** \`<!-- doc-class: frozen -->\`\n\n${banner}`,
      ),
    );
    equal(
      result.findings.some((item) => item.code === 'SUPERSESSION_FROZEN_BANNER_MISSING'),
      true,
      banner,
    );
  }

  const naturalPositiveWording = checkSupersessionTemplate(
    fixture('valid')
      .replace(
        'Update the `STANDARDS.md` Canonical documents pointer to the new authority.',
        "Don't forget to update the `STANDARDS.md` Canonical documents pointer to the new authority.",
      )
      .replace(
        '**Atomic PR:** This one pull request carries every checked item below.',
        '**Atomic PR:** This one pull request is unchanged from the planned atomic transaction.',
      ),
  );
  equal(naturalPositiveWording.ok, true);

  const repositoryBannerShape = checkSupersessionTemplate(
    fixture('valid').replace(
      /^- \*\*Frozen header:\*\*.*$/m,
      '- **Frozen marker:** `<!-- doc-class: frozen -->`\n\n> **SUPERSEDED–FROZEN (Epic 2 bead 2.12; historical evidence only).**',
    ),
  );
  equal(repositoryBannerShape.ok, true);
});

test('fenced and surrounding-comment decoys are not completed records', () => {
  const parsed = parseSupersessionRecords(fixture('decoys-only'));
  equal(parsed.records.length, 0);
  deepEqual(
    parsed.findings.map((item) => item.code),
    ['SUPERSESSION_RECORD_MISSING'],
  );
});

test('requirements present only in fenced or commented decoys cannot satisfy a real block', () => {
  const result = checkSupersessionTemplate(fixture('decoy-elements'));
  equal(result.ok, false);
  for (const code of [
    'SUPERSESSION_FROZEN_MARKER_MISSING',
    'SUPERSESSION_FROZEN_BANNER_MISSING',
    'SUPERSESSION_DISPOSITION_TABLE_MISSING',
    'SUPERSESSION_CANONICAL_POINTER_TASK_MISSING',
    'SUPERSESSION_ONE_PR_ATOMICITY_MISSING',
  ])
    equal(
      result.findings.some((item) => item.code === code),
      true,
      code,
    );
});

test('placeholder form outside completed blocks is ignored', () => {
  const markdown = `${fixture('valid')}\n\n\`\`\`markdown\n${fixture('placeholder-row')}\n\`\`\`\n`;
  const result = checkSupersessionTemplate(markdown);
  equal(result.ok, true);
  equal(result.records.length, 1);
});

test('corpus mode checks every visible record attempt and ignores ordinary or decoy-only docs', () => {
  const empty = checkSupersessionCorpus([
    { path: 'plain.md', markdown: '# No supersession here\n' },
    { path: 'decoy.md', markdown: fixture('decoys-only') },
  ]);
  equal(empty.ok, false);
  equal(empty.recordCount, 0);
  deepEqual(empty.documents, []);

  const result = checkSupersessionCorpus([
    { path: 'plain.md', markdown: '# No supersession here\n' },
    { path: 'decoy.md', markdown: fixture('decoys-only') },
    { path: 'valid.md', markdown: fixture('valid') },
    { path: 'invalid.md', markdown: fixture('missing-pointer') },
    { path: 'unclosed.md', markdown: '<!-- BEGIN SUPERSESSION RECORD -->\n' },
  ]);
  equal(result.ok, false);
  equal(result.recordCount, 2);
  deepEqual(
    result.documents.map((document) => document.path),
    ['valid.md', 'invalid.md', 'unclosed.md'],
  );
  equal(
    result.documents[1].findings.some(
      (item) => item.code === 'SUPERSESSION_CANONICAL_POINTER_TASK_MISSING',
    ),
    true,
  );
  equal(
    result.documents[2].findings.some((item) => item.code === 'SUPERSESSION_RECORD_UNCLOSED'),
    true,
  );
});

test('tracked corpus CLI validates every filed record in repository order', () => {
  const paths = trackedDocumentationPaths(repositoryRoot);
  equal(paths.includes('000-docs/746-DR-TMPL-document-supersession.md'), true);

  const script = join(repositoryRoot, 'scripts', 'check-supersession-template.mjs');
  const checked = spawnSync(process.execPath, [script, '--all'], {
    cwd: repositoryRoot,
    encoding: 'utf8',
  });
  equal(checked.status, 0);
  match(
    checked.stdout,
    /supersession-corpus: OK \([1-9]\d* completed record\(s\) in [1-9]\d* tracked document\(s\)\)/,
  );
});

test('tracked symlinks cannot escape the physical repository boundary', (context) => {
  const root = mkdtempSync(join(tmpdir(), 'supersession-corpus-root-'));
  const outside = mkdtempSync(join(tmpdir(), 'supersession-corpus-outside-'));
  context.after(() => {
    rmSync(root, { recursive: true, force: true });
    rmSync(outside, { recursive: true, force: true });
  });

  mkdirSync(join(root, '000-docs'));
  const outsideRecord = join(outside, 'record.md');
  writeFileSync(outsideRecord, fixture('valid'));
  symlinkSync(outsideRecord, join(root, '000-docs', 'escape.md'));
  execFileSync('git', ['init', '--quiet'], { cwd: root });
  execFileSync('git', ['add', '000-docs/escape.md'], { cwd: root });

  throws(
    () => readTrackedDocumentation(root),
    /tracked documentation path is not a regular file: 000-docs\/escape\.md/,
  );
});

test('CLI returns zero for a valid record and nonzero red proof for an incomplete one', () => {
  const script = join(repositoryRoot, 'scripts', 'check-supersession-template.mjs');
  const pass = spawnSync(process.execPath, [script, join(fixtureRoot, 'valid.md')], {
    encoding: 'utf8',
  });
  equal(pass.status, 0);
  match(pass.stdout, /supersession-template: OK \(1 completed record\(s\)\)/);

  const red = spawnSync(process.execPath, [script, join(fixtureRoot, 'missing-pointer.md')], {
    encoding: 'utf8',
  });
  equal(red.status, 1);
  match(red.stderr, /SUPERSESSION_CANONICAL_POINTER_TASK_MISSING/);
  match(red.stderr, /supersession-template: 1 violation\(s\)/);
});
