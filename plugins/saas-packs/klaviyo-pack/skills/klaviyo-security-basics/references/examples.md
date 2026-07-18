# Klaviyo Security — Worked Examples

Concrete scenarios showing how to apply the skill end-to-end. Each example
references code in [implementation.md](implementation.md).

## Example 1: Wire up a validated config loader

Situation: a new service needs the Klaviyo private key, and startup should fail
fast if the secret is missing rather than 401-ing at first API call.

1. Add the three env vars to `.env` and confirm `.env` is in `.gitignore`.
2. Add `src/config/klaviyo.ts` from
   [implementation.md → Environment Variable Configuration](implementation.md#environment-variable-configuration).
3. Import `klaviyoConfig` at boot. `requireEnv('KLAVIYO_PRIVATE_KEY')` throws at
   import time when the secret is absent, surfacing the misconfig in the deploy
   log instead of in production traffic.

Expected result: a missing `KLAVIYO_PRIVATE_KEY` aborts startup with
`Missing required env: KLAVIYO_PRIVATE_KEY`; the public key and webhook secret
degrade to empty strings because they are optional for read-only flows.

## Example 2: Reject a forged webhook

Situation: an endpoint receives a POST claiming to be a Klaviyo event, but the
signature does not match the signing secret.

1. Mount the raw-body middleware from
   [implementation.md → Express Webhook Middleware](implementation.md#express-webhook-middleware).
2. Send a request with a tampered body but the original `klaviyo-webhook-signature`.
3. `verifyKlaviyoWebhookSignature` recomputes the HMAC-SHA256 digest over the raw
   body; because the body changed, the digest differs and `timingSafeEqual`
   returns `false`.

Expected result: the request is answered with `401 { "error": "Invalid signature" }`
and `[Security] Invalid webhook signature rejected` is logged. Only payloads whose
HMAC matches the signing secret reach the event handler.

## Example 3: Zero-downtime key rotation

Situation: the production private key is 90+ days old and must be rotated without
dropping traffic.

1. Follow the five steps in
   [implementation.md → API Key Rotation Procedure](implementation.md#api-key-rotation-procedure).
2. Generate the replacement with identical scopes, deploy it to the secret store,
   then run the `curl` verification against `/api/accounts/`.

Expected result: the verification `curl` prints `200`; after the old key is
revoked, log monitoring shows no `401`s, confirming every service picked up the
new secret before the old one was deleted.
