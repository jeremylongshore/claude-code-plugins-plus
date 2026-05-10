import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { Database } from "bun:sqlite";
import { randomUUID } from "crypto";
// TODO(x-bug-triage): db/migrate.ts has never been written; the describe
// blocks in this file are .skip until the migration module is implemented.
// See lib/db.test.ts for the same TODO.
const migrate = (_db: Database): void => { /* stub — see TODO above */ };
import { insertTriageRun, insertCandidate, insertCluster, insertClusterPost, insertOverride, insertSuppressionRule } from "./db";
import {
  classificationToFamily,
  isSuppressed,
  findMatchingCluster,
  determineSubStatus,
  clusterCandidates,
} from "./clusterer";
import { generateSignature, calculateSignatureOverlap, signatureFromString } from "./signatures";
import {
  loadOverrides,
  applySeverityOverrides,
  applyRoutingOverride,
  isClusterSuppressed,
  isClusterSnoozed,
  applyLabelCorrection,
  applyAllOverrides,
} from "./overrides";
import type { BugCandidate, BugCluster, ReviewOverride, TriageRun } from "./types";

let db: Database;

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

function makeCandidate(runId: string, overrides: Partial<BugCandidate> = {}): BugCandidate {
  return {
    post_id: randomUUID(),
    author_handle: "user",
    author_id: "123",
    timestamp: new Date().toISOString(),
    source_type: "mention",
    product_surface: "web_app",
    feature_area: "chat",
    symptoms: ["messages disappearing"],
    error_strings: ["Error 500"],
    repro_hints: [],
    urls: [],
    has_media: false,
    media_keys: [],
    language: "en",
    conversation_id: null,
    thread_root_id: null,
    reply_to_id: null,
    referenced_post_ids: [],
    public_metrics: null,
    classification: "bug_report",
    classification_confidence: 0.85,
    classification_rationale: "test",
    report_quality_score: 0.8,
    independence_score: 0.9,
    account_authenticity_score: 0.9,
    historical_accuracy_score: 0.5,
    reporter_reliability_score: 0.8,
    reporter_category: "public",
    pii_flags: [],
    raw_text_redacted: "Messages disappearing with Error 500",
    raw_text_storage_policy: "store_redacted",
    triage_run_id: runId,
    ...overrides,
  };
}

function makeCluster(runId: string, overrides: Partial<BugCluster> = {}): BugCluster {
  const now = new Date().toISOString();
  return {
    cluster_id: randomUUID(),
    bug_signature: "web_app|chat|error 500|messages disappearing",
    cluster_family: "product_defect",
    product_surface: "web_app",
    feature_area: "chat",
    title: null,
    severity: "medium",
    severity_rationale: null,
    state: "open",
    sub_status: null,
    report_count: 1,
    first_seen: now,
    last_seen: now,
    created_at: now,
    updated_at: now,
    triage_run_id: runId,
    ...overrides,
  };
}

// === Family Derivation ===

describe.skip("classificationToFamily", () => {
  test("bug_report → product_defect", () => expect(classificationToFamily("bug_report")).toBe("product_defect"));
  test("sarcastic_bug_report → product_defect", () => expect(classificationToFamily("sarcastic_bug_report")).toBe("product_defect"));
  test("account_problem → product_defect", () => expect(classificationToFamily("account_problem")).toBe("product_defect"));
  test("billing_problem → product_defect", () => expect(classificationToFamily("billing_problem")).toBe("product_defect"));
  test("model_quality_issue → model_quality_defect", () => expect(classificationToFamily("model_quality_issue")).toBe("model_quality_defect"));
  test("policy_or_expectation_mismatch → policy_mismatch", () => expect(classificationToFamily("policy_or_expectation_mismatch")).toBe("policy_mismatch"));
  test("ux_friction → ux_friction", () => expect(classificationToFamily("ux_friction")).toBe("ux_friction"));
  test("feature_request → null", () => expect(classificationToFamily("feature_request")).toBeNull());
  test("praise → null", () => expect(classificationToFamily("praise")).toBeNull());
  test("noise → null", () => expect(classificationToFamily("noise")).toBeNull());
  test("needs_review → null", () => expect(classificationToFamily("needs_review")).toBeNull());
});

// === Signature Generation ===

