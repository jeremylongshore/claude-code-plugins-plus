# OpenEvidence Reference Architecture - Implementation Details

## Client Wrapper with Caching & Monitoring
```typescript
export class OpenEvidenceService {
  async query(request: ClinicalQueryRequest, context: RequestContext): Promise<ClinicalQueryResponse> {
    const cached = await this.cache.get(request.question, request.context);
    if (cached) { this.metrics.incrementCounter('cache_hit'); return cached; }
    const response = await this.client.query(request);
    await this.cache.set(request.question, request.context, response);
    await this.auditLogger.logQuery(context.userId, context.userRole, response.id, true);
    return response;
  }
}
```

## Service Facade
```typescript
export class ClinicalEvidenceService {
  async queryClinicalEvidence(question: string, patientContext, context): Promise<FormattedClinicalAnswer> {
    const sanitizedRequest = this.phiHandler.sanitizeQuery(question, patientContext);
    const response = await this.openEvidence.query(sanitizedRequest, context);
    return this.formatClinicalAnswer(response);
  }

  async checkDrugInteraction(drugs: string[], context): Promise<DrugInteractionResult> {
    const question = `What are the drug interactions between ${drugs.join(' and ')}?`;
    const response = await this.openEvidence.query({ question, context: { specialty: 'pharmacology', urgency: 'urgent' } }, context);
    return this.parseDrugInteractionResponse(response);
  }
}
```

## EHR Integration (FHIR CDS Hooks)
```typescript
export class FHIRIntegration {
  async handleCDSHook(request: CDSHooksRequest): Promise<CDSHooksResponse> {
    switch (request.hook) {
      case 'medication-prescribe': return this.handleMedicationPrescribe(request);
      case 'order-sign': return this.handleOrderSign(request);
      default: return { cards: [] };
    }
  }
}
```

## Data Flow
```
User/EHR Request → API Gateway (Auth, Rate) → PHI Sanitizer → Clinical Query Service → Cache Layer (Redis) → OpenEvidence API Client → OpenEvidence Cloud API
```

## Configuration Management (convict)
Type-safe config with environment-specific JSON files, sensitive field handling, and strict validation.
