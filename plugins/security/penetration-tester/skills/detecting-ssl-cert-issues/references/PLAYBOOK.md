# Certificate Posture Remediation Playbook

## Enable OCSP stapling

### nginx

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;

    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;
}
```

The `ssl_trusted_certificate` directive is REQUIRED for stapling to
work — nginx uses it to verify the OCSP response signature.

Reload: `nginx -t && systemctl reload nginx`

Verify:

```bash
openssl s_client -connect example.com:443 -status < /dev/null 2>&1 | grep -A 20 "OCSP response:"
```

Expected: a populated OCSP response block, NOT "no response sent".

### Caddy

Auto-enabled since Caddy 2.0. No config needed. Verify with the same
openssl command.

### Apache (httpd 2.4)

```apache
SSLUseStapling on
SSLStaplingCache shmcb:/var/run/ocsp(150000)
SSLStaplingResponderTimeout 5
SSLStaplingReturnResponderErrors off
```

Place `SSLStaplingCache` at the global / virtualhost-shared scope, not
inside a single virtualhost.

### HAProxy

```haproxy
frontend https
    bind :443 ssl crt /etc/ssl/private/cert.pem
    # Manual stapling — HAProxy doesn't fetch OCSP itself
```

HAProxy requires an external OCSP fetcher (e.g., `haproxy-ocsp-updater`
or systemd timer running `openssl ocsp` and writing to a `.ocsp` file
that HAProxy auto-loads).

## Fix chain order

Most common cause: `fullchain.pem` is correct but operators serve
`cert.pem` (leaf only) or `chain.pem` (intermediate only). Verify:

```bash
openssl crl2pkcs7 -nocrl -certfile /etc/letsencrypt/live/example.com/fullchain.pem \
    | openssl pkcs7 -print_certs -noout
```

Expected output: leaf subject first, then intermediate(s). If you see
the root subject anywhere, the wrong file is being served. Update
nginx/Apache config to point at `fullchain.pem` (Let's Encrypt) or
rebuild from `cat cert.pem intermediate.pem > fullchain.pem` (NOT
`intermediate.pem cert.pem`).

## SCT shortage

You cannot add SCTs to an issued cert. Reissue from a CA that submits
to ≥2 CT logs:

### Let's Encrypt (default)

```bash
sudo certbot certonly --nginx -d example.com --force-renewal
```

Let's Encrypt submits to ≥3 logs at issuance.

### Verify SCTs post-issuance

```bash
openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem -noout -text \
    | grep -A 4 "CT Precertificate"
```

You should see ≥2 `Signed Certificate Timestamp:` blocks.

Or cross-check via crt.sh:

```bash
curl -s "https://crt.sh/?q=example.com&output=json" | jq '.[0].id'
```

## AIA correctness

If your cert is from a public CA and AIA is missing, contact the CA
support team — this is unusual.

If your cert is from a private CA, edit the CA's issuance template to
include AIA URLs. For step-ca:

```yaml
authority:
  template: |
    {
      "extensions": {
        "authorityInfoAccess": [
          {"id": "ocsp", "value": "http://ocsp.internal.example.com/"},
          {"id": "caIssuers", "value": "http://ca.internal.example.com/intermediate.crt"}
        ]
      }
    }
```

## Wildcard scope tightening

You cannot narrow an issued cert. Reissue:

### Let's Encrypt — replace wildcard with explicit SANs

```bash
sudo certbot certonly --nginx \
    -d example.com \
    -d www.example.com \
    -d api.example.com \
    -d app.example.com
```

This issues one cert with explicit SAN list instead of a wildcard.
Performance is identical at handshake time; blast radius if private
key compromised is bounded to the SAN list.

### Move to per-service certs

For high-security postures (banking, healthcare), issue one cert per
service so a key compromise on `internal-admin.example.com` doesn't
allow MITM on `app.example.com`. Use Caddy with auto-issuance per host
or certbot with `--cert-name` per service.

## Key Usage fix

CA-side issuance config. For step-ca:

```yaml
keyUsage:
  - digitalSignature
  - keyEncipherment
```

For public CAs, this is set correctly by default; missing KU on a
public cert means contact CA support.

## CI posture monitoring

Run on every deploy + nightly:

```yaml
- name: Certificate posture audit
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-ssl-cert-issues/scripts/check_cert_chain.py \
        "${{ secrets.PROD_URL }}" \
        --authorized \
        --min-severity medium \
        --format json \
        --output cert-posture.json
- uses: actions/upload-artifact@v4
  with:
    name: cert-posture
    path: cert-posture.json
```

Pair with skill #1 `analyzing-tls-config` for a complete TLS-layer
audit on the same target.

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-ssl-cert-issues/scripts/check_cert_chain.py \
    https://example.com \
    --authorized \
    --min-severity high
```

Expected: exit code 0, no HIGH / CRITICAL findings.

For a paranoid pre-launch check, drop `--min-severity` to surface all
LOW findings — they're operational backlog hardening rather than
blockers.
