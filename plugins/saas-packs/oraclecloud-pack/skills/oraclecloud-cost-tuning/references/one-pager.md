# oraclecloud-cost-tuning — One-Pager

Track OCI spend with the Usage API and set up proactive budget alerts before Universal Credits run out.

## The Problem

OCI Universal Credits run out faster than expected because pricing varies by shape, region, and commitment level. The Cost Analysis tool in the console is buried and confusing. Teams get surprised by bills because they lack programmatic cost visibility and proactive alerting.

## The Solution

This skill uses the Usage API to track spend programmatically and set budget alerts before you're surprised. It covers cost queries by service, compartment, and SKU, budget creation with percentage-based alert rules, forecast-based overspend warnings, and optimization strategies including Always Free tier resources, preemptible instances for batch workloads, and reserved capacity commitments.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers, FinOps practitioners, and team leads managing OCI spending |
| **What** | Usage API queries, budget creation with 80%/95% alerts, forecast alerts, and cost optimization patterns (Always Free, preemptible, reserved) |
| **When** | Setting up cost monitoring for a new tenancy, investigating unexpected charges, or implementing FinOps practices for OCI |

## Key Features

1. **Usage API queries** — Cost breakdown by service, compartment, and SKU using `oci.usage_api.UsageapiClient`
2. **Budget alerts** — Percentage-based and forecast-based alert rules with email notification
3. **Optimization patterns** — Always Free tier, preemptible instances (50% savings), and reserved capacity guidance

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
