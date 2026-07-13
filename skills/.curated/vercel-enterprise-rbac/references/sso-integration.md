# Sso Integration

## SSO Integration

### SAML Configuration

```typescript
// Vercel SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://vercel.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/vercel/callback',
};

// Map IdP groups to Vercel roles
const groupRoleMapping: Record<string, VercelRole> = {
  'Engineering': VercelRole.Developer,
  'Platform-Admins': VercelRole.Admin,
  'Data-Team': VercelRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from 'vercel';

const oauthClient = new OAuth2Client({
  clientId: process.env.VERCEL_OAUTH_CLIENT_ID!,
  clientSecret: process.env.VERCEL_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/vercel/callback',
  scopes: read, write, deploy,
});
```
