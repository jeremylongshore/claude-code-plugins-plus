# The PrivateLink Cost-Leak Map

Enabling **Databricks PrivateLink** privatizes the workspace's control-plane
connection and is routinely mistaken for "all traffic is private now." It is not.
The compute plane still calls three AWS regional services on the data path —
**S3, STS, Kinesis** — and without their own VPC endpoints those calls fall
through to the public regional endpoints, which in a private-subnet deployment
means they exit through the **NAT gateway**. The bill arrives with no errors and
no failed jobs: just NAT data-processing and cross-AZ data-transfer charges that
scale with every gigabyte of Delta I/O.

This map itemizes what PrivateLink covers, which services leak, the two AWS bill
line items the leak produces, and the per-service endpoint fix. Primarily AWS,
with Azure Private Link / GCP Private Service Connect deltas where the equivalent
trap exists. The companion detector is `scripts/audit-vpc-endpoints.py`.

## What Databricks PrivateLink actually covers

Classic-plane PrivateLink has two connection types, and each covers a
compute-plane ↔ control-plane path — never the data-plane egress to AWS regional
services.

- **Front-end (user → workspace).** Users and BI tools reach the workspace web
  UI and REST API over an interface VPC endpoint into the Databricks control
  plane, instead of the public internet.
- **Back-end (compute plane → control plane).** Two sub-connections: the
  workspace/REST API connection, and the **secure cluster connectivity (SCC)
  relay** connection — the relay clusters use to call home without public IPs.

What that buys you, and what it does not:

| Traffic path | Covered by PrivateLink? | Endpoint that carries it |
| --- | --- | --- |
| User/BI → workspace web app + REST API | Yes (front-end) | Interface endpoint → Databricks control plane |
| Compute plane → control plane REST API | Yes (back-end) | Interface endpoint → Databricks control plane |
| Compute plane → SCC relay | Yes (back-end) | Interface endpoint → Databricks SCC relay |
| Compute plane → **S3** (DBFS, Delta data + logs) | **No** | NAT gateway → public S3 endpoint (until fixed) |
| Compute plane → **STS** (credential vending) | **No** | NAT gateway → public STS endpoint (until fixed) |
| Compute plane → **Kinesis** (internal telemetry) | **No** | NAT gateway → public Kinesis endpoint (until fixed) |

The mental model: PrivateLink privatizes the *Databricks* connections. S3/STS/
Kinesis are *AWS* services Databricks depends on, and each needs its own VPC
endpoint. Nothing in the Databricks console tells you they are missing.

## The leak — how data-plane calls reach the NAT

A PrivateLink deployment puts the compute plane in **private subnets** with no
public IPs. Anything those subnets need from the public internet — including the
public AWS regional service endpoints — routes through a **NAT gateway** to an
internet gateway. The three data-plane callers:

- **S3 — the workhorse.** Every Delta read/write is an S3 `GET`/`PUT`/`LIST`:
  DBFS root, Unity Catalog managed and external table data, Delta transaction
  logs, cluster log delivery, init scripts, and library downloads. This is the
  highest-volume, highest-cost caller by a wide margin — it scales directly with
  data processed.
- **STS — credential vending.** AWS Security Token Service issues the temporary
  credentials the compute plane runs on: UC credential vending, instance-profile
  refresh, and `sts:AssumeRole` for cross-account access. Small payloads, but
  constant token refresh keeps it chatty.
- **Kinesis — internal telemetry.** Databricks streams internal logs and
  telemetry to a Databricks-managed Kinesis stream in the workspace region.
  Background-constant, low-to-moderate volume.

Without endpoints, all three resolve to public regional hostnames
(`s3.<region>.amazonaws.com`, `sts.<region>.amazonaws.com`,
`kinesis.<region>.amazonaws.com`) and the only route out of the private subnet is
the NAT. Same-region S3↔EC2 transfer is normally **free** — routing it through a
NAT converts free bytes into paid, NAT-processed bytes. That inversion is the
core of the leak.

## The two cost lines

The leak shows up as exactly two line items on the AWS bill, both per-GB, both
additive to the NAT's hourly charge:

- **NAT gateway data processing — `$/GB` on every byte through the NAT.** Charged
  regardless of direction, on top of the NAT hourly rate. Every S3/STS/Kinesis
  byte the compute plane moves is billed here (~$0.045/GB *(verify)*). Because S3
  volume tracks data processed, this line grows with the workload and is the one
  that shocks the month-end review.
