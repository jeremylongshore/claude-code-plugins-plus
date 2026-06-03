# PLAYBOOK — Remediating npm Findings

## Decision flow

```
                npm audit finding
                       |
                       v
            +-------------------+
            | DIRECT or         |
            | TRANSITIVE?       |
            +---+-----------+---+
                |           |
        DIRECT  |           |  TRANSITIVE
                v           v
       +----------+   +-----------------+
       | semver-  |   | parent has new  |
       | minor    |   | version with    |
       | fix?     |   | floor above fix?|
       +-+----+---+   +--+----------+---+
         |    |          |          |
       YES   NO        YES        NO
         |    |          |          |
         v    v          v          v
    audit  manual      bump      overrides
    fix    review     parent     block
```

## Per-runtime remediation patterns

### Frontend bundler (webpack / vite / next.js)

CVEs in build-time-only deps (loaders, transformers, dev plugins)
are lower priority than CVEs in runtime deps that ship in the
bundle.

- Build-time only: file ticket, fix in next sprint.
- Runtime in bundle: block release.
- Use `npm audit --omit=dev` to focus on runtime; this skill's
  `--include-dev` flag toggles the inverse.

### Node server (Express, Fastify, Hapi)

Every advisory affects a long-running process. Treat all of them
as runtime, including those marked dev-only — `eslint` etc. usually
DON'T ship to production, but if they're in your Docker image at
runtime, they do.

Inspect your `Dockerfile`. If it copies `node_modules` whole, every
dep ships. If it uses `npm ci --omit=dev`, devDeps are pruned.

### Electron desktop app

Electron apps bundle Chromium + Node into a binary distributed to
end-users. A vulnerable dep ships to every user. Patches require a
full app release; you cannot ship a runtime hotpatch. CRITICAL
findings require an emergency release.

### AWS Lambda / serverless function

Each function invocation loads the dependency tree. The blast radius
of a compromised dep is whatever the Lambda's IAM role grants. Audit
the IAM role alongside the dep audit — a compromised `request` package
in a Lambda with `s3:*` permissions is an exfiltration vector to
every object in your S3 buckets.

### Monorepo (Nx / Turborepo / pnpm workspaces)

Audit each workspace separately. `npm audit --workspaces` exists in
npm 7+ but produces output keyed by workspace and is awkward to
parse. This skill currently scans one package.json at a time; for
monorepos, iterate over the workspace globs in your top-level
`package.json` and run the scanner per package.

## Override-block templates

### Single-package override

```json
{
  "overrides": {
    "minimist": "^1.2.6"
  }
}
```

Use when one transitive package needs a floor and the rest of the
parent's deps are fine.

### Nested override (specific parent only)

```json
{
  "overrides": {
    "express": {
      "qs": "^6.10.3"
    }
  }
}
```

Force `qs@^6.10.3` only when pulled in through `express` — leave
other consumers of `qs` untouched. Use when an override breaks an
unrelated package and you need surgical control.

### Wildcard override (rare)

```json
{
  "overrides": {
    "lodash": "$lodash"
  }
}
```

`$lodash` resolves to the version declared in your `dependencies`.
Use to enforce that every transitive use of `lodash` matches your
declared version. Reserve for cases where transitive duplication is
causing real bundle-size or behavior problems.

## Provider rotation procedures

Vulnerabilities sometimes overlap credential leaks: a CVE in a
package that handles auth tokens may incidentally expose tokens.
After fixing the dep, check whether the vulnerable version logged
or transmitted secrets in a way that requires rotation.

| Provider | Rotation surface |
|---|---|
| GitHub | Settings → Developer settings → Personal access tokens → Regenerate |
| npm | `npm token revoke <id>` + `npm token create` |
| AWS | IAM → Access keys → Deactivate → Delete → New access key |
| Stripe | Dashboard → Developers → API keys → Roll key |
| Sentry | Settings → Auth Tokens → Revoke + Create |

## GitHub Dependabot integration

Dependabot opens automatic PRs when GitHub's vulnerability database
flags a finding. This skill is complementary, not redundant:

- Dependabot is the long-running watcher.
- This skill is the PR-time gate that ensures Dependabot's findings
  haven't accumulated unreviewed.

In CI:

```yaml
- name: npm audit
  run: |
    python3 plugins/security/penetration-tester/skills/auditing-npm-dependencies/scripts/audit_npm.py . \
        --min-severity high --format markdown --output npm-audit.md
- name: Comment on PR
  if: github.event_name == 'pull_request'
  uses: marocchino/sticky-pull-request-comment@v2
  with:
    path: npm-audit.md
```

## SOC2 evidence retention

For Trust Service Category CC7 (System Operations) and CC8 (Change
Management), retain npm audit output as evidence that dependency
vulnerabilities are tracked:

```bash
mkdir -p evidence/CC7/
python3 ./scripts/audit_npm.py . --include-dev --no-cache \
    --format json \
    --output evidence/CC7/npm-audit-$(date +%Y%m%d).json
```

Keep at least one audit per quarter. Auditors will ask for evidence
that you ran the audit, that findings were triaged, and that
remediation timing matched your published vulnerability-response
policy.
