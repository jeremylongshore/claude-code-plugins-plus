export interface SemanticChange {
	type: "function" | "class" | "import" | "export" | "config" | "type" | "test" | "other";
	name: string;
	action: "added" | "removed" | "modified";
	file: string;
}

/** Minimal file shape required by semantic diff analysis */
interface SemanticFile {
	filename: string;
	patch?: string;
}

/**
 * Extract semantic meaning from diffs — identifies functions, classes,
 * imports, exports, and config changes from patch data.
 * Deterministic heuristic analysis, no AST parsing needed.
 */
export function analyzeSemanticDiff(files: SemanticFile[]): SemanticChange[] {
	const changes: SemanticChange[] = [];

	for (const file of files) {
		if (!file.patch) continue;

		const added = extractLines(file.patch, "+");
		const removed = extractLines(file.patch, "-");

		// Detect function changes
		for (const line of added) {
			const fn = matchFunction(line);
			if (fn) {
				changes.push({ type: "function", name: fn, action: "added", file: file.filename });
			}
		}
		for (const line of removed) {
			const fn = matchFunction(line);
			if (fn) {
				const wasModified = added.some((a) => matchFunction(a) === fn);
				if (!wasModified) {
					changes.push({ type: "function", name: fn, action: "removed", file: file.filename });
				}
			}
		}

		// Detect class changes
		for (const line of added) {
			const cls = matchClass(line);
			if (cls) changes.push({ type: "class", name: cls, action: "added", file: file.filename });
		}
		for (const line of removed) {
			const cls = matchClass(line);
			if (cls) {
				const wasModified = added.some((a) => matchClass(a) === cls);
				if (!wasModified) {
					changes.push({ type: "class", name: cls, action: "removed", file: file.filename });
				}
			}
		}

		// Detect import changes
		for (const line of added) {
			const imp = matchImport(line);
			if (imp) changes.push({ type: "import", name: imp, action: "added", file: file.filename });
		}
		for (const line of removed) {
			const imp = matchImport(line);
			if (imp && !added.some((a) => matchImport(a) === imp)) {
				changes.push({ type: "import", name: imp, action: "removed", file: file.filename });
			}
		}

		// Detect export changes
		for (const line of added) {
			const exp = matchExport(line);
			if (exp) changes.push({ type: "export", name: exp, action: "added", file: file.filename });
		}

		// Detect type/interface changes
		for (const line of added) {
			const t = matchType(line);
			if (t) changes.push({ type: "type", name: t, action: "added", file: file.filename });
		}
	}

	return deduplicateChanges(changes);
}

function extractLines(patch: string, prefix: "+" | "-"): string[] {
	return patch
		.split("\n")
		.filter((line) => line.startsWith(prefix) && !line.startsWith(`${prefix}${prefix}${prefix}`))
		.map((line) => line.slice(1).trim());
}

// Language-agnostic function patterns
function matchFunction(line: string): string | null {
	// TypeScript/JavaScript: function name(, const name = (, async function name(
	const tsMatch = line.match(
		/(?:export\s+)?(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(/,
	);
	if (tsMatch) return tsMatch[1] ?? tsMatch[2] ?? null;

	// Python: def name(
	const pyMatch = line.match(/(?:async\s+)?def\s+(\w+)\s*\(/);
	if (pyMatch) return pyMatch[1] ?? null;

	// Go: func name( or func (receiver) name(
	const goMatch = line.match(/func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(/);
	if (goMatch) return goMatch[1] ?? null;

	// Rust: fn name( or pub fn name(
	const rsMatch = line.match(/(?:pub\s+)?(?:async\s+)?fn\s+(\w+)/);
	if (rsMatch) return rsMatch[1] ?? null;

	return null;
}

function matchClass(line: string): string | null {
	const match = line.match(/(?:export\s+)?(?:abstract\s+)?class\s+(\w+)/);
	return match?.[1] ?? null;
}

function matchImport(line: string): string | null {
	// JS/TS: import ... from "module"
	const jsMatch = line.match(/import\s+.*from\s+["']([^"']+)["']/);
	if (jsMatch) return jsMatch[1] ?? null;

	// Python: from module import ... or import module
	const pyMatch = line.match(/(?:from\s+(\S+)\s+import|import\s+(\S+))/);
	if (pyMatch) return pyMatch[1] ?? pyMatch[2] ?? null;

	// Go: "package/path"
	const goMatch = line.match(/^\s*"([^"]+)"\s*$/);
	if (goMatch) return goMatch[1] ?? null;

	return null;
}

function matchExport(line: string): string | null {
	const match = line.match(
		/export\s+(?:default\s+)?(?:function|class|const|type|interface)\s+(\w+)/,
	);
	return match?.[1] ?? null;
}

function matchType(line: string): string | null {
	const match = line.match(/(?:export\s+)?(?:type|interface)\s+(\w+)/);
	return match?.[1] ?? null;
}

function deduplicateChanges(changes: SemanticChange[]): SemanticChange[] {
	const seen = new Set<string>();
	return changes.filter((c) => {
		const key = `${c.type}:${c.name}:${c.action}:${c.file}`;
		if (seen.has(key)) return false;
		seen.add(key);
		return true;
	});
}
