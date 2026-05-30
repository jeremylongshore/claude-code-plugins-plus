# TLS Remediation Playbook — copy-paste templates per finding

Match the finding to a row below; the right column is a copy-paste-ready
config snippet for the relevant server type. Reload (NOT restart) the
server after applying — restart drops in-flight connections; reload
preserves them on every server type listed here.

## Obsolete protocol (TLSv1.0 / TLSv1.1)

### nginx

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
```

Reload: `nginx -t && systemctl reload nginx`

### Caddy

TLSv1.2 is the minimum default since Caddy 2.0; no config needed unless
you've explicitly downgraded. Verify with `caddy adapt --pretty` and
look for any `min_version` overrides.

### Apache (httpd 2.4)

```apache
SSLProtocol TLSv1.2 TLSv1.3
SSLHonorCipherOrder on
```

Reload: `apachectl configtest && systemctl reload httpd`

### HAProxy

```haproxy
bind :443 ssl crt /etc/ssl/private/cert.pem ssl-min-ver TLSv1.2
```

Reload: `systemctl reload haproxy`

### AWS ALB

Listener config → Security policy → choose `ELBSecurityPolicy-TLS13-1-2-2021-06` (TLSv1.2+TLSv1.3) or `ELBSecurityPolicy-TLS13-1-3-2021-06` (TLSv1.3 only).
Console path: EC2 → Load Balancers → your ALB → Listeners tab → edit on the HTTPS listener.

### GCP HTTPS Load Balancer

```bash
gcloud compute ssl-policies create modern-tls \
    --profile MODERN --min-tls-version 1.2
# then attach to your target proxy:
gcloud compute target-https-proxies update YOUR_PROXY --ssl-policy modern-tls
```

## Weak cipher (RC4 / 3DES / NULL / EXPORT)

### nginx (Mozilla intermediate)

```nginx
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
```

### Caddy

Default cipher list is already safe. To explicitly set:

```caddy
example.com {
    tls {
        ciphers TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
    }
}
```

### Apache

```apache
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
```

### HAProxy

```haproxy
bind :443 ssl crt /etc/ssl/private/cert.pem \
    ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305 \
    ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
```

## Certificate expires soon

### Let's Encrypt via certbot

Verify the renewal timer is healthy:

```bash
systemctl status certbot.timer
sudo certbot renew --dry-run
```

Force renewal in an emergency:

```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx  # or apache / haproxy
```

### Caddy auto-issuance

Caddy auto-renews; if it's failing, check logs:

```bash
journalctl -u caddy -n 200 | grep -i tls
```

Common cause: ACME challenge failure due to firewall blocking port 80
(HTTP-01) or DNS API credentials expired (DNS-01).

### AWS ACM

Renewal is automatic for ACM-issued certs. If the cert shows "Pending
renewal" for >7 days, ACM cannot validate ownership — usually because
the CNAME validation record is missing or pointing to an old cert.
Re-issue the validation record from the ACM console.

## Certificate hostname mismatch

You will need to reissue the cert with the correct SAN list. There is no
runtime-only fix.

### Let's Encrypt — single-cert SAN reissuance

```bash
sudo certbot certonly --nginx \
    -d example.com \
    -d www.example.com \
    -d api.example.com \
    --expand
```

The `--expand` flag tells Let's Encrypt to expand an existing cert with
additional SANs rather than issue a new cert.

### Caddy

Just list every hostname in your Caddyfile; Caddy issues separate certs
per hostname automatically, or you can request one cert with SAN
via the `tls.issuance_policy` block (advanced).

### AWS ACM

Request a new cert with all required SANs (you cannot edit SANs on an
issued ACM cert). After validation, swap the ACM ARN on the ALB
listener.

## Chain trust failure

The leaf cert is fine, but the chain to the trusted root is broken.
Most common cause: the server isn't returning intermediate certs.

### Verify locally

```bash
openssl s_client -connect example.com:443 -showcerts < /dev/null
```

Look for **two or three** `BEGIN CERTIFICATE` blocks. One = chain broken.

### nginx

```nginx
ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
```

Use `fullchain.pem` (not `cert.pem`) — fullchain includes the
intermediate.

### Apache

```apache
SSLCertificateFile /etc/letsencrypt/live/example.com/cert.pem
SSLCertificateKeyFile /etc/letsencrypt/live/example.com/privkey.pem
SSLCertificateChainFile /etc/letsencrypt/live/example.com/chain.pem
```

On Apache 2.4.8+, fullchain via SSLCertificateFile also works.

### Caddy

Auto-handled. If you see this finding on Caddy, look at storage
permissions — Caddy couldn't load the chain from `~/.local/share/caddy/`.

## Forward secrecy absent

Pure RSA key exchange (TLS_RSA_*) — fix by enabling ECDHE.

### nginx

```nginx
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA256:...;
ssl_ecdh_curve secp384r1:secp521r1;
```

### Generic — use Mozilla's intermediate config

Visit [ssl-config.mozilla.org](https://ssl-config.mozilla.org/), pick
your server type + version, paste the generated config. Every snippet
in that generator enables ECDHE by default.

## Weak key size

Reissue the cert with adequate key size. Modern issuance defaults are
2048-bit RSA or P-256 ECDSA — both meet the floor.

### Let's Encrypt — request RSA 4096 or ECDSA P-384

```bash
sudo certbot certonly --nginx \
    -d example.com \
    --key-type rsa --rsa-key-size 4096
```

Or:

```bash
sudo certbot certonly --nginx \
    -d example.com \
    --key-type ecdsa --elliptic-curve secp384r1
```

### AWS ACM

Request → "Request a public certificate" → "Algorithm" → choose
`RSA 2048`, `ECDSA P-256`, or stronger.

## Validation after remediation

After applying any fix, re-run this skill:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/analyzing-tls-config/scripts/analyze_tls.py \
    https://example.com \
    --authorized \
    --min-severity high
```

Expected: exit code 0, no HIGH or CRITICAL findings.

For ongoing posture monitoring, embed the scanner in CI:

```yaml
# GitHub Actions example
- name: TLS posture check
  run: |
    python3 plugins/security/penetration-tester/skills/analyzing-tls-config/scripts/analyze_tls.py \
        "${{ secrets.PROD_URL }}" \
        --authorized \
        --min-severity high \
        --format json \
        --output tls-report.json
- uses: actions/upload-artifact@v4
  with:
    name: tls-report
    path: tls-report.json
```
