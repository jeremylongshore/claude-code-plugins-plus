# The agent card is an identity claim wearing a discovery document's clothes

## The observation

Strip an agent card down and what remains is: a name, an address, a list of things the holder says it
can do, and an optional self-attached signature. That is an **ID badge**. It is not comms — the
messaging surface is `SendMessage`, the task lifecycle, and the streams, none of which the card
touches.

Which raises the useful question: if the card is doing identity, why is it doing it with a bespoke
JSON document instead of an identity standard that already exists?

## What a real workload identity looks like

SPIFFE — Secure Production Identity Framework For Everyone, a CNCF project — solves exactly this
problem for workloads:

| Concept | SPIFFE | A2A agent card |
| --- | --- | --- |
| Identifier | `spiffe://trust-domain/path` — a URI naming the workload | `name` — a self-asserted display string |
| Credential | SVID: an X.509 cert or JWT the workload can present | `signatures[]` — optional JWS over the document |
| Verification root | A **trust bundle** distributed out of band by the trust domain | `jku` — a JWKS URL, frequently on the same origin as the card |
| Issuer | An attesting authority (SPIRE) that verified the workload before issuing | Whoever served the JSON |
| Rotation | Short-lived SVIDs, rotated automatically | `version` bump, by convention |

The row that decides everything is **verification root**. A2A does define a signature path — a JWS
with `kid` and `jku` pointing at a JWKS, and the spec says public keys SHOULD be retrieved over
secure channels. But if the verifier learns the key location *from the card*, the card is verifying
itself. Nothing is established that an attacker who controls the origin could not also arrange.

SPIFFE's answer is that the trust bundle arrives through a channel the workload does not control. That
one difference is what separates "signed" from "authenticated."

## Why this matters here, concretely

**This is the reason the card is treated as untrusted input.** Not squeamishness — the document simply
carries no identity a verifier can check without out-of-band material. Given that, the only sound
posture is the one this skill takes: enumerate claims, attach dispositions, and refuse to convert any
of it into local authority.

It is also the reason the `a2a-client` MCP server needs a network guard at all. If a card's interface
URL came with a verifiable identity bound to a trust domain, "is this a host I should talk to" would be
answerable from the credential. It does not, so the guard answers it from operator-supplied policy
instead — an allowlist and a private-range refusal.

## The hook that already exists

`securitySchemes` includes a **mutual TLS** scheme. That is the natural slot for a real workload
identity: present an X.509-SVID, verify the peer against a trust bundle obtained out of band, and the
agent's identity stops being a string in a JSON file and becomes something the transport establishes
before any A2A message is parsed.

Nothing in this pack implements that — it needs infrastructure (an attesting authority, bundle
distribution) that is an organizational decision, not a skill. But it is the direction, and it is worth
knowing that the standard's own security-scheme list leaves the door open.

## What to take from this

1. **Separate the two jobs when reasoning about a system.** Discovery answers *where and what*.
   Identity answers *who, provably*. The card conflates them, and conflating them is what makes
   "trusting the card" sound reasonable when it is not.
2. **A signature is not an identity.** Report `unverified` unless a key arrived independently.
3. **Where real identity exists, prefer it.** Inside an infrastructure that already issues workload
   identities, bind the A2A connection to mutual TLS and treat the card as what it is: a convenience
   index of endpoints and capabilities, not a credential.
4. **Where it does not, compensate with policy.** Operator-nominated destination allowlists, refusal of
   private ranges, and human sign-off on adoption — which is what the rest of this pack does.
