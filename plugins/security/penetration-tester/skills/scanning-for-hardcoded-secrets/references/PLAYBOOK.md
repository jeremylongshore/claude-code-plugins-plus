# Hardcoded-Secrets Remediation Playbook

## After detection: the standing procedure

1. **Rotate.** Same hour. The window between detection and rotation
   is dead time for the credential's usefulness to anyone but
   attackers.
2. **Audit upstream logs.** Check the provider's API audit log
   (AWS CloudTrail, GitHub audit log, Stripe events, etc.) for any
   request against the credential since the leak commit timestamp.
3. **Remove from source.** Replace the literal with an env-var
   lookup or secrets-manager fetch. See per-language patterns
   below.
4. **Add a pre-commit gate.** Wire this skill into the pre-commit
   hook so the same engineer doesn't re-introduce the same class
   tomorrow.
5. **(Optional) Scrub history.** Only if private repo with
   controlled clones AND credential is non-rotatable AND
   coordination overhead is acceptable.

## Per-language migration patterns

### Python — `python-dotenv`

```python
# Before (vulnerable):
STRIPE_KEY = "sk_live_abc123..."

# After:
import os
from dotenv import load_dotenv
load_dotenv()
STRIPE_KEY = os.environ["STRIPE_KEY"]  # KeyError on missing
```

`.env` (gitignored):

```
STRIPE_KEY=sk_live_abc123...
```

`.gitignore`:

```
.env
.env.local
.env.production
```

### Python — pydantic-settings (typed config)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    stripe_key: str
    aws_access_key_id: str
    aws_secret_access_key: str

settings = Settings()
```

### Node.js — dotenv

```javascript
// Before:
const STRIPE_KEY = "sk_live_abc123...";

// After:
require('dotenv').config();
const STRIPE_KEY = process.env.STRIPE_KEY;
if (!STRIPE_KEY) throw new Error("STRIPE_KEY not configured");
```

### Ruby on Rails — `Rails.application.credentials`

```bash
# Edit (creates / decrypts encrypted credentials)
EDITOR=vim rails credentials:edit
```

In the editor:

```yaml
stripe:
  api_key: sk_live_abc123...
```

Then in code:

```ruby
Rails.application.credentials.dig(:stripe, :api_key)
```

The encrypted file (`config/credentials.yml.enc`) commits to git;
the decryption key (`config/master.key`) does NOT. Both are
required to read the secret at runtime.

### Go — `envconfig`

```go
package main

import (
    "log"
    "github.com/kelseyhightower/envconfig"
)

type Config struct {
    StripeKey      string `envconfig:"STRIPE_KEY" required:"true"`
    AWSAccessKeyID string `envconfig:"AWS_ACCESS_KEY_ID" required:"true"`
    AWSSecretKey   string `envconfig:"AWS_SECRET_ACCESS_KEY" required:"true"`
}

func main() {
    var c Config
    if err := envconfig.Process("", &c); err != nil {
        log.Fatal(err)
    }
}
```

### Rust — `dotenvy` + `envy`

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct Config {
    stripe_key: String,
    aws_access_key_id: String,
    aws_secret_access_key: String,
}

fn main() {
    dotenvy::dotenv().ok();
    let config: Config = envy::from_env().expect("missing env config");
}
```

### Java — Spring Boot `@Value`

```java
@Component
public class StripeConfig {
    @Value("${stripe.api.key}")
    private String stripeKey;
}
```

`application.yml`:

```yaml
stripe:
  api:
    key: ${STRIPE_KEY}   # interpolated from environment
```

Production: set `STRIPE_KEY` in the environment (Kubernetes secret,
ECS task definition, etc.) and Spring picks it up at startup.

## Secrets managers

For production, env vars alone aren't sufficient (they leak via
process listings, container introspection, error reports). Use a
dedicated secrets manager.

### AWS Secrets Manager

