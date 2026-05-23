# Oracle Cloud Infrastructure (OCI) — Company Brief

## Overview

Oracle Cloud Infrastructure is Oracle's IaaS/PaaS cloud platform competing with AWS, Azure, and GCP. Strengths: Always Free tier (ARM instances), Autonomous Database, competitive pricing. Weaknesses: capacity constraints, complex IAM, slow console UI, underdocumented APIs.

## Real Pain Points (sourced from community, reviews, GitHub)

| # | Pain Point | Source | Severity |
|---|-----------|--------|----------|
| 1 | "Out of host capacity" for ARM instances — users write browser automation to retry for HOURS | GitHub (4+ retry repos), Medium, Reddit | Critical |
| 2 | ~/.oci/config auth hell — "did not find a proper configuration for user", public vs private key confusion, fingerprint mismatches | Oracle SDK troubleshooting docs | Critical |
| 3 | IAM policy language is impenetrable — `Allow group X to manage Y in compartment Z where ...` syntax trips everyone | Community forums, PeerSpot reviews | High |
| 4 | SDK memory leaks — Instance/Resource Principal auth leaks ~10 MiB/hour from unreleased signer objects | Oracle known issues docs | High |
| 5 | SSL CERTIFICATE_VERIFY_FAILED — different fix per SDK (Python, Java, Go, TS, .NET, Ruby) | SDK troubleshooting docs | High |
| 6 | Timeout errors — different exception type per SDK, no unified handling | SDK troubleshooting docs | Medium |
| 7 | Console UI is unnavigable — slow, confusing, can't find things | PeerSpot, Capterra reviews | Medium |
| 8 | Terraform provider bugs — ResourcePrincipal forces primary region, null keyword handling, plugin crashes | GitHub issues | Medium |
| 9 | Pricing/credits confusion — Universal Credits run out unexpectedly, complex pricing model | Reviews, Finout analysis | Medium |
| 10 | Status page doesn't acknowledge outages — London region Jan 2026, users left guessing | The Register | Medium |
| 11 | Support is slow and unhelpful — "responds promptly but without impact" | TrustRadius, PeerSpot | Medium |
| 12 | Account closure takes weeks — hard to even find the option | Reviews | Low |

## Canonical SDK/URL Reference

### Python SDK

- Install: `pip install oci`
- Import: `import oci`
- Config load: `config = oci.config.from_file("~/.oci/config")`
- Compute client: `oci.core.ComputeClient(config)`
- Network client: `oci.core.VirtualNetworkClient(config)`
- Object Storage: `oci.object_storage.ObjectStorageClient(config)`
- Database: `oci.database.DatabaseClient(config)`
- Identity: `oci.identity.IdentityClient(config)`
- Monitoring: `oci.monitoring.MonitoringClient(config)`
- Events: `oci.events.EventsClient(config)`
- Notifications: `oci.ons.NotificationDataPlaneClient(config)`

### Auth Config File (~/.oci/config)

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaexample
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
tenancy=ocid1.tenancy.oc1..aaaaaaaexample
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

### OCI CLI

- Install: `bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"`
- Config setup: `oci setup config`
- Example: `oci compute instance list --compartment-id <OCID>`

### API Bases

- Compute: `https://iaas.{region}.oraclecloud.com/20160918/`
- Object Storage: `https://objectstorage.{region}.oraclecloud.com/n/{namespace}/`
- Identity: `https://identity.{region}.oraclecloud.com/20160918/`
- Database: `https://database.{region}.oraclecloud.com/20160918/`

### Canonical URLs

- Docs: https://docs.oracle.com/en-us/iaas/Content/
- API ref: https://docs.oracle.com/en-us/iaas/api/
- Python SDK ref: https://docs.oracle.com/en-us/iaas/tools/python/latest/
- CLI ref: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm
- Terraform: https://registry.terraform.io/providers/oracle/oci/latest/docs
- Console: https://cloud.oracle.com
- Status: https://ocistatus.oraclecloud.com
- Known issues: https://docs.oracle.com/en-us/iaas/Content/knownissues.htm
- SDK troubleshooting: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm
- Pricing: https://www.oracle.com/cloud/pricing/
- Always Free: https://www.oracle.com/cloud/free/

### Real Error Codes

- 401 NotAuthenticated — bad config/key
- 404 NotAuthorizedOrNotFound — IAM OR wrong OCID
- 429 TooManyRequests — rate limited (no Retry-After header)
- 500 InternalError — OCI service error
- ServiceError with status -1 — timeout
- CERTIFICATE_VERIFY_FAILED — SSL cert issue

## Key OCI Concepts

- **Compartments**: Logical grouping (like AWS accounts but nested, within a single tenancy)
- **OCIDs**: Oracle Cloud Identifiers (format: `ocid1.<resource_type>.oc1..<unique_id>`)
- **Tenancy**: Root compartment, top-level account
- **Availability Domains**: Data centers within a region (1-3 per region)
- **Fault Domains**: Logical groupings within an AD for HA
- **Shapes**: Instance types (e.g., VM.Standard.E5.Flex, VM.Standard.A1.Flex)
- **Security Lists**: Stateful firewall rules on subnets (legacy)
- **Network Security Groups (NSGs)**: Firewall rules on VNICs (preferred)
- **Dynamic Groups**: IAM groups for compute instances (like AWS instance profiles)
- **Pre-Authenticated Requests (PARs)**: Signed URLs for Object Storage

## Common Shapes

| Shape | Arch | Free? | Notes |
|-------|------|-------|-------|
| VM.Standard.A1.Flex | ARM | Yes (4 OCPU, 24GB) | Chronic capacity issues |
| VM.Standard.E5.Flex | AMD | No | Current gen |
| VM.Standard3.Flex | Intel | No | Previous gen |
| VM.Standard.E4.Flex | AMD | No | Still common |
| BM.Standard.E5.192 | AMD | No | Bare metal |
