# Documenso Cost Tuning - Implementation Guide

## Documenso Pricing Model

Documenso offers multiple plans:

| Plan | Best For | Key Limits |
|------|----------|------------|
| Free | Testing/Personal | Limited documents |
| Individual | Freelancers | Higher document limits |
| Teams | Small teams | Team collaboration |
| Enterprise | Large organizations | Custom limits |

## Cost Optimization Strategies

### Strategy 1: Template Reuse

```typescript
// EXPENSIVE: Creating from scratch each time
async function createContractExpensive(data: ContractData) {
  const doc = await client.documents.createV0({
    title: data.title,
    file: await generatePdf(data),  // PDF generation cost
  });

  // Add recipients each time
  await client.documentsRecipients.createV0({
    documentId: doc.documentId!,
    email: data.signerEmail,
    name: data.signerName,
    role: "SIGNER",
  });

  // Add fields each time
  await client.documentsFields.createV0({
    documentId: doc.documentId!,
    recipientId: "...",
    type: "SIGNATURE",
    page: 1,
    positionX: 100,
    positionY: 600,
    width: 200,
    height: 60,
  });

  return doc;
}

// EFFICIENT: Use templates
async function createContractEfficient(data: ContractData) {
  // Template already has fields and recipient placeholders
  const envelope = await client.envelopes.useV0({
    templateId: STANDARD_CONTRACT_TEMPLATE,
    title: data.title,
    recipients: [
      {
        email: data.signerEmail,
        name: data.signerName,
        signerIndex: 0,
      },
    ],
  });

  return envelope;
}
```

### Strategy 2: Document Consolidation

```typescript
// EXPENSIVE: Multiple documents for one transaction
// Creates 3 documents = 3x cost
async function handleDealExpensive(deal: Deal) {
  await createDocument("NDA", deal);
  await createDocument("MSA", deal);
  await createDocument("SOW", deal);
}

// EFFICIENT: Combine into one document package
// Creates 1 document = 1x cost
async function handleDealEfficient(deal: Deal) {
  // Combine PDFs into single document
  const combinedPdf = await combinePdfs([
    "./templates/nda.pdf",
    "./templates/msa.pdf",
    "./templates/sow.pdf",
  ]);

  await createDocument("Deal Package", deal, combinedPdf);
}
```

### Strategy 3: Draft Cleanup

```typescript
// Clean up abandoned drafts to avoid confusion and track true usage
async function cleanupOldDrafts(daysOld = 30): Promise<number> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - daysOld);

  const docs = await client.documents.findV0({});
  const oldDrafts = docs.documents?.filter(
    (d) =>
      d.status === "DRAFT" &&
      new Date(d.createdAt!) < cutoffDate
  ) ?? [];

  let deleted = 0;
  for (const draft of oldDrafts) {
    try {
      await client.documents.deleteV0({ documentId: draft.id! });
      deleted++;
    } catch (error) {
      console.warn(`Failed to delete draft ${draft.id}`);
    }
  }

  console.log(`Deleted ${deleted} old drafts`);
  return deleted;
}

// Schedule weekly cleanup
// cron: "0 0 * * 0" (Sunday midnight)
```

### Strategy 4: Usage Monitoring