```python
import boto3, json
client = boto3.client("secretsmanager")
secret_value = client.get_secret_value(SecretId="prod/stripe")["SecretString"]
config = json.loads(secret_value)
STRIPE_KEY = config["api_key"]
```

IAM policy grants the runtime role `secretsmanager:GetSecretValue`
on the specific secret ARN. No literal in source; no literal in
env-var dumps.

### GCP Secret Manager

```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = "projects/my-project/secrets/stripe-key/versions/latest"
response = client.access_secret_version(request={"name": name})
STRIPE_KEY = response.payload.data.decode("UTF-8")
```

### HashiCorp Vault

```bash
# At runtime, runtime fetches the secret
vault kv get -field=api_key secret/stripe
```

Or via the SDK:

```python
import hvac
client = hvac.Client(url="https://vault.internal:8200")
client.auth.approle.login(role_id=..., secret_id=...)
secret = client.secrets.kv.v2.read_secret_version(path="stripe")
STRIPE_KEY = secret["data"]["data"]["api_key"]
```

### Doppler / 1Password Secrets Automation / Bitwarden Secrets

All follow the same pattern: SDK call at startup, no literals in
source.

## Pre-commit hook integration

### Using `pre-commit` framework

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: scan-secrets
        name: Scan for hardcoded secrets
        entry: python3 plugins/security/penetration-tester/skills/scanning-for-hardcoded-secrets/scripts/scan_secrets.py
        language: system
        args: ['--min-severity', 'high']
        pass_filenames: false
```

Install: `pre-commit install`. Now every `git commit` runs the
scan; commits abort if the scan finds a high/critical credential.

### Husky (Node projects)

`package.json`:

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "python3 plugins/security/penetration-tester/skills/scanning-for-hardcoded-secrets/scripts/scan_secrets.py --min-severity high . || exit 1"
    }
  }
}
```

## Provider rotation procedures

### AWS access key

```bash
# Create new key (keep old active until apps cut over)
aws iam create-access-key --user-name myuser

# Update app config / secrets manager with new key
# Verify apps are using new key (CloudTrail will show old key inactive)

# Then deactivate + delete old key
aws iam update-access-key --user-name myuser --access-key-id AKIAOLD --status Inactive
# After 24h grace:
aws iam delete-access-key --user-name myuser --access-key-id AKIAOLD
```

### GitHub PAT

Settings → Developer settings → Personal access tokens → revoke
old, generate new. Update CI / local config.

### Stripe

Dashboard → Developers → API keys → roll secret key. Two-step:
generate new, deploy, deactivate old.

### Anthropic

Console → API keys → revoke old, create new. Update env / secrets
manager.

### Slack

App settings → OAuth & Permissions → "Reinstall to Workspace" with
admin approval generates fresh bot/user tokens.

## GitHub Secret Scanning integration

If your repo is on GitHub:

- Settings → Code security → enable "Secret scanning alerts"
- Settings → Code security → enable "Push protection" (this is the
  game-changer: blocks pushes that contain detected credential
  shapes, BEFORE the commit lands on the remote)

GitHub's pattern library is roughly equivalent to this skill's;
running both is defense-in-depth.

## CI integration

```yaml
- name: Hardcoded-secrets scan
  run: |
    python3 plugins/security/penetration-tester/skills/scanning-for-hardcoded-secrets/scripts/scan_secrets.py \
        . --min-severity high --format json --output secrets-scan.json
- name: Fail on findings
  run: |
    if [ "$(jq 'length' secrets-scan.json)" != "0" ]; then
      cat secrets-scan.json
      exit 1
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/scanning-for-hardcoded-secrets/scripts/scan_secrets.py \
    /path/to/repo --min-severity high
```

Expected: exit 0, zero high/critical findings. MEDIUM entropy-based
findings may persist if your codebase legitimately contains high-
entropy literals in test fixtures or build artifacts; verify
manually.
