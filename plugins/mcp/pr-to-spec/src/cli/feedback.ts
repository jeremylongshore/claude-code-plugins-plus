import { Command } from "commander";
import {
	type CIFeedback,
	type ReviewFeedback,
	ingestFeedback,
	summarizeFeedback,
} from "../core/feedback/ingester.js";
import { getStaleNodes } from "../core/graph/propagation.js";
import { readGraph, writeGraph } from "../core/graph/storage.js";

export const feedbackCommand = new Command("feedback").description(
	"Ingest review/CI feedback and update the intent graph",
);

feedbackCommand
	.command("review")
	.description("Ingest a code review result")
	.requiredOption("--reviewer <name>", "Reviewer name")
	.requiredOption("--status <status>", "Review status: approved, changes_requested, commented")
	.option("--comment <text...>", "Review comments (can repeat)")
	.requiredOption("--target <id...>", "Target node IDs to attach feedback to")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const graph = readGraph();

		const review: ReviewFeedback = {
			reviewer: opts.reviewer,
			status: opts.status as ReviewFeedback["status"],
			comments: opts.comment ?? [],
		};

		const targetIds: string[] = opts.target;

		const createdIds = ingestFeedback(graph, { type: "review", data: review }, targetIds);

		writeGraph(graph);

		if (opts.json) {
			const summary = summarizeFeedback(graph);
			process.stdout.write(
				`${JSON.stringify(
					{
						created_feedback_ids: createdIds,
						...summary,
						stale_node_ids: getStaleNodes(graph).map((n) => n.node_id),
					},
					null,
					2,
				)}\n`,
			);
		} else {
			console.log(`Feedback ingested from ${review.reviewer} (${review.status})`);
			if (review.status === "changes_requested") {
				const stale = getStaleNodes(graph);
				console.log(`${stale.length} node(s) marked as stale`);
			}
		}
	});

feedbackCommand
	.command("ci")
	.description("Ingest CI pipeline results")
	.requiredOption("--pipeline <name>", "Pipeline/workflow name")
	.requiredOption("--status <status>", "CI status: passed, failed")
	.option("--failure <text...>", "Failure descriptions (can repeat)")
	.requiredOption("--target <id...>", "Target node IDs to attach feedback to")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const graph = readGraph();

		const ci: CIFeedback = {
			pipeline: opts.pipeline,
			status: opts.status as CIFeedback["status"],
			failures: opts.failure,
		};

		const targetIds: string[] = opts.target;

		const createdIds = ingestFeedback(graph, { type: "ci", data: ci }, targetIds);

		writeGraph(graph);

		if (opts.json) {
			const summary = summarizeFeedback(graph);
			process.stdout.write(
				`${JSON.stringify(
					{
						created_feedback_ids: createdIds,
						...summary,
						stale_node_ids: getStaleNodes(graph).map((n) => n.node_id),
					},
					null,
					2,
				)}\n`,
			);
		} else {
			console.log(`CI feedback ingested: ${ci.pipeline} (${ci.status})`);
			if (ci.status === "failed") {
				const stale = getStaleNodes(graph);
				console.log(`${stale.length} node(s) marked as stale`);
			}
		}
	});

feedbackCommand
	.command("status")
	.description("Show current feedback and graph status")
	.option("--json", "Output as JSON", false)
	.action((opts) => {
		const graph = readGraph();
		const summary = summarizeFeedback(graph);
		const stale = getStaleNodes(graph);

		if (opts.json) {
			process.stdout.write(
				`${JSON.stringify(
					{
						...summary,
						stale_nodes: stale.map((n) => ({
							node_id: n.node_id,
							node_type: n.node_type,
							invalidated_at: n.invalidated_at,
							version: n.version,
						})),
					},
					null,
					2,
				)}\n`,
			);
		} else {
			console.log(`Graph: ${summary.total_nodes} nodes, ${summary.feedback_nodes} feedback`);
			console.log(`Stale: ${summary.stale_nodes} node(s)`);
			if (stale.length > 0) {
				for (const n of stale.slice(0, 10)) {
					console.log(
						`  [${n.node_type}] ${n.node_id} (v${n.version}, stale since ${n.invalidated_at})`,
					);
				}
			}
		}
	});
