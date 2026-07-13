# Sso Integration

## SSO Integration

### SAML Configuration

```typescript
// Supabase SAML setup
const samlConfig = {
  entryPoint: 'https://idp.company.com/saml/sso',
  issuer: 'https://supabase.com/saml/metadata',
  cert: process.env.SAML_CERT,
  callbackUrl: 'https://app.yourcompany.com/auth/supabase/callback',
};

// Map IdP groups to Supabase roles
const groupRoleMapping: Record<string, SupabaseRole> = {
  'Engineering': SupabaseRole.Developer,
  'Platform-Admins': SupabaseRole.Admin,
  'Data-Team': SupabaseRole.Viewer,
};
```

### OAuth2/OIDC Integration

```typescript
import { OAuth2Client } from '@supabase/supabase-js';

const oauthClient = new OAuth2Client({
  clientId: process.env.SUPABASE_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SUPABASE_OAUTH_CLIENT_SECRET!,
  redirectUri: 'https://app.yourcompany.com/auth/supabase/callback',
  scopes: read, write, realtime,
});
```