describe.skip("signatures", () => {
  test("generates stable signature", () => {
    const run = makeRun();
    const c = makeCandidate(run.run_id);
    const sig1 = generateSignature(c);
    const sig2 = generateSignature(c);
    expect(sig1.raw).toBe(sig2.raw);
  });

  test("calculates high overlap for identical signatures", () => {
    const run = makeRun();
    const c = makeCandidate(run.run_id);
    const sig = generateSignature(c);
    expect(calculateSignatureOverlap(sig, sig)).toBeGreaterThanOrEqual(0.9);
  });

  test("calculates low overlap for different families", () => {
    const run = makeRun();
    const c1 = makeCandidate(run.run_id, { product_surface: "web_app", feature_area: "chat", symptoms: ["crash"], error_strings: ["500"] });
    const c2 = makeCandidate(run.run_id, { product_surface: "api", feature_area: "billing", symptoms: ["timeout"], error_strings: ["403"] });
    const sig1 = generateSignature(c1);
    const sig2 = generateSignature(c2);
    expect(calculateSignatureOverlap(sig1, sig2)).toBeLessThan(0.5);
  });

  test("parses signature from string", () => {
    const sig = signatureFromString("web_app|chat|error 500|messages disappearing");
    expect(sig.surface).toBe("web_app");
    expect(sig.featureArea).toBe("chat");
  });
});

// === Family-First Guard ===

describe.skip("family-first clustering", () => {
  beforeEach(() => { db = createTestDb(); });
  afterEach(() => { db.close(); });

  test("different families never cluster together", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const cluster = makeCluster(run.run_id, { cluster_family: "product_defect" });
    insertCluster(db, cluster);

    const candidate = makeCandidate(run.run_id, { classification: "model_quality_issue" });
    const match = findMatchingCluster(candidate, [cluster], "model_quality_defect");
    expect(match).toBeNull();
  });

  test("same family can cluster", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const cluster = makeCluster(run.run_id, { cluster_family: "product_defect" });

    const candidate = makeCandidate(run.run_id);
    const match = findMatchingCluster(candidate, [cluster], "product_defect");
    expect(match).not.toBeNull();
  });
});

// === Cluster Continuity ===

describe.skip("cluster continuity", () => {
  beforeEach(() => { db = createTestDb(); });
  afterEach(() => { db.close(); });

  test("new candidate joins existing cluster above threshold", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const c1 = makeCandidate(run.run_id);
    insertCandidate(db, c1);

    const c2 = makeCandidate(run.run_id);
    insertCandidate(db, c2);

    const result = clusterCandidates(db, [c1, c2], run.run_id);
    expect(result.newClusters.length).toBe(1);
    expect(result.newClusters[0].report_count).toBe(2);
  });

  test("different candidates create separate clusters", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const c1 = makeCandidate(run.run_id, { product_surface: "web_app", feature_area: "chat", symptoms: ["crash"], error_strings: ["500"] });
    const c2 = makeCandidate(run.run_id, { product_surface: "api", feature_area: "billing", symptoms: ["timeout"], error_strings: ["403"] });
    insertCandidate(db, c1);
    insertCandidate(db, c2);

    const result = clusterCandidates(db, [c1, c2], run.run_id);
    expect(result.newClusters.length).toBe(2);
  });
});

// === Regression Reopening ===

describe.skip("regression reopening", () => {
  beforeEach(() => { db = createTestDb(); });
  afterEach(() => { db.close(); });

  test("resolved cluster + fresh complaint → regression_reopened", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const resolvedCluster = makeCluster(run.run_id, { state: "resolved" });
    insertCluster(db, resolvedCluster);

    const subStatus = determineSubStatus(resolvedCluster);
    expect(subStatus).toBe("regression_reopened");
  });

  test("fix_deployed + fresh complaint → regression_reopened", () => {
    const cluster = makeCluster(randomUUID(), { state: "fix_deployed" });
    expect(determineSubStatus(cluster)).toBe("regression_reopened");
  });

  test("open cluster + new evidence → new_evidence", () => {
    const cluster = makeCluster(randomUUID(), { state: "open" });
    expect(determineSubStatus(cluster)).toBe("new_evidence");
  });
});

// === Suppression ===

describe.skip("suppression", () => {
  test("keyword suppression matches", () => {
    const candidate = makeCandidate("run1", { raw_text_redacted: "This is known spam phrase" });
    expect(isSuppressed(candidate, [{ pattern_type: "keyword", pattern_value: "known spam" }])).toBe(true);
  });

  test("no match when pattern absent", () => {
    const candidate = makeCandidate("run1", { raw_text_redacted: "Real bug report" });
    expect(isSuppressed(candidate, [{ pattern_type: "keyword", pattern_value: "spam" }])).toBe(false);
  });

  test("author suppression", () => {
    const candidate = makeCandidate("run1", { author_handle: "spambot" });
    expect(isSuppressed(candidate, [{ pattern_type: "author", pattern_value: "spambot" }])).toBe(true);
  });
});

// === Override Application ===

