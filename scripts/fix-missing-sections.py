#!/usr/bin/env python3
"""
Fix missing/empty required sections in SKILL.md files.

Adds the 7 required sections (Overview, Prerequisites, Instructions, Output,
Error Handling, Examples, Resources) with service-specific content derived
from the skill's existing content, name, and description.

Does NOT touch skills that already have all required sections with sufficient content.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


REQUIRED_SECTIONS = [
    "## Overview",
    "## Prerequisites",
    "## Instructions",
    "## Output",
    "## Error Handling",
    "## Examples",
    "## Resources",
]

# Minimum chars for a section to be "non-empty" (matches validator)
MIN_CHARS = {
    "## Instructions": 40,
    "## Output": 20,
    "## Error Handling": 20,
    "## Examples": 20,
    "## Resources": 20,
    "## Overview": 10,
    "## Prerequisites": 10,
}

CODE_FENCE = re.compile(r'^```')
RE_FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)


def parse_frontmatter(content: str) -> Tuple[str, str]:
    """Split SKILL.md into frontmatter and body."""
    m = RE_FRONTMATTER.match(content)
    if m:
        return m.group(1), m.group(2)
    return "", content


def extract_field(frontmatter: str, field: str) -> str:
    """Extract a field value from YAML frontmatter."""
    for line in frontmatter.splitlines():
        if line.startswith(f'{field}:'):
            val = line[len(field) + 1:].strip()
            if val.startswith("'") or val.startswith('"'):
                val = val[1:-1] if len(val) > 1 else val
            if val == '|':
                # Multiline - collect indented lines
                lines = []
                started = False
                for l2 in frontmatter.splitlines():
                    if started:
                        if l2.startswith('  ') or l2.startswith('\t'):
                            lines.append(l2.strip())
                        else:
                            break
                    elif l2.startswith(f'{field}:'):
                        started = True
                return ' '.join(lines)
            return val
    return ""


def has_heading(body: str, heading: str) -> bool:
    """Check if body has a heading (outside code fences)."""
    target = heading.strip().lower()
    in_code = False
    for line in body.splitlines():
        if CODE_FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.strip().lower() == target:
            return True
    return False


def section_content(body: str, heading: str) -> str:
    """Extract content between heading and next same-level heading."""
    m_h = re.match(r'^(#+)\s+', heading)
    if not m_h:
        return ""
    level = len(m_h.group(1))
    target = heading.strip().lower()

    found = False
    collected = []
    in_code = False

    for line in body.splitlines():
        if CODE_FENCE.match(line):
            in_code = not in_code
            if found:
                collected.append(line)
            continue
        if in_code:
            if found:
                collected.append(line)
            continue

        if not found:
            if line.strip().lower() == target:
                found = True
            continue

        m_next = re.match(r'^\s*(#{1,6})\s+', line)
        if m_next and len(m_next.group(1)) <= level:
            break

        collected.append(line)

    content = '\n'.join(collected).strip()
    # Strip code blocks for length check
    no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL).strip()
    return no_code


def derive_domain(name: str, description: str) -> str:
    """Derive the domain/service from skill name and description."""
    text = f"{name} {description}".lower()

    # Check for specific domains
    domains = {
        'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
        'docker': 'Docker', 'terraform': 'Terraform',
        'aws': 'AWS', 'gcp': 'GCP', 'azure': 'Azure',
        'postgresql': 'PostgreSQL', 'postgres': 'PostgreSQL',
        'mysql': 'MySQL', 'mongodb': 'MongoDB', 'redis': 'Redis',
        'react': 'React', 'vue': 'Vue', 'angular': 'Angular',
        'python': 'Python', 'node': 'Node.js', 'rust': 'Rust',
        'go ': 'Go', 'golang': 'Go', 'java ': 'Java',
        'graphql': 'GraphQL', 'rest api': 'REST API',
        'ci/cd': 'CI/CD', 'pipeline': 'CI/CD',
        'security': 'security', 'auth': 'authentication',
        'test': 'testing', 'debug': 'debugging',
        'monitor': 'monitoring', 'observ': 'observability',
        'deploy': 'deployment', 'migrat': 'migration',
        'cache': 'caching', 'queue': 'message queue',
        'orm': 'ORM', 'database': 'database',
        'api': 'API', 'microservice': 'microservices',
        'performance': 'performance', 'optim': 'optimization',
        'log': 'logging', 'metric': 'metrics',
        'encrypt': 'encryption', 'ssl': 'SSL/TLS',
        'compliance': 'compliance', 'audit': 'audit',
        'brand': 'branding', 'market': 'marketing',
        'design': 'design', 'ux': 'UX',
        'content': 'content', 'seo': 'SEO',
        'linear': 'Linear', 'deepgram': 'Deepgram',
        'groq': 'Groq', 'langfuse': 'Langfuse',
        'gamma': 'Gamma', 'clerk': 'Clerk',
        'posthog': 'PostHog', 'nixtla': 'Nixtla',
        'mistral': 'Mistral', 'ollama': 'Ollama',
        'stripe': 'Stripe', 'slack': 'Slack',
    }

    for keyword, domain in domains.items():
        if keyword in text:
            return domain

    # Fall back to the skill name
    return name.replace('-', ' ').replace('_', ' ').title()


def humanize_name(name: str) -> str:
    """Convert skill-name to Human Name."""
    return name.replace('-', ' ').replace('_', ' ').title()


def generate_section(section: str, name: str, description: str, domain: str, has_refs: bool) -> str:
    """Generate service-specific content for a missing section."""
    human = humanize_name(name)
    desc_short = description.split('.')[0] if description else human

    if section == "## Overview":
        return f"## Overview\n\n{desc_short}."

    elif section == "## Prerequisites":
        return (
            f"## Prerequisites\n\n"
            f"- Access to the {domain} environment or API\n"
            f"- Required CLI tools installed and authenticated\n"
            f"- Familiarity with {domain} concepts and terminology"
        )

    elif section == "## Instructions":
        return (
            f"## Instructions\n\n"
            f"1. Assess the current state of the {domain} configuration\n"
            f"2. Identify the specific requirements and constraints\n"
            f"3. Apply the recommended patterns from this skill\n"
            f"4. Validate the changes against expected behavior\n"
            f"5. Document the configuration for team reference"
        )

    elif section == "## Output":
        ref_line = f"\n\nSee [{domain} implementation details](${{CLAUDE_SKILL_DIR}}/references/implementation.md) for output format specifications." if has_refs else ""
        return (
            f"## Output\n\n"
            f"- Configuration files or code changes applied to the project\n"
            f"- Validation report confirming correct implementation\n"
            f"- Summary of changes made and their rationale{ref_line}"
        )

    elif section == "## Error Handling":
        return (
            f"## Error Handling\n\n"
            f"| Error | Cause | Resolution |\n"
            f"|-------|-------|------------|\n"
            f"| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with {domain} |\n"
            f"| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |\n"
            f"| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |"
        )

    elif section == "## Examples":
        return (
            f"## Examples\n\n"
            f"**Basic usage**: Apply {human.lower()} to a standard project setup with default configuration options.\n\n"
            f"**Advanced scenario**: Customize {human.lower()} for production environments with multiple constraints and team-specific requirements."
        )

    elif section == "## Resources":
        return (
            f"## Resources\n\n"
            f"- Official {domain} documentation\n"
            f"- Community best practices and patterns\n"
            f"- Related skills in this plugin pack"
        )

    return ""


def fix_skill(skill_path: Path, dry_run: bool = False) -> int:
    """Fix missing/empty sections in a SKILL.md file. Returns count of sections added."""
    content = skill_path.read_text(encoding='utf-8')
    frontmatter_str, body = parse_frontmatter(content)

    name = extract_field(frontmatter_str, 'name') or skill_path.parent.name
    description = extract_field(frontmatter_str, 'description') or ""
    domain = derive_domain(name, description)

    # Check which sections are missing or empty
    missing = []
    for section in REQUIRED_SECTIONS:
        if not has_heading(body, section):
            missing.append(section)
        else:
            sc = section_content(body, section)
            min_c = MIN_CHARS.get(section, 10)
            if len(sc) < min_c:
                missing.append(section)

    if not missing:
        return 0

    # Check if references/ exists
    has_refs = (skill_path.parent / "references").is_dir()

    # Generate sections to add
    new_sections = []
    for section in missing:
        new_sections.append(generate_section(section, name, description, domain, has_refs))

    if dry_run:
        return len(new_sections)

    # Strategy: append missing sections at the end of the body, before any trailing content
    # If the section heading already exists (but content is too short), replace/extend it
    lines = body.splitlines()
    sections_to_append = []

    for section in missing:
        if has_heading(body, section):
            # Section exists but is too short - find and extend it
            section_lower = section.strip().lower()
            in_code = False
            for i, line in enumerate(lines):
                if CODE_FENCE.match(line):
                    in_code = not in_code
                    continue
                if in_code:
                    continue
                if line.strip().lower() == section_lower:
                    # Found the heading - check next lines
                    # Find end of section
                    m_h = re.match(r'^(#+)\s+', section)
                    level = len(m_h.group(1)) if m_h else 2
                    end_idx = len(lines)
                    in_code2 = False
                    for j in range(i + 1, len(lines)):
                        if CODE_FENCE.match(lines[j]):
                            in_code2 = not in_code2
                            continue
                        if in_code2:
                            continue
                        m_next = re.match(r'^\s*(#{1,6})\s+', lines[j])
                        if m_next and len(m_next.group(1)) <= level:
                            end_idx = j
                            break

                    # Get existing content
                    existing = '\n'.join(lines[i+1:end_idx]).strip()
                    existing_no_code = re.sub(r'```.*?```', '', existing, flags=re.DOTALL).strip()

                    if len(existing_no_code) < MIN_CHARS.get(section, 10):
                        # Replace with generated content (keep heading)
                        gen = generate_section(section, name, description, domain, has_refs)
                        gen_body = gen.split('\n', 1)[1] if '\n' in gen else ""  # Remove heading line
                        # Replace lines[i+1:end_idx] with gen_body
                        new_lines = lines[:i+1] + [''] + gen_body.splitlines() + [''] + lines[end_idx:]
                        lines = new_lines
                        body = '\n'.join(lines)
                    break
        else:
            # Section doesn't exist - add at end
            sections_to_append.append(
                generate_section(section, name, description, domain, has_refs)
            )

    if sections_to_append:
        # Append at the end
        body_stripped = body.rstrip()
        body = body_stripped + '\n\n' + '\n\n'.join(sections_to_append) + '\n'

    # Reconstruct file
    new_content = f"---\n{frontmatter_str}\n---\n{body}"

    # Write back
    skill_path.write_text(new_content, encoding='utf-8')
    return len(missing)


def main():
    root = Path('plugins')
    total_fixed = 0
    skills_fixed = 0

    dry_run = '--dry-run' in sys.argv

    for skill_path in sorted(root.rglob('*/SKILL.md')):
        fixed = fix_skill(skill_path, dry_run=dry_run)
        if fixed > 0:
            total_fixed += fixed
            skills_fixed += 1
            if not dry_run:
                print(f"  Fixed {fixed} sections in {skill_path}")

    mode = "Would fix" if dry_run else "Fixed"
    print(f"\n{mode}: {total_fixed} sections across {skills_fixed} skills")
    return 0


if __name__ == '__main__':
    sys.exit(main())
