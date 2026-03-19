import { describe, expect, it, vi } from "vitest";

// Mock node:child_process at module level so buildLocalDiffSource never calls real git
vi.mock("node:child_process", () => ({
	execSync: vi.fn((cmd: string) => {
		if (cmd.includes("rev-parse --abbrev-ref")) return "feat/my-branch";
		if (cmd.includes("config user.name")) return "developer";
		if (cmd.includes("rev-list --count")) return "3";
		if (cmd.includes("--name-status")) return "M\tsrc/a.ts\nA\tsrc/b.ts\n";
		if (cmd.includes("--stat"))
			return " src/a.ts | 5 +++--\n src/b.ts | 10 ++++++++++\n 2 files changed\n";
		// per-file patch
		return "+changed line\n";
	}),
}));

const { buildLocalDiffSource } = await import("../src/core/sources/local.js");

describe("buildLocalDiffSource — staged mode", () => {
	it("sets source_type to local_staged", () => {
		const source = buildLocalDiffSource({ staged: true });
		expect(source.source_type).toBe("local_staged");
	});

	it("sets base_ref to HEAD for staged mode", () => {
		const source = buildLocalDiffSource({ staged: true });
		expect(source.base_ref).toBe("HEAD");
	});

	it("sets title to 'Staged changes'", () => {
		const source = buildLocalDiffSource({ staged: true });
		expect(source.title).toBe("Staged changes");
	});

	it("commits is undefined for staged mode (no commit range)", () => {
		const source = buildLocalDiffSource({ staged: true });
		expect(source.commits).toBeUndefined();
	});

	it("files array is populated from mocked name-status", () => {
		const source = buildLocalDiffSource({ staged: true });
		expect(source.files.length).toBeGreaterThan(0);
	});
});

describe("buildLocalDiffSource — commits mode", () => {
	it("sets source_type to local_commits", () => {
		const source = buildLocalDiffSource({ commits: 2 });
		expect(source.source_type).toBe("local_commits");
	});

	it("sets base_ref to HEAD~N", () => {
		const source = buildLocalDiffSource({ commits: 2 });
		expect(source.base_ref).toBe("HEAD~2");
	});

	it("title includes commit count and branch name", () => {
		const source = buildLocalDiffSource({ commits: 2 });
		expect(source.title).toContain("Last 2 commit");
		expect(source.title).toContain("feat/my-branch");
	});

	it("title uses singular 'commit' for commits=1", () => {
		const source = buildLocalDiffSource({ commits: 1 });
		expect(source.title).toContain("Last 1 commit");
	});

	it("commits field reflects mocked rev-list count", () => {
		const source = buildLocalDiffSource({ commits: 3 });
		// rev-list mock returns "3"
		expect(source.commits).toBe(3);
	});
});

describe("buildLocalDiffSource — branch mode", () => {
	it("sets source_type to local_branch", () => {
		const source = buildLocalDiffSource({ base: "main" });
		expect(source.source_type).toBe("local_branch");
	});

	it("uses provided base ref", () => {
		const source = buildLocalDiffSource({ base: "develop" });
		expect(source.base_ref).toBe("develop");
	});

	it("defaults base to main when no base option given", () => {
		const source = buildLocalDiffSource({});
		expect(source.base_ref).toBe("main");
	});

	it("title includes branch and base ref", () => {
		const source = buildLocalDiffSource({ base: "main" });
		expect(source.title).toContain("feat/my-branch");
		expect(source.title).toContain("main");
	});

	it("commits field is set from git rev-list count", () => {
		const source = buildLocalDiffSource({ base: "main" });
		expect(typeof source.commits).toBe("number");
		expect(source.commits).toBe(3);
	});

	it("files have filename, status, additions, deletions", () => {
		const source = buildLocalDiffSource({ base: "main" });
		for (const f of source.files) {
			expect(typeof f.filename).toBe("string");
			expect(["added", "modified", "removed", "renamed", "copied"]).toContain(f.status);
			expect(typeof f.additions).toBe("number");
			expect(typeof f.deletions).toBe("number");
		}
	});

	it("head_ref is the current branch from git", () => {
		const source = buildLocalDiffSource({ base: "main" });
		expect(source.head_ref).toBe("feat/my-branch");
	});

	it("author is taken from git config user.name", () => {
		const source = buildLocalDiffSource({ base: "main" });
		expect(source.author).toBe("developer");
	});
});
