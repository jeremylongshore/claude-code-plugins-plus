# Exposed-Files Remediation Playbook

## Pattern 1 — Block dot-directories at the web server

### nginx (location blocks)

```nginx
# Deny all dot-files / dot-directories
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}

# Belt-and-suspenders for specific high-value paths
location ~ ^/(\.git|\.svn|\.hg|\.bzr|\.env|\.aws|\.ssh) {
    deny all;
    return 404;
}
```

### Apache (vhost or .htaccess)

```apache
<DirectoryMatch "^\.|/\.">
    Require all denied
</DirectoryMatch>

<Files ~ "^\.">
    Require all denied
</Files>
```

### Caddy

Caddy denies dot-directories by default since v2.0. To explicitly
assert:

```caddy
example.com {
    @dot path */.git/* */.env */.aws/* */.ssh/* */.svn/*
    respond @dot 404
    file_server
}
```

### AWS ALB / WAF

Add a managed-rule-group or custom rule:

```json
{
    "Name": "BlockDotPaths",
    "Statement": {
        "RegexMatchStatement": {
            "FieldToMatch": {"UriPath": {}},
            "RegexString": "/\\.(git|env|aws|ssh|svn|hg|bzr|idea|vscode)(\\b|/)",
            "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}]
        }
    },
    "Action": {"Block": {}}
}
```

### Cloudflare WAF

```
http.request.uri.path matches "/\\.(git|env|aws|ssh|svn|hg|bzr)"
```

Action: Block.

## Pattern 2 — Block backup / dump file extensions

### nginx

```nginx
location ~* \.(sql|bak|dump|swp|swo|orig|backup|tar\.gz|tar\.bz2|zip|7z|rar)$ {
    deny all;
    return 404;
}
```

### Apache

```apache
<FilesMatch "\.(sql|bak|dump|swp|swo|orig|backup|tar\.gz|tar\.bz2|zip|7z|rar)$">
    Require all denied
</FilesMatch>
```

### Caddy

```caddy
@backups path *.sql *.bak *.dump *.swp *.tar.gz *.zip
respond @backups 404
```

## Pattern 3 — Block private key extensions

### nginx

```nginx
location ~* \.(pem|key|p12|pfx|jks|crt|cer|csr|kdb|kbx)$ {
    deny all;
    return 404;
}
```

These extensions should never be reachable via the web; if a key needs
to be served (e.g., a JWKS for OAuth), serve it at an explicit path
with a content-type check rather than relying on the extension.

## Pattern 4 — Block development metadata

### nginx

```nginx
location ~* /(phpinfo|info|test)\.php$ {
    deny all;
    return 404;
}

location ~* /(composer\.json|package\.json|Dockerfile|docker-compose\.yml|requirements\.txt|Gemfile|build\.gradle)$ {
    deny all;
    return 404;
}
```

`phpinfo.php` should be removed from any production environment.
Detection of an active `phpinfo.php` on prod is an audit-flag-worthy
operational gap; the fix is removal, not access control.

## Pattern 5 — Block at the build / deploy layer

The cleanest fix is preventing the files from getting deployed in
the first place.

### Dockerfile — multi-stage build with explicit copies

```dockerfile
# Build stage
FROM node:20 AS build
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY src/ ./src/
RUN npm run build

# Runtime stage — only copy the built artifact, NOT the build context
FROM nginx:alpine
COPY --from=build /build/dist /usr/share/nginx/html
```

Notice: no `COPY . .` anywhere. The build stage gets only what it
needs; the runtime stage gets only the `dist/` artifact. `.git/`,
`.env`, `node_modules/`, etc., never reach the runtime image.

### .dockerignore

```
.git
.env*
.aws
.ssh
*.pem
*.key
node_modules
.DS_Store
.idea
.vscode
backup.sql
*.sql
*.dump
```

### .gitlab-ci.yml / GitHub Actions — exclude sensitive paths from artifacts

```yaml
artifacts:
  paths:
    - dist/
  exclude:
    - "**/.git*"
    - "**/.env*"
    - "**/.aws/*"
    - "**/.ssh/*"
    - "**/*.pem"
    - "**/*.key"
    - "**/backup.*"
    - "**/*.sql"
```

## Pattern 6 — Cloud Run / Lambda artifact builds

Cloud Run and Lambda build the deployment artifact from your repo by
default. To exclude:

### Cloud Run via Cloud Build

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/app', '.']
options:
  ignoreFile: '.dockerignore'  # honored by Cloud Build
```

Combined with the `.dockerignore` above, this excludes the files.

### Lambda via SAM / Serverless Framework

```yaml
package:
  patterns:
    - '!.git/**'
    - '!.env*'
    - '!.aws/**'
    - '!.ssh/**'
    - '!**/*.pem'
    - '!**/*.key'
    - '!backup.*'
    - '!**/*.sql'
```

## Auditing existing deployments

Run the scanner on every production endpoint:

```bash
for ENDPOINT in $(cat production-urls.txt); do
    python3 plugins/security/penetration-tester/skills/detecting-exposed-secrets-files/scripts/probe_secrets.py \
        "$ENDPOINT" --authorized --min-severity critical \
        --format jsonl --output /dev/stdout
done > exposure-audit.jsonl
```

Treat any CRITICAL finding as ship-same-hour. Document the
remediation in the same PR as the audit (so the audit's grep target
gets re-verified on commit).

## After remediation — assume compromise

If `.git/` was exposed, assume:

- Every credential ever committed to the repo, including ones in past
  commits that were later removed, is compromised. Rotate them all.
- The full source code is in the attacker's hands. Treat any
  authentication / authorization logic as if it had been read.

If `.env` was exposed:

- Rotate every credential in the file
- Audit logs for any API call against those credentials in the
  past window from when the deploy happened to when you rotated
- Notify partners whose API keys you held

If a backup `.sql` was exposed:

- Assume the database is compromised in the state it was in when
  the backup was taken
- Trigger your data-breach response: regulator notification,
  customer notification, credential rotation for anyone whose
  data was in the dump

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-exposed-secrets-files/scripts/probe_secrets.py \
    https://example.com --authorized --min-severity info
```

Expected: exit 0, zero findings of any severity.
