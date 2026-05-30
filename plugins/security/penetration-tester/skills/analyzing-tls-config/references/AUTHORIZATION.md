# Authorization Attestation Pattern

Active security scanning against a target you don't own is a federal
crime in the United States (Computer Fraud and Abuse Act, 18 U.S.C. §
1030) and similar offenses in most jurisdictions globally. Every
penetration-tester v3 active-scan skill enforces a two-step attestation
gate so no scan fires by accident.

## The two-step gate

### Step 1 — Verbal attestation in Claude's conversation

Before invoking the scanner, Claude is instructed (via the skill's
SKILL.md "Step 1 — Confirm Authorization" section) to ask the user
verbatim:

> "Do you have authorization to perform security testing on this target?
> I need confirmation before proceeding."

If the user says no, or is unsure, Claude refuses to proceed and points
the user at the ROE template below to obtain written authorization
first.

### Step 2 — `--authorized` flag on the scanner

The Python scanner also requires the `--authorized` flag for any target
that isn't obviously local (loopback / RFC1918 / link-local). The flag
must be passed explicitly each invocation — there is no environment-
variable fallback, because CI environment variables can be set by
anyone with repo write access and silently authorize scans against
arbitrary targets.

Carve-outs (no `--authorized` needed):

- `localhost`, `127.0.0.0/8`, `::1`
- RFC1918 ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- Link-local: `169.254.0.0/16`, `fe80::/10`

Anything else: gate fires; scanner exits with code 2 and instructional
message.

## Rules of Engagement (ROE) — minimum template

Use this as the starting point for written authorization to test a
target you don't otherwise own. Adapt to your local legal counsel's
guidance; this is a working template, not a substitute for legal review.

```
RULES OF ENGAGEMENT — Security Testing Authorization

Date:                    [YYYY-MM-DD]
Authorizing party:       [organization name]
Authorizing signatory:   [name, title, contact email]
Tester:                  [your name / org]
Engagement period:       [YYYY-MM-DD] through [YYYY-MM-DD], inclusive.

Targets in scope:
    [URL or IP range, one per line]

Targets explicitly out of scope:
    [URL or IP range, one per line]

Permitted test types:
    [ ] Passive enumeration (no traffic to target)
    [ ] Active scanning (HTTP probes, TLS handshakes, port scans)
    [ ] Authentication testing (default credentials, weak password lists)
    [ ] Application-layer testing (SQL injection, XSS, command injection)
    [ ] Denial-of-service testing — DEFAULT NO; check only if explicit
    [ ] Social engineering — DEFAULT NO; check only if explicit
    [ ] Physical access testing — DEFAULT NO; check only if explicit

Maintenance windows:
    [Window during which tester may operate without notification]

Notification protocol:
    Before starting:       [Slack/Email/Phone to whom]
    On finding any CRITICAL: [Slack/Email/Phone to whom, within how long]
    On any service outage: [Phone to whom, within how long]
    Daily status:          [Email to whom, before what time]

Stop conditions:
    The tester WILL halt all active scanning if:
    - Target service goes down (regardless of cause)
    - Authorizing party requests halt
    - A finding suggests active exploitation by a third party
    - The engagement period ends

Data handling:
    All findings, evidence, and reports are confidential and shared only
    with [list]. Tester will retain copies for [N] days post-engagement,
    after which all materials are destroyed.

Signatures:
    Authorizing signatory: _______________  Date: ___________
    Tester:               _______________  Date: ___________
```

## What the skill does NOT enforce (you have to)

The `--authorized` flag is an attestation — it does not prove
authorization, just records that the tester asserts it. The tester
remains legally responsible for the truth of that assertion.

The skill does not:

- Verify the target is in scope of a real ROE.
- Verify the tester is who they say.
- Verify the engagement period is active.
- Notify the target party.

These are operator responsibilities. The skill provides the
defense-in-depth gate so a misconfigured CI workflow or a curious
engineer doesn't accidentally fire active scans at production third-
party targets.

## When to skip the gate

Never. If you find yourself wanting to bypass the gate, that is the
signal to stop and obtain authorization first. The gate exists because
silently disabled attestation has caused real legal exposure for
penetration testers in the past.

If you are scanning your own loopback / RFC1918 services and the gate
is misfiring (e.g., your DNS resolves a public hostname to a private
IP), use the `--port` flag against the IP directly rather than
disabling the gate.

## References

- [Computer Fraud and Abuse Act (CFAA), 18 U.S.C. § 1030](https://www.law.cornell.edu/uscode/text/18/1030)
- [Penetration Testing Execution Standard (PTES) — Pre-engagement Interactions](http://www.pentest-standard.org/index.php/Pre-engagement)
- [OWASP Web Security Testing Guide v4.2 § 2.1 — Set the scope](https://owasp.org/www-project-web-security-testing-guide/v42/)
- [NIST SP 800-115 — Technical Guide to Information Security Testing](https://csrc.nist.gov/publications/detail/sp/800-115/final)
