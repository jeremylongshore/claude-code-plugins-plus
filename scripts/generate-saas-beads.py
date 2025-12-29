#!/usr/bin/env python3
"""
Generate beads task creation and dependency commands for 50-Vendor SaaS Skill Packs.

Usage:
    python3 scripts/generate-saas-beads.py > beads-tasks.sh
    python3 scripts/generate-saas-beads.py --deps-only > beads-deps.sh
    bash beads-tasks.sh  # Creates ~2,186 tasks
    bash beads-deps.sh   # Sets up ~3,000+ dependencies
"""

import argparse
import csv
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
TRACKER_CSV = REPO_ROOT / "plugins" / "saas-packs" / "TRACKER.csv"

# Epic IDs (will be created by this script)
MASTER_EPIC = "ccpi-saas"
INFRA_EPIC = "ccpi-saas-infra"

# Slot definitions by tier
STANDARD_SLOTS = [
    ("s01", "install-auth", "Install & Auth"),
    ("s02", "hello-world", "Hello World"),
    ("s03", "local-dev-loop", "Local Dev Loop"),
    ("s04", "sdk-patterns", "SDK Patterns"),
    ("s05", "core-workflow-a", "Core Workflow A"),
    ("s06", "core-workflow-b", "Core Workflow B"),
    ("s07", "common-errors", "Common Errors"),
    ("s08", "debug-bundle", "Debug Bundle"),
    ("s09", "rate-limits", "Rate Limits"),
    ("s10", "security-basics", "Security Basics"),
    ("s11", "prod-checklist", "Prod Checklist"),
    ("s12", "upgrade-migration", "Upgrade Migration"),
]

PRO_SLOTS = [
    ("p13", "ci-integration", "CI Integration"),
    ("p14", "deploy-integration", "Deploy Integration"),
    ("p15", "webhooks-events", "Webhooks & Events"),
    ("p16", "performance-tuning", "Performance Tuning"),
    ("p17", "cost-tuning", "Cost Tuning"),
    ("p18", "reference-architecture", "Reference Architecture"),
]

FLAGSHIP_SLOTS = [
    ("f19", "multi-env-setup", "Multi-Env Setup"),
    ("f20", "observability", "Observability"),
    ("f21", "incident-runbook", "Incident Runbook"),
    ("f22", "data-handling", "Data Handling"),
    ("f23", "enterprise-rbac", "Enterprise RBAC"),
    ("f24", "migration-deep-dive", "Migration Deep Dive"),
]

FLAGSHIP_PLUS_SLOTS = [
    ("x25", "advanced-troubleshooting", "Advanced Troubleshooting"),
    ("x26", "load-scale", "Load & Scale"),
    ("x27", "reliability-patterns", "Reliability Patterns"),
    ("x28", "policy-guardrails", "Policy & Guardrails"),
    ("x29", "architecture-variants", "Architecture Variants"),
    ("x30", "known-pitfalls", "Known Pitfalls"),
]


def get_slots_for_tier(tier: str) -> list:
    """Get all slots for a given tier."""
    slots = list(STANDARD_SLOTS)
    if tier in ("flagship+", "flagship", "pro"):
        slots.extend(PRO_SLOTS)
    if tier in ("flagship+", "flagship"):
        slots.extend(FLAGSHIP_SLOTS)
    if tier == "flagship+":
        slots.extend(FLAGSHIP_PLUS_SLOTS)
    return slots


