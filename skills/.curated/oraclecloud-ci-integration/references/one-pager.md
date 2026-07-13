# oraclecloud-ci-integration — One-Pager

Configure CI/CD pipelines for OCI with Terraform and GitHub Actions, including known bug workarounds.

## The Problem

OCI Terraform provider crashes, ResourcePrincipal forces the wrong region (#1761), and CI auth requires either API keys in secrets or OIDC federation. Most teams waste days debugging provider crashes and auth failures that stem from these known issues. The OCI CLI setup in CI is also non-trivial — you need to reconstruct the config file and private key from secrets on every run.

## The Solution

This skill provides working GitHub Actions + Terraform patterns with the known bug workarounds baked in. It covers API key secret management, explicit region configuration to dodge the ResourcePrincipal bug, OCI CLI setup in CI runners, and Python SDK test patterns with proper mocking so your unit tests never hit real OCI endpoints.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and developers running OCI infrastructure as code in CI/CD pipelines |
| **What** | GitHub Actions workflow with OCI auth, Terraform provider config with region bug workaround, CLI setup, and SDK test mocks |
| **When** | Setting up a new CI pipeline for OCI, debugging Terraform provider crashes, or adding OCI integration tests |

## Key Features

1. **API key auth in CI** — Secure secret management pattern for OCI credentials in GitHub Actions
2. **Terraform region workaround** — Explicit region config to avoid ResourcePrincipal bug #1761
3. **SDK test mocking** — Unit test pattern using `unittest.mock` against `oci.core.ComputeClient`

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
