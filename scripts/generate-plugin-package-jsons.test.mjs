import assert from 'node:assert/strict';
import test from 'node:test';

import { reconcileGeneratedPackageMetadata } from './generate-plugin-package-jsons.mjs';

const canonicalRepository = {
  type: 'git',
  url: 'git+https://github.com/jeremylongshore/tons-of-skills-marketplace.git',
  directory: 'plugins/testing/example-plugin',
};

test('reconciles stale repository metadata on generated package manifests', () => {
  const input = {
    name: '@intentsolutionsio/example-plugin',
    version: '1.2.3',
    repository: {
      type: 'git',
      url: 'git+https://github.com/jeremylongshore/claude-code-plugins-plus-skills.git',
      directory: 'plugins/testing/example-plugin',
    },
    bugs: 'https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues',
  };

  const result = reconcileGeneratedPackageMetadata(input, 'plugins/testing/example-plugin');

  assert.equal(result.changed, true);
  assert.deepEqual(result.pkg.repository, canonicalRepository);
  assert.equal(
    result.pkg.bugs,
    'https://github.com/jeremylongshore/tons-of-skills-marketplace/issues',
  );
  assert.equal(result.pkg.version, '1.2.3');
});

test('leaves already canonical generated metadata byte-shape stable', () => {
  const input = {
    name: '@intentsolutionsio/example-plugin',
    repository: canonicalRepository,
    bugs: 'https://github.com/jeremylongshore/tons-of-skills-marketplace/issues',
  };

  const result = reconcileGeneratedPackageMetadata(input, 'plugins/testing/example-plugin');

  assert.equal(result.changed, false);
  assert.equal(result.pkg, input);
});

test('does not rewrite upstream-owned package metadata', () => {
  const input = {
    name: 'upstream-plugin',
    repository: 'https://example.com/upstream/plugin',
    bugs: 'https://example.com/upstream/plugin/issues',
  };

  const result = reconcileGeneratedPackageMetadata(input, 'plugins/community/upstream-plugin');

  assert.equal(result.changed, false);
  assert.equal(result.pkg, input);
});

test('reconciles a repository-managed manifest that uses an older Intent scope', () => {
  const input = {
    name: '@intentsolutions/example-plugin',
    repository: {
      type: 'git',
      url: 'git+https://github.com/jeremylongshore/claude-code-plugins-plus-skills.git',
      directory: 'plugins/testing/example-plugin',
    },
  };

  const result = reconcileGeneratedPackageMetadata(input, 'plugins/testing/example-plugin');

  assert.equal(result.changed, true);
  assert.deepEqual(result.pkg.repository, canonicalRepository);
});

test('does not invent missing metadata while replacing legacy repository URLs', () => {
  const input = {
    name: '@intentsolutionsio/example-plugin',
    repository: {
      type: 'git',
      url: 'git+https://github.com/jeremylongshore/claude-code-plugins.git',
      directory: 'plugins/testing/example-plugin',
    },
  };

  const result = reconcileGeneratedPackageMetadata(input, 'plugins/testing/example-plugin');

  assert.equal(result.changed, true);
  assert.deepEqual(result.pkg.repository, canonicalRepository);
  assert.equal(Object.hasOwn(result.pkg, 'bugs'), false);
});

test('does not rewrite a scoped manifest owned by a source-marked mirror', () => {
  const input = {
    name: '@intentsolutionsio/upstream-plugin',
    repository: {
      type: 'git',
      url: 'git+https://github.com/upstream/upstream-plugin.git',
    },
    bugs: 'https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues',
  };

  const result = reconcileGeneratedPackageMetadata(input, 'plugins/community/upstream-plugin', {
    sourceOwned: true,
  });

  assert.equal(result.changed, false);
  assert.equal(result.pkg, input);
});