- **Cross-AZ data transfer — `$/GB` when traffic crosses AZ boundaries.** If the
  NAT gateway sits in a different AZ than the compute node (or the path otherwise
  crosses an AZ), EC2 cross-AZ data transfer is billed per-GB in each direction
  (~$0.01/GB per direction *(verify)*). Keeping traffic on the AWS backbone via
  an endpoint eliminates this entirely for the endpoint-served services.

The failure mode has a second face: after a security team **locks down egress**
(removes the `0.0.0.0/0` → NAT route per policy) without first adding the
endpoints, jobs stop with **S3 timeouts** — the NAT was the only path out, and
now there is none. Same missing-endpoint root cause, reliability symptom instead
of a cost symptom.

## Per-service leak and fix map

| AWS service | Why the data plane calls it | Cost without an endpoint (through NAT) | Endpoint type | Endpoint cost |
| --- | --- | --- | --- | --- |
| **S3** | DBFS root, UC Delta table reads/writes, Delta logs, cluster log delivery, init scripts, libraries — highest-volume caller | NAT data processing on every GB **plus** cross-AZ transfer; converts free same-region S3↔EC2 transfer into paid NAT bytes | **Gateway** VPC endpoint | **Free** — no hourly, no per-GB processing *(verify)* |
| **STS** | Temporary credential vending — UC credential vending, instance-profile / `AssumeRole` refresh | NAT data processing per GB + the NAT hourly; small payloads but constant refresh | **Interface** VPC endpoint (PrivateLink ENI) | Per-AZ hourly + per-GB processed (~$0.01/GB *(verify)*) — far below NAT's ~$0.045/GB *(verify)* |
| **Kinesis** | Databricks-managed internal log / telemetry stream in the workspace region | NAT data processing per GB, background-constant | **Interface** VPC endpoint | Per-AZ hourly + per-GB processed (~$0.01/GB *(verify)*) — far below NAT's ~$0.045/GB *(verify)* |

The asymmetry is the whole point: **S3 is both the biggest leak and the free
fix.** A gateway endpoint for S3 removes the largest cost line at zero endpoint
cost, so it is always the first move.

## The fix, service by service

- **S3 → Gateway VPC endpoint (free).** Gateway endpoints attach to **route
  tables**, not ENIs — you add the S3 prefix-list route to every private-subnet
  route table that carries compute-plane traffic. No hourly charge, no per-GB
  processing charge, and the traffic stays on the AWS backbone (no NAT, no
  cross-AZ). This is the single highest-ROI change in the map. Miss a route
  table and that subnet's S3 traffic silently keeps using the NAT — coverage is
  per-route-table, not per-VPC.
- **STS → Interface VPC endpoint.** Interface endpoints are ENIs in your
  subnets, billed per-AZ-hour plus per-GB processed. Enable **Private DNS** on
  the endpoint so `sts.<region>.amazonaws.com` resolves to the ENI without app
  changes, and make sure workloads use the **regional** STS endpoint, not the
  global `sts.amazonaws.com`. Place an endpoint in **each AZ** the compute plane
  runs in.
- **Kinesis → Interface VPC endpoint.** Same interface-endpoint model and same
  per-AZ placement rule. Point it at the workspace's region — the
  Databricks-managed stream is regional.

Interface endpoints cost money (unlike the S3 gateway), but their per-GB rate is
well under the NAT's, and they eliminate the cross-AZ line for the traffic they
carry. The net is still a large saving on any workspace moving real data volume.

## Detecting it — scripts/audit-vpc-endpoints.py

The detector `scripts/audit-vpc-endpoints.py` walks every VPC associated with a
Databricks workspace (via the Databricks Account API cross-referenced with the
AWS `Describe*` APIs) and emits a per-VPC checklist:

- S3 gateway endpoint present — yes/no
- STS interface endpoint present — yes/no
- Kinesis interface endpoint present — yes/no
- Route-table coverage — is the S3 prefix-list route attached to **every**
  compute-plane private subnet's route table, not just one
- Remediation Terraform for whatever is missing

Run it against every workspace, not just one — endpoint coverage is per-VPC and
per-route-table, and a multi-workspace account commonly has it right in one VPC
and leaking in the next. The check is static and deterministic, which is why the
skill ships it as a script rather than a hook or an interactive tool.

## Validating the fix (VPC Flow Logs)

Endpoints existing is not proof the traffic moved. Confirm with **VPC Flow
Logs**:

- After adding the endpoints, S3/STS/Kinesis traffic should **no longer** appear
  destined for the NAT gateway's ENI. Flow Logs showing continued NAT-bound S3
  traffic mean a route table was missed or Private DNS is not resolving.
- Watch NAT data-processing bytes on the NAT gateway's CloudWatch metrics drop
  after the change — that is the dollar line falling.
