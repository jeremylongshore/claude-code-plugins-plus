---
name: configuring-auto-scaling-policies
description: |
  Configure use when you need to work with auto-scaling.
  This skill provides auto-scaling configuration with comprehensive guidance and automation.
  Trigger with phrases like "configure auto-scaling", "set up elastic scaling",
  or "implement scaling".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Configuring Auto-Scaling Policies

## Overview

Configure auto-scaling policies for cloud workloads across AWS Auto Scaling Groups, GCP Managed Instance Groups, Azure VMSS, and Kubernetes Horizontal Pod Autoscaler (HPA). Generate scaling configurations based on CPU, memory, request rate, or custom metrics with appropriate thresholds, cooldown periods, and scale-in protection.

## Prerequisites

- Cloud provider CLI installed and authenticated (`aws`, `gcloud`, or `az`)
- For Kubernetes HPA: `kubectl` configured with cluster access and metrics-server deployed
- Baseline performance data for the target workload (average CPU, memory, request rate)
- Understanding of traffic patterns (steady, bursty, scheduled)
- IAM permissions to create/modify scaling policies and CloudWatch/Stackdriver alarms

## Instructions

1. Identify the scaling target: EC2 Auto Scaling Group, GCP MIG, Azure VMSS, or Kubernetes Deployment
2. Analyze current workload metrics to establish baseline utilization and peak patterns
3. Define scaling boundaries: minimum instances/pods, maximum instances/pods, desired count
4. Select scaling metric(s): CPU utilization, memory, request count, queue depth, or custom metrics
5. Set target thresholds: scale-out trigger (e.g., CPU > 70%), scale-in trigger (e.g., CPU < 30%)
6. Configure cooldown periods to prevent flapping (typically 300s scale-out, 600s scale-in)
7. Add scale-in protection for stateful workloads or leader nodes if needed
8. Generate the scaling policy configuration in the appropriate format (Terraform, YAML, or CLI commands)
9. Validate by simulating load and confirming scaling events fire correctly

## Output

- Terraform HCL for AWS ASG scaling policies with CloudWatch alarms
- Kubernetes HPA manifests (YAML) with resource or custom metric targets
- GCP autoscaler configurations for Managed Instance Groups
- Scaling policy JSON/YAML for Azure VMSS
- CloudWatch or Stackdriver alarm definitions tied to scaling actions

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `No scaling activity despite high load` | Metric not reaching threshold or cooldown active | Verify metric source in CloudWatch/Stackdriver; check cooldown timer with `describe-scaling-activities` |
| `Scaling too aggressively (flapping)` | Cooldown too short or threshold too sensitive | Increase cooldown period and widen the gap between scale-out and scale-in thresholds |
| `Max capacity reached` | Instance/pod limit hit during traffic spike | Raise `max_size` or implement request queuing as a backpressure mechanism |
| `HPA unable to compute replica count` | Metrics server not deployed or metric unavailable | Install metrics-server and verify `kubectl top pods` returns data |
| `FailedScaleUp: insufficient capacity` | Cloud provider out of capacity in selected AZ/region | Add multiple AZs to the ASG or use mixed instance types with allocation strategy |

## Examples

- "Configure an AWS ASG with target tracking at 65% CPU, min 2 / max 20 instances, and 5-minute cooldown."
- "Create a Kubernetes HPA for a deployment that scales from 3 to 50 pods based on requests-per-second using a custom Prometheus metric."
- "Set up scheduled scaling for a GCP MIG: scale to 10 instances at 8am UTC and back to 2 at 10pm."

## Resources

- AWS Auto Scaling: https://docs.aws.amazon.com/autoscaling/ec2/userguide/
- Kubernetes HPA: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- GCP Autoscaler: https://cloud.google.com/compute/docs/autoscaler
- Azure VMSS Autoscale: https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-autoscale-overview
