# Certificate Posture Theory

## OCSP stapling — why it matters

OCSP (RFC 6960) lets clients ask the issuing CA "is this cert still
valid?" at handshake time. The problem: every client phoning home for
every connection (a) adds latency, (b) leaks browsing metadata to the
CA, (c) creates a CA-side single point of failure.

OCSP stapling (RFC 6066 `status_request` extension) fixes this. The
server periodically fetches a signed OCSP response from the CA, caches
it, and serves it inline during the TLS handshake. Clients trust the
stapled response because the CA's signature is verifiable offline.

If your server doesn't staple:

- **SOC2 CC6.6 / CC6.7** auditors flag this as transmission-confidentiality
  weakness because the CA learns who's connecting where.
- **Privacy regulators** treat OCSP traffic as PII metadata.
- **Latency** — first-handshake users pay an extra round trip to the CA.
- **Reliability** — if the CA's OCSP responder is down, clients with
  must-staple cached fail-closed (the original purpose of Must-Staple).

## Certificate Transparency — why ≥2 SCTs

CT logs (RFC 6962) are append-only, publicly auditable records of every
issued certificate. The intent: if a CA mis-issues a cert (e.g., for
google.com to an attacker), someone monitoring the logs sees it.

The model relies on browser enforcement. Chrome's CT policy (active
since 2018) requires every TLS cert to be accompanied by ≥2 Signed
Certificate Timestamps from independently-operated logs. Delivery
options:

1. **Embedded** — SCTs baked into the cert at issuance via the
   `precertificate_signed_certificate_timestamps` extension (the common
   path; what this skill checks).
2. **TLS extension** — server sends SCTs in the handshake via the
   `signed_certificate_timestamp` extension.
3. **OCSP-stapled SCTs** — SCTs delivered alongside an OCSP staple.

Public CAs (Let's Encrypt, ZeroSSL, DigiCert, etc.) all submit to ≥2
logs at issuance. If the leaf has fewer than 2 SCTs, the most common
cause is a private CA cert masquerading as public.

Chrome enforcement is silent — connections fail, users see generic
errors, and the diagnostic surface is limited. This skill surfaces the
SCT shortage explicitly.

## Chain ordering — RFC 5246 §7.4.2

The TLS Certificate message includes a `certificate_list` field. The
RFC requires it to be ordered: leaf first, each subsequent certificate
must directly certify the one preceding it, root SHOULD be excluded
(clients have it in their trust store; sending it is wasted bytes).

Common misorder causes:

- Cert files concatenated in alphabetical order rather than chain order.
- A migration where `cat *.pem > fullchain.pem` orders by filename.
- An ops engineer who saw the chain rejected and reordered "fix" trips
  by also including the root.

Older clients (Java 6, older curl) reject out-of-order chains. Modern
browsers tolerate but log. Either way, an audit catches it; a slow
handshake or odd-platform compatibility report leads back to chain
ordering.

## AIA extension — Authority Info Access

RFC 5280 §4.2.2.1 defines two access methods worth tracking:

- **CA Issuers** — URL where the issuing intermediate cert can be
  downloaded. Some clients fetch missing intermediates here ("AIA chasing").
- **OCSP responder** — URL where revocation can be queried.

Missing AIA → clients with incomplete chains have no recovery path;
clients that don't trust a stapled OCSP response have nowhere to verify.

Both fields are CA-side issuance config. Public CAs include them by
default. A leaf cert without AIA is almost certainly from a private CA
or a misconfigured private PKI.

## Wildcard scope — CA/B Baseline Requirements §3.2.2

CA/Browser Forum BR forbids wildcards at certain scopes:

- `*.com`, `*.net`, etc. — public suffix; would cover every site on the
  TLD. Public CAs MUST refuse to issue.
- `*.example` (single-label) — same reasoning at private-TLD level.

Allowed scope: `*.example.com` (covers `api.example.com` but not
`example.com` itself, and not `x.api.example.com`).

A public cert with over-broad wildcard scope means the CA mis-issued
and may be subject to log-monitor investigation; private-CA wildcards
at apex-TLD scope are equally dangerous because anyone with the
private key can MITM any subdomain.

## Key Usage extension — RFC 5280 §4.2.1.3

The KU extension asserts what cryptographic operations the cert's
public key is authorized for. TLS server certs need at minimum:

- `digitalSignature` — for the server's ServerKeyExchange signature in
  non-static-RSA modes
- `keyEncipherment` — for static RSA key transport (legacy, rare in
  modern stacks)

Missing `digitalSignature` on a TLS server cert is unusual; strict
clients reject it.

## Chain length — operational concern

Modern CAs issue 2-cert chains: leaf + one intermediate (the root is
in client trust stores). Chains of 3+ usually mean:

- Cross-signing for backward compatibility (intentional, fine).
- Misconfiguration including the root (waste, fixable).
- Vendored chain from a different CA (rare, audit-flagged).

>4 certs raises handshake latency noticeably (more bytes, more
verification ops on the client side); flagged LOW for awareness.

## Primary sources

- [RFC 5246 — TLS 1.2 §7.4.2](https://datatracker.ietf.org/doc/html/rfc5246#section-7.4.2)
- [RFC 5280 — Internet X.509 PKIX](https://datatracker.ietf.org/doc/html/rfc5280)
- [RFC 6066 — TLS Extension Definitions §8 (status_request)](https://datatracker.ietf.org/doc/html/rfc6066#section-8)
- [RFC 6960 — OCSP](https://datatracker.ietf.org/doc/html/rfc6960)
- [RFC 6962 — Certificate Transparency](https://datatracker.ietf.org/doc/html/rfc6962)
- [CA/Browser Forum Baseline Requirements](https://cabforum.org/baseline-requirements-documents/)
- [Chrome CT Policy](https://googlechrome.github.io/CertificateTransparency/ct_policy.html)
