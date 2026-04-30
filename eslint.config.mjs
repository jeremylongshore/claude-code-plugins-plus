// Root ESLint flat config (ESLint 9).
//
// Scope: deliberately narrow. We lint root-level scripts (scripts/, root .mjs/.cjs)
// and packages/cli/src/. Individual workspaces (marketplace, plugins/mcp/*, packages/*)
// retain their own configs and remain authoritative for their trees.
//
// To extend coverage to a new directory, add it to `files` below — but expect
// pre-existing errors and address them in a separate cleanup PR.
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  {
    ignores: [
      'node_modules/**',
      '**/node_modules/**',
      'dist/**',
      '**/dist/**',
      '.astro/**',
      '**/.astro/**',
      'coverage/**',
      '**/coverage/**',
      'backups/**',
      'archive/**',
      '_PRESERVE_MIGRATION/**',
      '.firebase/**',
      'marketplace/**',
      'packages/analytics-daemon/**',
      'packages/analytics-dashboard/**',
      'plugins/**',
      'freshie/**',
      'functions/**',
      'workspace/**',
      '.husky/**',
      '.beads/**',
      '.claude/**',
      '.venv/**',
      'redirects/**',
      'planned-skills/**',
      'claudes-docs/**',
      // Out-of-scope subtrees (own configs / large surface area / Python)
      'packages/plugin-validator/**',
      'tests/e2e/**',
      'tests/**/*.py',
      // Auto-generated catalogs
      '.claude-plugin/marketplace.json',
      'marketplace/src/data/**/*.json',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['scripts/**/*.{js,mjs,cjs}', '*.{js,mjs,cjs}', 'packages/cli/src/**/*.ts'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        // Node + browser unions cover the majority of root scripts
        process: 'readonly',
        console: 'readonly',
        Buffer: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        require: 'readonly',
        module: 'readonly',
        exports: 'readonly',
        global: 'readonly',
        URL: 'readonly',
        URLSearchParams: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearTimeout: 'readonly',
        clearInterval: 'readonly',
      },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      'no-unused-vars': 'off',
      'no-empty': ['error', { allowEmptyCatch: true }],
    },
  },
  {
    // CommonJS files legitimately use require()
    files: ['**/*.cjs'],
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
];
