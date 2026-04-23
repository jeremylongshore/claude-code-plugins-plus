# Compliance Posture — GDPR / HIPAA / SOC2 Touchpoints

A LangChain app with real users has compliance obligations that a reviewer
will ask about. This reference maps the three most common frameworks
(GDPR, HIPAA, SOC2) to the LangChain 1.0 controls that actually satisfy them,
and documents the provider safety-settings decisions and audit-log fields a
security reviewer expects to see.

## Scope

This is not legal advice. It is a practitioner's map from compliance
requirements to LangChain configuration — intended to help you prepare for a
review, not to replace a CISO, a privacy counsel, or an auditor.

## GDPR — personal data in prompts and traces

| Article | Requirement | LangChain mitigation |
|---------|-------------|----------------------|
| Art. 5(1)(c) — data minimization | Only process personal data you need | PII redaction middleware upstream of the LLM call; remove unused fields before prompt |
| Art. 5(1)(e) — storage limitation | Define and enforce retention | OTEL trace retention policy (≤ 30 days typical); cache TTL aligned; no prompts in long-term logs |
| Art. 15 — right of access | Provide user's data on request | Structured logs keyed by user_id; query interface returns prompts, responses, metadata |
| Art. 17 — right to erasure | Delete user's data on request | Scriptable deletion across OTEL store, cache, structured logs; provider data processor agreement includes deletion |
| Art. 28 — processors | DPA with every third party | Signed DPA with Anthropic, OpenAI, Google; listed in privacy notice |
| Art. 32 — security of processing | Encryption at rest and in transit | TLS for all provider calls (default); secrets in Secret Manager encrypted at rest |
| Art. 44 — cross-border transfers | Legal basis for transfer outside EEA | Provider DPA + SCCs; document data residency (e.g., Anthropic EU-region endpoint if available) |

### Practical GDPR controls for a LangChain app

- **Redact before LLM call.** Presidio-style detector on `email`, `phone`,
  `credit_card`, `ssn`, `person_name`, `location`. Replace with tokens
  (`[EMAIL_1]`) so the model still gets structure.
- **Turn OTEL content capture off in EEA-user multi-tenant.**
  `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false` (P27). If you
  need debug traces, export to a separately-permissioned sink with shorter
  retention.
- **Right to erasure script.** A deterministic deletion job that walks OTEL,
  cache, and structured logs keyed by user_id.
- **Consent surface.** If the LangChain app is user-facing, the privacy notice
  names each provider and the purpose.

## HIPAA — PHI in healthcare apps

| Safeguard | Requirement | LangChain mitigation |
|-----------|-------------|----------------------|
| § 164.312(a)(1) — access control | Unique user IDs, emergency access | Per-tenant agent construction (see P33); audit log identifies the user for every call |
| § 164.312(b) — audit controls | Record who accessed what PHI | Structured logs with `{user_id, tenant_id, tool, args_redacted, response_summary, request_id}` |
| § 164.312(c)(1) — integrity | Prevent improper alteration | Output validation (Pydantic); canary token detection for injection |
| § 164.312(e)(1) — transmission security | Encrypt in transit | TLS to providers; no raw HTTP |
| BAA | Business Associate Agreement with each vendor | Signed BAA with the provider — Anthropic, OpenAI, Google each have BAA programs. Verify your usage is in-scope. |

### HIPAA-specific LangChain decisions

- **Provider selection.** Only use a provider with a signed BAA. Document
  the tier — Anthropic's BAA applies to the API, not the consumer Claude.ai
  product; same for OpenAI Enterprise.
- **Gemini safety settings.** Medical prompts trip `HARM_CATEGORY_MEDICAL`
  at the default threshold (P65). Override to `BLOCK_NONE` for medical
  workloads, **document the override** in the compliance posture doc, and
  rely on your own PII redaction + output validation instead.
- **No prompts in OTEL.** Even with a BAA, the less PHI in tooling the
  better. Keep `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false`.
- **Minimum necessary.** Don't feed the entire patient chart into a prompt.
  Retrieve the narrowest relevant context (RAG with per-patient filter).

## SOC2 — Trust Services Criteria