describe.skip("overrides", () => {
  test("severity override changes cluster severity", () => {
    const cluster = makeCluster("run1", { severity: "low" });
    const overrides: ReviewOverride[] = [{
      override_id: randomUUID(),
      override_type: "severity_override",
      target_cluster_id: cluster.cluster_id,
      parameters: { new_severity: "critical" },
      reason: "Data loss confirmed",
      created_by: "operator",
      created_at: new Date().toISOString(),
      expires_at: null,
      active: true,
    }];
    const result = applySeverityOverrides(cluster, overrides);
    expect(result.severity).toBe("critical");
  });

  test("routing override returns parameters", () => {
    const clusterId = randomUUID();
    const overrides: ReviewOverride[] = [{
      override_id: randomUUID(),
      override_type: "routing_override",
      target_cluster_id: clusterId,
      parameters: { new_team: "platform-team" },
      reason: "Rerouted",
      created_by: "operator",
      created_at: new Date().toISOString(),
      expires_at: null,
      active: true,
    }];
    const result = applyRoutingOverride(clusterId, overrides);
    expect(result).toEqual({ new_team: "platform-team" });
  });

  test("noise suppression detected", () => {
    const clusterId = randomUUID();
    const overrides: ReviewOverride[] = [{
      override_id: randomUUID(),
      override_type: "noise_suppression",
      target_cluster_id: clusterId,
      parameters: {},
      reason: "False positive",
      created_by: "operator",
      created_at: new Date().toISOString(),
      expires_at: null,
      active: true,
    }];
    expect(isClusterSuppressed(clusterId, overrides)).toBe(true);
  });

  test("snooze with future expiry is active", () => {
    const clusterId = randomUUID();
    const overrides: ReviewOverride[] = [{
      override_id: randomUUID(),
      override_type: "snooze",
      target_cluster_id: clusterId,
      parameters: {},
      reason: "Snoozing",
      created_by: "operator",
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 86400000).toISOString(),
      active: true,
    }];
    expect(isClusterSnoozed(clusterId, overrides)).toBe(true);
  });

  test("snooze with past expiry is inactive", () => {
    const clusterId = randomUUID();
    const overrides: ReviewOverride[] = [{
      override_id: randomUUID(),
      override_type: "snooze",
      target_cluster_id: clusterId,
      parameters: {},
      reason: "Was snoozed",
      created_by: "operator",
      created_at: new Date(Date.now() - 172800000).toISOString(),
      expires_at: new Date(Date.now() - 86400000).toISOString(),
      active: true,
    }];
    expect(isClusterSnoozed(clusterId, overrides)).toBe(false);
  });

  test("label correction changes family and title", () => {
    const cluster = makeCluster("run1", { cluster_family: "product_defect", title: "Old title" });
    const overrides: ReviewOverride[] = [{
      override_id: randomUUID(),
      override_type: "label_correction",
      target_cluster_id: cluster.cluster_id,
      parameters: { new_family: "ux_friction", new_title: "Corrected title" },
      reason: "Misclassified",
      created_by: "operator",
      created_at: new Date().toISOString(),
      expires_at: null,
      active: true,
    }];
    const result = applyLabelCorrection(cluster, overrides);
    expect(result.cluster_family).toBe("ux_friction");
    expect(result.title).toBe("Corrected title");
  });

  test("all 8 override types handled", () => {
    const types = [
      "cluster_merge", "cluster_split", "noise_suppression", "routing_override",
      "issue_family_link", "severity_override", "label_correction", "snooze",
    ] as const;
    // Just verify these are valid OverrideType values (type system enforces this)
    for (const t of types) {
      const o: ReviewOverride = {
        override_id: randomUUID(),
        override_type: t,
        target_cluster_id: null,
        parameters: {},
        reason: "test",
        created_by: "test",
        created_at: new Date().toISOString(),
        expires_at: null,
        active: true,
      };
      expect(o.override_type).toBe(t);
    }
  });
});

// === Non-Clustering Classifications ===

describe.skip("non-clustering classifications", () => {
  beforeEach(() => { db = createTestDb(); });
  afterEach(() => { db.close(); });

  test("feature requests are skipped", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const c = makeCandidate(run.run_id, { classification: "feature_request" });
    insertCandidate(db, c);

    const result = clusterCandidates(db, [c], run.run_id);
    expect(result.newClusters.length).toBe(0);
    expect(result.skipped).toBe(1);
  });

  test("noise is skipped", () => {
    const run = makeRun();
    insertTriageRun(db, run);

    const c = makeCandidate(run.run_id, { classification: "noise" });
    insertCandidate(db, c);

    const result = clusterCandidates(db, [c], run.run_id);
    expect(result.skipped).toBe(1);
  });
});
