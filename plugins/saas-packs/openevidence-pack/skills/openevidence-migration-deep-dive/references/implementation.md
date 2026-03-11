# OpenEvidence Migration Deep Dive - Implementation Details

## Legacy System Assessment
```typescript
async function assessLegacySystem(): Promise<LegacySystemAssessment> {
  return {
    systemName: 'LegacyCDS',
    queryVolume: { dailyQueries, peakQueriesPerMinute, uniqueUsers },
    features: { clinicalQuery: true, drugInfo: true, guidelines: true, deepResearch: false },
    integrations: { ehr: ['Epic', 'Cerner'], sso: ['ADFS'], audit: ['Splunk'] },
    dataToMigrate: { savedSearches: true, userPreferences: true, auditLogs: true },
  };
}
```

## Parallel Running Period
```typescript
export class ParallelRunner {
  async query(question: string, context: any) {
    const oeResult = await this.openEvidenceClient.query({ question, context });
    if (shouldCompare) {
      const legacyResult = await this.legacyClient.query(question);
      await this.logComparison(question, oeResult, legacyResult);
    }
    return { result: oeResult, source: 'openevidence' };
  }
}
```

## Data Migration
User migration with role mapping (doctor->Physician, nurse->Nurse), audit log migration (HIPAA required), batch processing with progress tracking and error handling.

## EHR Integration (Epic SMART on FHIR)
```typescript
export const epicConfig: SMARTConfig = {
  scope: ['openid', 'fhirUser', 'launch/patient', 'patient/Patient.read', 'patient/MedicationRequest.read', 'patient/Condition.read'],
};
```

## CDS Hooks Integration
Discovery endpoint and service endpoints for patient-view and medication-prescribe hooks. Drug interaction checking with severity-based CDS cards.

## Multi-Site Expansion
Site-specific configuration with per-site OpenEvidence org IDs, EHR system selection (epic/cerner/meditech/none), feature flags, and quota management.
