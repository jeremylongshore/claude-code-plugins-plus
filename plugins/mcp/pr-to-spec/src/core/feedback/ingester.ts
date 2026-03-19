import type { IntentGraph } from "../graph/edge.js";
import type { IntentNode } from "../graph/node.js";
import { addEdge, propagateInvalidation, upsertNode } from "../graph/propagation.js";
import { computeContentHash, computeFragmentId } from "../schema/prompt-spec.js";

export interface ReviewFeedback {
	reviewer: string;
	status: "approved" | "changes_requested" | "commented";
	comments: string[];
	file_comments?: Array<{ file: string; comment: string }>;
}

export interface CIFeedback {
	pipeline: string;
	status: "passed" | "failed";
	failures?: string[];
}

export type FeedbackInput =
	| { type: "review"; data: ReviewFeedback }
	| { type: "ci"; data: CIFeedback };

/**
 * Ingest feedback and create feedback nodes in the graph.
 * Returns the IDs of newly created feedback nodes.
 */
export function ingestFeedback(
	graph: IntentGraph,
	feedback: FeedbackInput,
	targetNodeIds: string[],
): string[] {
	const now = new Date().toISOString();
	const createdIds: string[] = [];

	if (feedback.type === "review") {
		const review = feedback.data;
		const content = {
			reviewer: review.reviewer,
			status: review.status,
			comments: review.comments,
			file_comments: review.file_comments,
		};
		const hash = computeContentHash(content);
		const nodeId = computeFragmentId(hash);

		const feedbackNode: IntentNode = {
			node_id: nodeId,
			node_type: "feedback",
			content,
			parent_ids: targetNodeIds,
			// Confidence reflects how much the feedback validates the upstream intent:
			// approved (0.9) = strong signal that intent was correctly captured
			// changes_requested/commented (0.3) = weak signal, intent likely needs revision
			confidence: review.status === "approved" ? 0.9 : 0.3,
			source: "feedback",
			invalidated_at: null,
			version: 1,
			created_at: now,
			updated_at: now,
		};

		upsertNode(graph, feedbackNode);
		createdIds.push(nodeId);

		// If changes requested, this feedback invalidates the target nodes
		if (review.status === "changes_requested") {
			for (const targetId of targetNodeIds) {
				addEdge(graph, {
					source_id: nodeId,
					target_id: targetId,
					edge_type: "invalidates",
					created_at: now,
				});
				propagateInvalidation(graph, targetId);
			}
		}
	} else {
		const ci = feedback.data;
		const content = {
			pipeline: ci.pipeline,
			status: ci.status,
			failures: ci.failures,
		};
		const hash = computeContentHash(content);
		const nodeId = computeFragmentId(hash);

		const feedbackNode: IntentNode = {
			node_id: nodeId,
			node_type: "feedback",
			content,
			parent_ids: targetNodeIds,
			// Confidence reflects CI signal strength:
			// passed (0.95) = near-certain the code matches intent
			// failed (0.1) = strong negative signal, upstream nodes likely wrong
			confidence: ci.status === "passed" ? 0.95 : 0.1,
			source: "feedback",
			invalidated_at: null,
			version: 1,
			created_at: now,
			updated_at: now,
		};

		upsertNode(graph, feedbackNode);
		createdIds.push(nodeId);

		// CI failures invalidate target nodes
		if (ci.status === "failed") {
			for (const targetId of targetNodeIds) {
				addEdge(graph, {
					source_id: nodeId,
					target_id: targetId,
					edge_type: "invalidates",
					created_at: now,
				});
				propagateInvalidation(graph, targetId);
			}
		}
	}

	return createdIds;
}

/**
 * Create a summary of the graph's feedback state.
 */
export interface FeedbackSummary {
	total_nodes: number;
	feedback_nodes: number;
	stale_nodes: number;
	invalidation_chains: number;
}

export function summarizeFeedback(graph: IntentGraph): FeedbackSummary {
	const feedbackNodes = graph.nodes.filter((n) => n.node_type === "feedback");
	const staleNodes = graph.nodes.filter((n) => n.invalidated_at !== null);
	const invalidationEdges = graph.edges.filter((e) => e.edge_type === "invalidates");

	return {
		total_nodes: graph.nodes.length,
		feedback_nodes: feedbackNodes.length,
		stale_nodes: staleNodes.length,
		invalidation_chains: invalidationEdges.length,
	};
}
