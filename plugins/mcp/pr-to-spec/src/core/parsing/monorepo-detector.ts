export interface MonorepoInfo {
	detected: boolean;
	affected_packages: string[];
	workspace_root?: string;
}

/** Well-known monorepo workspace directories */
const WORKSPACE_DIRS = ["packages", "apps", "libs", "modules", "services", "plugins", "crates"];

/** Config files that indicate a monorepo workspace root */
const WORKSPACE_INDICATORS = [
	"pnpm-workspace.yaml",
	"lerna.json",
	"nx.json",
	"turbo.json",
	"rush.json",
	"Cargo.toml", // Rust workspaces
];

/** Minimal file shape required by monorepo detection */
interface MonorepoFile {
	filename: string;
}

/**
 * Detect monorepo structure from changed files.
 * Returns undefined if not a monorepo.
 */
export function detectMonorepo(files: MonorepoFile[]): MonorepoInfo | undefined {
	const packages = new Set<string>();
	let workspaceRoot: string | undefined;

	for (const file of files) {
		// Check for workspace root indicators
		const basename = file.filename.split("/").pop() ?? "";
		if (WORKSPACE_INDICATORS.includes(file.filename) || WORKSPACE_INDICATORS.includes(basename)) {
			workspaceRoot = file.filename.includes("/")
				? file.filename.split("/").slice(0, -1).join("/")
				: ".";
		}

		// Check if file is under a known workspace directory
		const parts = file.filename.split("/");
		if (parts.length >= 3) {
			const topDir = parts[0];
			if (WORKSPACE_DIRS.includes(topDir)) {
				packages.add(`${topDir}/${parts[1]}`);
			}
		}
	}

	// Also detect by package.json presence in subdirectories
	for (const file of files) {
		const parts = file.filename.split("/");
		if (
			parts.length >= 3 &&
			parts[parts.length - 1] === "package.json" &&
			parts[0] !== "node_modules"
		) {
			const pkgPath = parts.slice(0, -1).join("/");
			packages.add(pkgPath);
		}
	}

	if (packages.size === 0) {
		return undefined;
	}

	return {
		detected: true,
		affected_packages: [...packages].sort(),
		workspace_root: workspaceRoot,
	};
}
