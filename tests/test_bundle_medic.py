"""Unit tests for the databricks-bundle-medic deterministic core (bead claude-jhnj):
the two hooks (PreToolUse state guard + PostToolUse D6 retry) and the three scripts.

The two hooks carry the load-bearing precision contracts:
  * the PostToolUse D6 hook must fire ONLY on the exact grant-ordering signature on a
    bundle deploy — never on another error class (that would mask a real failure);
  * the PreToolUse state guard must be advisory + fail-open (never block a deploy).

Run: python3 -m unittest tests.test_bundle_medic -v
"""

import importlib.util
import unittest
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[1]
    / "plugins" / "saas-packs" / "databricks-pack" / "skills"
    / "databricks-bundle-medic"
)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load("bundle_deploy_guard", SKILL / "hooks" / "bundle-deploy-guard.py")
retry = _load("bundle_grant_retry", SKILL / "hooks" / "bundle-grant-retry.py")
imp = _load("import_uc_resource", SKILL / "scripts" / "import-uc-resource-to-bundle.py")
drain = _load("drain_workspace", SKILL / "scripts" / "drain-workspace.py")
vpc = _load("audit_vpc_endpoints", SKILL / "scripts" / "audit-vpc-endpoints.py")


class DeployGuardTests(unittest.TestCase):
    def test_detects_bundle_deploy(self):
        self.assertTrue(guard.is_bundle_deploy("databricks bundle deploy -t prod"))
        self.assertTrue(guard.is_bundle_deploy("DATABRICKS_BUNDLE_ENGINE=direct databricks bundle deploy"))

    def test_ignores_non_deploy(self):
        self.assertFalse(guard.is_bundle_deploy("databricks bundle validate"))
        self.assertFalse(guard.is_bundle_deploy("databricks bundle summary"))
        self.assertFalse(guard.is_bundle_deploy("ls -la"))

    def test_classify_good_state(self):
        r = guard.classify_tfstate('{"resources":[{"a":1},{"b":2},{"c":3}]}')
        self.assertTrue(r["ok"])
        self.assertEqual(r["resources"], 3)

    def test_classify_truncated_state_is_the_d5_signature(self):
        r = guard.classify_tfstate('{"resources":[{"a":1}')  # EOF mid-write
        self.assertFalse(r["ok"])
        self.assertIn("JSON", r["error"])

    def test_classify_empty(self):
        self.assertFalse(guard.classify_tfstate("")["ok"])
        self.assertFalse(guard.classify_tfstate("   ")["ok"])

    def test_advisory_corrupt_names_4986(self):
        bad = guard.classify_tfstate("{oops")
        self.assertIn("4986", guard.deploy_advisory(bad, None))

    def test_advisory_shrink_warns(self):
        good_small = {"ok": True, "size": 100, "resources": 1, "error": None}
        self.assertIn("shrank", guard.deploy_advisory(good_small, 1000))

    def test_advisory_healthy_is_silent(self):
        good = {"ok": True, "size": 1000, "resources": 5, "error": None}
        self.assertIsNone(guard.deploy_advisory(good, 1000))
        self.assertIsNone(guard.deploy_advisory(good, None))

    def test_guard_fails_open_on_non_deploy(self):
        # not a deploy → no advisory regardless of cwd
        self.assertIsNone(guard.guard("git status", "/nonexistent"))


class GrantRetryTests(unittest.TestCase):
    D6 = "Error: terraform apply: User does not have CREATE TABLE on Schema 'main.analytics'"

    def test_fires_on_exact_d6_on_deploy(self):
        self.assertTrue(retry.is_d6_grant_ordering("databricks bundle deploy -t dev", self.D6))

    def test_fires_on_create_variants(self):
        self.assertTrue(retry.is_d6_grant_ordering(
            "databricks bundle deploy", "User does not have CREATE on Schema 'c.s'"))
        self.assertTrue(retry.is_d6_grant_ordering(
            "databricks bundle deploy", "does not have MODIFY on Schema `c`.`s`"))

    def test_does_not_fire_on_other_permission_errors(self):
        # A SELECT-on-table denial is NOT the schema-grant-ordering transient.
        self.assertFalse(retry.is_d6_grant_ordering(
            "databricks bundle deploy", "User does not have SELECT on Table 'main.t'"))
        self.assertFalse(retry.is_d6_grant_ordering(
            "databricks bundle deploy", "does not have USE CATALOG on Catalog 'main'"))

    def test_does_not_fire_on_non_deploy_command(self):
        # Same error text, but not a bundle deploy → must not fire (no masking).
        self.assertFalse(retry.is_d6_grant_ordering("databricks catalogs list", self.D6))

    def test_does_not_fire_on_clean_output(self):
        self.assertFalse(retry.is_d6_grant_ordering("databricks bundle deploy", "Deployment complete!"))

    def test_extract_output_handles_shapes(self):
        self.assertIn("CREATE TABLE", retry.extract_output({"stderr": self.D6}))
        self.assertEqual(retry.extract_output("plain"), "plain")
        self.assertEqual(retry.extract_output(None), "")

    def test_decide_returns_additionalcontext_only(self):
        ev = {"tool_input": {"command": "databricks bundle deploy"}, "tool_response": {"stderr": self.D6}}
        out = retry.decide(ev)
        self.assertIsNotNone(out)
        hso = out["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PostToolUse")
        self.assertIn("additionalContext", hso)
        # never a block/deny — surfaces, does not mask
        self.assertNotIn("decision", out)
        self.assertIn("once", hso["additionalContext"].lower())

    def test_decide_silent_on_other_errors(self):
        ev = {"tool_input": {"command": "databricks bundle deploy"},
              "tool_response": {"stderr": "network timeout"}}
        self.assertIsNone(retry.decide(ev))


