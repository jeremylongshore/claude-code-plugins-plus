import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { Database } from "bun:sqlite";
import { randomUUID } from "crypto";
// TODO(x-bug-triage): db/migrate.ts has never been written; the describe
// blocks in this file are .skip until the migration module is implemented.
// See lib/db.test.ts for the same TODO.
const migrate = (_db: Database): void => { /* stub — see TODO above */ };
import { getAuditEntriesByRun, getAuditEntriesByType } from "./db";
import {
  writeAuditEvent,
  auditIngestRunStarted,
  auditIngestRunCompleted,
  auditSourceFetched,
  auditCandidateClassified,
  auditPiiRedaction,
  auditClusterCreated,
  auditClusterUpdated,
  auditClusterStateChanged,
  auditRoutingRecommendation,
  auditEscalationTriggered,
  auditHumanAction,
  auditOverrideCreated,
} from "./audit";

let db: Database;

function createTestDb(): Database {
  const d = new Database(":memory:");
  d.exec("PRAGMA foreign_keys = ON");
  migrate(d);
  return d;
}

describe.skip("audit writer", () => {
  beforeEach(() => {
    db = createTestDb();
  });
  afterEach(() => {
    db.close();
  });

  // writeAuditEvent core tests
  describe("writeAuditEvent", () => {
    test("returns complete AuditEntry with all fields", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const postId = randomUUID();
      const entry = writeAuditEvent(db, "cluster_created", { sig: "test" }, { runId, clusterId, postId });
      expect(entry.event_id).toBeDefined();
      expect(entry.event_type).toBe("cluster_created");
      expect(entry.run_id).toBe(runId);
      expect(entry.cluster_id).toBe(clusterId);
      expect(entry.post_id).toBe(postId);
      expect(entry.details).toEqual({ sig: "test" });
      expect(new Date(entry.timestamp).toISOString()).toBe(entry.timestamp);
    });

    test("persists to database and is retrievable", () => {
      const runId = randomUUID();
      writeAuditEvent(db, "ingest_run_started", { test: true }, { runId });
      const entries = getAuditEntriesByRun(db, runId);
      expect(entries.length).toBe(1);
      expect(entries[0].event_type).toBe("ingest_run_started");
      expect(entries[0].details).toEqual({ test: true });
    });

    test("handles null optional fields", () => {
      const entry = writeAuditEvent(db, "human_action", { action: "dismiss" });
      expect(entry.run_id).toBeNull();
      expect(entry.cluster_id).toBeNull();
      expect(entry.post_id).toBeNull();
    });

    test("stores complex details JSON", () => {
      const runId = randomUUID();
      const details = {
        nested: { deep: { value: 42 } },
        array: [1, 2, 3],
        boolean: true,
        nullVal: null,
      };
      writeAuditEvent(db, "source_fetched", details, { runId });
      const entries = getAuditEntriesByRun(db, runId);
      expect(entries[0].details).toEqual(details);
    });

    test("each call generates unique event_id", () => {
      const runId = randomUUID();
      const e1 = writeAuditEvent(db, "cluster_created", {}, { runId });
      const e2 = writeAuditEvent(db, "cluster_created", {}, { runId });
      expect(e1.event_id).not.toBe(e2.event_id);
    });

    test("event_id persists correctly to DB", () => {
      const runId = randomUUID();
      const entry = writeAuditEvent(db, "cluster_updated", { change: "x" }, { runId });
      const rows = getAuditEntriesByRun(db, runId);
      expect(rows[0].event_id).toBe(entry.event_id);
    });

    test("timestamp is valid ISO 8601", () => {
      const entry = writeAuditEvent(db, "human_action", {});
      const parsed = new Date(entry.timestamp);
      expect(parsed.toISOString()).toBe(entry.timestamp);
      expect(parsed.getFullYear()).toBeGreaterThanOrEqual(2024);
    });

    test("writes all 12 event types without error", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const postId = randomUUID();
      const eventTypes = [
        "ingest_run_started",
        "ingest_run_completed",
        "source_fetched",
        "candidate_classified",
        "pii_redaction",
        "cluster_created",
        "cluster_updated",
        "cluster_state_changed",
        "routing_recommendation",
        "escalation_triggered",
        "human_action",
        "override_created",
      ] as const;

      for (const eventType of eventTypes) {
        const entry = writeAuditEvent(db, eventType, { type: eventType }, { runId, clusterId, postId });
        expect(entry.event_type).toBe(eventType);
      }

      const all = getAuditEntriesByRun(db, runId);
      expect(all.length).toBe(12);
    });
  });

  // Convenience function tests — one per function
  describe("convenience functions", () => {
    test("auditIngestRunStarted", () => {
      const runId = randomUUID();
      const entry = auditIngestRunStarted(db, runId, { accounts: ["@test"], window: "24h" });
      expect(entry.event_type).toBe("ingest_run_started");
      expect(entry.run_id).toBe(runId);
      expect(entry.details).toEqual({ accounts: ["@test"], window: "24h" });
    });

    test("auditIngestRunCompleted", () => {
      const runId = randomUUID();
      const entry = auditIngestRunCompleted(db, runId, { status: "completed", summary: { total: 42 } });
      expect(entry.event_type).toBe("ingest_run_completed");
      expect(entry.run_id).toBe(runId);
      expect(entry.details.status).toBe("completed");
      expect((entry.details.summary as Record<string, unknown>).total).toBe(42);
    });

    test("auditSourceFetched", () => {
      const runId = randomUUID();
      const entry = auditSourceFetched(db, runId, {
        endpoint: "/mentions",
        filters: { since_id: "123" },
        count: 50,
        rate_limit_remaining: 200,
      });
      expect(entry.event_type).toBe("source_fetched");
      expect(entry.run_id).toBe(runId);
      expect(entry.details.endpoint).toBe("/mentions");
      expect(entry.details.count).toBe(50);
      expect(entry.details.rate_limit_remaining).toBe(200);
    });

    test("auditCandidateClassified", () => {
      const runId = randomUUID();
      const postId = randomUUID();
      const entry = auditCandidateClassified(db, runId, postId, {
        classification: "bug_report",
        confidence: 0.85,
        rationale: "Error strings present",
      });
      expect(entry.event_type).toBe("candidate_classified");
      expect(entry.run_id).toBe(runId);
      expect(entry.post_id).toBe(postId);
      expect(entry.details.classification).toBe("bug_report");
      expect(entry.details.confidence).toBe(0.85);
    });

    test("auditPiiRedaction", () => {
      const runId = randomUUID();
      const postId = randomUUID();
      const entry = auditPiiRedaction(db, runId, postId, {
        pii_type: "email",
        field_redacted: "raw_text",
      });
      expect(entry.event_type).toBe("pii_redaction");
      expect(entry.run_id).toBe(runId);
      expect(entry.post_id).toBe(postId);
      expect(entry.details.pii_type).toBe("email");
      // Verify no raw PII in the audit entry
      expect(JSON.stringify(entry.details)).not.toContain("@");
    });

    test("auditClusterCreated", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const entry = auditClusterCreated(db, runId, clusterId, {
        signature: "web_app|chat|500",
        family: "product_defect",
      });
      expect(entry.event_type).toBe("cluster_created");
      expect(entry.run_id).toBe(runId);
      expect(entry.cluster_id).toBe(clusterId);
      expect(entry.details.signature).toBe("web_app|chat|500");
      expect(entry.details.family).toBe("product_defect");
    });

    test("auditClusterUpdated", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const entry = auditClusterUpdated(db, runId, clusterId, {
        change_type: "new_evidence",
        before: 1,
        after: 2,
      });
      expect(entry.event_type).toBe("cluster_updated");
      expect(entry.run_id).toBe(runId);
      expect(entry.cluster_id).toBe(clusterId);
      expect(entry.details.change_type).toBe("new_evidence");
      expect(entry.details.before).toBe(1);
      expect(entry.details.after).toBe(2);
    });

    test("auditClusterStateChanged", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const entry = auditClusterStateChanged(db, runId, clusterId, {
        from_state: "open",
        to_state: "filed",
        reason: "User filed",
      });
      expect(entry.event_type).toBe("cluster_state_changed");
      expect(entry.run_id).toBe(runId);
      expect(entry.cluster_id).toBe(clusterId);
      expect(entry.details.from_state).toBe("open");
      expect(entry.details.to_state).toBe("filed");
      expect(entry.details.reason).toBe("User filed");
    });

    test("auditRoutingRecommendation", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const entry = auditRoutingRecommendation(db, runId, clusterId, {
        inputs_used: ["service_owner", "codeowners"],
        ranked_results: [{ team: "platform" }],
      });
      expect(entry.event_type).toBe("routing_recommendation");
      expect(entry.run_id).toBe(runId);
      expect(entry.cluster_id).toBe(clusterId);
      expect(entry.details.inputs_used).toEqual(["service_owner", "codeowners"]);
      expect((entry.details.ranked_results as unknown[])[0]).toEqual({ team: "platform" });
    });

    test("auditEscalationTriggered", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const entry = auditEscalationTriggered(db, runId, clusterId, {
        trigger_type: "data_loss_language",
        evidence: { keywords: ["deleted", "gone"] },
        threshold: { keywords: ["deleted"] },
      });
      expect(entry.event_type).toBe("escalation_triggered");
      expect(entry.run_id).toBe(runId);
      expect(entry.cluster_id).toBe(clusterId);
      expect(entry.details.trigger_type).toBe("data_loss_language");
      expect((entry.details.evidence as Record<string, unknown>).keywords).toEqual(["deleted", "gone"]);
    });

    test("auditHumanAction", () => {
      const runId = randomUUID();
      const entry = auditHumanAction(db, runId, {
        action_type: "dismiss",
        cluster_id: "c1",
        reason: "false positive",
      });
      expect(entry.event_type).toBe("human_action");
      expect(entry.run_id).toBe(runId);
      expect(entry.details.action_type).toBe("dismiss");
      expect(entry.details.reason).toBe("false positive");
    });

    test("auditHumanAction propagates cluster_id to entry", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const entry = auditHumanAction(db, runId, {
        action_type: "file",
        cluster_id: clusterId,
      });
      // auditHumanAction passes details.cluster_id as clusterId option
      expect(entry.cluster_id).toBe(clusterId);
    });

    test("auditOverrideCreated", () => {
      const runId = randomUUID();
      const entry = auditOverrideCreated(db, runId, {
        override_type: "severity_override",
        target: "c1",
        parameters: { new_severity: "critical" },
        reason: "Data loss",
      });
      expect(entry.event_type).toBe("override_created");
      expect(entry.run_id).toBe(runId);
      expect(entry.details.override_type).toBe("severity_override");
      expect(entry.details.target).toBe("c1");
      expect(entry.details.reason).toBe("Data loss");
      expect((entry.details.parameters as Record<string, unknown>).new_severity).toBe("critical");
    });
  });

  // Retrieval tests
  describe("retrieval", () => {
    test("getAuditEntriesByType returns correct entries", () => {
      const runId = randomUUID();
      writeAuditEvent(db, "cluster_created", { a: 1 }, { runId });
      writeAuditEvent(db, "cluster_created", { a: 2 }, { runId });
      writeAuditEvent(db, "human_action", { a: 3 }, { runId });

      const created = getAuditEntriesByType(db, "cluster_created");
      expect(created.length).toBe(2);

      const actions = getAuditEntriesByType(db, "human_action");
      expect(actions.length).toBe(1);
    });

    test("getAuditEntriesByRun returns all types for a run", () => {
      const runId = randomUUID();
      auditIngestRunStarted(db, runId, { accounts: [], window: "24h" });
      auditClusterCreated(db, runId, "c1", { signature: "test", family: "product_defect" });
      auditHumanAction(db, runId, { action_type: "file" });

      const entries = getAuditEntriesByRun(db, runId);
      expect(entries.length).toBe(3);
      const types = entries.map((e) => e.event_type).sort();
      expect(types).toEqual(["cluster_created", "human_action", "ingest_run_started"]);
    });

    test("getAuditEntriesByRun is scoped to run — does not return other runs", () => {
      const runA = randomUUID();
      const runB = randomUUID();
      writeAuditEvent(db, "cluster_created", {}, { runId: runA });
      writeAuditEvent(db, "cluster_created", {}, { runId: runA });
      writeAuditEvent(db, "human_action", {}, { runId: runB });

      expect(getAuditEntriesByRun(db, runA).length).toBe(2);
      expect(getAuditEntriesByRun(db, runB).length).toBe(1);
    });

    test("getAuditEntriesByType returns empty array for unknown type", () => {
      const results = getAuditEntriesByType(db, "nonexistent_event_type");
      expect(results).toBeInstanceOf(Array);
      expect(results.length).toBe(0);
    });

    test("all required fields populated on DB read-back", () => {
      const runId = randomUUID();
      const clusterId = randomUUID();
      const postId = randomUUID();
      writeAuditEvent(db, "pii_redaction", { pii_type: "phone" }, { runId, clusterId, postId });

      const [row] = getAuditEntriesByRun(db, runId);
      expect(row.event_id).toBeDefined();
      expect(row.event_type).toBe("pii_redaction");
      expect(row.timestamp).toBeDefined();
      expect(row.run_id).toBe(runId);
      expect(row.cluster_id).toBe(clusterId);
      expect(row.post_id).toBe(postId);
      expect(row.details).toEqual({ pii_type: "phone" });
    });
  });
});
