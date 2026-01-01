#!/usr/bin/env python3
"""Generate README.md files for each skill category."""

import os
from pathlib import Path

SKILLS_DIR = Path("/home/jeremy/000-projects/claude-code-plugins/skills")

CATEGORY_DESCRIPTIONS = {
    "01-devops-basics": {
        "title": "DevOps Basics",
        "description": "Foundational DevOps skills covering CI/CD pipelines, containerization, infrastructure basics, and deployment workflows.",
        "tags": ["devops", "ci-cd", "docker", "kubernetes", "infrastructure"]
    },
    "02-devops-advanced": {
        "title": "DevOps Advanced",
        "description": "Advanced DevOps practices including GitOps, service mesh, observability, and multi-cloud orchestration.",
        "tags": ["devops", "gitops", "service-mesh", "observability", "multi-cloud"]
    },
    "03-security-fundamentals": {
        "title": "Security Fundamentals",
        "description": "Essential security skills covering authentication, authorization, encryption, and vulnerability scanning.",
        "tags": ["security", "authentication", "encryption", "vulnerability", "owasp"]
    },
    "04-security-advanced": {
        "title": "Security Advanced",
        "description": "Advanced security practices including zero-trust architecture, threat modeling, and security automation.",
        "tags": ["security", "zero-trust", "threat-modeling", "devsecops", "compliance"]
    },
    "05-frontend-dev": {
        "title": "Frontend Development",
        "description": "Modern frontend development skills covering React, Vue, performance optimization, and accessibility.",
        "tags": ["frontend", "react", "vue", "typescript", "accessibility"]
    },
    "06-backend-dev": {
        "title": "Backend Development",
        "description": "Backend development patterns including API design, database optimization, and microservices architecture.",
        "tags": ["backend", "api", "database", "microservices", "nodejs"]
    },
    "07-ml-training": {
        "title": "ML Training",
        "description": "Machine learning training workflows including data preprocessing, model training, and hyperparameter tuning.",
        "tags": ["ml", "training", "pytorch", "tensorflow", "data-science"]
    },
    "08-ml-deployment": {
        "title": "ML Deployment",
        "description": "ML model deployment and serving including MLOps, model monitoring, and inference optimization.",
        "tags": ["ml", "mlops", "deployment", "inference", "monitoring"]
    },
    "09-test-automation": {
        "title": "Test Automation",
        "description": "Test automation skills covering unit testing, integration testing, and end-to-end testing frameworks.",
        "tags": ["testing", "automation", "jest", "pytest", "cypress"]
    },
    "10-performance-testing": {
        "title": "Performance Testing",
        "description": "Performance testing and optimization including load testing, benchmarking, and profiling.",
        "tags": ["performance", "load-testing", "benchmarking", "profiling", "optimization"]
    },
    "11-data-pipelines": {
        "title": "Data Pipelines",
        "description": "Data pipeline development including ETL workflows, stream processing, and data orchestration.",
        "tags": ["data", "etl", "streaming", "airflow", "spark"]
    },
    "12-data-analytics": {
        "title": "Data Analytics",
        "description": "Data analytics and visualization skills including SQL, business intelligence, and reporting.",
        "tags": ["analytics", "sql", "bi", "visualization", "reporting"]
    },
    "13-aws-skills": {
        "title": "AWS Skills",
        "description": "Amazon Web Services skills covering compute, storage, networking, and managed services.",
        "tags": ["aws", "cloud", "lambda", "s3", "ec2"]
    },
    "14-gcp-skills": {
        "title": "GCP Skills",
        "description": "Google Cloud Platform skills covering compute, storage, BigQuery, Vertex AI, and Firebase.",
        "tags": ["gcp", "bigquery", "vertex-ai", "cloud-run", "firebase"]
    },
    "15-api-development": {
        "title": "API Development",
        "description": "API development skills including REST, GraphQL, OpenAPI, and API gateway patterns.",
        "tags": ["api", "rest", "graphql", "openapi", "gateway"]
    },
    "16-api-integration": {
        "title": "API Integration",
        "description": "API integration patterns including webhooks, OAuth, rate limiting, and error handling.",
        "tags": ["api", "integration", "webhooks", "oauth", "sdk"]
    },
    "17-technical-docs": {
        "title": "Technical Documentation",
        "description": "Technical documentation skills including API docs, README writing, and documentation systems.",
        "tags": ["docs", "technical-writing", "api-docs", "readme", "docusaurus"]
    },
    "18-visual-content": {
        "title": "Visual Content",
        "description": "Visual content creation including diagrams, screenshots, video tutorials, and design assets.",
        "tags": ["visual", "diagrams", "mermaid", "screenshots", "video"]
    },
    "19-business-automation": {
        "title": "Business Automation",
        "description": "Business process automation including workflow automation, reporting, and integrations.",
        "tags": ["automation", "workflow", "zapier", "n8n", "reporting"]
    },
    "20-enterprise-workflows": {
        "title": "Enterprise Workflows",
        "description": "Enterprise-grade workflow patterns including governance, compliance, and cross-team collaboration.",
        "tags": ["enterprise", "governance", "compliance", "workflow", "collaboration"]
    }
}

def get_skills_in_category(category_path: Path) -> list:
    """Get list of skills in a category."""
    skills = []
    for skill_dir in sorted(category_path.iterdir()):
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                skills.append(skill_dir.name)
    return skills

def generate_readme(category_id: str, info: dict, skills: list) -> str:
    """Generate README.md content for a category."""
    tags_str = ", ".join(f"`{tag}`" for tag in info["tags"])
    skills_list = "\n".join(f"- [{skill}](./{skill}/SKILL.md)" for skill in skills)

    return f"""# {info["title"]}

{info["description"]}

## Skills ({len(skills)})

{skills_list}

## Tags

{tags_str}

## Usage

These skills auto-activate when Claude Code detects relevant context in your conversation. Simply describe what you need, and the appropriate skill will engage.

## Installation

Skills are included with the Claude Code Plugins marketplace:

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

## License

MIT License - See individual skill files for details.
"""

def main():
    for category_dir in sorted(SKILLS_DIR.iterdir()):
        if not category_dir.is_dir():
            continue

        category_id = category_dir.name
        if category_id not in CATEGORY_DESCRIPTIONS:
            print(f"Warning: No description for {category_id}")
            continue

        info = CATEGORY_DESCRIPTIONS[category_id]
        skills = get_skills_in_category(category_dir)

        readme_content = generate_readme(category_id, info, skills)
        readme_path = category_dir / "README.md"
        readme_path.write_text(readme_content)
        print(f"Created {readme_path} ({len(skills)} skills)")

if __name__ == "__main__":
    main()
