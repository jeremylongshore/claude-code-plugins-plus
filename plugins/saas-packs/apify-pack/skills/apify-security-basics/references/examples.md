# Apify Security — Worked Examples

End-to-end walkthroughs that combine the individual steps in
[implementation.md](implementation.md) into complete scenarios.

## Example 1: Bootstrap a new project securely

```bash
# 1. Add secrets to .gitignore BEFORE creating .env
cat >> .gitignore <<'EOF'
.env
.env.local
.env.*.local
storage/
EOF

# 2. Create the local .env with your dev token
echo 'APIFY_TOKEN=apify_api_dev_token' > .env

# 3. Confirm nothing is tracked
git status --short   # .env must NOT appear
```

```typescript
// 4. Fail fast at startup if the token is missing or malformed
import { requireToken } from './security';
const token = requireToken(); // throws if unset, warns on bad prefix
```

## Example 2: Rotate a token across all environments

```bash
# Generate a new token in Console > Settings > Integrations, then:
NEW_TOKEN=apify_api_NEW_TOKEN

# Push to every environment secret store
gh secret set APIFY_TOKEN --body "$NEW_TOKEN"
vercel env add APIFY_TOKEN production

# Verify the new token authenticates before revoking the old one
curl -sf -H "Authorization: Bearer $NEW_TOKEN" \
  https://api.apify.com/v2/users/me | jq '.data.username'

# Only after a successful 200: revoke the old token in Console.
```

## Example 3: Verify a webhook and sanitize before storage

```typescript
import { verifyWebhookPayload, sanitizeForDataset } from './security';

app.post('/webhook', async (req, res) => {
  const ok = await verifyWebhookPayload(req.body, apifyClient);
  if (!ok) return res.status(401).send('unverified run');

  const clean = sanitizeForDataset(req.body.resource ?? {});
  await dataset.pushData(clean); // PII fields already redacted
  res.sendStatus(200);
});
```

## Example 4: Audit git history for a leaked token

```bash
# Search the entire history (all branches) for the token prefix
git log --all -p -- '*.env' '*.json' | grep apify_api_

# If a match is found: rotate immediately, then scrub with BFG
bfg --replace-text <(echo 'apify_api_==>***REMOVED***') .
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```
