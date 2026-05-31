# Directory-Listing Theory

## The recurring pattern

Web servers default-handle a directory request in one of three ways:

1. **Serve the directory's `index` file** (`index.html`, `index.php`,
   etc.) — the safe default.
2. **Generate an autoindex** — list every file in the directory as
   HTML. The dangerous default.
3. **Return 403 / 404** — deny the listing entirely. The defensive
   default.

Which behavior applies depends on the server's configuration and
whether an index file is present. The risk surface: a directory
without an `index.html`, where the server is configured to
fall back to autoindex.

This was the default in older Apache configurations. Modern stacks
(Caddy, nginx defaults) deny by default but legacy configs still
have it enabled.

## Per-server behavior

### Apache mod_autoindex

```apache
Options +Indexes        # autoindex ENABLED — bad on app servers
Options -Indexes        # autoindex DISABLED — safe default
```

The default in Apache 2.4 depends on the distribution: Debian /
Ubuntu have `Indexes` enabled in the default `<Directory /var/www/>`
block. Red Hat / CentOS disable it by default.

Fingerprint: `<title>Index of /<path></title>` + an HTML table of
file entries with mtime + size columns.

### nginx autoindex

```nginx
location /uploads/ {
    autoindex on;          # enabled — bad
}
location /uploads/ {
    autoindex off;         # disabled — safe (default)
}
```

nginx defaults to autoindex off; you have to explicitly enable it.
When seen, it's a deliberate config someone added.

Fingerprint: HTML body with `<pre>` formatting, lines like
`<a href="filename">filename</a>` with size + mtime columns.

### Caddy file_server browse

```caddy
example.com {
    root * /srv/site
    file_server browse    # autoindex enabled
}
```

vs.

```caddy
example.com {
    root * /srv/site
    file_server           # no browse — disabled (default)
}
```

Caddy v2 defaults to NOT browse. The browse mode generates a styled
HTML directory listing.

Fingerprint: `<table class="listing">` with sortable column headers.

### Lighttpd mod_dirlisting

```lighttpd
dir-listing.activate = "enable"
```

Less common in modern deployments but still found in IoT firmware
web UIs and embedded server setups.

### Python http.server (dev only)

`python3 -m http.server 8000` — the stdlib dev server defaults to
autoindex. Should never be in production but sometimes runs on a
forgotten port.

Fingerprint: `<title>Directory listing for /<path></title>`.

### Node `serve` / `http-server`

`npx serve` and `http-server` both default to autoindex. Common in
developer-facing tooling, hosting docs sites, or "I just need a
quick static server" setups.

### IIS

IIS disables directory browsing by default. If enabled in
`web.config`:

```xml
<system.webServer>
    <directoryBrowse enabled="true" />
</system.webServer>
```

Fingerprint: HTML body with "Directory browsing" title.

### AWS S3 ListBucket

S3 buckets aren't web servers in the conventional sense but expose
similar functionality. A bucket policy that grants `s3:ListBucket`
to the public lets unauthenticated requestors list every object.

Fingerprint: XML response with `<ListBucketResult>` root element,
listing every key in the bucket.

### Azure Blob Storage list-blob

Same pattern: `?restype=container&comp=list` on a public-list
container returns XML enumeration of every blob.

Fingerprint: `<EnumerationResults>` root + blob entries with
properties.

### GCS bucket "list" permission

GCP Cloud Storage equivalent: `storage.objects.list` granted to
`allUsers` lets anyone enumerate bucket contents.

Fingerprint: similar XML / JSON enumeration depending on whether
the request hit the JSON or XML API.

## Why directory listings escalate other findings

Directory listings rarely stand alone. They compound the impact of
other findings:

### Combined with `.git/` exposure

Skill #6 detects `.git/HEAD` reachable. If the parent `.git/`
directory ALSO has autoindex on, every object in `.git/objects/`
is enumerable. GitDumper-style tools become unnecessary — you can
just `wget -r` the directory.

### Combined with backup-file exposure

Skill #6 probes specific backup file paths (`backup.sql`,
`dump.sql`). Autoindex on `/backup/` lets the attacker see every
backup file the operator ever left, including ones with non-
canonical names (`db-snapshot-2024-03-15.sql.bz2`,
`pre-migration-dump.sql`).

### Combined with upload directories

If `/uploads/` lists, every user-uploaded file is enumerable
including potentially-sensitive private uploads that the
application's auth layer was supposed to gate.

## Why static-asset hosts are a common pitfall

A common pattern: front-end is hosted on a CDN (S3 plus CloudFront,
GCS plus Cloud CDN). The bucket policy is set to "allow public read
of specific objects" but the BUCKET listing permission is left at
default, which on S3 with an explicit grant is "public ListBucket."

The fix is to:

1. Make individual objects publicly readable (`s3:GetObject`).
2. NOT grant `s3:ListBucket` to `*`.

Result: clients can fetch `https://cdn.example.com/assets/logo.png`
if they know the path, but `https://cdn.example.com/assets/`
returns AccessDenied.

## Why the SPA case isn't autoindex

Single-Page Applications using client-side routing return the app's
`index.html` for any unknown route. That's NOT an autoindex page —
it's a deliberate routing decision. The fingerprint check
distinguishes:

- Autoindex → HTML body contains "Index of /<path>" or framework
  banner
- SPA → HTML body is the application's own UI

A 200 response with HTML body that doesn't match any autoindex
fingerprint is an SPA catch-all and is NOT flagged.

## Primary sources

- [OWASP WSTG-CONF-04 — Review Old Backup and Unreferenced Files](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/04-Review_Old_Backup_and_Unreferenced_Files_for_Sensitive_Information)
- [CWE-548 — Exposure of Information Through Directory Listing](https://cwe.mitre.org/data/definitions/548.html)
- [nginx autoindex module](https://nginx.org/en/docs/http/ngx_http_autoindex_module.html)
- [Apache mod_autoindex](https://httpd.apache.org/docs/2.4/mod/mod_autoindex.html)
- [Caddy file_server directive](https://caddyserver.com/docs/caddyfile/directives/file_server)
- [AWS S3 — Blocking public access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
