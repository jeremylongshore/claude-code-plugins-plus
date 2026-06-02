# Security

Worker containment via prompt-injected blocklists. Workers get preventive rules (don't do X), reviewers get detective rules (verify the worker didn't do X). Configurable via `~/.hyperflow/config.json`.

## Blocked File Patterns

Workers must never read or modify files matching these patterns:

| Category | Patterns |
|----------|----------|
| Secrets & credentials | `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `credentials.json`, `service-account*.json`, `*-secret.json`, `*-secret.yaml` |
| SSH & GPG | `~/.ssh/*`, `~/.gnupg/*`, `id_rsa*`, `id_ed25519*`, `*.gpg` |
| Auth tokens | `.npmrc` (with token), `.pypirc`, `.docker/config.json`, `*.keychain`, `*-credentials` |
| Cloud configs | `~/.aws/credentials`, `~/.azure/*`, `~/.config/gcloud/*`, `~/.kube/config` |

**Allowlisted (not blocked):** `.env.example`, `.env.template`, `.env.sample` — templates, not secrets.

## Blocked Commands

Workers must never execute these:

| Category | Patterns |
|----------|----------|
| Destructive | `rm -rf /`, `rm -rf ~`, `rm -rf .` (root/home/cwd wipe), `mkfs.*`, `dd if=` |
| Git dangerous | `git push --force` to main/master, `git reset --hard` without user request, `git clean -fdx` |
| Network exfiltration | `curl`/`wget`/`nc` piping file contents to external URLs |
| Privilege escalation | `sudo`, `chmod 777`, `chmod -R 777` |
| Package publish | `npm publish`, `pip upload`, `gem push`, `cargo publish` |

## Secret Detection Patterns

Reviewer checks committed content for hardcoded secrets:

| Pattern | Matches |
|---------|---------|
| API key prefixes | `sk-` (Stripe/OpenAI), `AKIA` (AWS), `ghp_`/`gho_` (GitHub), `glpat-` (GitLab), `xoxb-`/`xoxp-` (Slack) |
| Generic secrets | `password\s*=\s*["'][^"']+`, `secret\s*=`, `token\s*=` with non-placeholder values |
| Private keys | `-----BEGIN (RSA|EC|DSA)? PRIVATE KEY-----` |
| Connection strings | `postgres://.*:.*@`, `mongodb+srv://.*:.*@`, `redis://.*:.*@` |

**Not flagged:** Placeholder values (`"changeme"`, `"<your-token>"`), test fixtures, `.env.example` templates.

## Worker Prompt Injection

Appended to every worker prompt after `## Constraints`:

```
## Security Constraints
You MUST NOT:
- Read, modify, or reference files matching blocked patterns: .env, *.pem, *.key,
  ~/.ssh/*, credentials.json, service-account*.json, ~/.aws/credentials, etc.
- Run destructive commands: rm -rf (root/home/cwd), git push --force to main/master,
  git reset --hard, sudo, chmod 777
- Pipe file contents to external URLs via curl/wget/nc
- Run package publish commands (npm publish, pip upload, etc.)
- Hardcode secrets, API keys, passwords, or connection strings in source code

If a task requires accessing a blocked file, STOP and report:
"BLOCKED: Task requires access to [file] which is security-restricted."
```

## Reviewer Prompt Injection

Appended to every reviewer prompt after `## Check`:

```
## Security Review
After checking code quality, verify:
1. No blocked files were read or modified
2. No secrets/credentials hardcoded (check for API key patterns: sk-*, AKIA*, ghp_*,
   private keys, connection strings with passwords)
3. No dangerous commands executed (rm -rf, force push, sudo, chmod 777)
4. No data exfiltration (file contents piped to external URLs)

If ANY security violation found, respond:
SECURITY_VIOLATION: [specific violation]
This takes priority over all other review feedback.
```

## Orchestrator Handling

When the reviewer reports `SECURITY_VIOLATION`:

1. Do NOT retry automatically (unlike `NEEDS_FIX`)
2. Report the violation to the user immediately
3. Other parallel workers continue unaffected — each is reviewed independently
4. User decides whether to override or abort the flagged task
5. If user overrides, proceed with an explicit note in the session log

## Configuration

`~/.hyperflow/config.json` → `security` key:

```json
{
  "security": {
    "enabled": true,
    "blockedFiles": {
      "add": ["internal/secrets/**", "*.vault"],
      "remove": [".env.example"]
    },
    "blockedCommands": {
      "add": ["docker rm -f"],
      "remove": []
    },
    "secretPatterns": {
      "add": ["MYAPP_KEY_[A-Z0-9]{32}"],
      "remove": []
    }
  }
}
```

- `add`/`remove` extends defaults — never replaces them
- `enabled: true` is the default; set `false` to disable entirely
- `.env.example` is already allowlisted in defaults

## Runtime Commands

| Command | Effect | Scope |
|---------|--------|-------|
| `hyperflow: security off` | Disable security layer | Current session |
| `hyperflow: security on` | Re-enable security layer | Current session |
| `hyperflow: security status` | Show current security config | Display only |
