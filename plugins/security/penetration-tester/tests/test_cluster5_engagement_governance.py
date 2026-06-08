"""Tests for cluster 5 skills: engagement governance (3 scripts).

Covers:
    - confirming-pentest-authorization / check_authorization.py
    - defining-pentest-scope / define_scope.py
    - recording-pentest-engagement / record_engagement.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

_PACK = Path(__file__).resolve().parents[1]


def _load_script(skill_dir: str, script_name: str):
    path = _PACK / "skills" / skill_dir / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(f"{skill_dir}_{script_name[:-3]}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- check_authorization.py -------------------------------------------------


class TestCheckAuthorization:
    @pytest.fixture
    def mod(self):
        return _load_script("confirming-pentest-authorization", "check_authorization.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "confirming-pentest-authorization"

    def test_load_roe_present(self, mod, sample_roe_path):
        data, err = mod.load_roe(sample_roe_path)
        assert err is None
        assert data is not None
        assert data.get("engagement_id") == "TEST-ENG-001"

    def test_load_roe_missing(self, mod, tmp_path):
        data, err = mod.load_roe(tmp_path / "no-such-file.yaml")
        assert data is None
        assert err is not None
        assert "not found" in err.lower()

    def test_validate_roe_complete(self, mod, sample_roe_dict):
        findings = mod.validate_roe(sample_roe_dict, "test", allowed=[])
        # A complete ROE with a far-future time window should produce no CRITICAL
        criticals = [f for f in findings if f.severity.value == "critical"]
        assert criticals == []

    def test_validate_roe_missing_authorizer(self, mod, sample_roe_dict):
        from copy import deepcopy

        data = deepcopy(sample_roe_dict)
        data["authorizer"] = {}
        findings = mod.validate_roe(data, "test", allowed=[])
        # Missing authorizer sub-fields should produce CRITICAL findings
        criticals = [f for f in findings if f.severity.value == "critical"]
        assert len(criticals) >= 3  # name, email, role

    def test_validate_roe_expired_time_window(self, mod, sample_roe_dict):
        from copy import deepcopy

        data = deepcopy(sample_roe_dict)
        data["time_window"]["end"] = "2020-01-01T00:00:00Z"
        findings = mod.validate_roe(data, "test", allowed=[])
        # Expired window should produce a HIGH finding
        highs = [f for f in findings if f.severity.value == "high"]
        assert any("expired" in f.title.lower() for f in highs)

    def test_validate_roe_signer_not_in_allowlist(self, mod, sample_roe_dict):
        # Signer is jane.doe@example.test; allowlist has someone else
        allowed = ["other@example.test"]
        findings = mod.validate_roe(sample_roe_dict, "test", allowed)
        criticals = [f for f in findings if f.severity.value == "critical"]
        assert any("allowed-authorizers" in f.title for f in criticals)

    def test_validate_roe_empty_in_scope(self, mod, sample_roe_dict):
        from copy import deepcopy

        data = deepcopy(sample_roe_dict)
        data["in_scope_targets"] = []
        findings = mod.validate_roe(data, "test", allowed=[])
        highs = [f for f in findings if f.severity.value == "high"]
        assert any("empty" in f.title.lower() for f in highs)

    def test_target_in_scope_exact_host(self, mod):
        assert mod.target_in_scope("app.example.test", ["app.example.test"])
        assert not mod.target_in_scope("other.example.test", ["app.example.test"])

    def test_target_in_scope_cidr_match(self, mod):
        assert mod.target_in_scope("203.0.113.10", ["203.0.113.0/24"])
        assert not mod.target_in_scope("203.0.114.10", ["203.0.113.0/24"])

    def test_target_in_scope_wildcard(self, mod):
        assert mod.target_in_scope("api.example.test", ["*.example.test"])
        assert mod.target_in_scope("app.example.test", ["*.example.test"])
        assert not mod.target_in_scope("api.other.test", ["*.example.test"])

    def test_parse_iso_valid(self, mod):
        assert mod._parse_iso("2026-01-01T00:00:00Z") is not None
        assert mod._parse_iso("2026-01-01T00:00:00+00:00") is not None

    def test_parse_iso_invalid_returns_none(self, mod):
        assert mod._parse_iso("not-a-date") is None
        assert mod._parse_iso("") is None


# --- define_scope.py --------------------------------------------------------


class TestDefineScope:
    @pytest.fixture
    def mod(self):
        return _load_script("defining-pentest-scope", "define_scope.py")

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "defining-pentest-scope"

    @pytest.mark.parametrize(
        "entry, expected_type",
        [
            ("app.example.test", "hostname"),
            ("*.example.test", "wildcard"),
            ("203.0.113.10", "ipv4"),
            ("203.0.113.0/24", "cidrv4"),
            ("2001:db8::1", "ipv6"),
            ("2001:db8::/32", "cidrv6"),
            ("https://app.example.test/path", "url"),
            ("aws:123456789012", "cloud"),
            ("okta:acme-corp", "saas"),
            ("not a real entry !!!", "malformed"),
            ("", "malformed"),
        ],
    )
    def test_classify_target(self, mod, entry, expected_type):
        _, t, _ = mod.classify_target(entry)
        assert t == expected_type

    def test_classify_target_dict_with_host(self, mod):
        _, t, _ = mod.classify_target({"host": "app.example.test"})
        assert t == "hostname"

    def test_classify_target_dict_with_cidr(self, mod):
        _, t, _ = mod.classify_target({"cidr": "203.0.113.0/24"})
        assert t == "cidrv4"

    def test_cidr_overlap_yes(self, mod):
        assert mod.cidr_overlap("203.0.113.0/24", "203.0.113.128/25")
        assert mod.cidr_overlap("203.0.113.128/25", "203.0.113.0/24")

    def test_cidr_overlap_no(self, mod):
        assert not mod.cidr_overlap("203.0.113.0/24", "198.51.100.0/24")

    def test_cidr_overlap_different_families(self, mod):
        assert not mod.cidr_overlap("203.0.113.0/24", "2001:db8::/32")

    def test_detect_reserved_rfc1918(self, mod):
        assert mod.detect_reserved("10.50.0.0/16") is not None
        assert mod.detect_reserved("192.168.1.0/24") is not None

    def test_detect_reserved_public(self, mod):
        assert mod.detect_reserved("203.0.113.10") is None

    def test_detect_reserved_link_local(self, mod):
        assert mod.detect_reserved("169.254.1.1") is not None

    def test_evaluate_scope_clean(self, mod):
        in_scope = [{"host": "app.example.test"}]
        out_of_scope = [{"host": "payments.example.test"}]
        findings, normalized, allowlist = mod.evaluate_scope(in_scope, out_of_scope, "test")
        # No malformed entries, no overlap → no high/critical findings
        assert not any(f.severity.value in ("critical", "high") for f in findings)
        assert len(normalized) == 1

    def test_evaluate_scope_overlap_critical(self, mod):
        in_scope = [{"cidr": "203.0.113.0/24"}]
        out_of_scope = [{"cidr": "203.0.113.128/25"}]
        findings, _, _ = mod.evaluate_scope(in_scope, out_of_scope, "test")
        criticals = [f for f in findings if f.severity.value == "critical"]
        assert any("overlap" in f.title.lower() for f in criticals)

    def test_evaluate_scope_malformed_high(self, mod):
        in_scope = ["not a real target !!!"]
        out_of_scope = []
        findings, _, _ = mod.evaluate_scope(in_scope, out_of_scope, "test")
        assert any(f.severity.value == "high" for f in findings)


# --- record_engagement.py ---------------------------------------------------


class TestRecordEngagement:
    @pytest.fixture
    def mod(self):
        return _load_script("recording-pentest-engagement", "record_engagement.py")

    @pytest.fixture
    def small_engagement(self, tmp_path: Path):
        """A tiny engagement directory with a few files."""
        eng = tmp_path / "test-eng"
        eng.mkdir()
        (eng / "roe.yaml").write_text("engagement_id: TEST\n")
        (eng / "findings").mkdir()
        (eng / "findings" / "f1.json").write_text("[]")
        (eng / "reports").mkdir()
        (eng / "reports" / "r1.md").write_text("# Report\n")
        return eng

    def test_skill_id(self, mod):
        assert mod.SKILL_ID == "recording-pentest-engagement"

    def test_sha256_file_matches_hashlib(self, mod, tmp_path):
        f = tmp_path / "x.txt"
        content = "hello world"
        f.write_text(content)
        expected = hashlib.sha256(content.encode()).hexdigest()
        assert mod._sha256_file(f) == expected

    def test_walk_files_finds_everything(self, mod, small_engagement):
        files, findings = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        # 3 files: roe.yaml, f1.json, r1.md
        assert len(files) == 3

    def test_walk_files_excludes_manifest(self, mod, small_engagement):
        # Create an existing manifest — should be excluded by default
        (small_engagement / "manifest.sha256").write_text("dummy")
        files, _ = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        names = [f.name for f in files]
        assert "manifest.sha256" not in names

    def test_walk_files_flags_symlink(self, mod, small_engagement, tmp_path):
        link = small_engagement / "link.txt"
        try:
            os.symlink(small_engagement / "roe.yaml", link)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks not supported on this platform")
        _, findings = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        assert any("symlink" in f.title.lower() for f in findings)

    def test_walk_files_flags_empty_file(self, mod, small_engagement):
        (small_engagement / "empty.txt").write_text("")
        _, findings = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        assert any("empty" in f.title.lower() for f in findings)

    def test_compute_manifest_entries(self, mod, small_engagement):
        files, _ = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        entries, _ = mod.compute_manifest(small_engagement, files)
        assert len(entries) == 3
        for digest, rel in entries:
            assert len(digest) == 64  # SHA-256 hex
            assert not rel.startswith("/")  # relative paths

    def test_write_and_load_manifest(self, mod, small_engagement, tmp_path):
        files, _ = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        entries, _ = mod.compute_manifest(small_engagement, files)
        manifest_path = tmp_path / "manifest.sha256"
        mod.write_manifest(entries, manifest_path)
        loaded = mod.load_existing_manifest(manifest_path)
        assert sorted(loaded) == sorted(entries)

    def test_verify_against_existing_clean(self, mod, small_engagement, tmp_path):
        files, _ = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        entries, _ = mod.compute_manifest(small_engagement, files)
        # Manifest matches reality → no findings
        findings = mod.verify_against_existing(small_engagement, entries, entries)
        assert findings == []

    def test_verify_against_existing_hash_mismatch(self, mod, small_engagement):
        files, _ = mod.walk_files(small_engagement, list(mod.DEFAULT_EXCLUDES))
        entries, _ = mod.compute_manifest(small_engagement, files)
        # Tamper: replace a digest
        tampered = [("0" * 64, e[1]) if i == 0 else e for i, e in enumerate(entries)]
        findings = mod.verify_against_existing(small_engagement, entries, tampered)
        criticals = [f for f in findings if f.severity.value == "critical"]
        assert any("mismatch" in f.title.lower() for f in criticals)

    def test_main_creates_manifest_on_clean_dir(self, mod, small_engagement):
        """Reviewer tightening (PR #837): `in (0, 1)` was vacuous — it
        covered the entire return space of report.exit_code(). A clean
        engagement directory should exit 0; any HIGH/CRITICAL op finding
        would be a regression worth investigating, not a "either is fine"
        scenario. Tighten the assertion to require exit 0."""
        exit_code = mod.main([str(small_engagement)])
        manifest = small_engagement / "manifest.sha256"
        assert manifest.exists()
        assert exit_code == 0, (
            f"clean engagement directory should exit 0, got {exit_code} — "
            f"a HIGH/CRITICAL op finding indicates a regression"
        )
