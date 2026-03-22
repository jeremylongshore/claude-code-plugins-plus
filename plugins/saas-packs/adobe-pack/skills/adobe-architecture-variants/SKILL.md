---
name: adobe-architecture-variants
description: |
  Choose and implement Adobe architecture blueprints: standalone SDK integration,
  Adobe App Builder serverless, and dedicated microservice with event-driven
  Firefly/PDF pipelines. Decision matrix based on team size and throughput.
  Trigger with phrases like "adobe architecture", "adobe blueprint",
  "adobe app builder vs standalone", "adobe microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Architecture Variants

## Overview

Three validated architecture blueprints for Adobe integrations: (A) direct SDK integration in existing app, (B) Adobe App Builder with Runtime actions, and (C) dedicated microservice with event-driven pipelines.

## Prerequisites

- Understanding of team size and throughput requirements
- Decision on which Adobe APIs to use (Firefly, PDF, Photoshop, Events)
- Knowledge of deployment infrastructure
- Growth projections for API usage

## Instructions

### Variant A: Direct SDK Integration (Simple)

**Best for:** MVPs, small teams (1-5), < 100 API calls/day, single Adobe API

```
my-app/
├── src/
│   ├── adobe/
│   │   ├── auth.ts              # OAuth token management
│   │   ├── firefly.ts           # or pdf-services.ts — one API client
│   │   └── types.ts
│   ├── routes/
│   │   └── api/
│   │       └── generate.ts      # Direct API call in route handler
│   └── index.ts
├── .env                         # ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET
└── package.json                 # @adobe/firefly-apis or @adobe/pdfservices-node-sdk
```

```typescript
// Direct integration — API call in route handler
app.post('/api/generate', async (req, res) => {
  try {
    const token = await getCachedToken();
    const result = await fetch('https://firefly-api.adobe.io/v3/images/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: req.body.prompt, n: 1, size: { width: 1024, height: 1024 } }),
    });
    res.json(await result.json());
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});
```

**Pros:** Fastest to build, simplest deployment, no extra infrastructure
**Cons:** No background processing, route handler blocks for 5-30s on Firefly calls

---

### Variant B: Adobe App Builder (Native Adobe)

**Best for:** Adobe-centric workflows, teams using Adobe ecosystem, event-driven CC Library automation

```
my-adobe-app/
├── actions/                         # Runtime actions (serverless functions)
│   ├── generate-image/
│   │   └── index.js                 # Firefly image generation action
│   ├── extract-pdf/
│   │   └── index.js                 # PDF extraction action
│   └── webhook-handler/
│       └── index.js                 # I/O Events webhook processor
├── web-src/                         # Optional frontend (React/SPA)
│   └── src/
├── app.config.yaml                  # App Builder configuration
├── .aio                             # AIO CLI configuration
└── package.json
```

```yaml
# app.config.yaml
application:
  actions: actions
  web: web-src
  runtimeManifest:
    packages:
      adobe-integration:
        actions:
          generate-image:
            function: actions/generate-image/index.js
            runtime: nodejs:20
            web: yes
            inputs:
              ADOBE_CLIENT_ID: $ADOBE_CLIENT_ID
              ADOBE_CLIENT_SECRET: $ADOBE_CLIENT_SECRET
            limits:
              timeout: 60000
              memory: 256
            annotations:
              require-adobe-auth: true

          webhook-handler:
            function: actions/webhook-handler/index.js
            runtime: nodejs:20
            web: yes
            annotations:
              require-adobe-auth: false  # Webhooks need public access
```

```javascript
// actions/generate-image/index.js — App Builder Runtime action
const { Core } = require('@adobe/aio-sdk');

async function main(params) {
  const logger = Core.Logger('generate-image');

  try {
    // Token management handled by App Builder automatically
    const token = params.__ow_headers?.authorization?.split(' ')[1]
      || await getServiceToken(params);

    const response = await fetch('https://firefly-api.adobe.io/v3/images/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': params.ADOBE_CLIENT_ID,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: params.prompt,
        n: 1,
        size: { width: params.width || 1024, height: params.height || 1024 },
      }),
    });

    const result = await response.json();
    return { statusCode: 200, body: result };
  } catch (error) {
    logger.error(error);
    return { statusCode: 500, body: { error: error.message } };
  }
}

exports.main = main;
```

