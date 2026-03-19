import { describe, expect, it } from "vitest";
import type { PRFile } from "../src/core/github/client.js";
import { detectMonorepo } from "../src/core/parsing/monorepo-detector.js";

function file(filename: string): PRFile {
	return { filename, status: "modified", additions: 10, deletions: 5 };
}

describe("detectMonorepo", () => {
	it("returns undefined for non-monorepo files", () => {
		const result = detectMonorepo([file("src/main.ts"), file("tests/main.test.ts")]);
		expect(result).toBeUndefined();
	});

	it("detects packages directory", () => {
		const result = detectMonorepo([
			file("packages/core/src/index.ts"),
			file("packages/cli/src/main.ts"),
		]);
		expect(result?.detected).toBe(true);
		expect(result?.affected_packages).toEqual(["packages/cli", "packages/core"]);
	});

	it("detects apps directory", () => {
		const result = detectMonorepo([file("apps/web/pages/index.tsx"), file("apps/api/src/main.ts")]);
		expect(result?.detected).toBe(true);
		expect(result?.affected_packages).toContain("apps/web");
		expect(result?.affected_packages).toContain("apps/api");
	});

	it("detects workspace root from pnpm-workspace.yaml", () => {
		const result = detectMonorepo([
			file("pnpm-workspace.yaml"),
			file("packages/core/src/index.ts"),
		]);
		expect(result?.detected).toBe(true);
		expect(result?.workspace_root).toBe(".");
	});

	it("detects turborepo", () => {
		const result = detectMonorepo([file("turbo.json"), file("packages/ui/src/Button.tsx")]);
		expect(result?.detected).toBe(true);
	});

	it("detects by nested package.json", () => {
		const result = detectMonorepo([file("libs/auth/package.json"), file("libs/auth/src/index.ts")]);
		expect(result?.detected).toBe(true);
		expect(result?.affected_packages).toContain("libs/auth");
	});

	it("detects Rust workspaces", () => {
		const result = detectMonorepo([file("crates/parser/src/lib.rs"), file("Cargo.toml")]);
		expect(result?.detected).toBe(true);
		expect(result?.affected_packages).toContain("crates/parser");
	});

	it("deduplicates packages", () => {
		const result = detectMonorepo([
			file("packages/core/src/a.ts"),
			file("packages/core/src/b.ts"),
			file("packages/core/tests/c.test.ts"),
		]);
		expect(result?.affected_packages).toEqual(["packages/core"]);
	});
});
