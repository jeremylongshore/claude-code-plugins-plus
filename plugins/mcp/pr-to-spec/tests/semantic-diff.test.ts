import { describe, expect, it } from "vitest";
import type { PRFile } from "../src/core/github/client.js";
import { analyzeSemanticDiff } from "../src/core/parsing/semantic-diff.js";

function file(filename: string, patch: string): PRFile {
	return { filename, status: "modified", additions: 10, deletions: 5, patch };
}

describe("analyzeSemanticDiff", () => {
	it("detects added TypeScript functions", () => {
		const changes = analyzeSemanticDiff([
			file(
				"src/utils.ts",
				"+export function formatDate(date: Date) {\n+  return date.toISOString();\n+}",
			),
		]);
		expect(
			changes.some((c) => c.type === "function" && c.name === "formatDate" && c.action === "added"),
		).toBe(true);
	});

	it("detects removed functions", () => {
		const changes = analyzeSemanticDiff([
			file("src/old.ts", "-function deprecated() {\n-  // old code\n-}"),
		]);
		expect(
			changes.some(
				(c) => c.type === "function" && c.name === "deprecated" && c.action === "removed",
			),
		).toBe(true);
	});

	it("detects Python functions", () => {
		const changes = analyzeSemanticDiff([
			file("app/views.py", "+def handle_request(request):\n+    pass"),
		]);
		expect(changes.some((c) => c.type === "function" && c.name === "handle_request")).toBe(true);
	});

	it("detects Go functions", () => {
		const changes = analyzeSemanticDiff([
			file("main.go", "+func handleHTTP(w http.ResponseWriter, r *http.Request) {"),
		]);
		expect(changes.some((c) => c.type === "function" && c.name === "handleHTTP")).toBe(true);
	});

	it("detects Rust functions", () => {
		const changes = analyzeSemanticDiff([
			file("src/lib.rs", "+pub async fn process(data: &[u8]) -> Result<()> {"),
		]);
		expect(changes.some((c) => c.type === "function" && c.name === "process")).toBe(true);
	});

	it("detects class additions", () => {
		const changes = analyzeSemanticDiff([file("src/models.ts", "+export class UserService {")]);
		expect(changes.some((c) => c.type === "class" && c.name === "UserService")).toBe(true);
	});

	it("detects import changes", () => {
		const changes = analyzeSemanticDiff([
			file("src/main.ts", '+import { Router } from "express";\n-import { App } from "./old-app"'),
		]);
		const addedImport = changes.find((c) => c.type === "import" && c.action === "added");
		expect(addedImport?.name).toBe("express");
		const removedImport = changes.find((c) => c.type === "import" && c.action === "removed");
		expect(removedImport?.name).toBe("./old-app");
	});

	it("detects type/interface additions", () => {
		const changes = analyzeSemanticDiff([
			file("src/types.ts", "+export interface UserConfig {\n+  name: string;\n+}"),
		]);
		expect(changes.some((c) => c.type === "type" && c.name === "UserConfig")).toBe(true);
	});

	it("returns empty array for files without patches", () => {
		const changes = analyzeSemanticDiff([
			{ filename: "src/test.ts", status: "modified", additions: 5, deletions: 2 },
		]);
		expect(changes).toEqual([]);
	});

	it("deduplicates identical changes", () => {
		const changes = analyzeSemanticDiff([
			file("src/a.ts", "+function bar() {}\n+function bar() {}"),
		]);
		const bars = changes.filter((c) => c.name === "bar" && c.type === "function");
		expect(bars).toHaveLength(1);
	});
});
