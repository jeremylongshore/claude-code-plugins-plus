# oraclecloud-local-dev-loop — One-Pager

Set up a productive local OCI development workflow using CLI and SDK instead of the web console.

## The Problem

The OCI console is slow and unnavigable. Listing instances takes 5+ clicks through nested menus. Switching between compartments reloads the entire page. Finding an image OCID requires navigating three screens. Every common operation — launch, stop, list, upload — is faster from a terminal. But the OCI CLI has verbose syntax, no default compartment, and no built-in profile switching shortcut.

## The Solution

This skill sets up a productive local workflow that avoids the console entirely. Multi-profile `~/.oci/config` lets you switch between dev/staging/prod with a single alias. Shell aliases turn verbose OCI CLI commands into one-word shortcuts. A Python dev helper script provides health checks, resource listing, and profile-aware configuration. Environment variables via `.env` remove the need to pass compartment OCIDs on every command.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers and DevOps engineers who interact with OCI daily and want faster feedback |
| **What** | CLI profiles, shell aliases, env var management, Python dev helper, and project structure template |
| **When** | Setting up a new OCI project, onboarding a teammate, or migrating from console-only workflows |

## Key Features

1. **Multi-profile config** — Dev/staging/prod profiles with one-command switching via aliases
2. **Shell aliases** — One-word commands for instances, buckets, VCNs, and health checks
3. **Python dev helper** — Reusable script for listing resources and health checks with profile awareness
4. **Project template** — Standard directory structure with .env management and .gitignore

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
