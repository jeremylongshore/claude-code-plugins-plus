import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { type IntentGraph, IntentGraphSchema } from "./edge.js";
import { createEmptyGraph } from "./propagation.js";

const GRAPH_DIR = process.env.PR_TO_SPEC_DIR ?? ".pr-to-spec";
const GRAPH_FILE = "graph.json";

export function getGraphPath(cwd: string = process.cwd()): string {
	return resolve(cwd, GRAPH_DIR, GRAPH_FILE);
}

export function readGraph(cwd: string = process.cwd()): IntentGraph {
	const path = getGraphPath(cwd);
	if (!existsSync(path)) return createEmptyGraph();
	const raw = JSON.parse(readFileSync(path, "utf-8"));
	return IntentGraphSchema.parse(raw);
}

export function writeGraph(graph: IntentGraph, cwd: string = process.cwd()): void {
	const dir = resolve(cwd, GRAPH_DIR);
	mkdirSync(dir, { recursive: true });
	const path = getGraphPath(cwd);
	writeFileSync(path, JSON.stringify(graph, null, 2), "utf-8");
}
