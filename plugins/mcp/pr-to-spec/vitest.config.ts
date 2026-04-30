import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["tests/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html", "lcov"],
      include: ["src/**/*.ts"],
      exclude: ["src/cli/**", "src/action/**"],
      // Floor declared in tests/TESTING.md (lines/functions/statements: 70,
      // branches: 60). Per-config values may exceed the floor; lowering them
      // below the floor is REFUSED by audit-harness escape-scan.
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 70,
        statements: 80,
      },
    },
  },
});
