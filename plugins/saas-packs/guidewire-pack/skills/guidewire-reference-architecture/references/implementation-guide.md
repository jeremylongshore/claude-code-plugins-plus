# Guidewire Reference Architecture — Implementation Guide

## High-Level Architecture

```
                              ┌─────────────────────────────────────────────┐
                              │         External Users & Channels           │
                              │  (Agents, Customers, Partners, Regulators)  │
                              └─────────────────┬───────────────────────────┘
                                                │
                              ┌─────────────────▼───────────────────────────┐
                              │           Digital Experience Layer          │
                              │  ┌─────────┐ ┌─────────┐ ┌─────────────┐   │
                              │  │  Agent  │ │Customer │ │  Partner    │   │
                              │  │ Portal  │ │ Portal  │ │   Portal    │   │
                              │  │ (Jutro) │ │ (Jutro) │ │   (API)     │   │
                              │  └────┬────┘ └────┬────┘ └──────┬──────┘   │
                              └───────┼──────────┼─────────────┼───────────┘
                                      │          │             │
                              ┌───────▼──────────▼─────────────▼───────────┐
                              │              API Gateway                    │
                              │      (Authentication, Rate Limiting)        │
                              └────────────────────┬────────────────────────┘
                                                   │
  ┌────────────────────────────────────────────────┼────────────────────────────────────────────────┐
  │                                    Guidewire Cloud Platform                                     │
  │                                                │                                                │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌──┴──────────────┐  ┌─────────────────┐            │
  │  │   PolicyCenter  │  │   ClaimCenter   │  │  BillingCenter  │  │  Contact        │            │
  │  │                 │  │                 │  │                 │  │  Manager        │            │
  │  │ • Submissions   │  │ • FNOL          │  │ • Invoicing     │  │                 │            │
  │  │ • Quoting       │  │ • Investigation │  │ • Payments      │  │ • Contacts      │            │
  │  │ • Binding       │  │ • Settlement    │  │ • Collections   │  │ • Addresses     │            │
  │  │ • Issuance      │  │ • Payments      │  │ • Commissions   │  │ • Roles         │            │
  │  │ • Endorsements  │  │ • Litigation    │  │                 │  │                 │            │
  │  │ • Renewals      │  │                 │  │                 │  │                 │            │
  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
  │           └────────────────────┴────────────────────┴────────────────────┘                     │
  │                                           │                                                    │
  │                              ┌────────────▼────────────┐                                       │
  │                              │     Shared Services     │                                       │
  │                              │ • Document Management   │                                       │
  │                              │ • Workflow Engine       │                                       │
  │                              │ • Rules Engine          │                                       │
  │                              │ • Reporting             │                                       │
  │                              └────────────┬────────────┘                                       │
  │                                           │                                                    │
  │  ┌────────────────────────────────────────┴────────────────────────────────────────┐          │
  │  │                         Integration Layer                                        │          │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │          │
  │  │  │   Cloud API  │  │  App Events  │  │  Integration │  │    Batch     │        │          │
  │  │  │   (REST)     │  │   (Kafka)    │  │   Gateway    │  │   Services   │        │          │
  │  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │          │
  │  └─────────────────────────────────────────────────────────────────────────────────┘          │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
  ┌─────────────────────────────────────────────┼─────────────────────────────────────────────────┐
  │                              Enterprise Integration Layer                                      │
  │  ┌───────────┐  ┌───────────┐  ┌─────────────────────────┐  ┌───────────┐  ┌───────────┐     │
  │  │    CRM    │  │  ERP/GL   │  │   Rating Engines        │  │  Document │  │  Legacy   │     │
  │  │(Salesforce)│  │(SAP/Oracle)│ │  (External/Internal)    │  │   Mgmt    │  │  Systems  │     │
  │  └───────────┘  └───────────┘  └─────────────────────────┘  └───────────┘  └───────────┘     │
  └────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Integration Patterns

### Pattern 1: Synchronous API Integration

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Cloud API  │────▶│  External   │
│ Application │◀────│             │◀────│   Service   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Use Cases:** Real-time policy quoting, address validation, credit scoring, real-time fraud detection.

```typescript
async function getRealTimeQuote(submissionId: string): Promise<Quote> {
  const ratingResponse = await ratingService.calculatePremium({
    submissionId,
    effectiveDate: submission.effectiveDate,
    coverages: submission.coverages
  });

  return await guidewireClient.updateQuote(submissionId, {
    premium: ratingResponse.premium,
    taxes: ratingResponse.taxes,
    fees: ratingResponse.fees
  });
}
```

### Pattern 2: Asynchronous Event-Driven

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│InsuranceSuite│──▶│  App Events │──▶│    Kafka    │──▶│  Consumer   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Use Cases:** Policy issued notifications, claims status updates, billing events, data warehouse sync.

### Pattern 3: Batch Integration

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    SFTP     │────▶│    Batch    │────▶│  Transform  │────▶│InsuranceSuite│
│   Server    │     │   Pickup    │     │   & Load    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Use Cases:** Nightly policy updates, bulk claims import, premium bordereaux, regulatory reporting.

## Data Flow Architecture

### Policy Lifecycle Data Flow

```yaml
policy_flow:
  1_submission:
    source: Agent Portal / Direct Customer
    target: PolicyCenter
    data: [applicant_info, coverage_requests, risk_data]

  2_underwriting:
    source: PolicyCenter
    integrations: [external_rating_engine, credit_bureau, mvr_service, loss_history]
    data: [risk_scores, premium_calculations, underwriting_decision]

  3_binding:
    source: PolicyCenter
    target: BillingCenter
    data: [policy_terms, premium_schedule, payment_plan]

  4_document_generation:
    source: PolicyCenter
    target: Document Service
    data: [policy_documents, dec_pages, endorsements]

  5_distribution:
    source: Document Service
    targets: [customer_email, agent_portal, document_archive]
