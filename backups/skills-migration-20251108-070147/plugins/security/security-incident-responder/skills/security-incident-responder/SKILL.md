---
name: responding-to-security-incidents
description: |
  Assists with security incident response, investigation, and remediation. This skill is triggered when the user requests help with incident response, mentions specific incident types (e.g., data breach, ransomware, DDoS), or uses terms like "incident response plan", "containment", "eradication", or "post-incident activity". It guides the user through the incident response lifecycle, from preparation to post-incident analysis. It is useful for classifying incidents, creating response playbooks, collecting evidence, constructing timelines, and generating remediation steps. Use this skill when needing to respond to a "security incident".
---

## Overview

This skill empowers Claude to guide you through the security incident response process, ensuring a structured and effective approach to handling security breaches and attacks. It helps you classify incidents, develop response strategies, gather crucial evidence, and implement remediation steps to minimize damage and prevent future occurrences.

## How It Works

1. **Incident Classification**: Analyzes the incident details to determine the type, severity, and scope of the security event.
2. **Playbook Generation**: Creates a tailored response playbook based on the incident classification, outlining the necessary steps for containment, eradication, and recovery.
3. **Evidence Gathering**: Provides guidance on collecting relevant logs, network data, and forensic evidence to support the investigation.
4. **Remediation Planning**: Develops a detailed plan for remediating the vulnerabilities exploited during the incident and restoring affected systems.

## When to Use This Skill

This skill activates when you need to:
- Respond to a suspected security breach or attack.
- Develop an incident response plan.
- Investigate a security incident and gather evidence.
- Remediate vulnerabilities exploited during a security incident.
- Generate a post-incident report and lessons learned.

## Examples

### Example 1: Responding to a Ransomware Attack

User request: "We've been hit with a ransomware attack. What should we do?"

The skill will:
1. Classify the incident as a ransomware attack.
2. Generate a response playbook including steps for containment (isolating affected systems), eradication (removing the ransomware), and recovery (restoring from backups).

### Example 2: Investigating a Data Breach

User request: "Investigate a potential data breach on our customer database."

The skill will:
1. Provide guidance on collecting evidence such as database logs, network traffic, and application logs.
2. Help construct a timeline of events to identify the attack vector and scope of the breach.

## Best Practices

- **Prioritization**: Focus on containing the incident first to prevent further damage.
- **Evidence Preservation**: Carefully preserve all evidence to support the investigation and potential legal action.
- **Communication**: Maintain clear and consistent communication with stakeholders throughout the incident response process.

## Integration

This skill can be integrated with other security tools and plugins to automate tasks such as vulnerability scanning, log analysis, and threat intelligence gathering. It can also be used in conjunction with project management tools to track incident response tasks and assign responsibilities.