class ImportPlanTests(unittest.TestCase):
    def test_catalog_import_plan(self):
        p = imp.build_import_plan("catalog", "analytics", "analytics_cat")
        self.assertEqual(p["tf_type"], "databricks_catalog")
        self.assertIn("databricks_catalog.analytics_cat", p["import_block"])
        self.assertIn('id = "analytics"', p["import_block"])
        self.assertIn("catalogs:", p["yaml_block"])
        self.assertIn("4842", p["self_deprecation"])

    def test_external_location_import_plan(self):
        p = imp.build_import_plan("external_location", "raw_zone", "raw_zone_loc")
        self.assertEqual(p["tf_type"], "databricks_external_location")
        self.assertIn("external_locations:", p["yaml_block"])

    def test_unsupported_type_raises(self):
        with self.assertRaises(ValueError):
            imp.build_import_plan("volume", "v", "k")

    def test_warns_against_state_hand_edit(self):
        p = imp.build_import_plan("catalog", "c", "k")
        self.assertTrue(any("hand" in w.lower() for w in p["warnings"]))


class DrainTests(unittest.TestCase):
    INV = {
        "clusters": [
            {"cluster_id": "c1", "cluster_name": "etl", "state": "RUNNING"},
            {"cluster_id": "c2", "cluster_name": "old", "state": "TERMINATED"},
        ],
        "warehouses": [{"id": "w1", "name": "bi", "state": "RUNNING"}],
        "instance_pools": [
            {"instance_pool_id": "p1", "instance_pool_name": "hot", "idle": 3},
            {"instance_pool_id": "p2", "instance_pool_name": "cold", "idle": 0},
        ],
    }

    def test_plan_drain_skips_already_stopped(self):
        actions = drain.plan_drain(self.INV)
        by_id = {a["id"]: a for a in actions}
        self.assertEqual(by_id["c1"]["action"], "terminate")
        self.assertEqual(by_id["c2"]["action"], "skip")       # already TERMINATED
        self.assertEqual(by_id["w1"]["action"], "stop")
        self.assertEqual(by_id["p1"]["action"], "drain-pool")  # idle>0
        self.assertEqual(by_id["p2"]["action"], "skip")        # idle==0

    def test_drain_manifest_excludes_skips(self):
        manifest = drain.drain_manifest(drain.plan_drain(self.INV))
        self.assertEqual({a["id"] for a in manifest}, {"c1", "w1", "p1"})

    def test_idempotent_when_all_stopped(self):
        inv = {"clusters": [{"cluster_id": "c", "cluster_name": "x", "state": "TERMINATED"}]}
        self.assertEqual(drain.drain_manifest(drain.plan_drain(inv)), [])

    def test_resume_only_restarts_drained(self):
        manifest = drain.drain_manifest(drain.plan_drain(self.INV))
        resume = drain.plan_resume(manifest)
        kinds = {a["kind"]: a["action"] for a in resume}
        self.assertEqual(kinds["cluster"], "start")
        self.assertEqual(kinds["warehouse"], "start")
        self.assertIn("manual", kinds["instance_pool"])  # pool min-idle is a capacity decision

    def test_pool_with_no_idle_key_is_active(self):
        inv = {"instance_pools": [{"instance_pool_id": "p", "instance_pool_name": "n"}]}
        self.assertEqual(drain.plan_drain(inv)[0]["action"], "drain-pool")


class VpcAuditTests(unittest.TestCase):
    def test_all_present_no_leak(self):
        r = vpc.audit_endpoints(["s3", "sts", "kinesis"])
        self.assertTrue(r["ok"])
        self.assertEqual(r["missing"], [])

    def test_only_s3_leaks_sts_and_kinesis(self):
        r = vpc.audit_endpoints(["s3"])
        self.assertFalse(r["ok"])
        self.assertEqual(set(r["missing"]), {"sts", "kinesis"})

    def test_none_present_all_leak(self):
        r = vpc.audit_endpoints([])
        self.assertEqual(set(r["missing"]), {"s3", "sts", "kinesis"})

    def test_case_insensitive(self):
        r = vpc.audit_endpoints(["S3", " STS "])
        self.assertEqual(r["missing"], ["kinesis"])

    def test_remediation_terraform_targets_missing(self):
        tf = vpc.remediation_terraform(["s3", "sts"], "vpc-1", "us-east-1")
        self.assertIn("aws_vpc_endpoint", tf)
        self.assertIn("com.amazonaws.us-east-1.s3", tf)
        self.assertIn("Gateway", tf)          # s3
        self.assertIn("Interface", tf)        # sts
        self.assertNotIn("kinesis", tf)       # kinesis was present

    def test_s3_is_gateway_sts_kinesis_interface(self):
        self.assertEqual(vpc.REQUIRED["s3"]["endpoint_type"], "Gateway")
        self.assertEqual(vpc.REQUIRED["sts"]["endpoint_type"], "Interface")
        self.assertEqual(vpc.REQUIRED["kinesis"]["endpoint_type"], "Interface")


if __name__ == "__main__":
    unittest.main(verbosity=2)
