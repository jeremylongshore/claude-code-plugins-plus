---
name: adobe-hello-world
description: |
  Create minimal working examples for Adobe APIs: Firefly image generation,
  PDF extraction, and Photoshop background removal.
  Use when starting a new Adobe integration, testing your setup,
  or learning basic Adobe API patterns.
  Trigger with phrases like "adobe hello world", "adobe example",
  "adobe quick start", "simple adobe code", "first adobe API call".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Hello World

## Overview

Three minimal working examples covering Adobe's core API surfaces: Firefly AI image generation, PDF content extraction, and Photoshop background removal.

## Prerequisites

- Completed `adobe-install-auth` setup
- Valid OAuth Server-to-Server credentials
- Node.js 18+ with `@adobe/firefly-apis` or `@adobe/pdfservices-node-sdk` installed

## Instructions

### Example 1: Firefly Text-to-Image Generation

```typescript
// hello-firefly.ts
import 'dotenv/config';
import { getAdobeAccessToken } from './adobe/auth';

async function generateImage() {
  const token = await getAdobeAccessToken();

  const response = await fetch(
    'https://firefly-api.adobe.io/v3/images/generate',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: 'A futuristic cityscape at sunset with flying cars',
        n: 1,              // number of images
        size: {
          width: 1024,
          height: 1024,
        },
        contentClass: 'art', // "art" or "photo"
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Firefly API error: ${response.status} ${await response.text()}`);
  }

  const result = await response.json();
  console.log('Generated image URL:', result.outputs[0].image.url);
  return result;
}

generateImage().catch(console.error);
```

### Example 2: PDF Text Extraction

```typescript
// hello-pdf.ts
import {
  ServicePrincipalCredentials,
  PDFServices,
  MimeType,
  ExtractPDFParams,
  ExtractElementType,
  ExtractPDFJob,
  ExtractPDFResult,
} from '@adobe/pdfservices-node-sdk';
import * as fs from 'fs';

async function extractPDF() {
  const credentials = new ServicePrincipalCredentials({
    clientId: process.env.ADOBE_CLIENT_ID!,
    clientSecret: process.env.ADOBE_CLIENT_SECRET!,
  });

  const pdfServices = new PDFServices({ credentials });

  // Upload the PDF
  const inputStream = fs.createReadStream('./sample.pdf');
  const inputAsset = await pdfServices.upload({
    readStream: inputStream,
    mimeType: MimeType.PDF,
  });

  // Configure extraction (text + tables)
  const params = new ExtractPDFParams({
    elementsToExtract: [ExtractElementType.TEXT, ExtractElementType.TABLES],
  });

  // Run extraction job
  const job = new ExtractPDFJob({ inputAsset, params });
  const pollingURL = await pdfServices.submit({ job });
  const result = await pdfServices.getJobResult({
    pollingURL,
    resultType: ExtractPDFResult,
  });

  // Download result ZIP containing structuredData.json
  const resultAsset = result.result!.resource;
  const streamAsset = await pdfServices.getContent({ asset: resultAsset });
  const outputStream = fs.createWriteStream('./extracted-output.zip');
  streamAsset.readStream.pipe(outputStream);

  console.log('Extraction complete: ./extracted-output.zip');
}

extractPDF().catch(console.error);
```

### Example 3: Photoshop Remove Background

```typescript
// hello-photoshop.ts
import 'dotenv/config';
import { getAdobeAccessToken } from './adobe/auth';

async function removeBackground() {
  const token = await getAdobeAccessToken();

  // Input/output must be pre-signed URLs (S3, Azure Blob, Dropbox)
  const response = await fetch(
    'https://image.adobe.io/sensei/cutout',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: {
          href: 'https://your-bucket.s3.amazonaws.com/input-photo.jpg',
          storage: 'external',
        },
        output: {
          href: 'https://your-bucket.s3.amazonaws.com/output-cutout.png',
          storage: 'external',
          type: 'image/png',
        },
      }),
    }
  );

  const result = await response.json();
  console.log('Job status URL:', result._links.self.href);

  // Poll for completion
  let status = result;
  while (status.status !== 'succeeded' && status.status !== 'failed') {
    await new Promise(r => setTimeout(r, 2000));
    const poll = await fetch(status._links.self.href, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
      },
    });
    status = await poll.json();
  }

  console.log('Background removal:', status.status);
}

removeBackground().catch(console.error);
```

## Output

- Generated AI image URL from Firefly API
- Extracted PDF text/tables in structured JSON format
- Background-removed PNG from Photoshop API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | Missing API entitlement | Enable the API in Developer Console project |
| `400 Bad Request` on Firefly | Invalid prompt or parameters | Check content policy; prompts cannot request trademarks or people |
| `invalid_content_type` on PDF | Wrong MimeType | Ensure input is actually a PDF, not a renamed file |
| `InputValidationError` on Photoshop | Invalid storage URL | Use pre-signed URLs with read/write permissions |
| `429 Too Many Requests` | Rate limit exceeded | Implement backoff; see `adobe-rate-limits` |

## Resources

- [Firefly API Quickstart](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/)
- [PDF Services Node.js Quickstart](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/quickstarts/nodejs/)
- [Photoshop API Getting Started](https://developer.adobe.com/firefly-services/docs/photoshop/getting-started)

## Next Steps

Proceed to `adobe-local-dev-loop` for development workflow setup.
