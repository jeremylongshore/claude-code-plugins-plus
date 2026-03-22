---
name: adobe-core-workflow-b
description: |
  Execute Adobe PDF Services workflow: create PDFs from HTML/DOCX, extract text/tables,
  document generation from templates, and PDF-to-Markdown conversion.
  Use when building document automation, extracting content from PDFs,
  or generating dynamic reports.
  Trigger with phrases like "adobe pdf", "pdf services", "extract pdf",
  "create pdf", "document generation", "pdf to markdown".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Core Workflow B — PDF Services

## Overview

Document automation using Adobe PDF Services API: create PDFs from HTML/DOCX, extract structured text and tables with Sensei AI, generate documents from Word templates with JSON data, and convert PDFs to LLM-friendly Markdown.

## Prerequisites

- Completed `adobe-install-auth` with PDF Services credentials
- `npm install @adobe/pdfservices-node-sdk` (v4.x+)
- 500 free document transactions/month on the free tier

## Instructions

### Step 1: Create PDF from HTML

```typescript
// src/workflows/pdf-create.ts
import {
  ServicePrincipalCredentials,
  PDFServices,
  MimeType,
  CreatePDFJob,
  CreatePDFResult,
} from '@adobe/pdfservices-node-sdk';
import * as fs from 'fs';

const credentials = new ServicePrincipalCredentials({
  clientId: process.env.ADOBE_CLIENT_ID!,
  clientSecret: process.env.ADOBE_CLIENT_SECRET!,
});
const pdfServices = new PDFServices({ credentials });

export async function htmlToPdf(htmlPath: string, outputPath: string): Promise<void> {
  const inputStream = fs.createReadStream(htmlPath);
  const inputAsset = await pdfServices.upload({
    readStream: inputStream,
    mimeType: MimeType.HTML,
  });

  const job = new CreatePDFJob({ inputAsset });
  const pollingURL = await pdfServices.submit({ job });
  const result = await pdfServices.getJobResult({
    pollingURL,
    resultType: CreatePDFResult,
  });

  const resultAsset = result.result!.asset;
  const streamAsset = await pdfServices.getContent({ asset: resultAsset });
  const output = fs.createWriteStream(outputPath);
  streamAsset.readStream.pipe(output);

  await new Promise((resolve, reject) => {
    output.on('finish', resolve);
    output.on('error', reject);
  });

  console.log(`PDF created: ${outputPath}`);
}
```

### Step 2: Extract Text and Tables from PDF (Sensei AI)

```typescript
// src/workflows/pdf-extract.ts
import {
  PDFServices,
  MimeType,
  ExtractPDFParams,
  ExtractElementType,
  ExtractPDFJob,
  ExtractPDFResult,
  ExtractRenditionsElementType,
} from '@adobe/pdfservices-node-sdk';
import * as fs from 'fs';
import AdmZip from 'adm-zip';

export async function extractPdfContent(
  pdfPath: string,
  options?: { tables?: boolean; figures?: boolean }
): Promise<{ text: string; tables: any[]; }> {
  const inputStream = fs.createReadStream(pdfPath);
  const inputAsset = await pdfServices.upload({
    readStream: inputStream,
    mimeType: MimeType.PDF,
  });

  const elements = [ExtractElementType.TEXT];
  if (options?.tables !== false) elements.push(ExtractElementType.TABLES);

  const params = new ExtractPDFParams({
    elementsToExtract: elements,
    ...(options?.figures && {
      elementsToExtractRenditions: [ExtractRenditionsElementType.FIGURES],
    }),
  });

  const job = new ExtractPDFJob({ inputAsset, params });
  const pollingURL = await pdfServices.submit({ job });
  const result = await pdfServices.getJobResult({
    pollingURL,
    resultType: ExtractPDFResult,
  });

  // Download and parse the result ZIP
  const resultAsset = result.result!.resource;
  const streamAsset = await pdfServices.getContent({ asset: resultAsset });
  const chunks: Buffer[] = [];
  for await (const chunk of streamAsset.readStream) {
    chunks.push(Buffer.from(chunk));
  }

  const zip = new AdmZip(Buffer.concat(chunks));
  const structuredData = JSON.parse(
    zip.readAsText('structuredData.json')
  );

  // Parse text elements
  const textElements = structuredData.elements
    .filter((el: any) => el.Text)
    .map((el: any) => el.Text);

  // Parse table elements
  const tableElements = structuredData.elements
    .filter((el: any) => el.Path?.includes('/Table'));

  return { text: textElements.join('\n'), tables: tableElements };
}
```

