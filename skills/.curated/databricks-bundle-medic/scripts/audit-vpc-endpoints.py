#!/usr/bin/env python3
"""audit-vpc-endpoints.py — detect the PrivateLink cost-leak: a Databricks data-plane
VPC missing the S3 / STS / Kinesis VPC endpoints, so that traffic still traverses the
NAT gateway and racks up NAT-processing + cross-AZ transfer charges (bundle-medic, D9).

Pain D9: enabling PrivateLink for the Databricks CONTROL plane is mistaken for "all
traffic is private now." It is not — the DATA plane still calls S3 (DBFS/Delta), STS
(credential vending), and Kinesis (logs) constantly, and without per-service VPC
endpoints those calls go out through the NAT gateway, billed twice (NAT data-processing
$/GB + cross-AZ data-transfer $/GB). The fix is a Gateway endpoint for S3 (free) and
Interface endpoints for STS and Kinesis (hourly + $/GB, far cheaper than NAT at volume).

This script audits which of the three required endpoints exist and emits the remediation
Terraform for the missing ones. Deterministic — the "which endpoints are present"
decision is data, not judgement.

Usage:
  audit-vpc-endpoints.py --present s3            # only S3 gateway exists → STS+Kinesis leak
  audit-vpc-endpoints.py --present s3,sts,kinesis  # all good
  audit-vpc-endpoints.py --present "" --vpc-id vpc-123 --region us-east-1 --emit-terraform
Exit: 0 no leak · 1 leak found (missing endpoints) · 2 bad usage.
"""

import argparse
import sys

# The three services the Databricks data plane calls that MUST have their own VPC
# endpoint, or they leak through the NAT. Gateway endpoints are free; Interface
# endpoints cost an hourly + per-GB fee but undercut NAT at any real volume.
REQUIRED = {
    "s3": {
        "endpoint_type": "Gateway",
        "why": "DBFS/Delta object I/O — the highest-volume data-plane call",
        "cost_without": "NAT data-processing $/GB + cross-AZ transfer on every object read/write",
        "endpoint_cost": "free (Gateway endpoints have no hourly or per-GB charge)",
        "tf": """resource "aws_vpc_endpoint" "s3" {
  vpc_id            = "{vpc_id}"
  service_name      = "com.amazonaws.{region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [] # <-- fill: the data-plane subnets' route table ids
}""",
    },
    "sts": {
        "endpoint_type": "Interface",
        "why": "IAM credential vending for cluster instance profiles",
        "cost_without": "NAT data-processing on every credential refresh",
        "endpoint_cost": "hourly per-AZ + $/GB (far below NAT at volume)",
        "tf": """resource "aws_vpc_endpoint" "sts" {
  vpc_id              = "{vpc_id}"
  service_name        = "com.amazonaws.{region}.sts"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = [] # <-- fill: the data-plane subnet ids
  security_group_ids  = [] # <-- fill: an SG allowing 443 from the data-plane subnets
}""",
    },
    "kinesis": {
        "endpoint_type": "Interface",
        "why": "cluster/driver log delivery (kinesis-streams)",
        "cost_without": "NAT data-processing on continuous log shipping",
        "endpoint_cost": "hourly per-AZ + $/GB (far below NAT at volume)",
        "tf": """resource "aws_vpc_endpoint" "kinesis_streams" {
  vpc_id              = "{vpc_id}"
  service_name        = "com.amazonaws.{region}.kinesis-streams"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = [] # <-- fill: the data-plane subnet ids
  security_group_ids  = [] # <-- fill: an SG allowing 443 from the data-plane subnets
}""",
    },
}


def audit_endpoints(present):
    """Given the set of services that already have an endpoint, return
    {ok, missing, leaks}. Pure. `missing` is the ordered list of service keys with no
    endpoint; `leaks` is the human-readable finding per missing service."""
    present_set = {s.strip().lower() for s in present if s and s.strip()}
    missing = [svc for svc in REQUIRED if svc not in present_set]
    leaks = []
    for svc in missing:
        spec = REQUIRED[svc]
        leaks.append(
            f"{svc.upper()} has NO {spec['endpoint_type']} endpoint → {spec['why']}; "
            f"cost leak: {spec['cost_without']} (fix cost: {spec['endpoint_cost']})"
        )
    return {"ok": not missing, "missing": missing, "leaks": leaks}


def remediation_terraform(missing, vpc_id, region):
    """Render the Terraform for the missing endpoints. Pure."""
    vpc_id = vpc_id or "vpc-XXXX"
    region = region or "REGION"
    blocks = [REQUIRED[svc]["tf"].replace("{vpc_id}", vpc_id).replace("{region}", region) for svc in missing]
    return "\n\n".join(blocks)


def main():
    ap = argparse.ArgumentParser(
        description="Audit a Databricks data-plane VPC for missing S3/STS/Kinesis endpoints (D9)"
    )
    ap.add_argument(
        "--present", default="", help="comma-separated services that already have endpoints (s3,sts,kinesis)"
    )
    ap.add_argument("--vpc-id", default="", help="VPC id for the remediation Terraform")
    ap.add_argument("--region", default="", help="AWS region for the remediation Terraform")
    ap.add_argument("--emit-terraform", action="store_true", help="print remediation Terraform for missing endpoints")
    args = ap.parse_args()

    present = args.present.split(",") if args.present else []
    result = audit_endpoints(present)

    if result["ok"]:
        print("SAFE: S3, STS, and Kinesis all have VPC endpoints — no NAT cost leak from these.")
        return 0

    print(f"COST LEAK: {len(result['missing'])} of 3 required data-plane endpoints missing.\n")
    for leak in result["leaks"]:
        print(f"  - {leak}")
    print(
        "\nPrivateLink covers the CONTROL plane only; these DATA-plane calls leak through "
        "the NAT until each has its own endpoint (S3=Gateway/free, STS+Kinesis=Interface)."
    )
    if args.emit_terraform:
        print("\n# --- remediation Terraform (fill the subnet/route-table/SG ids) ---\n")
        print(remediation_terraform(result["missing"], args.vpc_id, args.region))
    return 1


if __name__ == "__main__":
    sys.exit(main())
