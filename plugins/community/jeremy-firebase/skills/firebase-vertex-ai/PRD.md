# PRD: Firebase Vertex AI Skill

## Problem Statement

Building Firebase applications with Vertex AI integration requires coordinating multiple services (Auth, Firestore, Functions, Hosting) while managing secrets, IAM roles, security rules, and deployment pipelines. Developers face a steep learning curve assembling these pieces correctly, and mistakes in secrets management or IAM configuration lead to security vulnerabilities or production outages.

Common failure modes without this skill:

- API keys leaked into client-side code or version control
- Overly permissive Firestore/Storage security rules deployed to production
- Vertex AI calls made from client-side code instead of secure Cloud Functions
- Missing composite indexes discovered only after deployment
- No emulator testing, leading to slow feedback loops and costly mistakes

## Target Users

| Persona | Description | Key Need |
|---------|-------------|----------|
| Full-stack developer | Building web/mobile apps on Firebase | End-to-end project scaffold with AI features |
| Firebase practitioner | Experienced with Firebase, new to Vertex AI | Safe Gemini integration patterns in Functions |
| GCP team lead | Managing multi-environment Firebase deployments | Security rules, IAM, and deployment automation |
| AI prototyper | Experimenting with Gemini for content analysis or RAG | Working Firebase backend with Vertex AI in < 10 min |

## Success Criteria

1. **Time to deploy**: A developer with Firebase CLI installed can have a working Firebase project with a Gemini-backed Cloud Function deployed in under 10 minutes.
2. **Security by default**: Every generated project uses Secret Manager for API keys, least-privilege IAM roles, and non-trivial security rules.
3. **Emulator-first**: All generated code runs against Firebase Emulator Suite before touching production.
4. **Zero leaked secrets**: No API keys, service account JSON, or credentials appear in client code, logs, or version control.
5. **Production readiness**: Deployed Functions include error handling, structured logging, and retry logic for transient Vertex AI failures.

## Scope

### In Scope

- Firebase project initialization (firebase init with Functions, Firestore, Hosting, Emulators)
- Cloud Functions that call Vertex AI Gemini (chat, embeddings, content analysis)
- Firestore security rules and composite index generation
- Storage security rules with file-type and size constraints
- Auth provider configuration and custom claims for RBAC
- Secret Manager integration for API keys and service credentials
- Emulator Suite configuration and smoke test commands
- Single-command deployment (firebase deploy) with environment targeting
- Structured logging and basic cost alerting guidance

### Out of Scope

- Firebase Extensions marketplace integration
- Firebase ML custom model training and deployment
- Firebase Analytics event design and conversion funnels
- Multi-region Firestore replication strategies
- Firebase A/B testing and Remote Config workflows
- Custom domain and SSL certificate management for Hosting

## Functional Requirements

### FR-1: Project Initialization

The skill must detect whether a Firebase project exists (presence of `firebase.json`) and either initialize a new project or validate the existing one. Initialization selects Functions (Node.js 20, TypeScript), Firestore, Hosting, and Emulators.

### FR-2: Vertex AI Backend Function

The skill must generate a Cloud Function that:

- Imports `@google-cloud/vertexai`
- Reads the GCP project ID from environment configuration
- Calls a Gemini model (defaulting to `gemini-2.5-flash`)
- Validates input, returns structured JSON, and handles errors with appropriate HTTP status codes

### FR-3: Security Configuration

The skill must produce:

- `firestore.rules` with helper functions (`isAuthenticated`, `isOwner`, `hasRole`)
- `firestore.indexes.json` with any composite indexes required by generated queries
- `storage.rules` with file-type and size constraints
- Auth provider setup guidance (Email/Password at minimum)

### FR-4: Secrets Management

The skill must use Firebase Functions secrets (backed by Secret Manager) for any API keys. No secrets may appear in `firebase.json`, source code literals, or `.env` files committed to version control.

### FR-5: Emulator Testing

The skill must produce emulator configuration in `firebase.json` and provide commands to start emulators and run smoke tests against local endpoints.

### FR-6: Deployment

The skill must generate a deployment command targeting the correct Firebase project alias (dev/staging/prod) and deploying only the changed services.

## Non-Functional Requirements

- **Latency**: Cloud Functions calling Gemini should respond in < 5 seconds for typical prompts (< 500 tokens).
- **Cost**: Default function configuration uses `minInstances: 0` to avoid idle billing. Budget alerts are documented.
- **Observability**: Functions emit structured logs parseable by Cloud Logging. Error rates are surfaced via Cloud Monitoring.
- **Portability**: Generated code targets Node.js 20 LTS and uses only `@google-cloud/vertexai` and `firebase-admin` SDKs.

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Firebase CLI | >= 13.0 | Project init, deploy, emulators |
| Node.js | >= 20 LTS | Cloud Functions runtime |
| @google-cloud/vertexai | >= 1.0 | Gemini API access |
| firebase-admin | >= 12.0 | Firestore, Auth, Storage admin ops |
| firebase-functions | >= 5.0 | Cloud Functions triggers and config |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vertex AI API not enabled on project | Function deployment succeeds but calls fail | Pre-check: `gcloud services list --enabled` for aiplatform.googleapis.com |
| Billing not enabled | Functions and Vertex AI calls rejected | Detect billing status early; provide `gcloud billing` remediation |
| Region mismatch | Gemini model unavailable in selected region | Default to `us-central1`; document region availability |
| Security rules too permissive | Data exposure in production | Generate locked-down rules by default; warn on any `allow read: if true` |
| Cold start latency | First request > 10s | Document `minInstances` trade-off; default to 0 with guidance to increase |
