---
name: Creating Ansible Playbooks
description: |
  This skill creates Ansible playbooks for automating configuration management tasks. It generates production-ready, multi-platform playbooks based on user-defined requirements, incorporating best practices and a security-first approach. Use this skill when you need to automate server configurations, software deployments, or infrastructure management using Ansible. Trigger this skill by requesting "Ansible playbook," specifying configuration details, or asking for automation of a particular setup.
---

## Overview

This skill empowers Claude to generate Ansible playbooks, streamlining infrastructure automation. It takes your specifications and translates them into executable Ansible code, allowing for repeatable and reliable deployments.

## How It Works

1. **Receiving User Request**: Claude receives the user's request for an Ansible playbook, including details about the desired configuration.
2. **Generating Playbook**: Based on the user's input, Claude utilizes the `ansible-playbook-creator` plugin to generate a complete Ansible playbook.
3. **Presenting the Playbook**: Claude presents the generated Ansible playbook to the user for review and execution.

## When to Use This Skill

This skill activates when you need to:
- Automate server configuration management tasks.
- Deploy applications across multiple servers consistently.
- Create repeatable and reliable infrastructure setups.

## Examples

### Example 1: Setting up a web server

User request: "Create an Ansible playbook to install and configure Apache on Ubuntu servers."

The skill will:
1. Generate an Ansible playbook that installs the Apache web server and configures it with a default virtual host.
2. Present the playbook to the user, ready for execution against Ubuntu servers.

### Example 2: Deploying a Docker container

User request: "Generate an Ansible playbook to deploy a Docker container running Nginx on CentOS servers."

The skill will:
1. Generate an Ansible playbook that installs Docker, pulls the Nginx image, and runs it as a container on CentOS servers.
2. Provide the playbook to the user for immediate deployment.

## Best Practices

- **Specificity**: Provide detailed requirements for the desired configuration to generate accurate playbooks.
- **Security**: Review the generated playbooks for security best practices before deploying them in production.
- **Testing**: Always test generated playbooks in a staging environment before applying them to production servers.

## Integration

This skill integrates with Claude's core capabilities by providing a specialized tool for Ansible playbook creation. It enhances Claude's ability to assist with DevOps tasks and infrastructure automation.