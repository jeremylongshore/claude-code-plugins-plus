"""Tests for cluster 6 skills: reporting (3 scripts).

Covers:
    - composing-vulnerability-report / compose_report.py
    - mapping-findings-to-owasp-top10 / map_owasp.py
    - generating-executive-summary / exec_summary.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

_PACK = Path(__file__).resolve().parents[1]


def _load_script(skill_dir: str, script_name: str):
    path = _PACK / "skills" / skill_dir / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(f"{skill_dir}_{script_name[:-3]}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- compose_report.py ------------------------------------------------------


class TestComposeReport:
    @pytest.fixture
    def mod(self):
        return _load_script("composing-vulnerability-report", "compose_report.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "composing-vulnerability-report"

    def test_load_finding_records_jsonl(self, mod, sample_findings_jsonl):
        records, err = mod.load_finding_records(sample_findings_jsonl)
        assert err is None
        assert len(records) == 3

    def test_load_finding_records_json_list(self, mod, tmp_path, sample_findings):
        f = tmp_path / "findings.json"
        f.write_text(json.dumps(sample_findings))
        records, err = mod.load_finding_records(f)
        assert err is None
        assert len(records) == 3

    def test_load_finding_records_findings_key(self, mod, tmp_path, sample_findings):
        f = tmp_path / "findings.json"
        f.write_text(json.dumps({"findings": sample_findings}))
        records, err = mod.load_finding_records(f)
        assert err is None
        assert len(records) == 3

    def test_load_finding_records_missing(self, mod, tmp_path):
        records, err = mod.load_finding_records(tmp_path / "no-such-file.jsonl")
        assert err is not None

    def test_normalize_record_complete(self, mod, sample_findings):
        finding, err = mod.normalize_record(sample_findings[0])
        assert err is None
        assert finding is not None
        assert finding.title == "Critical CVE in lodash"

    def test_normalize_record_missing_field(self, mod):
        record = {"skill_id": "test", "title": "x", "severity": "high", "target": "y"}
        # missing detail + remediation
        finding, err = mod.normalize_record(record)
        assert finding is None
        assert err is not None
        assert "missing required fields" in err

    def test_render_summary_table(self, mod, sample_findings):
        from lib.finding import from_json

        findings = [from_json(r) for r in sample_findings]
        from collections import defaultdict

        by_sev: dict[Any, list[Any]] = defaultdict(list)
        for f in findings:
            by_sev[f.severity].append(f)
        table = mod.render_summary_table(by_sev)
        assert "CRITICAL" in table
        assert "HIGH" in table
        assert "MEDIUM" in table

    def test_render_finding_section_has_anchor(self, mod, sample_findings):
        from lib.finding import from_json

        f = from_json(sample_findings[0])
        section = mod.render_finding_section(f)
        assert f.fingerprint() in section
        assert "## " in section or "### " in section

    def test_detect_engagement_id_from_roe(self, mod, engagement_dir):
        eid = mod.detect_engagement_id(engagement_dir)
        assert eid == "TEST-ENG-001"

    def test_detect_engagement_id_fallback_dirname(self, mod, tmp_path):
        eng = tmp_path / "no-roe-eng"
        eng.mkdir()
        assert mod.detect_engagement_id(eng) == "no-roe-eng"

    def test_main_produces_report(self, mod, engagement_dir):
        mod.main([str(engagement_dir)])
        report_path = engagement_dir / "reports" / "vulnerability-report.md"
        assert report_path.exists()
        text = report_path.read_text()
        assert "Vulnerability Report" in text
        assert "TEST-ENG-001" in text


# --- map_owasp.py -----------------------------------------------------------


class TestMapOwasp:
    @pytest.fixture
    def mod(self):
        return _load_script("mapping-findings-to-owasp-top10", "map_owasp.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "mapping-findings-to-owasp-top10"

    def test_owasp_categories_complete(self, mod):
        # All 10 A0X categories should be present
        codes = set(mod.OWASP_CATEGORIES.keys())
        expected = {f"A{n:02d}" for n in range(1, 11)}
        assert codes == expected

    def test_skill_to_owasp_covers_cluster_4(self, mod):
        for skill in [
            "auditing-npm-dependencies",
            "auditing-python-dependencies",
            "checking-license-compliance",
            "tracing-transitive-vulnerabilities",
        ]:
            assert skill in mod.SKILL_TO_OWASP
            assert mod.SKILL_TO_OWASP[skill] == "A06"  # all vulnerable-components

    def test_skill_to_owasp_covers_cluster_5(self, mod):
        for skill in [
            "confirming-pentest-authorization",
            "defining-pentest-scope",
        ]:
            assert mod.SKILL_TO_OWASP[skill] == "A04"  # insecure design
        assert mod.SKILL_TO_OWASP["recording-pentest-engagement"] == "A09"

    def test_classify_by_cwe(self, mod):
        record = {"cwe_id": "CWE-79"}
        code, rule = mod.classify(record, overrides=[])
        assert code == "A03"  # XSS → injection
        assert "cwe-mapping" in rule

    def test_classify_by_skill(self, mod):
        record = {"skill_id": "auditing-npm-dependencies"}
        code, rule = mod.classify(record, overrides=[])
        assert code == "A06"
        assert "skill-default" in rule

    def test_classify_by_detail_keyword(self, mod):
        record = {
            "skill_id": "unknown-skill",
            "detail": "Found SQL injection",
            "title": "test",
        }
        code, rule = mod.classify(record, overrides=[])
        assert code == "A03"  # injection
        assert "keyword" in rule

    def test_classify_override_wins(self, mod):
        overrides = [
            {
                "skill_id": "auditing-npm-dependencies",
                "owasp_category": "A05:2021 — Security Misconfiguration",
                "reason": "test override",
            }
        ]
        record = {"skill_id": "auditing-npm-dependencies"}
        code, rule = mod.classify(record, overrides)
        assert code == "A05"
        assert "override" in rule

    def test_classify_unmapped(self, mod):
        record = {
            "skill_id": "unknown-skill",
            "detail": "no matching keyword",
            "title": "no match",
        }
        code, _ = mod.classify(record, overrides=[])
        assert code is None

    def test_apply_override_detail_match(self, mod):
        override = {"skill_id": "x", "detail_contains": ".env"}
        record = {"skill_id": "x", "detail": "leaked .env file"}
        assert mod.apply_override(record, override) is True

    def test_apply_override_skill_mismatch(self, mod):
        override = {"skill_id": "x"}
        record = {"skill_id": "y"}
        assert mod.apply_override(record, override) is False

    def test_main_writes_enriched_and_coverage(self, mod, engagement_dir):
        mod.main([str(engagement_dir)])
        enriched = engagement_dir / "findings" / "all-with-owasp.jsonl"
        coverage = engagement_dir / "reports" / "owasp-coverage.md"
        assert enriched.exists()
        assert coverage.exists()
        # Every enriched record has an owasp_category field
        for line in enriched.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                assert "owasp_category" in rec


# --- exec_summary.py --------------------------------------------------------


class TestExecSummary:
    @pytest.fixture
    def mod(self):
        return _load_script("generating-executive-summary", "exec_summary.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "generating-executive-summary"

    def test_severity_counts(self, mod, sample_findings):
        counts = mod.severity_counts(sample_findings)
        assert counts["critical"] == 1
        assert counts["high"] == 1
        assert counts["medium"] == 1

    def test_compute_risk_score_clean(self, mod):
        # 0 findings → 0 score; roe_clean subtracts 10 but min is 0
        assert mod.compute_risk_score([], roe_clean=True) == 0
        assert mod.compute_risk_score([], roe_clean=False) == 0

    def test_compute_risk_score_critical_only(self, mod):
        finding = {"severity": "critical"}
        score = mod.compute_risk_score([finding], roe_clean=False)
        assert score == 20

    def test_compute_risk_score_clamps_high(self, mod):
        # 20 criticals → 400 raw, clamped to 100
        findings = [{"severity": "critical"} for _ in range(20)]
        assert mod.compute_risk_score(findings, roe_clean=False) == 100

    def test_compute_risk_score_governance_bonus(self, mod):
        findings = [{"severity": "high"}]  # 10 raw
        no_bonus = mod.compute_risk_score(findings, roe_clean=False)
        with_bonus = mod.compute_risk_score(findings, roe_clean=True)
        assert with_bonus < no_bonus

    @pytest.mark.parametrize(
        "score, band",
        [
            (0, "Low"),
            (25, "Low"),
            (50, "Moderate"),
            (75, "Elevated"),
            (90, "High"),
            (100, "Critical"),
        ],
    )
    def test_interpret_risk_bands(self, mod, score, band):
        assert mod.interpret_risk(score) == band

    def test_pick_top_priorities_picks_criticals_first(self, mod):
        findings = [
            {"severity": "low", "title": "low-1", "target": "x", "skill_id": "s"},
            {"severity": "critical", "title": "crit-1", "target": "y", "skill_id": "s"},
            {"severity": "high", "title": "high-1", "target": "z", "skill_id": "s"},
        ]
        priorities = mod.pick_top_priorities(findings, overrides=[])
        # First priority should be the critical
        assert priorities[0]["title"] == "crit-1"
        assert priorities[0]["severity"] == "critical"

    def test_pick_top_priorities_overrides_win(self, mod):
        overrides = [
            {
                "title": "Manual priority",
                "effort": "Days",
                "impact": "Material",
                "severity": "high",
                "skill_id": "manual",
                "reach": 1,
                "owasp": "A02",
                "fingerprint": "abc",
            }
        ]
        priorities = mod.pick_top_priorities([], overrides=overrides)
        assert priorities[0]["title"] == "Manual priority"

    def test_estimate_effort_dependencies(self, mod):
        record = {"skill_id": "auditing-npm-dependencies", "severity": "high"}
        assert mod.estimate_effort(record) == "Hours"

    def test_estimate_effort_injection(self, mod):
        record = {"skill_id": "detecting-sql-injection-patterns", "severity": "high"}
        assert mod.estimate_effort(record) == "Weeks"

    def test_estimate_impact_critical(self, mod):
        record = {"severity": "critical"}
        assert mod.estimate_impact(record, [record]) == "Material"

    def test_estimate_impact_high_reach(self, mod):
        record = {"severity": "high", "target": "a"}
        siblings = [record, {"severity": "high", "target": "b"}, {"severity": "high", "target": "c"}]
        assert mod.estimate_impact(record, siblings) == "Material"

    def test_estimate_impact_low_default(self, mod):
        record = {"severity": "low"}
        assert mod.estimate_impact(record, [record]) == "Limited"

    def test_summarize_roe_complete(self, mod, sample_roe_dict):
        summary = mod.summarize_roe(sample_roe_dict)
        assert "TEST-ENG-001" in summary
        assert "Jane Doe" in summary

    def test_summarize_roe_empty(self, mod):
        summary = mod.summarize_roe({})
        assert "not available" in summary.lower()

    def test_main_writes_exec_summary(self, mod, engagement_dir):
        # First run map_owasp to produce the enriched file
        map_mod = _load_script("mapping-findings-to-owasp-top10", "map_owasp.py")
        map_mod.main([str(engagement_dir)])
        # Now run exec_summary
        mod.main([str(engagement_dir)])
        summary_path = engagement_dir / "reports" / "executive-summary.md"
        assert summary_path.exists()
        text = summary_path.read_text()
        assert "Executive Summary" in text
        assert "Risk score" in text
        assert "TEST-ENG-001" in text

    def test_render_summary_byte_stability_modulo_timestamp(self, mod):
        """Re-rendering with the same inputs produces identical output (except timestamp)."""
        from collections import Counter

        counts = Counter({"high": 1})
        priorities = [
            {
                "title": "x",
                "severity": "high",
                "reach": 1,
                "effort": "Days",
                "impact": "Material",
                "owasp": "A06",
                "skill_id": "s",
                "fingerprint": "abc",
            }
        ]
        out1 = mod.render_summary([], 10, "Low", counts, priorities, "ROE", "Coverage", "test-eng")
        out2 = mod.render_summary([], 10, "Low", counts, priorities, "ROE", "Coverage", "test-eng")
        # Strip the date line (only difference between runs)
        clean1 = "\n".join(l for l in out1.splitlines() if "Generated:" not in l)
        clean2 = "\n".join(l for l in out2.splitlines() if "Generated:" not in l)
        assert clean1 == clean2
