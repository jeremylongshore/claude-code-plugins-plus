---
name: coreweave-data-handling
description: |
  Handle training data and model artifacts on CoreWeave persistent storage.
  Use when managing large datasets, configuring storage classes,
  or implementing data pipelines for GPU workloads.
  Trigger with phrases like "coreweave data", "coreweave storage",
  "coreweave pvc", "coreweave dataset management".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Data Handling

## Storage Classes

| Class | Type | Use Case |
|-------|------|----------|
| `shared-hdd-ord1` | HDD | Training data archival |
| `shared-ssd-ord1` | SSD | Model weights, active datasets |
| `block-nvme-ord1` | NVMe | High-performance training |

## PVC Configuration

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
spec:
  accessModes: ["ReadWriteMany"]
  resources:
    requests:
      storage: 500Gi
  storageClassName: shared-ssd-ord1
```

## Data Loading Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: download-model
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: downloader
          image: python:3.11-slim
          command: ["python3", "-c"]
          args:
            - |
              from huggingface_hub import snapshot_download
              snapshot_download("meta-llama/Llama-3.1-8B-Instruct", local_dir="/models/llama-8b")
          volumeMounts:
            - name: models
              mountPath: /models
          env:
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: hf-token
                  key: token
      volumes:
        - name: models
          persistentVolumeClaim:
            claimName: model-storage
```

## Resources

- [CoreWeave Storage](https://docs.coreweave.com)

## Next Steps

For RBAC configuration, see `coreweave-enterprise-rbac`.
