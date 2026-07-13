# Directory-Listing Remediation Playbook

## Apache mod_autoindex

### Disable autoindex globally (preferred)

`httpd.conf` or vhost:

```apache
<Directory /var/www/html>
    Options -Indexes
    AllowOverride None
    Require all granted
</Directory>
```

The `Options -Indexes` line is the critical part. Combined with no
`index.html` in a directory, requests return 403 (per Apache's
default fall-through) instead of an autoindex page.

### Per-directory override

If autoindex is needed in one specific directory (rare):

```apache
<Directory /var/www/html/public-archive>
    Options +Indexes
    IndexOptions +FancyIndexing +SuppressDescription
</Directory>
```

But this should require a deliberate decision, not a default.

### .htaccess (if `AllowOverride` permits)

```apache
Options -Indexes
```

In every directory you want to deny. The `AllowOverride` in vhost
must include `Options` for this to work.

## nginx autoindex

nginx defaults to autoindex off. The misconfiguration is when
someone explicitly enabled it:

```nginx
# In vhost or location block, REMOVE these lines if present:
autoindex on;
autoindex_format html;
autoindex_exact_size off;
autoindex_localtime on;
```

To explicitly assert off:

```nginx
location / {
    autoindex off;
    try_files $uri $uri/ =404;
}
```

The `try_files` directive ensures missing files return 404 instead
of any fallback behavior.

## Caddy file_server

Don't use `browse`:

```caddy
example.com {
    root * /srv/site
    file_server         # NO browse keyword
}
```

If browse was previously enabled, remove it:

```caddy
# BEFORE (vulnerable):
example.com {
    root * /srv/site
    file_server browse
}

# AFTER:
example.com {
    root * /srv/site
    file_server
    try_files {path} {path}/index.html =404
}
```

## Python http.server

Don't use in production. Period. If you absolutely must serve static
files with python in a constrained environment, use a real server
behind it OR a subclass that overrides `list_directory`:

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler

class NoBrowse(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(403, "Directory listing not permitted")
        return None

HTTPServer(('0.0.0.0', 8000), NoBrowse).serve_forever()
```

## Node serve / http-server

```bash
# serve — pass --single to disable directory listing
npx serve --single ./build

# http-server — pass -d false
npx http-server -d false ./build
```

Both options return 404 for missing files instead of generating a
listing page.

## IIS

`web.config`:

```xml
<system.webServer>
    <directoryBrowse enabled="false" />
    <defaultDocument>
        <files>
            <add value="index.html" />
            <add value="default.htm" />
        </files>
    </defaultDocument>
</system.webServer>
```

## AWS S3

### Block public ListBucket

S3 bucket policy — explicitly deny ListBucket to public:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyPublicList",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::my-public-cdn-bucket"
        },
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::my-public-cdn-bucket/*"
        }
    ]
}
```

Even better: enable S3 Block Public Access at the account level:

```bash
aws s3api put-public-access-block --bucket my-bucket \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

This blocks ALL public access at the bucket level. To then serve
content publicly, do it via CloudFront with Origin Access Control,
NOT via direct S3 URLs.

## AWS CloudFront in front of S3

When using CloudFront with Origin Access Control (recommended
pattern):

1. S3 bucket policy denies all public access.
2. Only the OAC's CloudFront distribution can read objects.
3. CloudFront's behavior settings determine what's reachable.

```bash
# Lock down the bucket
aws s3api put-bucket-policy --bucket my-bucket --policy '{
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowCloudFrontOAC",
        "Effect": "Allow",
        "Principal": {"Service": "cloudfront.amazonaws.com"},
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::my-bucket/*",
        "Condition": {
            "StringEquals": {
                "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID"
            }
        }
    }]
}'
```

## GCS

```bash
# Remove allUsers from objectViewer role
gsutil iam ch -d allUsers:objectViewer gs://my-bucket

# Make individual objects publicly readable instead (per-object ACL)
gsutil acl ch -u AllUsers:R gs://my-bucket/path/to/specific-file.png
```

Or use a Cloud CDN + signed URLs for true private serving.

## Azure Blob

```bash
# Set container access level to Private (not Container)
az storage container set-permission \
    --account-name myaccount \
    --name mycontainer \
    --public-access off
```

Then use SAS tokens or Azure CDN with private origin for public-facing
content.

## CI integration

```yaml
- name: Directory-listing posture gate
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-directory-listing/scripts/probe_directory_listing.py \
        "${{ secrets.PROD_URL }}" \
        --authorized \
        --min-severity high \
        --format json \
        --output autoindex-report.json
- run: |
    if jq 'any(.severity == "critical" or .severity == "high")' autoindex-report.json | grep -q true; then
      echo "::error::Directory listing detected"
      exit 1
    fi
```

## After remediation: assume enumeration occurred

If autoindex was exposed for any period:

- For `/backup/` listings: assume all backup files were enumerated.
  Rotate any credentials referenced in those files. Investigate
  whether any backup files contained PII that needs breach
  notification.
- For `/uploads/` listings: assume the file index was scraped.
  If any uploaded files were private (e.g., user-uploaded
  documents), assume those filenames are known to attackers
  even if the file contents required separate auth to fetch.
- For `/.git/` listings: assume the entire repository was
  reconstructed. Rotate every credential ever committed to the
  repo, including credentials in past commits that were later
  removed.

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-directory-listing/scripts/probe_directory_listing.py \
    https://example.com --authorized --min-severity info
```

Expected: exit 0, zero findings of any severity.