def load_vendors() -> list:
    """Load vendor data from TRACKER.csv."""
    vendors = []
    with open(TRACKER_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vendors.append({
                "company": row["company"],
                "display_name": row["display_name"],
                "tier": row["tier"],
                "skill_count": int(row["skill_count"]),
                "beads_epic_id": row["beads_epic_id"],
            })
    return vendors


def generate_infra_tasks() -> list:
    """Generate infrastructure tasks."""
    tasks = [
        ("infra.1", "Template system: Create 30 slot templates", "Create _templates/slots/*.md.j2 for all 30 slots"),
        ("infra.2", "Pack generator script", "Create _templates/scripts/generate-pack.py"),
        ("infra.3", "Validation extension", "Extend validate-skills-schema.py for pack validation"),
        ("infra.4", "Website /learn/ structure", "Create marketplace/src/pages/learn/ templates"),
        ("infra.5", "Gemini config for PR review", "Create .gemini/config.yaml for auto-review"),
        ("infra.6", "Auto-merge workflow", "Create .github/workflows/automerge-packs.yml"),
    ]

    commands = []
    for task_id, title, desc in tasks:
        cmd = f'bd create "{title}" -t task -p 1 --description "{desc}. On close: Update infrastructure progress."'
        commands.append(cmd)

    return commands


def generate_vendor_tasks(vendor: dict) -> list:
    """Generate all tasks for a vendor."""
    company = vendor["company"]
    display_name = vendor["display_name"]
    tier = vendor["tier"]
    skill_count = vendor["skill_count"]
    epic_id = vendor["beads_epic_id"]

    slots = get_slots_for_tier(tier)
    commands = []

    # Create vendor epic
    epic_desc = f"Complete {display_name} skill pack ({skill_count} skills). Track progress in TRACKER.csv"
    commands.append(f'bd create "EPIC: {display_name} Pack ({skill_count} skills)" -t epic -p 0 --description "{epic_desc}"')

    # Phase 1: Skill Creation
    for i, (slot_id, slug, name) in enumerate(slots, 1):
        skill_name = f"{company}-{slug}"
        desc = f"Create {slot_id.upper()} skill: {skill_name}. On close: Update TRACKER.csv skills_created={i}"
        commands.append(f'bd create "Create: {skill_name}" -t task -p 1 --description "{desc}"')

    # Phase 2: Skill Testing
    for i, (slot_id, slug, name) in enumerate(slots, 1):
        skill_name = f"{company}-{slug}"
        desc = f"Test {skill_name} triggers correctly. On close: Update TRACKER.csv skills_tested={i}"
        commands.append(f'bd create "Test: {skill_name}" -t task -p 1 --description "{desc}"')

    # Phase 3: Website
    commands.append(f'bd create "Website: /learn/{company}/ index" -t task -p 1 --description "Create vendor index page. On close: Update TRACKER.csv website_status=in_progress"')
    commands.append(f'bd create "Website: {company} skill docs" -t task -p 1 --description "Create skill documentation pages"')
    commands.append(f'bd create "Website: {company} navigation" -t task -p 1 --description "Add to website navigation. On close: Update TRACKER.csv website_status=complete"')

    # Phase 4: Publish
    commands.append(f'bd create "Repo: Add {company}-pack to marketplace" -t task -p 1 --description "Add to marketplace.extended.json. On close: Update TRACKER.csv marketplace_status=added"')
    commands.append(f'bd create "Repo: {company}-pack README" -t task -p 1 --description "Update README with install instructions"')
    commands.append(f'bd create "Repo: {company}-pack validation" -t task -p 1 --description "Run full validation suite"')
    commands.append(f'bd create "PR: Create {company}-pack PR" -t task -p 0 --description "Create PR, Gemini review, fix, merge. On close: Update TRACKER.csv marketplace_status=live, completion_pct=100"')

    return commands


def generate_dependencies(vendor: dict, infra_epic_id: str) -> list:
    """Generate dependency commands for a vendor."""
    company = vendor["company"]
    tier = vendor["tier"]
    skill_count = vendor["skill_count"]

    slots = get_slots_for_tier(tier)
    commands = []

    # Note: These are placeholder commands - actual IDs will be assigned by beads
    # In practice, you'd need to capture the IDs after creating tasks

    # Vendor epic depends on infrastructure
    commands.append(f"# {company}: vendor epic depends on infrastructure")
    commands.append(f"# bd dep add {company}-epic {infra_epic_id}")

    # Test tasks depend on create tasks
    commands.append(f"# {company}: test depends on create (need actual IDs)")
    for i, (slot_id, slug, name) in enumerate(slots):
        commands.append(f"# bd dep add {company}.t{i+1:02d} {company}.{slot_id}")

    # Website depends on last skill
    commands.append(f"# {company}: website depends on all skills")
    commands.append(f"# bd dep add {company}.web.1 {company}.s{len(slots):02d}")

    # Publish depends on all tests + website
    commands.append(f"# {company}: publish depends on tests + website")
    commands.append(f"# bd dep add {company}.pub {company}.t{len(slots):02d}")
    commands.append(f"# bd dep add {company}.pub {company}.web.3")

    return commands


def main():
    parser = argparse.ArgumentParser(description="Generate beads tasks for SaaS packs")
    parser.add_argument("--deps-only", action="store_true", help="Only output dependency commands")
    parser.add_argument("--vendor", help="Generate for specific vendor only")
    args = parser.parse_args()

    vendors = load_vendors()

    if args.vendor:
        vendors = [v for v in vendors if v["company"] == args.vendor]
        if not vendors:
            print(f"# ERROR: Vendor '{args.vendor}' not found")
            return

    if args.deps_only:
        # Output dependency commands
        print("#!/bin/bash")
        print("# Dependency setup for 50-Vendor SaaS Skill Packs")
        print("# NOTE: These need actual task IDs - run after task creation")
        print()
        for vendor in vendors:
            deps = generate_dependencies(vendor, INFRA_EPIC)
            for cmd in deps:
                print(cmd)
            print()
    else:
        # Output task creation commands
        print("#!/bin/bash")
        print("# Task creation for 50-Vendor SaaS Skill Packs")
        print(f"# Total vendors: {len(vendors)}")
        print()

        # Infrastructure tasks
        print("# ===== INFRASTRUCTURE TASKS =====")
        for cmd in generate_infra_tasks():
            print(cmd)
        print()

        # Vendor tasks
        for vendor in vendors:
            print(f"# ===== {vendor['display_name'].upper()} ({vendor['tier']}, {vendor['skill_count']} skills) =====")
            for cmd in generate_vendor_tasks(vendor):
                print(cmd)
            print()

        # Summary
        total_skills = sum(v["skill_count"] for v in vendors)
        print(f"# Summary: {len(vendors)} vendors, {total_skills} skills")
        print(f"# Estimated tasks: {len(vendors) * 7 + total_skills * 2 + 6}")


if __name__ == "__main__":
    main()
