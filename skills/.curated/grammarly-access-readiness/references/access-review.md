# Access review decisions

Grammarly documents API credentials for administrators with Grammarly Enterprise or
institution-wide Grammarly for Education licenses. A consumer account, unspecified
education plan, team-tier assumption, or self-authorization claim is not readiness
evidence.

Review in this order:

1. Confirm the access tier and administrator authority out of band.
2. Confirm credentials will be injected from an approved environment or secret manager.
3. Select only the operations the integration needs.
4. Compare granted scopes to the script-derived exact set.
5. For AI Detection or Plagiarism, record an authorized decision on the official scope
   catalog inconsistency; do not guess alternate scopes.

`READY` is a configuration-plan result. It does not mean Grammarly approved the
client, a beta API is enabled, a token is valid, or a production request succeeded.

If a credential is pasted, do not quote it. Stop the review, use the owning incident
process to rotate or revoke it, and start over with metadata only. The audit script has
no network or write behavior.

Sources checked 2026-09-04:
[OAuth credentials](https://developer.grammarly.com/oauth-credentials.html) and
[first API request](https://developer.grammarly.com/your-first-api-request.html).
