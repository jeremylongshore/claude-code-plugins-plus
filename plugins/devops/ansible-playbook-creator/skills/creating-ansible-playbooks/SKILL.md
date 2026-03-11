---
name: creating-ansible-playbooks
description: |
  Execute use when you need to work with Ansible automation.
  This skill provides Ansible playbook creation with comprehensive guidance and automation.
  Trigger with phrases like "create Ansible playbook", "automate with Ansible",
  or "configure with Ansible".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(ansible:*), Bash(terraform:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Creating Ansible Playbooks

## Overview

Generate production-ready Ansible playbooks, roles, and inventories for infrastructure automation. Supports provisioning servers, deploying applications, configuring services, and enforcing desired state across fleets of machines using SSH-based agentless automation.

## Prerequisites

- Ansible 2.14+ installed (`ansible --version`)
- SSH access to target hosts with key-based authentication
- Python 3.9+ on control node and managed nodes
- Inventory of target hosts (IPs or hostnames)
- Privilege escalation credentials (sudo) if configuring system-level resources
- `ansible-lint` installed for playbook validation

## Instructions

1. Scan the project for existing Ansible files (`ansible.cfg`, `inventory/`, `roles/`, `group_vars/`) to understand current structure
2. Determine the automation target: server provisioning, application deployment, configuration management, or security hardening
3. Create the playbook YAML with proper structure: `hosts`, `become`, `vars`, `tasks`, `handlers`
4. Extract reusable logic into roles using the standard directory layout (`tasks/`, `handlers/`, `templates/`, `defaults/`, `vars/`, `meta/`)
5. Define variables in `group_vars/` and `host_vars/` for environment-specific values, keeping secrets in `vault`-encrypted files
6. Use Jinja2 templates for configuration files that vary across environments
7. Add handlers for service restarts triggered by configuration changes
8. Validate the playbook with `ansible-lint` and `ansible-playbook --check --diff` (dry run)
9. Test idempotency by running the playbook twice and confirming no changes on the second run

## Output

- Ansible playbooks (`.yml`) with structured tasks, handlers, and variables
- Role directories following Ansible Galaxy structure
- Jinja2 templates (`.j2`) for dynamic configuration files
- Inventory files (INI or YAML) with host groups
- `group_vars/` and `host_vars/` for environment separation
- `ansible.cfg` with connection and privilege escalation settings

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `unreachable: Failed to connect to host` | SSH connection failure or wrong host/port | Verify SSH keys, host IPs, and that port 22 is open with `ansible -m ping` |
| `permission denied` on become | Missing or incorrect sudo password | Add `--ask-become-pass` or configure `ansible_become_password` in vault |
| `undefined variable` | Variable not defined in vars, defaults, or inventory | Check variable precedence; define in `defaults/main.yml` or `group_vars/` |
| `ansible-lint: syntax-check failed` | YAML syntax error or deprecated module usage | Run `ansible-lint -v` and fix reported issues; replace deprecated modules |
| `changed` on every run (not idempotent) | Using `command`/`shell` without `creates`/`removes` guards | Add `creates:` parameter or switch to purpose-built modules (`copy`, `template`, `file`) |

## Examples

- "Create an Ansible playbook to provision an Ubuntu 22.04 server with Nginx, Certbot, and a firewall allowing only 80/443."
- "Generate a role that deploys a Python Flask app with Gunicorn, systemd service file, and log rotation."
- "Write an Ansible playbook to harden SSH config across all servers: disable root login, enforce key auth, set idle timeout."

## Resources

- Ansible documentation: https://docs.ansible.com/ansible/latest/
- Ansible Galaxy roles: https://galaxy.ansible.com/
- Ansible Lint rules: https://ansible.readthedocs.io/projects/lint/rules/
- Best practices guide: https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html
