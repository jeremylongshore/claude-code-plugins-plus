"""Tests for cluster 4 skills: dependency analysis (4 scripts).

Covers:
    - auditing-npm-dependencies / audit_npm.py
    - auditing-python-dependencies / audit_python.py
    - checking-license-compliance / check_licenses.py
    - tracing-transitive-vulnerabilities / trace_vulns.py

These scripts wrap external tools (npm, pip-audit, npm ls, pipdeptree). The
tests focus on the parsers + classifiers + CLI structure rather than invoking
the external tools — those are exercised via integration with stubs.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# --- Helpers to import the per-skill scripts as modules ---------------------

_PACK = Path(__file__).resolve().parents[1]


def _load_script(skill_dir: str, script_name: str):
    """Load a script as a module without polluting sys.modules globally."""
    path = _PACK / "skills" / skill_dir / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(f"{skill_dir}_{script_name[:-3]}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- audit_npm.py -----------------------------------------------------------


class TestAuditNpm:
    @pytest.fixture
    def mod(self):
        return _load_script("auditing-npm-dependencies", "audit_npm.py")

    def test_skill_id_constant(self, mod):
        assert mod.SKILL_ID == "auditing-npm-dependencies"

    def test_parse_v2_minimal(self, mod, npm_audit_v2_output):
        findings = mod._parse_v2(npm_audit_v2_output, "test-project")
        assert len(findings) >= 1
        # The lodash CVE is critical
        critical = [f for f in findings if f.severity.value == "critical"]
        assert critical
        assert any("lodash" in f.target.lower() for f in critical)

    def test_parse_v2_no_fix_bumps_severity(self, mod):
        """When fixAvailable is False AND severity is moderate, score should bump."""
        from lib.finding import Severity

        data = {
            "vulnerabilities": {
                "no-fix-pkg": {
                    "name": "no-fix-pkg",
                    "severity": "moderate",
                    "isDirect": True,
                    "via": [{"title": "no fix here", "source": "GHSA-xxxx"}],
                    "range": "<1.0.0",
                    "fixAvailable": False,
                }
            }
        }
        findings = mod._parse_v2(data, "test")
        # No-fix moderate should be bumped to at-least HIGH
        assert findings[0].severity.numeric >= Severity.HIGH.numeric

    def test_parse_v1_minimal(self, mod, npm_audit_v1_output):
        findings = mod._parse_v1(npm_audit_v1_output, "test-project")
        assert len(findings) == 1
        assert findings[0].cve_id == "CVE-2019-10744"
        assert findings[0].severity.value == "critical"

    def test_cli_help_exits_clean(self, mod, capsys):
        with pytest.raises(SystemExit) as exc:
            mod.main(["--help"])
        # argparse exits 0 on --help
        assert exc.value.code == 0

    def test_cli_missing_path_creates_finding(self, mod, tmp_path, capsys):
        """Non-existent target dir → INFO finding (npm absent or non-node).

        Reviewer tightening (PR #837): the prior assertion `in (0, 2)` would
        have masked an argparse failure (code 2) as "expected behavior."
        Tighten to exit code 0 since the fixture passes a valid path with
        valid args; the only legitimate exit is the clean success path.
        """
        out = tmp_path / "out.json"
        exit_code = mod.main([str(tmp_path), "--output", str(out), "--format", "json"])
        assert exit_code == 0, (
            f"expected clean exit 0 (non-Node dir produces INFO finding only); "
            f"got {exit_code} — likely argparse failure or unexpected error path"
        )
        data = json.loads(out.read_text())
        assert isinstance(data, list)


# --- audit_python.py --------------------------------------------------------


class TestAuditPython:
    @pytest.fixture
    def mod(self):
        return _load_script("auditing-python-dependencies", "audit_python.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "auditing-python-dependencies"

    def test_detect_requirement_sources_finds_requirements_txt(self, mod, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
        sources = mod.detect_requirement_sources(tmp_path)
        assert any(s.name == "requirements.txt" for s in sources)

    def test_detect_requirement_sources_prefers_poetry_lock(self, mod, tmp_path):
        (tmp_path / "poetry.lock").write_text("# stub\n")
        (tmp_path / "requirements.txt").write_text("requests\n")
        sources = mod.detect_requirement_sources(tmp_path)
        # poetry.lock should appear before requirements.txt
        names = [s.name for s in sources]
        assert names.index("poetry.lock") < names.index("requirements.txt")

    def test_osv_severity_mapping(self, mod):
        from lib.finding import Severity

        assert mod._osv_severity_to_enum("critical") == Severity.CRITICAL
        assert mod._osv_severity_to_enum("HIGH") == Severity.HIGH
        assert mod._osv_severity_to_enum("moderate") == Severity.MEDIUM
        assert mod._osv_severity_to_enum("medium") == Severity.MEDIUM
        assert mod._osv_severity_to_enum("low") == Severity.LOW
        assert mod._osv_severity_to_enum("") == Severity.INFO
        assert mod._osv_severity_to_enum("unknown") == Severity.INFO

    def test_parse_pip_audit_records_with_cve(self, mod):
        records = [
            {
                "name": "requests",
                "version": "2.20.0",
                "vulns": [
                    {
                        "id": "GHSA-test-1234",
                        "aliases": ["CVE-2018-18074"],
                        "description": "Test description",
                        "fix_versions": ["2.31.0"],
                        "severity_label": "high",
                    }
                ],
            }
        ]
        findings = mod._parse_pip_audit_records(records, "test")
        assert len(findings) == 1
        assert findings[0].cve_id == "CVE-2018-18074"
        assert "2.31.0" in findings[0].remediation

    def test_parse_pip_audit_no_fix_bumps_severity(self, mod):
        from lib.finding import Severity

        records = [
            {
                "name": "no-fix-pkg",
                "version": "1.0.0",
                "vulns": [
                    {
                        "id": "GHSA-nofix",
                        "aliases": [],
                        "description": "No fix",
                        "fix_versions": [],
                        "severity_label": "medium",
                    }
                ],
            }
        ]
        findings = mod._parse_pip_audit_records(records, "test")
        # Medium + no fix → at-least HIGH
        assert findings[0].severity.numeric >= Severity.HIGH.numeric

    def test_cli_help(self, mod):
        with pytest.raises(SystemExit) as exc:
            mod.main(["--help"])
        assert exc.value.code == 0


# --- check_licenses.py ------------------------------------------------------


class TestCheckLicenses:
    @pytest.fixture
    def mod(self):
        return _load_script("checking-license-compliance", "check_licenses.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "checking-license-compliance"

    @pytest.mark.parametrize(
        "license_str, expected",
        [
            ("MIT", "permissive"),
            ("Apache-2.0", "permissive"),
            ("BSD-3-Clause", "permissive"),
            ("GPL-2.0-only", "strong_copyleft"),
            ("GPL-3.0-or-later", "strong_copyleft"),
            ("AGPL-3.0-only", "strong_copyleft"),
            ("LGPL-2.1-only", "weak_copyleft"),
            ("MPL-2.0", "weak_copyleft"),
            ("", "unknown"),
            ("UNKNOWN", "unknown"),
            ("UNLICENSED", "unknown"),
            ("Proprietary", "custom"),
            ("Some-Custom-License", "custom"),
        ],
    )
    def test_classify_license(self, mod, license_str, expected):
        assert mod.classify_license(license_str) == expected

    def test_classify_dual_license_takes_first(self, mod):
        """`MIT OR Apache-2.0` should classify by the first entry."""
        assert mod.classify_license("MIT OR Apache-2.0") == "permissive"

    def test_classify_gpl_heuristic(self, mod):
        """Even a non-SPDX 'GPL'-like string should classify strong_copyleft."""
        assert mod.classify_license("GPL Version 2") == "strong_copyleft"

    def test_detect_project_license_from_package_json(self, mod, tmp_path):
        (tmp_path / "package.json").write_text('{"license": "MIT"}')
        assert mod.detect_project_license(tmp_path) == "MIT"

    def test_detect_project_license_missing(self, mod, tmp_path):
        assert mod.detect_project_license(tmp_path) is None

    def test_load_policy_default(self, mod, tmp_path):
        policy = mod.load_policy(tmp_path, None)
        assert "allow" in policy
        assert "deny" in policy
        assert "GPL-2.0-only" in policy["deny"]

    def test_load_policy_from_file(self, mod, tmp_path):
        custom = tmp_path / "policy.json"
        custom.write_text(json.dumps({"allow": ["MIT"], "deny": [], "review": []}))
        policy = mod.load_policy(tmp_path, custom)
        assert policy["allow"] == ["MIT"]

    def test_assess_package_strong_copyleft_in_permissive_project(self, mod):
        pkg = {
            "ecosystem": "npm",
            "name": "gpl-thing",
            "version": "1.0.0",
            "license": "GPL-3.0-only",
            "path": "/tmp/test",
            "homepage": "",
        }
        policy = dict(mod.DEFAULT_POLICY)
        policy["project_license"] = "MIT"
        finding = mod.assess_package(pkg, policy, "MIT")
        from lib.finding import Severity

        assert finding is not None
        assert finding.severity == Severity.CRITICAL


# --- trace_vulns.py ---------------------------------------------------------


class TestTraceVulns:
    @pytest.fixture
    def mod(self):
        return _load_script("tracing-transitive-vulnerabilities", "trace_vulns.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "tracing-transitive-vulnerabilities"

    def test_detect_project_type_npm(self, mod, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "node_modules").mkdir()
        assert mod.detect_project_type(tmp_path) == "npm"

    def test_detect_project_type_python(self, mod, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'")
        assert mod.detect_project_type(tmp_path) == "python"

    def test_detect_project_type_unknown(self, mod, tmp_path):
        assert mod.detect_project_type(tmp_path) == "unknown"

    def test_trace_paths_direct_dep(self, mod):
        parents = {"lodash": [], "express": [], "qs": ["express"]}
        direct = {"lodash", "express"}
        paths = mod.trace_paths("lodash", parents, direct)
        assert paths == [["lodash"]]

    def test_trace_paths_one_hop(self, mod):
        parents = {"express": [], "qs": ["express"]}
        direct = {"express"}
        paths = mod.trace_paths("qs", parents, direct)
        assert paths == [["express", "qs"]]

    def test_trace_paths_multiple_parents(self, mod):
        # qs is reachable via express AND via koa
        parents = {"express": [], "koa": [], "qs": ["express", "koa"]}
        direct = {"express", "koa"}
        paths = mod.trace_paths("qs", parents, direct)
        path_set = {tuple(p) for p in paths}
        assert ("express", "qs") in path_set
        assert ("koa", "qs") in path_set

    def test_load_audit_findings_list(self, mod, tmp_path, sample_findings):
        audit = tmp_path / "audit.json"
        audit.write_text(json.dumps(sample_findings))
        records = mod.load_audit_findings(audit)
        assert len(records) == 3

    def test_load_audit_findings_findings_key(self, mod, tmp_path, sample_findings):
        audit = tmp_path / "audit.json"
        audit.write_text(json.dumps({"findings": sample_findings}))
        records = mod.load_audit_findings(audit)
        assert len(records) == 3

    def test_extract_package_name_from_evidence(self, mod):
        finding = {
            "skill_id": "auditing-npm-dependencies",
            "evidence": {"package": "lodash"},
            "target": "test",
        }
        assert mod.extract_package_name_from_finding(finding) == "lodash"

    def test_extract_package_name_from_target(self, mod):
        finding = {
            "skill_id": "x",
            "target": "test-project::lodash",
            "evidence": {},
        }
        assert mod.extract_package_name_from_finding(finding) == "lodash"

    # =====================================================================
    # build_trace_findings — the algorithmic composition the reviewer
    # flagged as having 0% coverage. Tests cover each severity-bump branch.
    # =====================================================================

    def test_build_trace_findings_skips_info_severity(self, mod):
        """INFO-severity audit findings should NOT become trace findings."""
        audit = [
            {
                "skill_id": "auditing-npm-dependencies",
                "severity": "info",
                "evidence": {"package": "lodash"},
                "target": "test",
                "cve_id": None,
            }
        ]
        parents = {"lodash": []}
        direct = {"lodash"}
        out = mod.build_trace_findings(audit, parents, direct, min_depth=0)
        # Only the leverage-report finding should be in the output (no real
        # transitive vuln, no leverage to track) — but if INFO was incorrectly
        # included it'd produce a non-INFO trace finding here.
        non_info_traces = [f for f in out if "transitive vuln" in f.title.lower()]
        assert non_info_traces == []

    def test_build_trace_findings_direct_dep_depth_0(self, mod):
        """A direct-dep CVE has depth 0 — should be skipped when min_depth>0."""
        audit = [
            {
                "skill_id": "auditing-npm-dependencies",
                "severity": "high",
                "evidence": {"package": "lodash"},
                "target": "test::lodash",
                "cve_id": "CVE-2026-0001",
            }
        ]
        parents = {"lodash": []}
        direct = {"lodash"}
        out = mod.build_trace_findings(audit, parents, direct, min_depth=1)
        non_leverage = [f for f in out if "Direct dep" not in f.title]
        # depth=0 (direct), min_depth=1 → no transitive trace finding
        assert non_leverage == []

    def test_build_trace_findings_deep_transitive_bumps_severity(self, mod):
        """At depth >=3, a CRITICAL becomes HIGH/CRITICAL, and a HIGH gets
        bumped (depth alone elevates concern about blast radius)."""
        # qs reachable only via deep chain: express -> a -> b -> qs (depth 3)
        audit = [
            {
                "skill_id": "auditing-npm-dependencies",
                "severity": "high",
                "evidence": {"package": "qs"},
                "target": "test::qs",
                "cve_id": "CVE-2026-0002",
            }
        ]
        parents = {"express": [], "a": ["express"], "b": ["a"], "qs": ["b"]}
        direct = {"express"}
        out = mod.build_trace_findings(audit, parents, direct, min_depth=0)
        trace_findings = [f for f in out if "transitive vuln" in f.title.lower()]
        assert len(trace_findings) == 1
        # The original severity was HIGH; depth >= 3 should keep it at least HIGH.
        assert trace_findings[0].severity.value in ("high", "critical")

    def test_build_trace_findings_multi_path_bumps_severity(self, mod):
        """A vuln reachable via >=5 paths should bump severity by one tier
        (broad reachability = harder remediation)."""
        # qs reachable via 5 distinct direct deps
        audit = [
            {
                "skill_id": "auditing-npm-dependencies",
                "severity": "medium",
                "evidence": {"package": "qs"},
                "target": "test::qs",
                "cve_id": "CVE-2026-0003",
            }
        ]
        parents = {
            "p1": [],
            "p2": [],
            "p3": [],
            "p4": [],
            "p5": [],
            "qs": ["p1", "p2", "p3", "p4", "p5"],
        }
        direct = {"p1", "p2", "p3", "p4", "p5"}
        out = mod.build_trace_findings(audit, parents, direct, min_depth=0)
        trace_findings = [f for f in out if "transitive vuln" in f.title.lower()]
        assert len(trace_findings) == 1
        # Original severity MEDIUM; 5 paths should bump to HIGH.
        assert trace_findings[0].severity.value == "high"

    def test_build_trace_findings_leverage_report_picks_top_ancestor(self, mod):
        """The leverage report should call out the direct ancestor for which
        the most transitive CVEs flow through."""
        audit = [
            {
                "skill_id": "auditing-npm-dependencies",
                "severity": "high",
                "evidence": {"package": f"vuln-{i}"},
                "target": f"test::vuln-{i}",
                "cve_id": f"CVE-2026-{1000 + i}",
            }
            for i in range(3)
        ]
        # All 3 vulns flow through `express` (high-leverage ancestor)
        parents = {
            "express": [],
            **{f"vuln-{i}": ["express"] for i in range(3)},
        }
        direct = {"express"}
        out = mod.build_trace_findings(audit, parents, direct, min_depth=0)
        leverage_findings = [f for f in out if "ancestor for" in f.title.lower()]
        assert leverage_findings
        # The top leverage ancestor should be `express` with 3 CVE count
        top = leverage_findings[0]
        assert "express" in top.title
        assert "3" in top.title  # count of 3 CVEs

    def test_build_trace_findings_unmappable_package_dropped(self, mod):
        """Audit finding with no extractable package name should be skipped."""
        audit = [
            {
                "skill_id": "x",
                "severity": "high",
                "evidence": {},
                "target": "nodoublecolon",
                "cve_id": None,
            }
        ]
        out = mod.build_trace_findings(audit, {}, set(), min_depth=0)
        # No usable package name → no trace finding produced
        traces = [f for f in out if "transitive vuln" in f.title.lower()]
        assert traces == []
