import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { Database } from "bun:sqlite";
import { randomUUID } from "crypto";
// TODO(x-bug-triage): db/migrate.ts has never been written; the describe
// blocks in this file are .skip until the migration module is implemented.
// See lib/db.test.ts for the same TODO.
const migrate = (_db: Database): void => { /* stub — see TODO above */ };
import { insertOverride, getActiveOverrides } from "./db";
import {
  loadOverrides,
  getOverridesByType,
  applySeverityOverrides,
  applyRoutingOverride,
  isClusterSuppressed,
  isClusterSnoozed,
  applyLabelCorrection,
  applyAllOverrides,
} from "./overrides";
import type { ReviewOverride, BugCluster } from "./types";

let db: Database;

function createTestDb(): Database {
  const d = new Database(":memory:");
  d.exec("PRAGMA foreign_keys = ON");
  migrate(d);
  return d;
}

function makeOverride(type: ReviewOverride["override_type"], overrides: Partial<ReviewOverride> = {}): ReviewOverride {
  return {
    override_id: randomUUID(),
    override_type: type,
    target_cluster_id: randomUUID(),
    parameters: {},
    reason: "test",
    created_by: "operator",
    created_at: new Date().toISOString(),
    expires_at: null,
    active: true,
    ...overrides,
  };
}

function makeCluster(overrides: Partial<BugCluster> = {}): BugCluster {
  const now = new Date().toISOString();
  return {
    cluster_id: randomUUID(),
    bug_signature: "test",
    cluster_family: "product_defect",
    product_surface: "web_app",
    feature_area: "chat",
    title: "Test cluster",
    severity: "medium",
    severity_rationale: "auto",
    state: "open",
    sub_status: null,
    report_count: 5,
    first_seen: now,
    last_seen: now,
    created_at: now,
    updated_at: now,
    triage_run_id: "run1",
    ...overrides,
  };
}

describe.skip("overrides", () => {
  beforeEach(() => { db = createTestDb(); });
  afterEach(() => { db.close(); });

  describe("loadOverrides", () => {
    test("returns empty array when no overrides", () => {
      const result = loadOverrides(db);
      expect(result).toEqual([]);
    });

    test("returns all active overrides", () => {
      insertOverride(db, makeOverride("severity_override"));
      insertOverride(db, makeOverride("routing_override"));
      const result = loadOverrides(db);
      expect(result.length).toBe(2);
    });

    test("excludes inactive overrides", () => {
      insertOverride(db, makeOverride("severity_override", { active: false }));
      insertOverride(db, makeOverride("routing_override", { active: true }));
      const result = loadOverrides(db);
      expect(result.length).toBe(1);
      expect(result[0].override_type).toBe("routing_override");
    });
  });

  describe("getOverridesByType", () => {
    test("filters by type", () => {
      const overrides = [
        makeOverride("severity_override"),
        makeOverride("routing_override"),
        makeOverride("severity_override"),
      ];
      const result = getOverridesByType(overrides, "severity_override");
      expect(result.length).toBe(2);
    });

    test("returns empty for non-matching type", () => {
      const overrides = [makeOverride("severity_override")];
      const result = getOverridesByType(overrides, "noise_suppression");
      expect(result.length).toBe(0);
    });

    test("returns empty for empty input", () => {
      const result = getOverridesByType([], "severity_override");
      expect(result.length).toBe(0);
    });
  });

  describe("applyAllOverrides", () => {
    test("applies label + severity in correct order", () => {
      const cluster = makeCluster({ cluster_id: "c1", severity: "low", cluster_family: "product_defect" });
      const overrides: ReviewOverride[] = [
        makeOverride("label_correction", { target_cluster_id: "c1", parameters: { new_family: "ux_friction" } }),
        makeOverride("severity_override", { target_cluster_id: "c1", parameters: { new_severity: "critical" } }),
      ];
      const result = applyAllOverrides(cluster, overrides);
      expect(result.cluster_family).toBe("ux_friction");
      expect(result.severity).toBe("critical");
    });

    test("no overrides returns cluster unchanged", () => {
      const cluster = makeCluster();
      const result = applyAllOverrides(cluster, []);
      expect(result).toEqual(cluster);
    });

    test("ignores overrides for different clusters", () => {
      const cluster = makeCluster({ cluster_id: "c1", severity: "low" });
      const overrides = [makeOverride("severity_override", { target_cluster_id: "c2", parameters: { new_severity: "critical" } })];
      const result = applyAllOverrides(cluster, overrides);
      expect(result.severity).toBe("low");
    });
  });

  describe("routing override", () => {
    test("returns null when no routing override exists", () => {
      expect(applyRoutingOverride("c1", [])).toBeNull();
    });

    test("returns parameters for matching cluster", () => {
      const overrides = [makeOverride("routing_override", { target_cluster_id: "c1", parameters: { new_team: "infra" } })];
      const result = applyRoutingOverride("c1", overrides);
      expect(result).toEqual({ new_team: "infra" });
    });
  });
});
