#!/usr/bin/env python3
"""
Document Organization Script
Organizes claudes-docs files according to Filing System Standard v2.0
"""

import os
import shutil
from pathlib import Path

# Base directory
DOCS_DIR = Path(__file__).parent

# File mapping: old_name → (category, type, new_description)
FILE_MAPPING = {
    # Analysis & Reports (RA)
    "ANALYSIS_INDEX.md": ("RA", "INDX", "master-index"),
    "ANTHROPIC_CALIBER_QUALITY_AUDIT.md": ("RA", "AUDT", "anthropic-quality-audit"),
    "ANTHROPIC_COMPLIANCE_AUDIT_REPORT.md": ("RA", "AUDT", "compliance-audit"),
    "AUDIT_SUMMARY.md": ("RA", "SUMM", "audit-summary"),
    "QUALITY_AUDIT_EXECUTIVE_SUMMARY.md": ("RA", "SUMM", "quality-exec-summary"),
    "REPOSITORY_AUDIT_REPORT_2025-10-11.md": ("RA", "AUDT", "repo-audit-oct-2025"),
    "REPOSITORY_ARCHITECTURE_ANALYSIS.md": ("RA", "ANLY", "architecture-analysis"),
    "SKILLS_POWERKIT_RELEASE_AUDIT.md": ("RA", "AUDT", "skills-powerkit-audit"),

    # Research & Learning (RL)
    "ANTHROPIC_UPDATES_RESEARCH_2025-10-16.md": ("RL", "RSRC", "anthropic-updates-oct-2025"),
    "market-intelligence-update-2025-10-10.md": ("RL", "RSRC", "market-intelligence-oct-2025"),
    "monetization-strategy-2025-10-09.md": ("RL", "PROP", "monetization-strategy"),

    # Architecture & Technical (AT)
    "ARCHITECTURE_DIAGRAMS.md": ("AT", "DIAG", "architecture-diagrams"),

    # Project Management (PM)
    "CLAUDE_CODE_QUALITY_MASTER_TASK_LIST.md": ("PM", "TASK", "quality-master-tasks"),
    "QUALITY_IMPROVEMENT_TASKS.md": ("PM", "TASK", "quality-improvements"),
    "SKILLS_IMPLEMENTATION_ACTION_PLAN.md": ("PM", "PLAN", "skills-implementation"),

    # Logs & Status (LS)
    "AUTONOMOUS_IMPLEMENTATION_COMPLETE.md": ("LS", "STAT", "autonomous-impl-complete"),
    "COMPLETE_SESSION_SUMMARY.md": ("LS", "SUMM", "session-summary"),
    "IMPLEMENTATION_COMPLETE_v1.0.42.md": ("LS", "STAT", "v1-0-42-complete"),
    "SKILLS_POWERKIT_RELEASE_REPORT.md": ("LS", "STAT", "skills-powerkit-release"),

    # Documentation & Reference (DR)
    "QUICK_REFERENCE_GUIDE.md": ("DR", "GUID", "quick-reference"),
    "QUALITY_TEMPLATE.md": ("DR", "TMPL", "quality-template"),
    "COMPLIANCE_FIX_REPORT.md": ("DR", "REFF", "compliance-fixes"),

    # Operations & Deployment (OD)
    "DEPLOYMENT_CHECKLIST_v1.0.42.md": ("OD", "CHKL", "deployment-v1-0-42"),
    "GITHUB_RELEASE_v1.0.40.md": ("OD", "RELS", "github-v1-0-40"),
    "RELEASE_COMPLETE_v1.0.40.md": ("OD", "RELS", "v1-0-40-complete"),

    # Meetings & Communication (MC)
    "GITHUB_DISCUSSIONS_ANNOUNCEMENT.md": ("MC", "MEMO", "github-discussions"),
    "LAUNCH_ANNOUNCEMENT_v1.0.42.md": ("MC", "MEMO", "launch-v1-0-42"),
    "RELEASE_ANNOUNCEMENT_v1.0.40.md": ("MC", "MEMO", "release-v1-0-40"),
    "RELEASE_ANNOUNCEMENT_v2.0.0.md": ("MC", "MEMO", "release-v2-0-0"),
    "SOCIAL_MEDIA_ANNOUNCEMENTS.md": ("MC", "MEMO", "social-media"),
    "twitter-launch-thread.md": ("MC", "MEMO", "twitter-thread"),
    "EXECUTIVE_SUMMARY_2025-10-16.md": ("MC", "SUMM", "exec-summary-oct-2025"),
}

