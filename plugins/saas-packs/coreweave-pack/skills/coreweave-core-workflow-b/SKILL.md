---
name: coreweave-core-workflow-b
description: |
  Run distributed GPU training jobs on CoreWeave with multi-node PyTorch.
  Use when training models across multiple GPUs, setting up distributed training,
  or running fine-tuning jobs on CoreWeave H100 clusters.
  Trigger with phrases like "coreweave training", "coreweave multi-gpu",
  "distributed training coreweave", "fine-tune on coreweave".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Core Workflow: GPU Training

## Overview

Run distributed GPU training on CoreWeave: single-node multi-GPU and multi-node training with PyTorch DDP, Slurm-on-Kubernetes, and shared storage.

## Prerequisites

- CKS cluster with multi-GPU node pools (8xA100 or 8xH100)
- Shared storage (CoreWeave PVC or NFS)
- Training container with PyTorch and NCCL

## Instructions

### Step 1: Single-Node Multi-GPU Training

```yaml
# training-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: llm-finetune
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: trainer
          image: ghcr.io/myorg/trainer:latest
          command: ["torchrun"]
          args:
            - "--nproc_per_node=8"
            - "train.py"
            - "--model_name=meta-llama/Llama-3.1-8B"
            - "--batch_size=4"
            - "--epochs=3"
          resources:
            limits:
              nvidia.com/gpu: "8"
              memory: 512Gi
              cpu: "64"
          volumeMounts:
            - name: data
              mountPath: /data
            - name: checkpoints
              mountPath: /checkpoints
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: training-data
        - name: checkpoints
          persistentVolumeClaim:
            claimName: model-checkpoints
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: gpu.nvidia.com/class
                    operator: In
                    values: ["A100_NVLINK_A100_SXM4_80GB"]
```

### Step 2: Persistent Storage for Training Data

```yaml
# storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: training-data
spec:
  accessModes: ["ReadWriteMany"]
  resources:
    requests:
      storage: 500Gi
  storageClassName: shared-hdd-ord1
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-checkpoints
spec:
  accessModes: ["ReadWriteMany"]
  resources:
    requests:
      storage: 200Gi
  storageClassName: shared-ssd-ord1
```

### Step 3: Monitor Training Progress

```bash
# Watch training logs
kubectl logs -f job/llm-finetune

# Check GPU utilization
kubectl exec -it $(kubectl get pod -l job-name=llm-finetune -o name) -- nvidia-smi

# Check training metrics
kubectl exec -it $(kubectl get pod -l job-name=llm-finetune -o name) -- \
  cat /checkpoints/training_log.json | tail -5
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| NCCL timeout | Network issue between GPUs | Use NVLink nodes (SXM4/SXM5) |
| OOMKilled | Batch size too large | Reduce batch size or use gradient accumulation |
| Checkpoint save failed | PVC full | Increase storage or prune old checkpoints |
| Job evicted | Preemption | Use on-demand nodes for training |

## Resources

- [CoreWeave CKS](https://docs.coreweave.com/docs/products/cks)
- [PyTorch Distributed Training](https://pytorch.org/tutorials/intermediate/ddp_tutorial.html)

## Next Steps

For troubleshooting, see `coreweave-common-errors`.
