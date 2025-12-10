#!/usr/bin/env python3
"""
Fix the remaining 43 skills that still have issues after the overnight batch processing.
This script targets specific skills that need manual intervention.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List

# Skills that need immediate attention (from audit report)
PRIORITY_SKILLS = {
    "excel-skills": [
        "excel-dcf-modeler",
        "excel-lbo-modeler",
        "excel-pivot-wizard",
        "excel-variance-analyzer"
    ],
    "database-skills": [
        "database-connection-pooler",
        "database-health-monitor",
        "database-migration-manager",
        "database-partition-manager",
        "firestore-manager"
    ],
    "devops-skills": [
        "backup-strategy-implementor",
        "ci-cd-pipeline-builder",
        "container-registry-manager",
        "disaster-recovery-planner",
        "fairdb-backup-manager",
        "gitops-workflow-builder",
        "infrastructure-drift-detector",
        "gh-actions-validator",
        "sugar",
        "pi-pathfinder",
        "marketplace-manager"
    ],
    "plugin-skills": [
        "plugin-auditor",
        "plugin-creator",
        "plugin-validator",
        "version-bumper"
    ],
    "ai-ml-skills": [
        "experiment-tracking-setup",
        "model-deployment-helper"
    ],
    "performance-skills": [
        "cache-performance-optimizer",
        "infrastructure-metrics-collector"
    ],
    "productivity-skills": [
        "000-jeremy-content-consistency-validator",
        "001-jeremy-taskwarrior-integration",
        "yaml-master",
        "vertex-media-master",
        "agent-sdk-master",
        "overnight-dev"
    ]
}

# Skills that don't need scripts (special skills)
SKIP_SKILLS = [
    "adk-deployment-specialist",
    "gcp-examples-expert",
    "genkit-production-expert",
    "vertex-engine-inspector",
    "validator-expert",
    "memory",
    "adk-infra-expert",
    "genkit-infra-expert",
    "vertex-infra-expert",
    "adk-agent-builder",
    "vertex-agent-builder"
]

def find_skill_path(skill_name: str, base_path: str = "/home/jeremy/000-projects/claude-code-plugins") -> Path:
    """Find the path to a skill directory."""
    for skill_file in Path(base_path).rglob('SKILL.md'):
        if skill_file.parent.name == skill_name:
            return skill_file.parent
    return None

def get_todo_items(readme_path: Path) -> List[str]:
    """Extract TODO items from README.md."""
    todos = []
    if readme_path.exists():
        content = readme_path.read_text()
        for line in content.split('\n'):
            if line.strip().startswith('- [ ]'):
                todos.append(line.strip())
    return todos

def create_fix_plan() -> Dict:
    """Create a plan for fixing remaining skills."""
    plan = {
        "total_skills": sum(len(skills) for skills in PRIORITY_SKILLS.values()),
        "categories": {},
        "estimated_scripts": 0
    }

    for category, skills in PRIORITY_SKILLS.items():
        category_info = {
            "skills": [],
            "total_scripts_needed": 0
        }

        for skill_name in skills:
            skill_path = find_skill_path(skill_name)
            if skill_path:
                readme_path = skill_path / "scripts" / "README.md"
                todos = get_todo_items(readme_path)

                skill_info = {
                    "name": skill_name,
                    "path": str(skill_path),
                    "scripts_needed": len(todos),
                    "todos": todos
                }

                category_info["skills"].append(skill_info)
                category_info["total_scripts_needed"] += len(todos)
                plan["estimated_scripts"] += len(todos)

        plan["categories"][category] = category_info

    return plan

def main():
    """Main function to coordinate the fix process."""
    print("🔧 Planning fixes for remaining skills with issues...\n")

    # Create fix plan
    plan = create_fix_plan()

    # Display plan
    print(f"📊 Fix Plan Summary")
    print(f"=" * 50)
    print(f"Total skills to fix: {plan['total_skills']}")
    print(f"Estimated scripts needed: {plan['estimated_scripts']}")
    print()

    # Show breakdown by category
    for category, info in plan["categories"].items():
        print(f"\n📁 {category.replace('-', ' ').title()}")
        print(f"  Skills: {len(info['skills'])}")
        print(f"  Scripts needed: {info['total_scripts_needed']}")

        for skill in info["skills"]:
            print(f"    • {skill['name']}: {skill['scripts_needed']} scripts")

    # Save plan to JSON for processing
    plan_file = Path("/tmp/remaining_skills_fix_plan.json")
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2)

    print(f"\n💾 Fix plan saved to: {plan_file}")
    print("\n📝 Next Steps:")
    print("1. Review the plan above")
    print("2. Run fix-remaining-skills.sh to execute fixes")
    print("3. Use parallel agents for faster processing")
    print("4. Validate all fixes with audit script")

    # Show priority order
    print("\n🎯 Recommended Priority Order:")
    print("1. Excel Skills (4) - Business critical, completely empty")
    print("2. Database Skills (5) - Core functionality")
    print("3. DevOps Skills (11) - High visibility")
    print("4. AI/ML Skills (2) - Important for ML users")
    print("5. Other Skills (21) - Lower priority")

    return 0

if __name__ == "__main__":
    sys.exit(main())