```typescript
interface UsageMetrics {
  period: { start: Date; end: Date };
  documentsCreated: number;
  documentsCompleted: number;
  templateUsage: Map<string, number>;
  activeRecipients: Set<string>;
}

async function trackUsage(): Promise<UsageMetrics> {
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

  const metrics: UsageMetrics = {
    period: { start: startOfMonth, end: now },
    documentsCreated: 0,
    documentsCompleted: 0,
    templateUsage: new Map(),
    activeRecipients: new Set(),
  };

  // Iterate through documents
  const docs = await client.documents.findV0({});

  for (const doc of docs.documents ?? []) {
    const createdAt = new Date(doc.createdAt!);

    if (createdAt >= startOfMonth) {
      metrics.documentsCreated++;

      if (doc.status === "COMPLETED") {
        metrics.documentsCompleted++;
      }

      // Track recipients
      for (const recipient of doc.recipients ?? []) {
        metrics.activeRecipients.add(recipient.email!);
      }
    }
  }

  return metrics;
}

// Alert when approaching limits
async function checkUsageLimits() {
  const metrics = await trackUsage();
  const MONTHLY_LIMIT = 100; // Your plan's limit

  const usagePercent = (metrics.documentsCreated / MONTHLY_LIMIT) * 100;

  if (usagePercent > 80) {
    console.warn(`Usage at ${usagePercent.toFixed(0)}% of monthly limit!`);
    // Send alert
  }
}
```

### Strategy 5: Efficient Field Placement

```typescript
// Reduce API calls by batching field creation
async function addFieldsEfficiently(
  documentId: string,
  fields: FieldConfig[]
): Promise<void> {
  // Use batch endpoint when available
  if (fields.length > 1) {
    await client.documentsFields.createManyV0({
      documentId,
      fields: fields.map((f) => ({
        recipientId: f.recipientId,
        type: f.type as any,
        page: f.page,
        positionX: f.x,
        positionY: f.y,
        width: f.width ?? 200,
        height: f.height ?? 60,
      })),
    });
  } else if (fields.length === 1) {
    const f = fields[0];
    await client.documentsFields.createV0({
      documentId,
      recipientId: f.recipientId,
      type: f.type as any,
      page: f.page,
      positionX: f.x,
      positionY: f.y,
      width: f.width ?? 200,
      height: f.height ?? 60,
    });
  }
}
```

### Strategy 6: Self-Hosting Consideration

For high-volume use cases, self-hosting may be more cost-effective:

```yaml
# docker-compose.yml for self-hosted Documenso
version: '3.8'

services:
  documenso:
    image: documenso/documenso:latest
    ports:
      - "3000:3000"
    environment:
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXT_PRIVATE_DATABASE_URL=${DATABASE_URL}
      - NEXT_PRIVATE_SMTP_HOST=${SMTP_HOST}
    volumes:
      - ./cert.p12:/opt/documenso/cert.p12:ro

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Cost comparison (example):**
- Cloud: $49/user/month at 10 users = $490/month
- Self-hosted: Server + DB + maintenance = ~$100-200/month

### Strategy 7: Usage Reporting Dashboard

```typescript
// Generate monthly cost report
async function generateCostReport(month: Date): Promise<CostReport> {
  const metrics = await trackUsage();

  // Calculate costs (example rates)
  const perDocumentCost = 0.5; // Example: $0.50 per document
  const estimatedCost = metrics.documentsCreated * perDocumentCost;

  const report = {
    period: `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`,
    metrics: {
      documentsCreated: metrics.documentsCreated,
      documentsCompleted: metrics.documentsCompleted,
      completionRate:
        (metrics.documentsCompleted / metrics.documentsCreated) * 100,
      uniqueRecipients: metrics.activeRecipients.size,
    },
    costs: {
      estimated: estimatedCost,
      perDocument: perDocumentCost,
    },
    recommendations: [] as string[],
  };

  // Add recommendations
  if (report.metrics.completionRate < 50) {
    report.recommendations.push(
      "Low completion rate - consider simplifying signing process"
    );
  }

  if (metrics.documentsCreated > 500) {
    report.recommendations.push(
      "High volume - consider Enterprise plan or self-hosting"
    );
  }

  return report;
}
```

## Cost Optimization Checklist

- [ ] Use templates instead of creating from scratch
- [ ] Combine related documents into packages
- [ ] Clean up abandoned drafts regularly
- [ ] Monitor usage against plan limits
- [ ] Use batch APIs where available
- [ ] Consider self-hosting for high volume
- [ ] Review monthly usage reports