### Step 3: Document Generation from Word Template

```typescript
// src/workflows/pdf-docgen.ts
import {
  PDFServices,
  MimeType,
  DocumentMergeJob,
  DocumentMergeParams,
  DocumentMergeResult,
  OutputFormat,
} from '@adobe/pdfservices-node-sdk';
import * as fs from 'fs';

export async function generateDocument(
  templatePath: string,   // .docx Word template with {{tags}}
  data: Record<string, any>,
  outputPath: string,
  format: 'pdf' | 'docx' = 'pdf'
): Promise<void> {
  const inputStream = fs.createReadStream(templatePath);
  const inputAsset = await pdfServices.upload({
    readStream: inputStream,
    mimeType: MimeType.DOCX,
  });

  const params = new DocumentMergeParams({
    jsonDataForMerge: data,
    outputFormat: format === 'pdf' ? OutputFormat.PDF : OutputFormat.DOCX,
  });

  const job = new DocumentMergeJob({ inputAsset, params });
  const pollingURL = await pdfServices.submit({ job });
  const result = await pdfServices.getJobResult({
    pollingURL,
    resultType: DocumentMergeResult,
  });

  const resultAsset = result.result!.asset;
  const streamAsset = await pdfServices.getContent({ asset: resultAsset });
  const output = fs.createWriteStream(outputPath);
  streamAsset.readStream.pipe(output);

  console.log(`Document generated: ${outputPath}`);
}

// Usage: Invoice generation
// await generateDocument('./templates/invoice.docx', {
//   company: 'Acme Corp',
//   invoiceNumber: 'INV-2026-001',
//   items: [
//     { description: 'API Integration', quantity: 1, price: 5000 },
//     { description: 'Support Plan', quantity: 12, price: 200 },
//   ],
//   total: '$7,400.00',
// }, './output/invoice.pdf');
```

### Step 4: PDF to Markdown (LLM-Friendly)

```typescript
// PDF Extract API supports structured output for LLM ingestion
export async function pdfToMarkdown(pdfPath: string): Promise<string> {
  const { text } = await extractPdfContent(pdfPath, { tables: false });

  // The structuredData.json includes element paths indicating heading levels
  // For full Markdown fidelity, parse element Paths:
  //   /H1 -> # heading, /H2 -> ## heading, /L/LI -> bullet
  return text;
}
```

## Output

- PDF files created from HTML, DOCX, or other formats
- Structured JSON with text, tables, and figures extracted from PDFs
- Dynamic documents generated from Word templates with JSON data
- Markdown text extracted from PDFs for LLM consumption

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `DISQUALIFIED` | Encrypted or DRM-protected PDF | Remove encryption before processing |
| `BAD_PDF` | Corrupted PDF file | Validate PDF with `pdfinfo` before upload |
| `TIMEOUT` | Large PDF (100+ pages) | Split into smaller PDFs first |
| `QUOTA_EXCEEDED` | Free tier limit (500 tx/month) | Upgrade plan or wait for monthly reset |
| `UNSUPPORTED_MEDIA_TYPE` | Wrong MimeType for input | Match MimeType to actual file format |

## Resources

- [PDF Services API How-Tos](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/howtos/)
- [Document Generation API](https://developer.adobe.com/document-services/docs/overview/document-generation-api/)
- [PDF Extract API](https://developer.adobe.com/document-services/docs/overview/pdf-extract-api/)
- [PDF Services Node SDK Samples](https://github.com/adobe/pdfservices-node-sdk-samples)

## Next Steps

For common errors, see `adobe-common-errors`.
