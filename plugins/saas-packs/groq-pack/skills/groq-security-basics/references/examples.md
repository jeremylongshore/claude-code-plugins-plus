# Groq Security — Worked Examples

Concrete, copy-ready command sequences for the operational steps summarized in
`SKILL.md`.

## Example 1: Secure Key Storage by Environment

Store the key in `.env` for local development (never committed) and in a
platform secret manager for production.

```bash
# Development: .env file (NEVER commit)
echo "GROQ_API_KEY=gsk_dev_key_here" > .env.local

# .gitignore (mandatory)
echo -e ".env\n.env.local\n.env.*.local" >> .gitignore

# Production: use platform secret managers
# Vercel
vercel env add GROQ_API_KEY production

# AWS
aws secretsmanager create-secret --name groq-api-key --secret-string "gsk_..."

# GCP
echo -n "gsk_..." | gcloud secrets create groq-api-key --data-file=-

# GitHub Actions
gh secret set GROQ_API_KEY --body "gsk_..."
```

## Example 2: Zero-Downtime Key Rotation

Both keys work simultaneously, so deploy the new one, verify, monitor, then
delete the old key.

```bash
set -euo pipefail
# 1. Create new key in console.groq.com/keys
#    Name it with a date: "prod-2026-03"

# 2. Deploy new key to production first (both keys work simultaneously)
#    Update secret manager with new value

# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $NEW_GROQ_KEY"
# Should return 200

# 4. Monitor for 24h -- ensure no requests use old key
# 5. Delete old key in console.groq.com/keys
```

## Example 3: Git Leak Prevention Pre-Commit Hook

Block any commit that stages a `gsk_` key. This is the same pattern the
`Grep` scan in the checklist uses.

```bash
# Pre-commit hook to detect leaked keys
cat > .git/hooks/pre-commit << 'HOOKEOF'
#!/bin/bash
if git diff --cached --diff-filter=ACM | grep -qE "gsk_[a-zA-Z0-9]{20,}"; then
  echo "ERROR: Groq API key detected in staged files!"
  echo "Remove the key and use environment variables instead."
  exit 1
fi
HOOKEOF
chmod +x .git/hooks/pre-commit
```

## Example 4: Scan an Existing Repo for Leaked Keys

Before adding the hook, sweep the working tree and history for keys that may
already be committed.

```bash
# Scan the working tree
grep -rnE "gsk_[a-zA-Z0-9]{20,}" . --exclude-dir=.git

# Scan full git history
git log -p | grep -nE "gsk_[a-zA-Z0-9]{20,}"
```
