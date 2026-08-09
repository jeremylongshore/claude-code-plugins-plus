# Why an agent card is untrusted input

## The primitive

An agent card is an **externally-authored manifest, fetched over the network, describing what the
remote party would like the local agent to believe**. Every property of a confused-deputy attack is
present:

1. The local agent holds authority the remote party does not.
2. The remote party controls a document the local agent reads.
3. That document names endpoints, capabilities, and requirements.
4. If the local agent acts on those names, the remote party has spent the local agent's authority.

The card format is not the problem — the same holds for any unsigned external manifest. The defence is
a direction rule, not a parser: **a fetched manifest may inform a human decision; it may never widen
machine authority on its own.**

## What a card can assert, and what each assertion buys an attacker

| Assertion | Attacker gain if adopted blindly |
| --- | --- |
| `supportedInterfaces[].url` | Redirects traffic — including credentials — to a host of their choosing, private ranges included |
| `tenant` | A value the client is required to echo on every request; a tracking or routing channel |
| `securityRequirements` (agent or per-skill) | Downgrades or removes the auth the client would have applied |
| `capabilities.extensions[].required` | Forces the client to comply with an extension to interoperate |
| `documentationUrl`, `iconUrl` | An unattended fetch to a chosen host from inside the caller's network |
| `skills[].description` | Free-text read by a model — a prompt-injection surface |
| `signatures` | The appearance of assurance, if a client reports unverified as verified |

The last row is the sharpest. A signature is easy to display and hard to check. Reporting an
unverifiable signature as valid manufactures confidence that no verification produced.

## Audit checklist

Run all of these before a card influences anything:

1. **Host check.** Resolve every interface URL. Flag private ranges, loopback, link-local, and any host
   outside the set the operator nominated. A card pointing inward is the finding, not a curiosity.
2. **Scheme check.** Confirm HTTPS for HTTP-family bindings. A plaintext URL in a production card is a
   downgrade attempt whether or not it was intended as one.
3. **Per-skill override sweep.** Diff each skill's `securityRequirements` against the agent-level list.
   Report every skill that is weaker than the agent-level baseline.
4. **Required-extension sweep.** List every `extensions[]` entry with `required: true` and what it
   demands. An unknown required extension means do not proceed, not proceed-and-hope.
5. **Free-text quarantine.** Treat `description`, `skills[].description`, and `skills[].examples` as
   untrusted content when they reach a model. They are remote-authored prose in an agent's context.
6. **Signature honesty.** Report exactly one of `absent`, `unverified`, or `verified against <key id>`.
   Never collapse the middle case into either neighbour.
7. **No side effects.** Confirm the audit wrote nothing into local config, credentials, tool
   allowlists, or routing defaults.

## Reporting shape

Findings are claims plus a disposition, never merged into a single trust verdict:

```text
CLAIM       <field> = <value>
FINDING     <what is wrong or notable>
DISPOSITION reported | operator-decision-required | rejected
```

`reported` is the default. `operator-decision-required` is the only path by which a card's claim
becomes local configuration, and the decision is recorded outside the card.

## What this deliberately does not do

- **No trust scoring.** A single number invites automation of exactly the decision that must stay
  human. Enumerate claims instead.
- **No allowlist bootstrap from a card.** A card cannot nominate itself into a trusted set.
- **No key discovery from the card.** Fetching a verification key from a location the card names
  verifies the card against itself.