**Pros:** Native Adobe hosting, built-in auth, I/O Events integration, no infra management
**Cons:** Vendor lock-in, cold start latency, limited runtime options

---

### Variant C: Dedicated Microservice (Enterprise)

**Best for:** High throughput (1000+ calls/day), multi-API workflows, strict SLAs

```
adobe-service/                          # Dedicated microservice
├── src/
│   ├── adobe/                          # Client layer
│   │   ├── auth.ts
│   │   ├── firefly-client.ts
│   │   ├── pdf-client.ts
│   │   ├── photoshop-client.ts
│   │   └── events-client.ts
│   ├── pipelines/                      # Workflow orchestration
│   │   ├── image-pipeline.ts           # Firefly → Photoshop → Storage
│   │   └── document-pipeline.ts        # PDF Extract → Transform → Store
│   ├── workers/                        # Background job processors
│   │   ├── firefly-worker.ts
│   │   └── pdf-worker.ts
│   ├── api/
│   │   ├── grpc/adobe.proto            # Internal API (gRPC)
│   │   └── rest/routes.ts              # External API + webhooks
│   └── index.ts
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml                        # Auto-scale on pending jobs
│   └── configmap.yaml
└── package.json

other-services/
├── web-api/                            # Calls adobe-service via gRPC
├── marketing-automation/               # Calls adobe-service for assets
└── document-processor/                 # Calls adobe-service for PDFs
```

```typescript
// src/pipelines/image-pipeline.ts
// Multi-step pipeline: Generate → Remove BG → Store
export async function imageProductionPipeline(request: {
  prompt: string;
  removeBackground: boolean;
  outputBucket: string;
}) {
  // Step 1: Generate with Firefly
  const generated = await fireflyClient.generate({
    prompt: request.prompt,
    size: { width: 2048, height: 2048 },
  });

  let imageUrl = generated.outputs[0].image.url;

  // Step 2: Optionally remove background with Photoshop
  if (request.removeBackground) {
    const presignedInput = await uploadToStorage(imageUrl);
    const presignedOutput = await getPresignedUploadUrl(request.outputBucket);

    await photoshopClient.removeBackground({
      input: { href: presignedInput, storage: 'external' },
      output: { href: presignedOutput, storage: 'external', type: 'image/png' },
    });

    imageUrl = presignedOutput;
  }

  // Step 3: Store final asset
  return { url: imageUrl, pipeline: 'image-production' };
}
```

**Pros:** Full control, independent scaling, multi-API orchestration, strict isolation
**Cons:** Complex ops, needs K8s/container platform, higher development cost

---

## Decision Matrix

| Factor | A: Direct SDK | B: App Builder | C: Microservice |
|--------|---------------|----------------|-----------------|
| Team Size | 1-5 | 3-10 | 10+ |
| API Calls/Day | < 100 | 100-1000 | 1000+ |
| Adobe APIs Used | 1 | 1-3 | 2+ |
| I/O Events | No | Yes (native) | Yes (custom) |
| Deployment | Any platform | Adobe hosting | K8s/containers |
| Time to Market | Days | 1-2 weeks | 3-8 weeks |
| Vendor Lock-in | Low | High (Adobe) | Low |
| Operational Cost | Lowest | Low (managed) | Highest |

## Migration Path

```
A (Direct) → B (App Builder):
  Move route handlers to Runtime actions
  Add I/O Events registration
  Deploy with `aio app deploy`

A (Direct) → C (Microservice):
  Extract Adobe code to dedicated service
  Add background job queue (BullMQ)
  Define gRPC API contract
  Deploy to Kubernetes

B (App Builder) → C (Microservice):
  Port Runtime actions to Express/Fastify
  Replace I/O Events with custom webhook handling
  Add HPA and monitoring
```

## Output

- Architecture variant selected based on decision matrix
- Project structure matching chosen pattern
- Migration path documented for future scaling

## Resources

- [Adobe App Builder](https://developer.adobe.com/app-builder/docs/)
- [Firefly Services SDK](https://developer.adobe.com/firefly-services/docs/guides/sdks/)
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)

## Next Steps

For common anti-patterns, see `adobe-known-pitfalls`.
