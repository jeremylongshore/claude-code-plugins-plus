# TLS Theory — what this skill checks and why each check matters

## TLS handshake in one paragraph

A client opens a TCP connection to the server's TLS port. They negotiate a
**protocol version** (TLSv1.0–1.3), pick a **cipher suite** describing how
to authenticate, exchange keys, and bulk-encrypt, then exchange the
server's **certificate chain**. The client verifies the chain validates
to a trusted root and the leaf cert's SAN/CN matches the hostname it
intended to reach. If any step fails, the handshake aborts. If every step
succeeds, both sides derive session keys and switch to encrypted
application data.

Every check this skill performs maps to one of those four phases
(protocol, cipher, cert, hostname). A finding tells you which phase
landed in a posture below current best practice.

## Why protocol version matters

Each TLS version has known weaknesses that have driven the IETF and
NIST to mark them obsolete:

- **SSLv2/SSLv3** — DROWN (CVE-2016-0800), POODLE (CVE-2014-3566). Deprecated
  by RFC 7568 (SSLv3) and RFC 6176 (SSLv2). Should never appear on any
  production endpoint.
- **TLSv1.0** — BEAST (CVE-2011-3389), block-cipher IV-reuse vulnerabilities.
  Deprecated by RFC 8996 (March 2021). PCI DSS forbids since v3.1 (2015).
- **TLSv1.1** — same RFC 8996 deprecation. Inherited TLSv1.0's MAC-then-encrypt
  pattern with no AEAD support.
- **TLSv1.2** — current acceptable minimum. AEAD support via GCM and
  ChaCha20-Poly1305 cipher suites. Required by NIST 800-52r2.
- **TLSv1.3** — preferred. RFC 8446 (2018). Reduces handshake round trips,
  removes legacy options entirely, mandates forward secrecy.

Primary references:

- [RFC 8996 — Deprecating TLS 1.0 and TLS 1.1](https://datatracker.ietf.org/doc/html/rfc8996)
- [NIST SP 800-52r2 §3.1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf)
- [PCI DSS v4.0 Req 4.2.1.1](https://www.pcisecuritystandards.org/)

## Why cipher suite matters

A cipher suite in TLSv1.2 names four algorithms:
`TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384` =
ECDHE (key exchange) + RSA (auth) + AES-256-GCM (bulk) + SHA384 (HMAC for PRF).

A weak cipher in any axis weakens the whole connection:

- **NULL** ciphers — no encryption. Any in-path attacker reads cleartext.
  Used historically for negotiation testing; should never be permitted.
- **EXPORT** ciphers — intentionally weakened in the 1990s to comply with
  US export controls. Broken (FREAK CVE-2015-0204, Logjam CVE-2015-4000).
- **aNULL** (anonymous DH) — no server authentication. MITM trivially.
- **RC4** — biased keystream byte distribution makes plaintext recovery
  feasible at scale ([RFC 7465](https://datatracker.ietf.org/doc/html/rfc7465)).
- **3DES** — 64-bit block size makes Sweet32 (CVE-2016-2183) practical
  for long-lived sessions.
- **CBC-mode without AEAD** — vulnerable to padding-oracle attacks
  (Lucky13, POODLE). AEAD modes (GCM, CCM, ChaCha20-Poly1305) eliminate
  the class.
- **Non-(EC)DHE key exchange** — no forward secrecy. If the server key is
  later compromised, all past traffic an attacker captured decrypts.

Mozilla maintains the canonical "what's safe to use" recommendation at
[ssl-config.mozilla.org](https://ssl-config.mozilla.org/). The
"intermediate" config is the right default for backward-compat with
existing browsers; the "modern" config is for greenfield TLSv1.3-only
deployments.

## Why certificate expiry matters

Three classes of expiry pain:

1. **Service outage** — the next handshake fails, the service is
   unreachable to validating clients. This is the most common security-
   related outage cause in production.
2. **Forced rotation noise** — short-notice renewals trigger urgent
   change tickets at 2am. Automated renewal (certbot, caddy) is the fix;
   surfacing expiry early gives you time to verify automation is healthy.
3. **OCSP/CRL window** — even after renewal, OCSP stapling caches the old
   response for some seconds; clients hitting the lag window see slow
   handshakes or transient validation errors.

NIST SP 800-52r2 §4.1 mandates lifecycle monitoring. PCI DSS Req 4.2.1
flags expired certs as cardholder-data-exposure issues.

## Why hostname matching matters

RFC 6125 §6 requires the client to verify the leaf cert's SAN (or, for
legacy clients, CN) covers the hostname it dialed. A mismatch means
either:

- The server is mis-configured (cert for `example.com` serving
  `api.example.com` traffic) — operational error.
- A proxy or load balancer is presenting a different cert than intended —
  configuration drift.
- An attacker has hijacked DNS or BGP and presented their own cert — the
  client SHOULD reject and surface to the user, but legacy clients may
  not, opening MITM.

Wildcard cert handling: `*.example.com` covers `api.example.com` and
`www.example.com` but NOT `example.com` (the apex) or
`x.api.example.com` (deeper sub). This skill's `_check_hostname`
implements the RFC 6125 rules precisely.

## Why key size matters

Brute-force resistance against current attacker compute:

- **RSA < 2048 bits** — factoring within reach for sustained adversary
  effort (1024-bit broken by 2003 academic teams; 2048 still considered
  safe through ~2030 per NIST SP 800-57).
- **ECDSA < 256 bits** — discrete-log over weak curves vulnerable to
  Pollard rho. 256-bit curves (P-256, Curve25519) are the current floor.

NIST SP 800-52r2 §3.4 mandates these floors. PCI DSS Req 4.2.1.1
includes "strong cryptography" requirement; the SAQ glossary defines
"strong" by the same NIST bands.

## Primary sources

- [NIST SP 800-52r2 — Guidelines for the Selection, Configuration, and Use of TLS Implementations](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf)
- [NIST SP 800-57 — Recommendation for Key Management](https://csrc.nist.gov/projects/key-management/key-management-guidelines)
- [Mozilla TLS Configuration Generator](https://ssl-config.mozilla.org/)
- [RFC 8446 — TLS 1.3](https://datatracker.ietf.org/doc/html/rfc8446)
- [RFC 8996 — Deprecating TLS 1.0 and TLS 1.1](https://datatracker.ietf.org/doc/html/rfc8996)
- [RFC 6125 — Server Hostname Verification](https://datatracker.ietf.org/doc/html/rfc6125)
- [RFC 7465 — Prohibiting RC4 Cipher Suites](https://datatracker.ietf.org/doc/html/rfc7465)
