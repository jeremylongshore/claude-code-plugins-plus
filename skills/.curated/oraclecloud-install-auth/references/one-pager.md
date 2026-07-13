# oraclecloud-install-auth — One-Pager

Install and configure OCI SDK and CLI authentication with API key signing.

## The Problem

OCI auth requires a 5-field config file (`~/.oci/config`) with RSA key pairs, OCIDs, and fingerprints. One wrong field produces the cryptic "did not find a proper configuration for user" error with no hint about which field failed. Public/private key confusion is the #1 onboarding blocker — pointing `key_file` to the public key instead of the private key silently fails. New users also miss the `chmod 600` requirement on both the config and key files.

## The Solution

This skill walks through the complete OCI authentication setup: generating an RSA key pair, computing the fingerprint, uploading the public key to the OCI Console, creating `~/.oci/config` with all five required fields, and verifying connectivity with both the Python SDK (`oci.config.from_file`) and the OCI CLI (`oci iam user get`). Includes a diagnostic validation script that checks all six common failure modes.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers and DevOps engineers starting their first OCI integration |
| **What** | Working `~/.oci/config` with RSA key pair, fingerprint verification, and connectivity proof via SDK and CLI |
| **When** | Setting up a new OCI account, onboarding a teammate, rotating API keys, or debugging auth failures |

## Key Features

1. **RSA key generation** — Complete OpenSSL commands for key pair and fingerprint extraction
2. **Config file creation** — All five required fields with explanations and common pitfalls
3. **Dual verification** — Test with both Python SDK and OCI CLI to confirm auth works
4. **Diagnostic script** — Automated checker that isolates which of the six auth failure modes you hit

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
