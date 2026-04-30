---
name: oraclecloud-performance-tuning
description: 'Optimize OCI compute shapes, block volume tiers, and network throughput.

  Use when choosing instance shapes, configuring block volume performance, or benchmarking
  OCI infrastructure.

  Trigger with "oraclecloud performance", "oci shape comparison", "oci block volume
  iops", "oracle cloud performance tuning".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Performance Tuning

## Overview

Navigate OCI's opaque shape naming, block volume performance tiers, and shape-dependent network bandwidth. OCI shapes like `VM.Standard.E5.Flex`, `VM.Standard3.Flex`, and `VM.Standard.A1.Flex` look similar but have wildly different performance profiles. Block volume tiers (Balanced, Higher Performance, Ultra High Performance) have different IOPS and throughput limits that are easy to get wrong. This skill maps performance characteristics to shapes and storage tiers so you can make informed infrastructure decisions.

**Purpose:** Choose the right compute shape and storage tier for your workload by understanding OCI's performance characteristics, and monitor those resources programmatically.

## Prerequisites

- **OCI tenancy** with an API signing key in `~/.oci/config`
- **Python 3.8+** with `pip install oci`
- **Compartment OCID** for querying available shapes and metrics
- Basic understanding of IOPS, throughput, and OCPU concepts

## Instructions

### Step 1: Understand Shape Naming

OCI shape names encode processor generation, type, and flexibility:

| Shape | Processor | OCPUs | Network Gbps per OCPU | Best For |
|-------|-----------|-------|----------------------|----------|
| `VM.Standard.E5.Flex` | AMD EPYC 9J14 (Genoa) | 1–94 | 1 Gbps | General workloads (latest gen) |
| `VM.Standard.E4.Flex` | AMD EPYC 7J13 (Milan) | 1–64 | 1 Gbps | General workloads |
| `VM.Standard3.Flex` | Intel Xeon (Ice Lake) | 1–32 | 1 Gbps | Intel-optimized software |
| `VM.Standard.A1.Flex` | Ampere Altra (ARM) | 1–80 | 1 Gbps | ARM-native, cost-efficient |
| `VM.Optimized3.Flex` | Intel Xeon (Ice Lake) | 1–18 | 4 Gbps | HPC, network-intensive |
| `BM.Standard.E5.192` | AMD EPYC 9J14 | 192 | 100 Gbps total | Bare metal, full isolation |

**Key insight:** Flex shapes let you choose OCPU and memory independently. Memory defaults to 1 GB/OCPU min, 64 GB/OCPU max (varies by shape). Network bandwidth scales linearly with OCPUs up to the shape maximum.

### Step 2: Query Available Shapes

Discover what shapes are available in your tenancy and region:

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

shapes = compute.list_shapes(
    compartment_id="ocid1.compartment.oc1..example"
).data

for shape in shapes:
    print(
        f"{shape.shape}: "
        f"OCPUs={shape.ocpus or 'flex'}, "
        f"Memory={shape.memory_in_gbs or 'flex'} GB, "
        f"Network={shape.networking_bandwidth_in_gbps} Gbps"
    )
```

### Step 3: Block Volume Performance Tiers

OCI block volumes have three performance tiers. IOPS and throughput scale with volume size:

| Tier | IOPS / GB | Max IOPS | Throughput / GB | Max Throughput | Cost Multiplier |
|------|-----------|----------|-----------------|----------------|-----------------|
| **Balanced** | 60 | 25,000 | 480 KB/s | 480 MB/s | 1x (default) |
| **Higher Performance** | 75 | 35,000 | 600 KB/s | 480 MB/s | ~1.7x |
| **Ultra High Performance** | 90–225 | 300,000 | 720 KB/s–2.4 MB/s | 2.4 GB/s | ~3.3x+ |

**Example:** A 1 TB Balanced volume gets 25,000 IOPS and 480 MB/s throughput. The same 1 TB on Ultra High Performance gets up to 225,000 IOPS and 2.4 GB/s.

### Step 4: Create a Performance-Tuned Block Volume

```python
config = oci.config.from_file("~/.oci/config")
block_storage = oci.core.BlockstorageClient(config)

# Create a Higher Performance tier volume
volume = block_storage.create_volume(
    oci.core.models.CreateVolumeDetails(
        compartment_id="ocid1.compartment.oc1..example",
        availability_domain="Uocm:US-ASHBURN-AD-1",
        display_name="high-perf-data-vol",
        size_in_gbs=500,
        vpus_per_gb=20  # 10=Balanced, 20=Higher, 30-120=Ultra High
    )
).data

