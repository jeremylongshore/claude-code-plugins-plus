import test from 'node:test';
import assert from 'node:assert/strict';
import {
  compareFrozenBytes,
  compareGeneratedBytes,
  expectedClass,
  parseDocClass,
} from './check-doc-classes.mjs';

test('accepts each supported class only at the first line', () => {
  for (const className of ['canonical', 'generated', 'frozen', 'record']) {
    assert.deepEqual(parseDocClass(`<!-- doc-class: ${className} -->\n\n# Doc\n`), {
      className,
      reason: null,
    });
  }
  assert.equal(parseDocClass(`# Doc\n<!-- doc-class: record -->\n`).reason, 'MISSING_MARKER');
});

test('rejects missing, malformed, and unknown classes fail closed', () => {
  assert.equal(parseDocClass('# Doc\n').reason, 'MISSING_MARKER');
  assert.equal(parseDocClass('<!-- doc-class: canonical\n').reason, 'MALFORMED_MARKER');
  assert.equal(parseDocClass('<!-- doc-class: draft -->\n').reason, 'UNKNOWN_CLASS');
});

test('maps frozen, generated, canonical, and record paths deterministically', () => {
  assert.equal(
    expectedClass('000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md'),
    'frozen',
  );
  assert.equal(expectedClass('000-docs/000-INDEX.md'), 'generated');
  assert.equal(
    expectedClass('000-docs/727-AT-ARCH-master-modernization-blueprint.md'),
    'canonical',
  );
  assert.equal(expectedClass('000-docs/769-AA-AACR-epic-1-count-cohort-closure.md'), 'record');
});

test('red fixture: edited frozen bytes are refused', () => {
  assert.deepEqual(compareFrozenBytes('same', 'same', 'frozen.md'), []);
  assert.deepEqual(compareFrozenBytes('edited', 'same', 'frozen.md'), [
    { code: 'FROZEN_CONTENT_DRIFT', path: 'frozen.md' },
  ]);
});

test('red fixture: generated output drift is refused', () => {
  assert.deepEqual(compareGeneratedBytes('same', 'same', 'generated.md'), []);
  assert.deepEqual(compareGeneratedBytes('edited', 'same', 'generated.md'), [
    { code: 'GENERATED_CONTENT_DRIFT', path: 'generated.md' },
  ]);
});
