# Exposed-Files Theory

## Why this probe class is the highest-value pentest call

Most pentest findings are about chained conditions and threshold judgments.
This one is binary: either the `.git/HEAD` is reachable or it's not. A
single 200 response answers the question. The consequence of a true
positive is direct: full repo history (with embedded credentials in old
commits), live API keys (in `.env`), and direct database access (in
`backup.sql`). No CVE chaining, no exploitation primitive needed.

The reason these exposures keep happening is operational: web servers
are designed to serve files from a directory tree, and deployment
processes routinely deploy the whole tree, including dot-directories
and config files the application never intended to expose. Modern
frameworks ship "deny" defaults (Caddy, nginx with a security baseline,
Cloud Run) but legacy stacks (LAMP on a shared host, hand-rolled
nginx vhosts on a VM) default to "allow."

## File-by-file: why each one matters

### `.git/` — version control directory

The `.git/` subdirectory contains the entire history of the repository.
Exposing it allows an attacker to clone the repo without needing
authentication:

```
git clone https://example.com/.git/  ./reconstructed-source
```

History reveals:

- API keys in old commits (before the `.env` was added to `.gitignore`)
- Hardcoded credentials someone removed but didn't rebase out
- Repo URL + branch names + commit messages → understanding the
  deployment process
- Database schemas if migrations are checked in
- Source code (obviously) → static analysis targets

Three minimal probes that confirm exposure:

- `.git/HEAD` — should be a small text file starting with `ref:` or a
  40-char hex SHA
- `.git/config` — `[remote "origin"]` block reveals the upstream
- `.git/index` — binary file starting with `DIRC` magic

The `.git/` exposure is so common that there are off-the-shelf tools
(GitDumper, git-dumper) that walk the exposed directory and reconstruct
the repo. Once exposed, assume the full history is compromised.

### `.env` — dotenv credentials

Most modern stacks (Node.js with dotenv, Python with python-dotenv,
Ruby with dotenv-rails, Laravel) load environment variables from a
`.env` file at startup. The file's contents are typically the most
sensitive thing the application has: API keys, database connection
strings, signing secrets, third-party credentials.

A leaked `.env`:

- Lets an attacker authenticate as the app to upstream services
  (Stripe, Twilio, OpenAI, etc.)
- Reveals database credentials if `DATABASE_URL` is present
- Discloses signing secrets for JWT / session tokens, enabling token
  forgery without further effort

Fingerprint: `KEY=VALUE` pattern on each line, often `[A-Z_]` keys.

### `.aws/credentials`, `.aws/config`

AWS SDK and CLI look in `~/.aws/credentials` by default. If a deploy
process accidentally copies the user's home directory into the web
root, AWS credentials are reachable.

`[default]\naws_access_key_id = AKIA...` is the fingerprint. Once
leaked, the credentials grant whatever permissions the IAM principal
had — historically that's "Administrator" on dev/test accounts
because the principle of least privilege is not the default.

### Private keys (`id_rsa`, `*.pem`, `*.key`)

SSH private keys, TLS private keys, or signing keys. Exposure means:

- An attacker can authenticate as the server to other systems (lateral
  movement)
- An attacker can MITM TLS connections by presenting the leaked cert +
  key combination
- An attacker can sign tokens / artifacts as the system

Fingerprint: any of `-----BEGIN RSA PRIVATE KEY-----`,
`-----BEGIN OPENSSH PRIVATE KEY-----`, `-----BEGIN PRIVATE KEY-----`,
`-----BEGIN EC PRIVATE KEY-----`, `-----BEGIN DSA PRIVATE KEY-----`.

### Backup files (`backup.sql`, `dump.sql`, `*.tar.gz`)

SQL dumps contain the entire database — schema and rows. A leaked
backup is functionally equivalent to RCE on the database server.
Common origins:

- Operator made a backup before a migration and left it in the web root
- Deploy script copies a tarball of the previous release into the web
  root for rollback purposes
- Cron job dumps a backup to a path the web server happens to serve

Fingerprint: SQL dumps contain `CREATE TABLE`, `INSERT INTO`. Archive
files (binary) get a no-fingerprint check — the path being reachable
at 200 is the finding.

### `.DS_Store`

macOS Finder creates a `.DS_Store` in every directory it views,
recording metadata about how the directory is displayed. The binary
format includes the filenames of every file in the directory.

Exposure is medium severity because it doesn't directly leak credentials
or source code, but it enumerates the directory structure, including
hidden files that wouldn't otherwise be discoverable by URL probing.

Fingerprint: binary blob with `Bud1` magic at offset 4 or 0.

### `phpinfo()` output

PHP's `phpinfo()` function dumps the full PHP environment — every
configuration directive, every environment variable, every loaded
module. Common in `phpinfo.php`, `info.php`, `test.php` files left
behind from initial server setup.

Includes:

- Document root path (informs directory traversal)
- Loaded extensions (informs exploit selection)
- Often: `SERVER` variables including request headers and cookies
- Sometimes: `ENV` variables including secrets

Fingerprint: HTML body containing `PHP Version` heading.

### IDE configs (`.idea/`, `.vscode/`)

Per-project IDE settings. Low severity but information disclosure:

- Run configurations (database connection strings, env vars used during dev)
- Recent file lists (informs which files the dev was working on)
- Inspection scope (informs which directories have application code)

### Dependency manifests on production root (`package.json`, etc.)

Information disclosure: exposes exact versions of every dependency,
enabling targeted CVE lookup. Not a vulnerability in itself, but a
recon enabler.

## Why fingerprint-checking matters

SPAs (Single-Page Applications) using client-side routing return the
app's `index.html` for any unknown route — including `/.git/HEAD`.
Without fingerprint verification, every `/.git/*` probe returns 200
and every `/.env` probe returns 200, all of them false positives.

The fingerprint check inspects the response body. If a request for
`.git/HEAD` returns 200 with body `<!DOCTYPE html>`, it's the SPA
catching the route, not a real `.git/HEAD`. If the body starts with
`ref:` or matches a 40-char hex SHA, it's the real file.

The skill's `--check-only` mode skips fingerprint verification for
cases where the operator wants to know about every 200, including
the SPA false positives, and accepts noise as the cost.

## Primary sources

- [OWASP WSTG-INFO-02 — Fingerprint Web Server](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server)
- [OWASP WSTG-CONF-04 — Review Old Backup and Unreferenced Files](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/04-Review_Old_Backup_and_Unreferenced_Files_for_Sensitive_Information)
- [CWE-538 — File and Directory Information Exposure](https://cwe.mitre.org/data/definitions/538.html)
- [CWE-200 — Information Exposure](https://cwe.mitre.org/data/definitions/200.html)
- [NIST SP 800-53 SC-28 — Protection of Information at Rest](https://nvd.nist.gov/800-53/Rev5/control/SC-28)
