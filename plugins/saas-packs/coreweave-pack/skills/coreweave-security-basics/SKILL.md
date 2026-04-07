---
name: coreweave-security-basics
description: |
  Secure CoreWeave deployments with RBAC, network policies, and secrets management.
  Use when hardening GPU workloads, managing model access,
  or configuring namespace isolation.
  Trigger with phrases like "coreweave security", "coreweave rbac",
  "secure coreweave", "coreweave secrets".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Security Basics

## Overview
CoreWeave provides bare-metal GPU cloud on Kubernetes. Security concerns center on compute credential management (kubeconfig, deploy tokens), network isolation between inference workloads, secrets for model registry access (HuggingFace, container registries), and protecting sensitive training data on persistent volumes. A compromised namespace can expose GPU resources, model weights, and customer inference data.

## API Key Management
```typescript
import { KubeConfig, CoreV1Api } from "@kubernetes/client-node";

function createCoreWeaveClient(): CoreV1Api {
  const apiKey = process.env.COREWEAVE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing COREWEAVE_API_KEY — set via secrets manager");
  }
  const kc = new KubeConfig();
  kc.loadFromDefault();
  const api = kc.makeApiClient(CoreV1Api);
  // Never log kubeconfig or API key contents
  console.log("CoreWeave client initialized for namespace:", process.env.CW_NAMESPACE);
  return api;
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyCoreWeaveWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-coreweave-signature"] as string;
  const secret = process.env.COREWEAVE_WEBHOOK_SECRET!;
  const expected = crypto.createHmac("sha256", secret).update(req.body).digest("hex");
  if (!signature || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    res.status(401).send("Invalid signature");
    return;
  }
  next();
}
```

## Input Validation
```typescript
import { z } from "zod";

const WorkloadRequestSchema = z.object({
  namespace: z.string().regex(/^[a-z0-9-]+$/).max(63),
  gpu_type: z.enum(["A100_80GB", "A100_40GB", "H100_80GB", "RTX_A6000"]),
  gpu_count: z.number().int().min(1).max(8),
  image: z.string().regex(/^[a-z0-9.\-/]+:[a-z0-9.\-]+$/),
  model_id: z.string().min(1).max(200),
});

function validateWorkloadRequest(data: unknown) {
  return WorkloadRequestSchema.parse(data);
}
```

## Data Protection
```typescript
const CW_SENSITIVE_FIELDS = ["kubeconfig", "hf_token", "registry_password", "api_key", "model_weights_url"];

function redactCoreWeaveLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of CW_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] Kubeconfig stored in secrets manager, never in repos
- [ ] Kubernetes Secrets used for model tokens (not env vars in YAML)
- [ ] Network policies restrict inference endpoint access
- [ ] RBAC limits namespace access per team
- [ ] Container images scanned for CVEs before deployment
- [ ] PVCs encrypted at rest for training data
- [ ] GPU workload namespaces isolated with NetworkPolicy
- [ ] Deploy tokens scoped per-namespace, not cluster-wide

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked kubeconfig | Full cluster access, GPU resource theft | Secrets manager + RBAC scoping |
| Open inference endpoints | Unauthorized model access | NetworkPolicy ingress rules |
| Unscanned container images | CVE exploitation in GPU pods | CI image scanning before deploy |
| Overly broad RBAC | Cross-namespace data leakage | Per-team namespace RBAC bindings |
| Unencrypted PVCs | Training data exposure | Encrypted storage classes |
## Resources
- [CoreWeave CKS Security](https://docs.coreweave.com/docs/products/cks)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `coreweave-prod-checklist`.
