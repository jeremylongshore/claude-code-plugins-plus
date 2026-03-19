export interface RiskFlag {
	category: string;
	description: string;
	severity: "low" | "medium" | "high";
}

/** Minimal file shape required by the risk classifier */
interface RiskFile {
	filename: string;
	additions: number;
	deletions: number;
	patch?: string;
}

interface RiskRule {
	category: string;
	description: string;
	severity: "low" | "medium" | "high";
	match: (file: RiskFile) => boolean;
}

/** Paths that are never risky (docs, tests, examples, generated files) */
function isDocOrTestPath(filename: string): boolean {
	return /\b(docs?|documentation|content|examples?|__tests__|test-fixtures|\.md$|\.rst$|\.txt$|\.adoc$)\b/i.test(
		filename,
	);
}

/** Check if a filename segment looks like a file (has extension) vs a directory */
function isFilename(segment: string): boolean {
	return /\.\w+$/.test(segment);
}

const RISK_RULES: RiskRule[] = [
	{
		category: "authentication",
		description: "Changes to authentication or authorization logic",
		severity: "high",
		match: (f) =>
			!isDocOrTestPath(f.filename) &&
			/\b(auth|login|session|oauth|jwt|passport)\b/i.test(f.filename),
	},
	{
		category: "secrets",
		description: "Changes to secrets or environment handling",
		severity: "high",
		match: (f) =>
			/\.(env|secret|key|pem|cert)(\..*)?$/.test(f.filename) ||
			/\b(secrets?|credentials?)\b/i.test(f.filename) ||
			// Only match "config" in clearly sensitive contexts
			(/\bconfig\b/i.test(f.filename) &&
				/\b(secret|credential|env|auth|database|db)\b/i.test(f.filename)),
	},
	{
		category: "dependencies",
		description: "Dependency changes may introduce supply chain risk",
		severity: "medium",
		match: (f) =>
			/^(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|Gemfile(\.lock)?|requirements.*\.txt|Cargo\.(toml|lock)|go\.(mod|sum)|composer\.(json|lock)|\.tool-versions)$/.test(
				f.filename,
			),
	},
	{
		category: "database",
		description: "Database migration or schema changes",
		severity: "high",
		match: (f) =>
			/\.sql$/.test(f.filename) ||
			/\b(migration|migrate)\b/i.test(f.filename) ||
			// Only match "schema" in database-related paths, not generic schemas
			(/\bschema\b/i.test(f.filename) &&
				/\b(db|database|prisma|drizzle|knex|sequelize|typeorm|migration|sql|alembic)\b/i.test(
					f.filename,
				)),
	},
	{
		category: "infrastructure",
		description: "Infrastructure or deployment configuration changes",
		severity: "medium",
		match: (f) =>
			/\b(docker|terraform|k8s|kubernetes|helm|deploy|infra)\b/i.test(f.filename) ||
			(/\.(ya?ml|toml)$/.test(f.filename) && /\b(deploy|infra|workflow)\b/i.test(f.filename)),
	},
	{
		category: "permissions",
		description: "Changes to permission, role, or access control logic",
		severity: "high",
		match: (f) =>
			!isDocOrTestPath(f.filename) &&
			/\b(permission|rbac|acl|access-control|policy)\b/i.test(f.filename),
	},
	{
		category: "payment",
		description: "Changes to payment, billing, or financial logic",
		severity: "high",
		match: (f) =>
			!isDocOrTestPath(f.filename) &&
			/\b(payment|billing|stripe|invoice|subscription|pricing)\b/i.test(f.filename),
	},
	{
		category: "destructive-operations",
		description: "File may contain destructive operations (delete, drop, truncate)",
		severity: "medium",
		match: (f) =>
			f.patch !== undefined &&
			/\b(DELETE\s+FROM|DROP\s+TABLE|TRUNCATE|destroy_all|remove_all|purge|wipe)\b/.test(f.patch),
	},
	{
		category: "security-config",
		description: "Changes to security configuration, CORS, or CSP",
		severity: "medium",
		match: (f) =>
			!isDocOrTestPath(f.filename) &&
			(/\b(cors|csp|helmet|security-headers)\b/i.test(f.filename) ||
				// Only flag "security" or "middleware" in source code paths
				(/\b(security|middleware)\b/i.test(f.filename) &&
					/\.(ts|js|py|rb|go|rs|java|php)$/.test(f.filename))),
	},
	{
		category: "large-change",
		description: "File has a large number of changes, increasing review risk",
		severity: "low",
		match: (f) => f.additions + f.deletions > 300,
	},
];

export function classifyRisks(files: RiskFile[]): RiskFlag[] {
	const flags: RiskFlag[] = [];
	const seen = new Set<string>();

	for (const file of files) {
		for (const rule of RISK_RULES) {
			if (rule.match(file) && !seen.has(`${rule.category}:${file.filename}`)) {
				seen.add(`${rule.category}:${file.filename}`);
				flags.push({
					category: rule.category,
					description: `${rule.description} (${file.filename})`,
					severity: rule.severity,
				});
			}
		}
	}

	// Sort by severity: high > medium > low
	const order = { high: 0, medium: 1, low: 2 };
	return flags.sort((a, b) => order[a.severity] - order[b.severity]);
}
