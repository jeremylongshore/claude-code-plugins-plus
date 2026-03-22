---
name: adobe-migration-deep-dive
description: |
  Execute major Adobe re-architecture: migrating from legacy Adobe APIs
  to Firefly Services, consolidating Creative Cloud integrations, and
  strangler-fig migration from competitor document/image APIs to Adobe.
  Trigger with phrases like "migrate adobe", "adobe migration",
  "switch to adobe", "adobe replatform", "replace with adobe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Migration Deep Dive

## Overview

Comprehensive guide for three major migration scenarios: (1) legacy Adobe API consolidation into Firefly Services, (2) migrating from competitor document/image APIs to Adobe, and (3) JWT credential migration to OAuth Server-to-Server.

## Prerequisites

- Current system documentation with API inventory
- Adobe Developer Console project with target APIs
- Feature flag infrastructure
- Rollback strategy tested in staging

## Instructions

### Migration Type Assessment

| Type | From | To | Complexity | Duration |
|------|------|----|-----------|----------|
| Auth migration | JWT credentials | OAuth Server-to-Server | Low | 1-2 days |
| API consolidation | Separate PS/LR endpoints | Firefly Services SDK | Medium | 1-2 weeks |
| Competitor replacement | Cloudinary/imgix/PDFTron | Adobe APIs | High | 4-8 weeks |
| Full replatform | Custom pipeline | Adobe App Builder | High | 2-3 months |

### Scenario 1: Consolidate to Firefly Services SDK

The Photoshop and Lightroom APIs were previously separate. They are now part of Firefly Services with a unified SDK:

```typescript
// BEFORE: Separate clients for each API
import { PhotoshopAPI } from 'some-old-photoshop-client';
import { LightroomAPI } from 'some-old-lightroom-client';

// AFTER: Unified Firefly Services SDK
import { PhotoshopClient } from '@adobe/photoshop-apis';
import { LightroomClient } from '@adobe/lightroom-apis';
import { FireflyClient } from '@adobe/firefly-apis';

// All use the same OAuth credentials
const config = {
  clientId: process.env.ADOBE_CLIENT_ID!,
  accessToken: await getAccessToken(),
};

const photoshop = new PhotoshopClient(config);
const lightroom = new LightroomClient(config);
const firefly = new FireflyClient(config);
```

### Scenario 2: Migrate from Competitor to Adobe PDF Services

```typescript
// src/adapters/document-adapter.ts
// Adapter pattern for gradual migration from PDFTron/other to Adobe

interface DocumentAdapter {
  extractText(pdfPath: string): Promise<string>;
  createPdf(htmlContent: string): Promise<Buffer>;
  mergePdfs(pdfPaths: string[]): Promise<Buffer>;
}

// Old implementation
class PdfTronAdapter implements DocumentAdapter {
  async extractText(pdfPath: string): Promise<string> {
    // ... existing PDFTron code
  }
  // ...
}

// New Adobe implementation
class AdobePdfAdapter implements DocumentAdapter {
  private pdfServices: PDFServices;

  constructor() {
    const credentials = new ServicePrincipalCredentials({
      clientId: process.env.ADOBE_CLIENT_ID!,
      clientSecret: process.env.ADOBE_CLIENT_SECRET!,
    });
    this.pdfServices = new PDFServices({ credentials });
  }

  async extractText(pdfPath: string): Promise<string> {
    const inputStream = fs.createReadStream(pdfPath);
    const inputAsset = await this.pdfServices.upload({
      readStream: inputStream,
      mimeType: MimeType.PDF,
    });

    const params = new ExtractPDFParams({
      elementsToExtract: [ExtractElementType.TEXT],
    });

    const job = new ExtractPDFJob({ inputAsset, params });
    const pollingURL = await this.pdfServices.submit({ job });
    const result = await this.pdfServices.getJobResult({
      pollingURL,
      resultType: ExtractPDFResult,
    });

    // Parse structuredData.json from result ZIP
    const streamAsset = await this.pdfServices.getContent({
      asset: result.result!.resource,
    });
    // ... extract text from ZIP
    return extractedText;
  }

  // ... implement createPdf, mergePdfs
}

// Feature-flag controlled routing
function getDocumentAdapter(): DocumentAdapter {
  const adobePercentage = getFeatureFlag('adobe_pdf_migration_pct');

  if (Math.random() * 100 < adobePercentage) {
    return new AdobePdfAdapter();
  }
  return new PdfTronAdapter();
}
```

