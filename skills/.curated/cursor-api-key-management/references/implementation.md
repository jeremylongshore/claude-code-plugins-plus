# API Key Management Implementation

## Key Rotation Strategy

1. Generate new key via Cursor Settings > API Keys
2. Update environment variables with new key
3. Verify new key works with test request
4. Revoke old key after confirmation

## Storage Patterns

- Environment variables (recommended): `CURSOR_API_KEY`
- `.env` file (local development only, never commit)
- Secret manager (production): AWS Secrets Manager, GCP Secret Manager, or Vault

## Security Checklist

- Never hardcode API keys in source code
- Rotate keys every 90 days minimum
- Use separate keys for development and production
- Monitor key usage for anomalies
- Revoke compromised keys immediately

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
