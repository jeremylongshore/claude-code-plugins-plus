# oraclecloud-security-basics — One-Pager

Master OCI IAM policy syntax, common policy patterns, and API key management.

## The Problem

OCI IAM policy syntax is the number one enterprise complaint. One wrong policy means locked out of your own resources. One missing verb and your automation silently fails with a `404 NotAuthorizedOrNotFound` that looks like a missing resource — because OCI returns the same error for "doesn't exist" and "no permission." This is the policy cheat sheet with tested patterns.

## The Solution

This skill provides the complete IAM reference: the four-verb hierarchy (inspect, read, use, manage), exact policy syntax with subject/verb/resource/location, six tested policy patterns (admin, read-only, compute-only, network-only, no-delete), resource family types, API key generation and upload, and ~/.oci/config setup with validation.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Cloud architects, DevOps engineers, and security teams configuring OCI access controls |
| **What** | Working IAM policies, API key pairs, and validated OCI config files |
| **When** | Setting up a new OCI tenancy, onboarding teams, debugging 404 permission errors, or auditing existing policies |

## Key Features

1. **Policy verb hierarchy** — Clear table showing inspect < read < use < manage with what each verb grants and when to use it
2. **Six tested policy patterns** — Copy-paste IAM policies for admin, read-only, compute-only, network-only, and delete-restricted scenarios
3. **API key lifecycle** — Key generation, public key upload, config file setup, and authentication verification

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
