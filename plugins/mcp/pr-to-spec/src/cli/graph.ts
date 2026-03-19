import { Command } from "commander";
import {
	computeGraphStats,
	findImpactedNodes,
	getAncestors,
	getDescendants,
} from "../core/graph/query.js";
import { readGraph } from "../core/graph/storage.js";

export const graphCommand = new Command("graph").description("Query and inspect the intent DAG");

graphCommand
	.command("query")
	.description("Query ancestors or descendants of a node")
	.requiredOption("--node <id>", "Node ID to query")
	.option("--direction <dir>", "Traversal direction: up (ancestors) or down (descendants)", "down")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const graph = readGraph();
		const node = graph.nodes.find((n) => n.node_id === opts.node);
		if (!node) {
			if (opts.json) {
				process.stdout.write(
					`${JSON.stringify({ error: "node_not_found", node_id: opts.node })}\n`,
				);
			} else {
				console.error(`Node not found: ${opts.node}`);
			}
			process.exit(1);
		}

		const ids =
			opts.direction === "up" ? getAncestors(graph, opts.node) : getDescendants(graph, opts.node);

		const nodes = ids.map((id) => graph.nodes.find((n) => n.node_id === id)).filter(Boolean);

		if (opts.json) {
			process.stdout.write(
				`${JSON.stringify({ direction: opts.direction, root: opts.node, nodes }, null, 2)}\n`,
			);
		} else {
			console.log(
				`${opts.direction === "up" ? "Ancestors" : "Descendants"} of ${opts.node} (${nodes.length}):`,
			);
			for (const n of nodes) {
				if (n) {
					const stale = n.invalidated_at ? " [STALE]" : "";
					console.log(`  ${n.node_id} (${n.node_type}, confidence: ${n.confidence})${stale}`);
				}
			}
		}
	});

graphCommand
	.command("impact")
	.description("Show nodes impacted by changes to given node IDs")
	.requiredOption("--changed <ids...>", "Changed node ID(s)")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const graph = readGraph();
		const report = findImpactedNodes(graph, opts.changed);

		if (opts.json) {
			process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
		} else {
			console.log(`Impact analysis for ${report.changed_node_ids.length} changed node(s):`);
			console.log(`Total impacted: ${report.total_impacted}`);
			for (const n of report.impacted_nodes) {
				console.log(
					`  ${n.node_id} (${n.node_type}, distance: ${n.distance}, confidence: ${n.confidence})`,
				);
			}
		}
	});

graphCommand
	.command("stats")
	.description("Show graph statistics")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const graph = readGraph();
		const stats = computeGraphStats(graph);

		if (opts.json) {
			process.stdout.write(`${JSON.stringify(stats, null, 2)}\n`);
		} else {
			console.log(`Nodes: ${stats.total_nodes}`);
			for (const [type, count] of Object.entries(stats.nodes_by_type)) {
				console.log(`  ${type}: ${count}`);
			}
			console.log(`Edges: ${stats.total_edges}`);
			for (const [type, count] of Object.entries(stats.edges_by_type)) {
				console.log(`  ${type}: ${count}`);
			}
			console.log(`Stale: ${stats.stale_nodes}`);
			console.log(`Avg confidence: ${stats.avg_confidence.toFixed(2)}`);
			console.log(`Min confidence: ${stats.min_confidence.toFixed(2)}`);
		}
	});
