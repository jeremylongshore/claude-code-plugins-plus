# Official License Management contract and safety boundary

Source: [License Management API](https://developer.grammarly.com/license-management-api.html)
(accessed 2026-09-04).

The official user-list contract documents `user_id`, `institution_id`, email, name,
`last_activity_at`, and `is_admin`. It says that when a user has no activity,
`last_activity_at` is set to the time the user was created. The sanitized snapshot
requires a producer-attested keyed `resource_id_hmac_sha256` pseudonym and omits
identity attributes; the script neither creates the pseudonym, cryptographically
verifies its provenance, nor reconstructs omitted fields. The keyed
derivation happens in the organization's approved boundary.

The same page says admin licenses cannot currently be removed. Therefore admins are
always excluded from this plan, even when their activity is older than the supplied
cutoff. The candidate output is a review queue for a human license owner, not an
instruction to remove a user.

The invitee contract documents `created_at`, status, and `is_admin`, but not a
`last_activity_at` field. In particular, an expired invitee can still occupy a
license. This skill therefore does not infer inactivity from invitee creation time;
invitee governance requires a separate human decision.

## Institution-summary path conflict — unresolved

The page's “Getting the institution summary” endpoint heading states:

`GET https://api.grammarly.com/ecosystem/api/v1/institutions-summary`

Its example request states instead:

`https://api.grammarly.com/ecosystem/api/institutions-summary`

These are materially different paths. Preserve both as unresolved official evidence.
Fail closed and obtain direct provider confirmation before any integration owner
chooses a path. No script in this skill performs that request, selects a path, or
deletes users or invitees.
