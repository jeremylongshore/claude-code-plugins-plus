# Intercom Security — Worked Examples

Concrete, end-to-end walkthroughs for the most common situations this skill is
invoked for. Pair each with the full code in `implementation.md`.

## Example 1: Secure a fresh integration from zero

You just created an Intercom app and want to store its credentials safely.

```bash
# 1. Store secrets in .env (NEVER commit)
cat > .env <<'EOF'
INTERCOM_ACCESS_TOKEN=dG9rOmFiY2RlZmdoaQ==
INTERCOM_WEBHOOK_SECRET=your-webhook-signing-secret
INTERCOM_IDENTITY_SECRET=your-identity-verification-secret
EOF

# 2. Guarantee .env is ignored
grep -qxF '.env' .gitignore || printf '.env\n.env.local\n.env.*.local\n' >> .gitignore

# 3. Confirm nothing is staged
git status --short | grep -i '\.env' && echo "STOP: .env is staged" || echo "clean"
```

Expected result: `.env` is git-ignored, no secrets are staged, and the three
secrets are available to the app via `process.env`.

## Example 2: Scan an existing repo for a leaked token

Before shipping, prove no Intercom token was ever committed.

```bash
# Scan git history for leaked tokens
git log --all -p | grep -i "INTERCOM_ACCESS_TOKEN\|dG9r" | head -5
# If any line prints: rotate the token immediately (see implementation.md),
# then scrub history with git-filter-repo before pushing.
```

Expected result: no output means the history is clean. Any match is a live
incident — rotate first, scrub second.

## Example 3: Add webhook verification to an Express app

You have a webhook endpoint accepting Intercom events unauthenticated. Add
signature verification so forged payloads are rejected with `401`.

1. Register the route with `express.raw({ type: "application/json" })` (parsing to
   JSON first breaks the HMAC).
2. Read the `X-Hub-Signature` header; reject a missing header with `401`.
3. Recompute `sha1=HMAC-SHA1(rawBody, INTERCOM_WEBHOOK_SECRET)` and compare with
   `crypto.timingSafeEqual`.

Full implementation: `implementation.md` § Webhook Signature Verification.

Expected result: legitimate Intercom deliveries return `200`; any payload with a
missing or mismatched signature returns `401` and is never processed.

## Example 4: Turn on Identity Verification for the Messenger

Your Messenger boots with just an email, so anyone can impersonate a user.

1. Add `INTERCOM_IDENTITY_SECRET` (from Developer Hub) to your secret store.
2. Generate `user_hash = HMAC-SHA256(userId, INTERCOM_IDENTITY_SECRET)` on the
   server and return it alongside `app_id` and `user_id`.
3. Pass `user_hash` into the Messenger boot config; never compute it in the
   browser.

Full implementation: `implementation.md` § Identity Verification.

Expected result: Intercom accepts the boot only when the hash matches the
`user_id`, and the dashboard "Identity Verification" warning clears.