print(f"Volume created: {volume.id}")
print(f"Performance: {volume.vpus_per_gb} VPUs/GB")
```

The `vpus_per_gb` parameter controls the tier:
- `10` = Balanced (default)
- `20` = Higher Performance
- `30`–`120` = Ultra High Performance (scales IOPS linearly)

### Step 5: Monitor Performance Metrics

Query actual performance data from running instances and volumes:

```python
from datetime import datetime, timedelta

monitoring = oci.monitoring.MonitoringClient(config)

# Query disk IOPS for a specific instance
response = monitoring.summarize_metrics_data(
    compartment_id="ocid1.compartment.oc1..example",
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query='DiskIopsRead[5m].mean() + DiskIopsWritten[5m].mean()',
        start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        end_time=datetime.utcnow().isoformat() + "Z"
    )
)

for metric in response.data:
    for dp in metric.aggregated_datapoints:
        print(f"{dp.timestamp}: {dp.value:.0f} total IOPS")
```

### Step 6: Network Bandwidth Validation

Verify you're getting expected network performance:

```python
# Query network bytes for bandwidth validation
response = monitoring.summarize_metrics_data(
    compartment_id="ocid1.compartment.oc1..example",
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query='NetworksBytesIn[5m].rate() + NetworksBytesOut[5m].rate()',
        start_time=(datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        end_time=datetime.utcnow().isoformat() + "Z"
    )
)

for metric in response.data:
    for dp in metric.aggregated_datapoints:
        gbps = (dp.value * 8) / 1_000_000_000
        print(f"{dp.timestamp}: {gbps:.2f} Gbps")
```

## Output

Successful completion produces:
- A shape comparison showing processor, OCPU range, and network bandwidth
- Available shapes queried from your tenancy and region
- A block volume created with the appropriate performance tier
- Performance monitoring queries showing actual IOPS and throughput
- Network bandwidth validation against expected shape limits

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthorizedOrNotFound | 404 | Shape not available in your region/AD | Check availability with `list_shapes`; try a different AD |
| LimitExceeded | 400 | Tenancy service limit reached | Request limit increase in Console > Governance > Limits |
| InvalidParameter | 400 | Invalid `vpus_per_gb` value | Use 10, 20, or 30–120 (multiples of 10) |
| TooManyRequests | 429 | Rate limited on metric queries | Reduce query frequency; widen time intervals |
| InternalError | 500 | OCI service issue | Check [OCI Status](https://ocistatus.oraclecloud.com) |
| NotAuthenticated | 401 | Bad config or expired key | Verify `~/.oci/config` and regenerate API key if needed |

## Examples

**Quick shape lookup with OCI CLI:**

```bash
# List all flex shapes available in your compartment
oci compute shape list \
  --compartment-id ocid1.compartment.oc1..example \
  --query "data[?contains(shape, 'Flex')].{Shape:shape, OCPUs:ocpus, Memory:\"memory-in-gbs\"}" \
  --output table

# Check block volume performance tier
oci bv volume get \
  --volume-id ocid1.volume.oc1..example \
  --query "data.{Name:\"display-name\", SizeGB:\"size-in-gbs\", VPUsPerGB:\"vpus-per-gb\"}"
```

**Right-size an instance based on CPU metrics:**

```python
import oci
from datetime import datetime, timedelta

config = oci.config.from_file("~/.oci/config")
monitoring = oci.monitoring.MonitoringClient(config)

# Get 7-day average CPU to check if over-provisioned
response = monitoring.summarize_metrics_data(
    compartment_id="ocid1.compartment.oc1..example",
    summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query='CpuUtilization[1h].mean()',
        start_time=(datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
        end_time=datetime.utcnow().isoformat() + "Z"
    )
)

for metric in response.data:
    avg_cpu = sum(dp.value for dp in metric.aggregated_datapoints) / len(metric.aggregated_datapoints)
    if avg_cpu < 20:
        print(f"Instance {metric.dimensions.get('resourceId', 'unknown')}: "
              f"avg CPU {avg_cpu:.1f}% — consider downsizing")
```

## Resources

- [OCI Compute Shapes](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm) — full shape specifications
- [OCI Block Volume Performance](https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/blockvolumeperformance.htm) — IOPS/throughput by tier
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — SDK reference
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — cost per OCPU, storage, and network
- [OCI API Reference](https://docs.oracle.com/en-us/iaas/api/) — REST API specs

## Next Steps

After optimizing shapes and storage, proceed to `oraclecloud-cost-tuning` to track spend and set budget alerts, or see `oraclecloud-observability` to set up ongoing performance monitoring with alarms.