# Backups directory mapping
BACKUPS_MAPPING = {
    "BATCH_PROCESSING_STATUS.md": ("LS", "LOGS", "batch-processing-status"),
    "HOW_AGENT_SKILLS_WORK.md": ("DR", "GUID", "agent-skills-guide"),
    "SAFETY_IMPROVEMENTS.md": ("AT", "ADEC", "safety-improvements"),
    "SKILLS_TESTING_PLAN.md": ("TQ", "TEST", "skills-testing-plan"),
    "TEST_RUN_SUCCESS.md": ("LS", "LOGS", "test-run-success"),
    "VERTEX_QUOTA_INCREASE_INSTRUCTIONS.md": ("DR", "GUID", "vertex-quota-instructions"),
}


def organize_files(mapping, source_dir=DOCS_DIR, start_number=1):
    """Organize files according to mapping"""
    counter = start_number
    organized = []

    for old_name, (category, doc_type, description) in sorted(mapping.items()):
        old_path = source_dir / old_name

        if not old_path.exists():
            print(f"⚠️  File not found: {old_name}")
            continue

        # Generate new name
        new_name = f"{counter:03d}-{category}-{doc_type}-{description}.md"
        new_path = DOCS_DIR / category / new_name

        # Move file
        try:
            shutil.move(str(old_path), str(new_path))
            organized.append({
                'number': counter,
                'category': category,
                'type': doc_type,
                'description': description,
                'old_name': old_name,
                'new_name': new_name,
                'path': f"{category}/{new_name}"
            })
            print(f"✅ {counter:03d}: {old_name} → {category}/{new_name}")
            counter += 1
        except Exception as e:
            print(f"❌ Error moving {old_name}: {e}")

    return organized, counter


def create_index(organized_files):
    """Create master index file"""
    index_content = """# Master Document Index

**Date:** 2025-10-17
**Standard:** Filing System v2.0
**Total Documents:** {total}

---

## Quick Navigation

{nav_by_category}

---

## Chronological Index

{chronological}

---

## Category Index

{by_category}

---

**Last Updated:** 2025-10-17
**Auto-generated by:** organize-docs.py
"""

    # Navigation by category
    categories = {}
    for doc in organized_files:
        cat = doc['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(doc)

    nav_lines = []
    for cat in sorted(categories.keys()):
        count = len(categories[cat])
        nav_lines.append(f"- **{cat}** ({count} documents)")

    # Chronological listing
    chron_lines = []
    for doc in organized_files:
        chron_lines.append(
            f"**{doc['number']:03d}** | {doc['category']}-{doc['type']} | "
            f"[{doc['description']}]({doc['path']})"
        )

    # Category listings
    cat_lines = []
    for cat in sorted(categories.keys()):
        cat_lines.append(f"\n### {cat} - {get_category_name(cat)}\n")
        for doc in categories[cat]:
            cat_lines.append(
                f"- **{doc['number']:03d}** - {doc['type']} - "
                f"[{doc['description']}]({doc['path']})"
            )

    # Format index
    index = index_content.format(
        total=len(organized_files),
        nav_by_category='\n'.join(nav_lines),
        chronological='\n'.join(chron_lines),
        by_category='\n'.join(cat_lines)
    )

    # Write index
    index_path = DOCS_DIR / "001-MS-INDX-master-index.md"
    index_path.write_text(index)
    print(f"\n✅ Created master index: 001-MS-INDX-master-index.md")


def get_category_name(code):
    """Get category full name"""
    names = {
        'PP': 'Product & Planning',
        'AT': 'Architecture & Technical',
        'DC': 'Development & Code',
        'TQ': 'Testing & Quality',
        'OD': 'Operations & Deployment',
        'LS': 'Logs & Status',
        'RA': 'Reports & Analysis',
        'MC': 'Meetings & Communication',
        'PM': 'Project Management',
        'DR': 'Documentation & Reference',
        'UC': 'User & Customer',
        'BL': 'Business & Legal',
        'RL': 'Research & Learning',
        'AA': 'After Action & Review',
        'WA': 'Workflows & Automation',
        'DD': 'Data & Datasets',
        'MS': 'Miscellaneous'
    }
    return names.get(code, code)


def main():
    print("📁 Organizing claudes-docs according to Filing System Standard v2.0\n")

    # Organize main docs
    print("📂 Organizing main documentation files...")
    organized, next_number = organize_files(FILE_MAPPING, DOCS_DIR, start_number=1)

    # Organize backups
    backups_dir = DOCS_DIR.parent / "backups"
    if backups_dir.exists():
        print(f"\n📂 Organizing backup files from {backups_dir}...")
        backups_organized, _ = organize_files(BACKUPS_MAPPING, backups_dir, start_number=next_number)
        organized.extend(backups_organized)

    # Create index
    print("\n📝 Creating master index...")
    create_index(organized)

    print(f"\n✅ Organization complete! {len(organized)} files organized.")
    print(f"📍 Location: {DOCS_DIR}")
    print(f"📖 View index: 001-MS-INDX-master-index.md")


if __name__ == "__main__":
    main()
