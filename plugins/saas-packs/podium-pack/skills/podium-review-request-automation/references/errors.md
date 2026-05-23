# Errors — podium-review-request-automation

Lookup table for `ERR_REVIEW_*` codes raised by the bridge service and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_REVIEW_001 — cooldown_violation_attempted

- **HTTP**: N/A (raised by `CooldownGate.can_send` returning False)
- **Cause**: A schedule-time evaluation found the contact's phone already in the cooldown window.
- **Detection**: `gate_review_request()` returns False with audit event `review_send_skipped_cooldown`.
- **Action**: No action — this is the system working correctly. Log and drop the inbound event. If the merchant complains about low review volume, run `cooldown_check.py` for a sample of skipped phones and confirm the window matches their expectation.

## ERR_REVIEW_002 — refund_status_blocked_send

- **HTTP**: N/A (raised at fire-time during the buffer)
- **Cause**: The Shopify order's `financial_status` matched `refunded`, `partially_refunded`, or `voided`, or `cancelled_at` was set.
- **Detection**: Fire-time `shopify.get_order()` returns a refunded/cancelled state; audit event `review_send_skipped_refund`.
- **Action**: No action — system working correctly. The refund-race buffer caught the case. Verify in the audit log that this scenario is happening at the expected refund rate.

## ERR_REVIEW_003 — optout_predicate_blocked_send

- **HTTP**: N/A (raised by `is_opted_out`)
- **Cause**: The merged contact record has at least one opt-out flag set.
- **Detection**: `is_opted_out()` returns True; audit event `review_send_skipped_optout`.
- **Action**: No action at the bridge level. If the merchant disputes the opt-out, run `optout_compliance_audit.py` for that phone — the output will show which specific flag is set and from which source flow.

## ERR_REVIEW_004 — phone_not_e164

- **HTTP**: N/A (raised by `normalize_e164`)
- **Cause**: The customer phone on the Shopify order cannot be parsed to E.164 (missing country code, malformed, internal extension format).
- **Detection**: `normalize_e164()` raises before cooldown check.
- **Action**: Log + drop. Open a ticket with the merchant to add a phone-format validator to their Shopify checkout. Do NOT fall back to a heuristic country code — silent mis-routing is worse than a missed request.

## ERR_REVIEW_005 — podium_invalid_phone

- **HTTP**: 400 from `POST /v4/review-invitations`
- **Cause**: Podium rejects the phone as unreachable (e.g., landline, VoIP that can't receive SMS).
- **Detection**: API call returns 400 with body `{"error": "invalid_phone"}`.
- **Action**: Log + skip + record the phone with a `non_sms_capable` flag on the contact so future attempts can be skipped at the gate. Do not retry.

## ERR_REVIEW_006 — podium_cooldown_violation

- **HTTP**: 409 from `POST /v4/review-invitations`
- **Cause**: Podium's server-side cooldown rejected the send (Podium maintains its own cooldown floor independent of ours).
- **Detection**: API call returns 409.
- **Action**: Trust Podium — log + skip. Do NOT bypass with retry. This indicates our cooldown is shorter than Podium's; consider raising `cooldown.default_days` to match.

## ERR_REVIEW_007 — invitation_failed_carrier

- **HTTP**: N/A (raised by `outbox.record_failed`)
- **Cause**: Podium accepted the send but the carrier filtered it (T-Mobile spam filter, Verizon STIR/SHAKEN rejection, etc.).
- **Detection**: Inbound webhook `review_invitation.failed` with reason in `{carrier_filtered, undeliverable}`.
- **Action**: Roll back cooldown for the phone (the customer never received the message). Flag the phone for manual review. Repeated carrier failures for the same merchant may indicate an upstream SMS reputation issue — escalate to Podium support.

## ERR_REVIEW_008 — invitation_failed_optout

- **HTTP**: N/A
- **Cause**: Podium reports the send failed because the recipient previously replied STOP to a Podium message on a different flow.
- **Detection**: Inbound webhook `review_invitation.failed` with reason in `{recipient_optout, stop_keyword}`.
- **Action**: Propagate the opt-out to the merged contact record via `PATCH /v4/contacts/{id}` setting `podium_keyword_optout=true`. Roll back cooldown. This is the failure mode that catches opt-out drift before it becomes a TCPA complaint.

## ERR_REVIEW_009 — outbox_stale_sent

- **HTTP**: N/A (raised by the background outbox sweeper)
- **Cause**: An outbox record has been in `sent` status for >24h without receiving a `delivered` or `failed` webhook.
- **Detection**: Background sweep finds `(now - sent_at) > delivery_sla_seconds` and `status == sent`.
- **Action**: Page on-call to investigate — likely a dropped Podium webhook. Manually query the invitation status via `GET /v4/review-invitations/{id}` and reconcile. If Podium reports no record of the invitation, this is a more serious upstream issue.

## ERR_REVIEW_010 — webhook_signature_mismatch

- **HTTP**: 401 returned from the webhook endpoint
- **Cause**: HMAC verification failed on an inbound Podium or Shopify webhook.
- **Detection**: `verify_signature()` returns False.
- **Action**: Return 401 immediately. Persistent mismatches indicate either a secret rotation that didn't propagate (check `podium-auth`'s rotation runbook) or an active attack — page on-call after 10 mismatches in 5 minutes.

## ERR_REVIEW_011 — idempotency_replay

- **HTTP**: 200 returned from the webhook endpoint
- **Cause**: Podium retried a `review.received` webhook that was already processed.
- **Detection**: `idempotency.claim(event_id)` returns False (key already exists).
- **Action**: Return 200 + "duplicate" — Podium's retry behavior is expected. Do NOT 4xx (that would trigger more retries). Log at debug level only.

## ERR_REVIEW_012 — platform_route_fallback

- **HTTP**: N/A (logged by `select_review_platform`)
- **Cause**: Campaign default platform required a customer account the contact does not have (e.g., Facebook routing for a customer with no `facebook_uid`).
- **Detection**: `select_review_platform()` returns `google` instead of the campaign default.
- **Action**: No immediate action — fallback is by design. If the rate of fallback exceeds 50% of a Facebook campaign, recommend the merchant switch the campaign default to Google.

## ERR_REVIEW_013 — opt_out_drift_detected

- **HTTP**: N/A (raised by `optout_compliance_audit.py`)
- **Cause**: A contact has `marketing_sms_opt_out=true` but `review_request_opt_out=false` (or any equivalent inconsistency across flow-level flags).
- **Detection**: Audit CLI detects mismatched flags vs the unified predicate.
- **Action**: Run `optout_compliance_audit.py --propagate` to write the union of opt-outs to every flow-level flag. Re-run the audit to confirm zero drift. Investigate the source flow that diverged.

## ERR_REVIEW_014 — sentiment_escalation_failed

- **HTTP**: N/A (raised by `escalate_negative_review`)
- **Cause**: The negative-review escalation channel (Slack, PagerDuty, email) did not confirm receipt within the SLA.
- **Detection**: Escalation client returns non-success or times out.
- **Action**: Retry with exponential backoff. If all retries fail, persist the unescalated review to a dead-letter queue and page on-call. A dropped 1-star alert that the customer-success team never sees is an SLA-defining failure.
