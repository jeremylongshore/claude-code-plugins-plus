import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      include: ['src/**/*.js'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.test.js',
        '**/*.spec.js',
      ],
      all: true,
      // Migrated from vitest 0.x flat format to vitest 2.x nested
      // `thresholds: {}`. Floor declared in tests/TESTING.md.
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
    include: ['tests/**/*.test.js'],
    exclude: ['node_modules/', 'dist/'],
  },
});