SOC2 is about demonstrating you have controls and they work. For a
LangChain app, the Trust Services Criteria map:

| Criterion | LangChain mitigation |
|-----------|----------------------|
| Security (CC6) | XML injection boundary + canary; tool allowlist via `create_react_agent`; secret manager + `SecretStr` |
| Availability (CC7) | `max_retries=2`, circuit breakers, provider fallbacks (see `langchain-sdk-patterns`); rate limits (`langchain-rate-limits`) |
| Processing Integrity (CC7) | Pydantic output validation; tool-arg deny-list; structured logging |
| Confidentiality (CC6, CC9) | PII redaction middleware; OTEL content off in multi-tenant; per-tenant data isolation (P33) |
| Privacy (CC9) | Same as GDPR — explicit consent, data minimization, deletion workflow |

### SOC2 evidence a reviewer expects

- **Policy documents.** Acceptable use policy for LLM; prompt-injection
  response plan; incident response runbook.
- **Configuration artifacts.** Terraform/Helm manifests showing Secret
  Manager bindings, IAM policies, network isolation.
- **Audit logs.** Immutable log of every tool call, with tenant/user/
  request_id, retained per policy (typically 1 year for SOC2 Type II).
- **Access reviews.** Quarterly review of who has access to Secret Manager,
  OTEL backend, and the app's admin surface.

## Provider safety settings — decision matrix

| Provider | Default | When to override | How to document |
|----------|---------|------------------|-----------------|
| Anthropic | No per-category safety toggle (provider moderates server-side) | N/A — adjust via `system` prompt if needed | Record system prompt version in compliance doc |
| OpenAI | Moderation API available as a separate call | Add moderation pre-call for user-facing; skip for internal | Log moderation decision per request |
| Gemini | `HARM_BLOCK_THRESHOLD=BLOCK_MEDIUM_AND_ABOVE` across all categories | Medical / legal / security domains trip defaults (P65) | Record override per category in compliance doc, example below |

```python
# compliance_posture.py — committed to the repo, reviewed quarterly
GEMINI_SAFETY_PROFILE = {
    "version": "2026-04-21",
    "rationale": "Medical record summarization — HARM_CATEGORY_MEDICAL default "
                 "rejects legitimate clinical content. Mitigations: PII "
                 "redaction middleware upstream, Pydantic output validation, "
                 "human-in-loop review for any output with a safety-flag rating.",
    "settings": {
        "HARM_CATEGORY_MEDICAL": "BLOCK_NONE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_LOW_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
    },
    "review_cadence": "quarterly",
    "approver": "CISO",
}
```

## Audit-log schema

Minimum fields a SOC2 / HIPAA reviewer will expect on every LLM call:

```json
{
  "request_id": "01HXYZ...ULID",
  "timestamp": "2026-04-21T14:32:11Z",
  "tenant_id": "tenant-42",
  "user_id": "user-8821",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "prompt_hash": "sha256:abc123...",
  "prompt_redacted": "[EMAIL_1] asked about [PERSON_1]'s order",
  "response_summary": "Provided order status for redacted user",
  "tool_calls": [
    {"name": "lookup_order", "args_hash": "sha256:...", "duration_ms": 42}
  ],
  "input_tokens": 420,
  "output_tokens": 180,
  "safety_profile_version": "2026-04-21",
  "canary_hit": false,
  "pii_redactions": {"email": 1, "person": 1}
}
```

The `prompt_hash` lets you prove (via hash comparison) that a specific
prompt was or was not processed, without storing the raw content. The
`prompt_redacted` field is optional — include only if your retention policy
and legal basis support it.

## Resources

- [GDPR full text](https://gdpr-info.eu/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)
- [AICPA SOC2 Trust Services Criteria](https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services)
- [Anthropic BAA program](https://www.anthropic.com/legal/commercial-terms) (verify current links)
- [OpenAI Enterprise DPA](https://openai.com/policies/eu-data-processing-addendum)
- [Google Cloud Vertex AI data governance](https://cloud.google.com/vertex-ai/docs/general/data-governance)
- Pack pain catalog: P27, P65
