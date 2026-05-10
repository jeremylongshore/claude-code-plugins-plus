import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { Database } from "bun:sqlite";
import { randomUUID } from "crypto";
// TODO(x-bug-triage): db/migrate.ts has never been written; the describe
// blocks in this file are .skip until the migration module is implemented.
// See lib/db.test.ts for the same TODO.
const migrate = (_db: Database): void => { /* stub — see TODO above */ };
import { insertTriageRun, insertCandidate, insertCluster } from "./db";
import { writeAuditEvent } from "./audit";
import { enforceRetention } from "./retention";
import type { RetentionPolicyConfig } from "./config";
import type { BugCandidate, BugCluster, TriageRun } from "./types";

let db: Database;

const testPolicy: RetentionPolicyConfig = {
  candidates_redacted_days: 90,
  candidates_hash_only_days: 365,
  clusters_after_closed_days: 365,
  clusters_while_open: "indefinite",
  overrides: "indefinite",
  suppression_rules: "indefinite",
  issue_links: "indefinite",
  audit_logs_minimum_days: 365,
  raw_unredacted_text: "never_stored",
};

function createTestDb(): Database {
  const d = new Database(":memory:");
  d.exec("PRAGMA foreign_keys = ON");
  migrate(d);
  return d;
}

function makeRun(): TriageRun {
  return {
    run_id: randomUUID(),
    started_at: new Date().toISOString(),
    completed_at: null,
    status: "running",
    accounts_ingested: [],
    endpoints_summary: null,
    candidates_parsed: 0,
    clusters_created: 0,
    clusters_updated: 0,
    warnings: null,
  };
}

describe.skip("retention enforcement", () => {
  beforeEach(() => { db = createTestDb(); });
  afterEach(() => { db.close(); });

  test("deletes expired redacted candidates", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    // Insert old candidate (91 days ago)
    const oldTimestamp = new Date(Date.now() - 91 * 86400000).toISOString();
    const candidate: BugCandidate = {
      post_id: randomUUID(),
      author_handle: "user",
      author_id: "123",
      timestamp: oldTimestamp,
      source_type: "mention",
      product_surface: null,
      feature_area: null,
      symptoms: [],
      error_strings: [],
      repro_hints: [],
      urls: [],
      has_media: false,
      media_keys: [],
      language: null,
      conversation_id: null,
      thread_root_id: null,
      reply_to_id: null,
      referenced_post_ids: [],
      public_metrics: null,
      classification: "bug_report",
      classification_confidence: 0.8,
      classification_rationale: "test",
      report_quality_score: null,
      independence_score: null,
      account_authenticity_score: null,
      historical_accuracy_score: null,
      reporter_reliability_score: null,
      reporter_category: "public",
      pii_flags: [],
      raw_text_redacted: "old test",
      raw_text_storage_policy: "store_redacted",
      triage_run_id: run.run_id,
    };
    insertCandidate(db, candidate);

    const report = enforceRetention(db, testPolicy);
    expect(report.candidatesRedactedDeleted).toBe(1);
  });

  test("keeps recent candidates", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const candidate: BugCandidate = {
      post_id: randomUUID(),
      author_handle: "user",
      author_id: "123",
      timestamp: new Date().toISOString(),
      source_type: "mention",
      product_surface: null,
      feature_area: null,
      symptoms: [],
      error_strings: [],
      repro_hints: [],
      urls: [],
      has_media: false,
      media_keys: [],
      language: null,
      conversation_id: null,
      thread_root_id: null,
      reply_to_id: null,
      referenced_post_ids: [],
      public_metrics: null,
      classification: "bug_report",
      classification_confidence: 0.8,
      classification_rationale: "test",
      report_quality_score: null,
      independence_score: null,
      account_authenticity_score: null,
      historical_accuracy_score: null,
      reporter_reliability_score: null,
      reporter_category: "public",
      pii_flags: [],
      raw_text_redacted: "recent test",
      raw_text_storage_policy: "store_redacted",
      triage_run_id: run.run_id,
    };
    insertCandidate(db, candidate);

    const report = enforceRetention(db, testPolicy);
    expect(report.candidatesRedactedDeleted).toBe(0);
  });

  test("deletes expired audit logs", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    // Insert old audit entry directly
    const oldTimestamp = new Date(Date.now() - 366 * 86400000).toISOString();
    db.query("INSERT INTO audit_log (event_id, event_type, timestamp, run_id, details) VALUES (?, ?, ?, ?, ?)")
      .run(randomUUID(), "ingest_run_started", oldTimestamp, run.run_id, "{}");

    const report = enforceRetention(db, testPolicy);
    expect(report.auditLogsDeleted).toBe(1);
  });
});
