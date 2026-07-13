# Hardcoded-Secrets Theory

## Why this class persists despite being well-known

The pattern is well-understood: don't hardcode credentials in source.
Every engineering team knows this. Every framework's getting-started
guide opens with "set this in your `.env` file, not in code." Yet
the class remains the #1 root cause of credential compromise year
over year.

Three reasons:

1. **The "just for testing" trap.** An engineer is debugging
   integration with a new API. The right thing is to set
   `STRIPE_KEY=...` in the local env and read from there. The fast
   thing is to paste the key into the integration test file as a
   literal. The test works, the engineer moves on, the literal
   stays.

2. **Migration leftovers.** A codebase migrated from one secrets
   pattern to another (e.g., from `.env` to AWS Secrets Manager)
   often leaves stale literals from the pre-migration state, even if
   the runtime fetches from the new location.

3. **Test fixtures with real keys.** Integration tests need real
   credentials to test against real APIs. Some teams check those
   into a `tests/fixtures/` directory with full intent. The test
   harness is now a permanent credential leak surface.

The defensive answer is automated detection: scan on every commit
(pre-commit hook), every push (CI gate), every release (full audit).
Tools like gitleaks, trufflehog, and GitHub Secret Scanning all
implement variations of the same regex library this skill uses.

## Why provider-specific regex is the right pattern

The naive approach is entropy detection: "find any long string with
high randomness." The problem is the false-positive rate. Hash
digests, base64-encoded image data, minified JavaScript, and
compiled artifacts all look entropy-shaped.

Provider-specific regex works because credential issuers use
prefixed shapes intentionally — partly for routing, partly so their
own scanners can find leaks in customer code. Examples:

| Provider | Prefix | Why prefixed |
|---|---|---|
| AWS | `AKIA`, `ASIA`, `ABIA` | IAM type indicator (`AKIA` = long-term, `ASIA` = STS session) |
| GitHub | `ghp_`, `gho_`, `ghs_`, `ghu_`, `ghr_` | Token-class router |
| Stripe | `sk_live_`, `sk_test_`, `rk_live_`, `pk_live_` | Environment + role |
| Anthropic | `sk-ant-api03-` | Format-version + env |
| OpenAI | `sk-` and `sk-proj-` | Origin (user vs project) |
| Slack | `xoxb-`, `xoxp-`, `xoxa-` | Token type |
| Twilio | `AC`, `SK` | Account SID vs API key SID |
| Google | `AIza` | Service-account vs user-creds router |

The prefix means the provider's own scanner can find the leak the
moment it lands in a public repo (GitHub Secret Scanning auto-
notifies the provider). The scanner runs at machine speed: a public
gist containing `AKIA...` is detected in seconds, and AWS gets a
push notification.

This skill scans the same set on the assumption: if the provider's
bots will find it within seconds, the defensive posture is to find
it before the commit lands.

## The 1-minute leak window

For public repos, the time between commit landing and credential
extraction is on the order of seconds. GitHub Secret Scanning is
roughly real-time; bot operators scraping the public push event
stream are also real-time. By the time a developer notices the
credential in their `git log` and force-pushes a rewrite, the
extraction has happened. The credential must be considered
compromised from the moment of push, regardless of subsequent
history-scrub.

For private repos: window depends on access posture. If contractors
can clone, the window is "until you trust every contractor with
every credential ever committed." If only employees clone, the
window is "until any employee departs."

Either way: rotate is mandatory, history-scrub is optional.

## Entropy as a fallback

Provider regex covers known credential shapes. New providers and
custom internal tokens don't match.

Shannon entropy measures information density in a string. Higher
entropy = less compressible = more "random-looking." Real
credentials are by design high-entropy (an attacker brute-forcing a
low-entropy credential succeeds instantly).

The threshold of ~4.5 bits/char is empirically calibrated:

- English text: ~3.5
- Base64: ~6.0
- Hex: ~4.0
- Random 32-char: ~5.0+

Above 4.5 in a field labeled `key:`, `token:`, `secret:`,
`password=` is a strong signal. Below 4.5 is usually English /
placeholder / template variable.

False positives:

- High-entropy hashes (commit SHAs, content hashes) appearing in a
  field labeled `key:` (e.g., `cache_key: a3b9...`). Use context to
  filter.
- Long base64-encoded test fixtures (PDF content, certificate
  blobs). The entropy check passes; the human-verification step
  rejects.

The skill emits these as MEDIUM, not CRITICAL, with explicit
"requires verification" framing.

## History-scrub decision framework

After finding a leaked credential in source:

**Always rotate the credential.** Non-negotiable.

**History scrub depends on these inputs:**

1. **Is the repo public?** Yes → scrub is roughly futile. Anyone
   who cloned has the history; mirror sites cache it. Public repo
   = "publish a forever-archive of every commit ever made."
2. **Is the credential still in the file's current state?** Yes →
   scrub removes the live exposure. No (file's been fixed) → history
   is the only remaining exposure surface.
3. **Are clones controlled?** Yes (private repo, employees only) →
   force-push + force-pull on every clone is feasible. No → don't
   bother.
4. **How long has the credential been in history?** Days → scrub
   may catch unindexed copies. Months → assume copies exist
   permanently.

**Pragmatic default:** rotate, fix the current state, don't scrub
history. The credential is dead either way; the historical
disclosure of "we leaked something at this point in time" is mostly
narrative, not technical risk, once the credential is rotated.

**Exception:** if the credential CAN'T be rotated (e.g., it's
embedded in a customer's deployed binary), scrub becomes the only
remediation. Plan accordingly.

## Why test directories are excluded by default

Test fixtures often contain credential-shaped strings that ARE
placeholders:

```python
# tests/fixtures/auth.py
TEST_API_KEY = "ghp_FAKE0000000000000000000000000000000000"
TEST_AWS_KEY = "AKIATESTKEY12345678"
```

These match the regex but are deliberately fake. Scanning tests by
default produces high false-positive rates that train operators to
ignore findings.

The `--include-tests` flag is for the audit case: when reviewing an
inherited codebase, you DO want to know whether fixtures contain
real credentials someone forgot to redact. The flag is opt-in.

## Primary sources

- [CWE-798 Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)
- [CWE-321 Use of Hard-coded Cryptographic Key](https://cwe.mitre.org/data/definitions/321.html)
- [OWASP A07:2021 Identification and Authentication Failures](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)
- [GitHub Secret Scanning patterns](https://docs.github.com/en/code-security/secret-scanning/secret-scanning-patterns)
- [AWS IAM access-key reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
- [Trufflehog detector list](https://github.com/trufflesecurity/trufflehog/tree/main/pkg/detectors)
- [Gitleaks rules](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml)
