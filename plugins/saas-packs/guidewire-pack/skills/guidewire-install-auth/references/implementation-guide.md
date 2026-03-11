# Guidewire Install Auth - Implementation Guide

# Guidewire Install & Auth

## Overview

Set up Guidewire InsuranceSuite development environment and configure Cloud API authentication with Guidewire Hub using OAuth2 and JWT tokens.

## Prerequisites

- JDK 11 or 17 (Guidewire Cloud 202503+ requires JDK 17)
- Gradle 7.x or 8.x
- Guidewire Cloud account with developer access
- Access to Guidewire Cloud Console (GCC)
- Guidewire Hub registration for your application

## Instructions

### Step 1: Install Development Tools

```bash
# Verify Java installation
java -version
# Required: openjdk 17.x or 11.x

# Install Gradle if needed
sdk install gradle 8.5

# Clone your InsuranceSuite configuration repository
git clone https://your-org@dev.azure.com/your-org/PolicyCenter/_git/PolicyCenter
cd PolicyCenter
```

### Step 2: Configure Guidewire Studio

```bash
# Set environment variables
export GW_HOME=/path/to/guidewire/installation
export JAVA_HOME=/path/to/jdk17

# Import project into IntelliJ IDEA (recommended IDE)
# File > Open > Select the build.gradle file
```

### Step 3: Register Application with Guidewire Hub

1. Log into Guidewire Cloud Console (GCC) at `https://gcc.guidewire.com`
2. Navigate to **Identity & Access > Applications**
3. Click **Register Application**
4. Select application type:
   - **Browser Application** - For Jutro frontends (OAuth2 Authorization Code flow)
   - **Service Application** - For backend integrations (OAuth2 Client Credentials flow)
5. Record the `client_id` and `client_secret`

### Step 4: Configure OAuth2 Credentials

```bash
# Create environment configuration
cat > .env << 'EOF'
# Guidewire Cloud API Configuration
GW_TENANT_ID=your-tenant-id
GW_CLIENT_ID=your-client-id
GW_CLIENT_SECRET=your-client-secret
GW_HUB_URL=https://hub.guidewire.com
GW_API_BASE_URL=https://your-tenant.cloud.guidewire.com

# Application endpoints
POLICYCENTER_URL=${GW_API_BASE_URL}/pc/rest
CLAIMCENTER_URL=${GW_API_BASE_URL}/cc/rest
BILLINGCENTER_URL=${GW_API_BASE_URL}/bc/rest
EOF
```

### Step 5: Obtain Access Token (Service Application)

```typescript
// TypeScript/Node.js - OAuth2 Client Credentials Flow
import axios from 'axios';

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

async function getAccessToken(): Promise<string> {
  const tokenUrl = `${process.env.GW_HUB_URL}/oauth/token`;

  const response = await axios.post<TokenResponse>(tokenUrl,
    new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.GW_CLIENT_ID!,
      client_secret: process.env.GW_CLIENT_SECRET!,
      scope: 'pc.policies cc.claims bc.billing'
    }),
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }
  );

  return response.data.access_token;
}
```

### Step 6: Verify Connection

```typescript
// Test API connection
async function verifyConnection(): Promise<void> {
  const token = await getAccessToken();

  const response = await axios.get(
    `${process.env.POLICYCENTER_URL}/common/v1/system-info`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  console.log('Connected to PolicyCenter:', response.data);
}
```

## Gosu Authentication (Server-Side)

```gosu
// Gosu - Internal authentication for plugins
uses gw.api.system.server.ServerUtil
uses gw.api.web.SessionUtil

class AuthHelper {
  static function getAuthenticatedUser() : User {
    return SessionUtil.CurrentUser
  }

  static function runAsSystemUser<T>(block() : T) : T {
    return ServerUtil.runAsSystemUser(\-> block())
  }
}
```

## Output

- Configured Guidewire Studio project
- OAuth2 credentials in environment variables
- Verified connection to Cloud API endpoints
- JWT token acquisition working

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong client credentials | Verify client_id and secret in GCC |
| `invalid_scope` | Unauthorized scope requested | Check API role assignments in GCC |
| `401 Unauthorized` | Expired or invalid token | Refresh token, check clock sync |
| `403 Forbidden` | Missing API role permissions | Assign appropriate API roles in GCC |
| `PKIX path building failed` | SSL certificate issue | Import Guidewire CA certificates |

## API Roles Configuration

Configure in Guidewire Cloud Console:

```yaml
# Recommended API roles for service applications
api_roles:
  - PolicyCenter:
      - pc_policy_admin
      - pc_submission_handler
      - pc_product_read
  - ClaimCenter:
      - cc_claim_admin
      - cc_fnol_handler
  - BillingCenter:
      - bc_billing_admin
      - bc_payment_handler
```

## Examples

### Complete TypeScript Client Setup

```typescript
import axios, { AxiosInstance } from 'axios';

class GuidewireClient {
  private token: string | null = null;
  private tokenExpiry: Date | null = null;
  private httpClient: AxiosInstance;

  constructor(
    private clientId: string,
    private clientSecret: string,
    private hubUrl: string,
    private apiBaseUrl: string
  ) {
    this.httpClient = axios.create({
      baseURL: apiBaseUrl,
      timeout: 30000
    });
  }

  private async ensureToken(): Promise<string> {
    if (this.token && this.tokenExpiry && this.tokenExpiry > new Date()) {
      return this.token;
    }

    const response = await axios.post(`${this.hubUrl}/oauth/token`,
      new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: this.clientId,
        client_secret: this.clientSecret
      })
    );

    this.token = response.data.access_token;
    this.tokenExpiry = new Date(Date.now() + (response.data.expires_in - 60) * 1000);
    return this.token;
  }

  async request<T>(method: string, path: string, data?: any): Promise<T> {
    const token = await this.ensureToken();
    const response = await this.httpClient.request<T>({
      method,
      url: path,
      data,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  }
}

// Usage
const client = new GuidewireClient(
  process.env.GW_CLIENT_ID!,
  process.env.GW_CLIENT_SECRET!,
  process.env.GW_HUB_URL!,
  process.env.POLICYCENTER_URL!
);
```

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Authentication](https://docs.guidewire.com/education/cloud-integration-basics/latest/docs/authentication/cloud_api_auth/)
- [Guidewire Hub Registration](https://docs.guidewire.com/cloud/pc/202503/cloudapica/cloudAPI/topics/702-AuthFlows/)
- [Guidewire Cloud Console](https://gcc.guidewire.com/)

## Next Steps

After successful auth, proceed to `guidewire-hello-world` for your first API calls.