- Keep an **endpoint inventory doc** per workspace: which VPCs, which endpoints,
  which route tables. It is not visible from the Databricks console and is the
  first thing lost when the platform team turns over.

## Azure and GCP deltas

The same trap exists off-AWS; the service names and the "free vs paid endpoint"
split differ.

| Cloud | Control-plane private connectivity | Data-plane services that still leak | Free "gateway-equivalent" | Paid "interface-equivalent" |
| --- | --- | --- | --- | --- |
| **AWS** | PrivateLink (front-end + back-end) | S3, STS, Kinesis | S3 **gateway** endpoint (free) | STS/Kinesis **interface** endpoints |
| **Azure** | Azure **Private Link** (front-end + back-end) | ADLS Gen2, Key Vault, Event Hubs, DBFS root storage | VNet **Service Endpoints** (free, backbone-only) | **Private Endpoints** to ADLS Gen2 + Key Vault |
| **GCP** | **Private Service Connect** (front-end + back-end) | GCS, and other Google APIs on the data path | **Private Google Access** (no external IP needed) | PSC endpoints for the relevant Google APIs |

- **Azure.** Databricks Private Link covers the workspace ↔ control-plane path;
  the data plane still reaches ADLS Gen2, Key Vault, and Event Hubs. Azure NAT
  Gateway also bills per-GB data processing (~$0.045/GB *(verify)*), so the same
  cost inversion applies. Azure gives you two tools: **Service Endpoints** (free,
  the ADLS analog of the S3 gateway endpoint — keeps traffic on the Azure
  backbone with no per-GB charge) and **Private Endpoints** (paid, the analog of
  interface endpoints, with a private IP). Prefer Service Endpoints for storage
  cost, Private Endpoints where a private IP or on-prem reach is required.
- **GCP.** Databricks on GCP uses Private Service Connect for front-end and
  back-end. The data-plane equivalent is **Private Google Access** on the
  compute subnets so GCS and Google APIs are reachable without external IPs;
  GCP **Cloud NAT** likewise bills per-GB data processing (*(verify)*). The trap
  is real but less-documented here — GCP has the thinnest Databricks install
  base, so the endpoint inventory is even more likely to be missing.

## Version-accuracy anchors

Pricing and exact endpoint semantics drift — verify each of these against
current AWS/Azure/GCP docs and the customer's actual bill before quoting a
number:

- **NAT gateway data-processing rate** — cited here as ~$0.045/GB *(verify)*.
  Region-dependent; confirm against current AWS NAT Gateway pricing.
- **Cross-AZ data-transfer rate** — cited as ~$0.01/GB per direction *(verify)*.
  Confirm current EC2 data-transfer pricing.
- **Interface endpoint rate** — cited as ~$0.01/GB processed + a per-AZ hourly
  charge *(verify)*. Confirm current AWS PrivateLink (interface endpoint)
  pricing; the hourly is per-endpoint-per-AZ.
- **S3 gateway endpoint is free** — no hourly and no per-GB processing charge
  *(verify)* (true at time of writing; gateway endpoints exist only for S3 and
  DynamoDB).
- **STS regional vs global endpoint** — the fix depends on workloads using
  `sts.<region>.amazonaws.com`; confirm the deployment is not pinned to the
  global `sts.amazonaws.com` *(verify)*.
- **Azure NAT Gateway per-GB processing** — ~$0.045/GB *(verify)*; confirm
  against current Azure NAT Gateway pricing.
- **Azure Service Endpoint = free / Private Endpoint = paid** — verify the
  current split; Private Endpoint carries an hourly + per-GB charge *(verify)*.
- **GCP Cloud NAT per-GB processing** — *(verify)* against current Cloud NAT
  pricing; Private Google Access itself has no direct charge but confirm.
- **Service inventory (S3/STS/Kinesis)** — this is the documented AWS classic
  data-plane set; confirm Databricks has not added or renamed a required
  regional dependency for the workspace's release channel *(verify)*.

## Sources

- Databricks — Enable AWS PrivateLink (classic compute plane):
  <https://docs.databricks.com/aws/en/security/network/classic/privatelink>
- Databricks — Serverless network security / cost management:
  <https://docs.databricks.com/aws/en/security/network/serverless-network-security/cost-management>
- Databricks — Optimizing AWS S3 access from Databricks:
  <https://www.databricks.com/blog/optimizing-aws-s3-access-databricks>
- Databricks — Hardened connectivity / deployment architecture:
  <https://docs.databricks.com/aws/en/security/network/deployment-architecture/hardened-connectivity>
- Companion detector in this skill: `scripts/audit-vpc-endpoints.py`
