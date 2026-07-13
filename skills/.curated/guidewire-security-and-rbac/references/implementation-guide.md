# Guidewire Security & RBAC — Implementation Guide

Extended walkthroughs and supplementary patterns for the SKILL.md.

## Vault Agent integration

For deployments where SOPS+age does not fit (e.g., short-lived deploy units, FedRAMP environments, rotating database credentials), HashiCorp Vault Agent provides equivalent properties with a different operational shape.

```hcl
# vault-agent.hcl
auto_auth {
  method "kubernetes" {
    config = {
      role = "guidewire-integration"
    }
  }
  sink "file" {
    config = { path = "/var/run/secrets/vault-token" }
  }
}

template {
  destination = "/etc/integration/secrets.env"
  contents = <<EOT
GW_CLIENT_ID="{{ with secret "kv/data/guidewire/prod" }}{{ .Data.data.client_id }}{{ end }}"
GW_CLIENT_SECRET="{{ with secret "kv/data/guidewire/prod" }}{{ .Data.data.client_secret }}{{ end }}"
EOT
  perms = "0600"
}
```

Vault Agent's renew-and-rotate semantics handle the dual-secret window automatically: Vault rotates the upstream credential, the template re-renders, the runtime re-reads on `SIGHUP`. No manual rotation runbook required.

## Dynamic secrets

Vault can issue per-deploy Service Application credentials that automatically expire after a configurable TTL. Combined with GCC's API for app registration (where available), every deployment gets its own short-lived `client_id`/`client_secret` pair, eliminating long-lived credentials entirely.

This is the strongest posture available for prod environments. Operational cost: a working Vault deployment, integration with GCC's app-registration API (not all tenants expose this), and tooling to manage the per-deploy registrations.

## Token-binding (RFC 8471)

Token binding cryptographically ties a bearer token to the TLS connection that issued it; a stolen token is unusable from a different connection. Cloud API support is tenant-dependent; check with the carrier's IAM team before relying on it.

## FIPS-140 trust stores

Carriers operating under federal contracts (e.g., serving as TPA for federal employee health benefits) may require FIPS-140-validated cryptographic modules. The default JVM trust store is not FIPS-validated; switch to BouncyCastle FIPS or the IBM JSSE FIPS provider, depending on JVM vendor.

```bash
java -Dcom.sun.net.ssl.checkRevocation=true \
     -Djava.security.properties=fips.security.properties \
     -jar app.jar
```

This is rarely needed for commercial P&C carriers but is non-negotiable for government-program TPAs.

## Federated identity for human users

This SKILL.md focuses on Service Applications (M2M auth). When the integration also handles human users (broker portal, claims self-service), use Authorization Code flow with PKCE and federate to the carrier's IdP (Okta, Azure AD, Ping). Do not implement username/password against Cloud API directly.

The OAuth Authorization Code flow is documented separately; this skill covers only the M2M side.

## Document-level encryption

Some Cloud API resources accept attached documents (claim photos, policy declarations, evidence). Documents may carry stronger PII than the structured fields. Encrypt at rest before upload using a KMS key the carrier controls; the document body becomes opaque to anyone without KMS decrypt access.

## Per-tenant logging

For multi-tenant integrations, log streams should partition by tenant. Datadog tags (`tenant:acme`), Splunk indexes (`integration-acme`), or Loki labels are all viable. The benefit: a tenant's logs never co-mingle in a single search; an investigator querying tenant A cannot see tenant B's data.

## Incident response checklist (template)

```markdown
## Incident: <slug>
- **Detected**: <timestamp>
- **Detector**: <person/system>
- **Tenant**: <tenant-slug or "all">
- **Suspected leak vector**: <slack/log/public-commit/...>
- **Window of exposure**: <start> to <end>

## Response
- [ ] Credentials rotated in GCC at <timestamp>
- [ ] Encrypted secret file updated at <commit>
- [ ] Deployment confirmed at <timestamp>; new token claims show iat > rotation time
- [ ] GCC audit pulled for <client_id> over window — <N> calls reviewed
- [ ] Anomalies: <list>
- [ ] Postmortem doc: <link>
- [ ] Audit table row inserted with reason="credential-rotation-suspected-leak"

## Closure
- **Closed**: <timestamp>
- **Time-to-rotate**: <minutes>
- **Root cause**: <summary>
- **Action items**: <list>
```

Practice the runbook quarterly with a tabletop exercise. The first real incident should not be the first time anyone has run through the steps.

## Related

- `SKILL.md` — production patterns
- `references/API_REFERENCE.md` — role catalog, PII paths, compliance mapping
- Sibling `guidewire-install-auth` — token-cache, dual-secret rotation
- Sibling `guidewire-observability-and-incident-response` — alerts that drive incidents into this runbook