```

### Claims Data Flow

```yaml
claims_flow:
  1_fnol:
    source: Customer Portal / Call Center
    target: ClaimCenter
    data: [loss_details, policy_verification, initial_reserve]

  2_investigation:
    source: ClaimCenter
    integrations: [fraud_detection, medical_records, police_reports]
    data: [investigation_results, liability_assessment]

  3_settlement:
    source: ClaimCenter
    target: BillingCenter
    data: [payment_authorization, vendor_payments, subrogation_recovery]

  4_reporting:
    source: ClaimCenter
    target: Data Warehouse
    data: [claim_metrics, loss_ratios, regulatory_reports]
```

## Security Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Security Perimeter                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                         WAF / DDoS                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              API Gateway (Rate Limiting, OAuth2/JWT)            │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │        Guidewire Hub (Identity Federation, MFA, RBAC)          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │   InsuranceSuite (AES-256 Encryption, PII Masking, Audit Log)  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │       Database Layer (TDE, Backup Encryption)                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## Scalability Configuration

```yaml
scaling:
  application_tier:
    min_instances: 2
    max_instances: 10
    target_cpu: 70%
    scale_up_cooldown: 300s
    scale_down_cooldown: 600s

  batch_processing:
    strategy: parallel_workers
    worker_count: 4
    queue_threshold: 1000

  database:
    read_replicas: 2
    connection_pool:
      min: 10
      max: 50
```

## Caching Strategy

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  L1 Cache   │────▶│  L2 Cache   │────▶│  Database   │
│  (In-Memory)│     │   (Redis)   │     │             │
│  TTL: 60s   │     │  TTL: 300s  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

- L1: Product models, typelists, user preferences
- L2: API responses, session data, rate tables
- Database: Transactional data, master data, historical

## Multi-Region Deployment

```
                    ┌─────────────────────────────────────┐
                    │          Global Load Balancer       │
                    └─────────────────┬───────────────────┘
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   US East       │       │   US West       │       │   EU West       │
│ ┌─────────────┐ │       │ ┌─────────────┐ │       │ ┌─────────────┐ │
│ │ App Cluster │ │       │ │ App Cluster │ │       │ │ App Cluster │ │
│ └─────────────┘ │       │ └─────────────┘ │       │ └─────────────┘ │
│ ┌─────────────┐ │       │ ┌─────────────┐ │       │ ┌─────────────┐ │
│ │  Database   │◀───────▶│ │  Database   │◀───────▶│ │  Database   │ │
│ │  (Primary)  │ │       │ │  (Replica)  │ │       │ │  (Replica)  │ │
│ └─────────────┘ │       │ └─────────────┘ │       │ └─────────────┘ │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Jutro Digital Platform | React-based portals |
| API Gateway | Guidewire Hub | Auth, routing |
| Core Apps | InsuranceSuite | PC, CC, BC |
| Integration | Integration Gateway | Apache Camel |
| Messaging | Apache Kafka | Event streaming |
| Database | PostgreSQL/Oracle | Relational data |
| Cache | Redis | Session, API cache |
| Search | Elasticsearch | Full-text search |
| Monitoring | Datadog/Splunk | Observability |
