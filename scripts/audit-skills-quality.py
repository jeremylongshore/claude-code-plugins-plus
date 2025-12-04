#!/usr/bin/env python3
"""
Audit skills for quality based on Anthropic's best practices
"""

import os
import re
from pathlib import Path
import json

def extract_frontmatter(content):
    """Extract YAML frontmatter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    frontmatter_str = match.group(1)
    frontmatter = {}
    current_key = None
    current_value = []

    for line in frontmatter_str.split('\n'):
        if ':' in line and not line.startswith(' '):
            if current_key:
                value = '\n'.join(current_value).strip()
                if value.startswith('|'):
                    value = value[1:].strip()
                frontmatter[current_key] = value

            key, val = line.split(':', 1)
            current_key = key.strip()
            current_value = [val.strip()] if val.strip() else []
        elif current_key and line.startswith(' '):
            current_value.append(line.strip())

    if current_key:
        value = '\n'.join(current_value).strip()
        if value.startswith('|'):
            value = value[1:].strip()
        frontmatter[current_key] = value

    return frontmatter

def analyze_description(description):
    """Analyze description quality"""
    issues = []
    score = 100

    if not description:
        return 0, ["No description provided"]

    # Check length
    if len(description) < 50:
        issues.append("Too short (< 50 chars)")
        score -= 20
    elif len(description) > 500:
        issues.append("Too long (> 500 chars)")
        score -= 10

    # Check for action verbs
    action_verbs = ['create', 'analyze', 'extract', 'generate', 'build', 'debug',
                    'optimize', 'validate', 'test', 'deploy', 'monitor', 'fix']
    has_action_verb = any(verb in description.lower() for verb in action_verbs)
    if not has_action_verb:
        issues.append("Missing action verbs")
        score -= 15

    # Check for trigger phrases
    trigger_patterns = ['use this', 'trigger', 'when', 'for']
    has_trigger = any(pattern in description.lower() for pattern in trigger_patterns)
    if not has_trigger:
        issues.append("Missing trigger guidance")
        score -= 15

    # Check for vague terms
    vague_terms = ['utilities', 'helper', 'tools', 'assists', 'handles']
    has_vague = any(term in description.lower() for term in vague_terms)
    if has_vague:
        issues.append("Contains vague terms")
        score -= 10

    return score, issues

def check_anthropic_compliance(frontmatter):
    """Check compliance with Anthropic's official spec"""
    issues = []

    # Required fields per Anthropic spec
    if 'name' not in frontmatter:
        issues.append("Missing required 'name' field")
    if 'description' not in frontmatter:
        issues.append("Missing required 'description' field")

    # Check for non-spec fields
    non_spec_fields = set(frontmatter.keys()) - {'name', 'description', 'license', 'allowed-tools', 'metadata'}
    for field in non_spec_fields:
        if field not in ['version', 'author', 'tags']:  # Common extras
            issues.append(f"Non-spec field: {field}")

    return issues

def check_structure(skill_dir, content):
    """Check for proper skill structure"""
    issues = []

    # Check for supplemental files
    skill_path = Path(skill_dir)
    has_scripts = (skill_path / 'scripts').exists()
    has_references = (skill_path / 'references').exists()
    has_assets = (skill_path / 'assets').exists()

    # Check SKILL.md length
    lines = content.count('\n')
    if lines > 800:  # ~5000 words
        issues.append(f"SKILL.md too long ({lines} lines)")
        if not has_references:
            issues.append("Consider using references/ for detailed docs")

    # Check for progressive disclosure
    if lines > 500 and not (has_references or has_scripts):
        issues.append("Large skill without supplemental files")

    return issues

def main():
    plugins_dir = Path(__file__).parent.parent / 'plugins'
    skill_files = list(plugins_dir.rglob('skills/*/SKILL.md'))

    print(f"🔍 SKILLS QUALITY AUDIT")
    print(f"{'=' * 70}\n")
    print(f"Found {len(skill_files)} skills to audit\n")

    stats = {
        'perfect': [],
        'good': [],
        'needs_work': [],
        'poor': [],
        'anthropic_compliant': [],
        'over_engineered': []
    }

    for skill_file in skill_files[:10]:  # Sample first 10 for detailed analysis
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter = extract_frontmatter(content)
        if not frontmatter:
            continue

        skill_name = frontmatter.get('name', 'unnamed')
        description = frontmatter.get('description', '')

        # Analyze description
        score, desc_issues = analyze_description(description)

        # Check Anthropic compliance
        compliance_issues = check_anthropic_compliance(frontmatter)

        # Check structure
        skill_dir = skill_file.parent
        struct_issues = check_structure(skill_dir, content)

        # Categorize
        if score >= 90 and not compliance_issues:
            stats['perfect'].append(skill_name)
            status = "✅ EXCELLENT"
        elif score >= 70:
            stats['good'].append(skill_name)
            status = "👍 GOOD"
        elif score >= 50:
            stats['needs_work'].append(skill_name)
            status = "⚠️ NEEDS WORK"
        else:
            stats['poor'].append(skill_name)
            status = "❌ POOR"

        if not compliance_issues:
            stats['anthropic_compliant'].append(skill_name)

        if 'version' in frontmatter or 'author' in frontmatter:
            stats['over_engineered'].append(skill_name)

        # Print details
        print(f"\n📦 {skill_name} - {status} (Score: {score}/100)")
        print(f"   Path: {skill_file.relative_to(plugins_dir)}")

        if desc_issues:
            print(f"   Description Issues:")
            for issue in desc_issues:
                print(f"     - {issue}")

        if compliance_issues:
            print(f"   Compliance Issues:")
            for issue in compliance_issues:
                print(f"     - {issue}")

        if struct_issues:
            print(f"   Structure Issues:")
            for issue in struct_issues:
                print(f"     - {issue}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 AUDIT SUMMARY (Sample of 10)")
    print(f"{'=' * 70}")
    print(f"✅ Excellent: {len(stats['perfect'])}")
    print(f"👍 Good: {len(stats['good'])}")
    print(f"⚠️  Needs Work: {len(stats['needs_work'])}")
    print(f"❌ Poor: {len(stats['poor'])}")
    print(f"\n📋 Compliance:")
    print(f"   Anthropic Compliant: {len(stats['anthropic_compliant'])}/10")
    print(f"   Over-engineered: {len(stats['over_engineered'])}/10")

    # Key recommendations
    print(f"\n🎯 KEY RECOMMENDATIONS:")
    print(f"1. Remove 'version' and 'author' fields (not in Anthropic spec)")
    print(f"2. Improve descriptions with action verbs and trigger phrases")
    print(f"3. Keep descriptions between 50-250 characters")
    print(f"4. Add references/ folders for skills with long SKILL.md files")
    print(f"5. Focus on 'name' and 'description' as primary fields")

if __name__ == '__main__':
    main()