### Scenario 3: Image API Migration (Cloudinary to Firefly/Photoshop)

```typescript
// src/adapters/image-adapter.ts
interface ImageAdapter {
  removeBackground(inputUrl: string): Promise<string>;
  resize(inputUrl: string, width: number, height: number): Promise<string>;
  generateImage(prompt: string): Promise<string>;
}

class CloudinaryAdapter implements ImageAdapter {
  async removeBackground(inputUrl: string): Promise<string> {
    // ... existing Cloudinary code
    return cloudinary.url(publicId, { effect: 'background_removal' });
  }
  // ...
}

class AdobeImageAdapter implements ImageAdapter {
  async removeBackground(inputUrl: string): Promise<string> {
    const token = await getAccessToken();
    const outputUrl = await generatePresignedUploadUrl();

    const response = await fetch('https://image.adobe.io/v2/remove-background', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: { href: inputUrl, storage: 'external' },
        output: { href: outputUrl, storage: 'external', type: 'image/png' },
      }),
    });

    const job = await response.json();
    const result = await pollAdobeJob(job._links.self.href);
    return outputUrl;
  }

  async generateImage(prompt: string): Promise<string> {
    const token = await getAccessToken();
    const response = await fetch('https://firefly-api.adobe.io/v3/images/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt, n: 1, size: { width: 1024, height: 1024 } }),
    });
    const result = await response.json();
    return result.outputs[0].image.url;
  }
  // ...
}
```

### Phase-Based Migration Plan

```
Week 1-2: Setup
├── Create Adobe Developer Console project
├── Install SDKs and implement adapter layer
├── Write integration tests for both old and new
└── Deploy adapter with 0% traffic to Adobe

Week 3-4: Validation
├── Route 5% traffic to Adobe adapter
├── Compare results (output quality, latency, error rate)
├── Fix edge cases discovered in production traffic
└── Increase to 25% if metrics are acceptable

Week 5-6: Gradual Migration
├── Increase to 50% traffic
├── Monitor cost impact (Adobe vs old provider)
├── Address any performance regressions
└── Increase to 100% if all metrics pass

Week 7-8: Cleanup
├── Remove old adapter code
├── Delete old provider credentials
├── Update documentation
└── Run postmortem on migration
```

### Post-Migration Validation

```typescript
async function validateMigration(): Promise<{ passed: boolean; checks: any[] }> {
  const checks = [
    { name: 'Auth working', fn: async () => !!(await getAccessToken()) },
    { name: 'PDF extract works', fn: async () => {
      const result = await adobeAdapter.extractText('./test/fixture.pdf');
      return result.length > 0;
    }},
    { name: 'Image generation works', fn: async () => {
      const url = await adobeAdapter.generateImage('test blue square');
      return url.startsWith('https://');
    }},
    { name: 'Error rate < 1%', fn: async () => {
      const metrics = await getErrorRate('adobe', '1h');
      return metrics < 0.01;
    }},
  ];

  const results = await Promise.all(
    checks.map(async c => ({ name: c.name, passed: await c.fn() }))
  );

  return { passed: results.every(r => r.passed), checks: results };
}
```

## Output

- Adapter layer abstracting old and new implementations
- Feature-flag controlled traffic split
- Phase-based migration with rollback at each stage
- Validation suite confirming migration success

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Quality difference | Different rendering engines | Compare side-by-side; tune parameters |
| Higher latency | Adobe async APIs | Use parallel job submission |
| Cost increase | Different pricing model | Implement caching; optimize batch sizes |
| Missing features | Not all features map 1:1 | Document gaps; find Adobe alternatives |

## Resources

- [Firefly Services SDK](https://developer.adobe.com/firefly-services/docs/guides/sdks/)
- [PDF Services Node SDK](https://www.npmjs.com/package/@adobe/pdfservices-node-sdk)
- [Photoshop API Reference](https://developer.adobe.com/firefly-services/docs/photoshop/api/)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Next Steps

For advanced troubleshooting, see `adobe-advanced-troubleshooting`.
