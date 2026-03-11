# Guidewire Security Basics - Implementation Guide

## Authentication Architecture

```
+------------------+      +------------------+      +------------------+
|                  |      |                  |      |                  |
|  Client App      |----->|  Guidewire Hub   |----->|  InsuranceSuite  |
|  (Frontend/API)  |      |  (IdP)           |      |  Cloud API       |
|                  |      |                  |      |                  |
+------------------+      +------------------+      +------------------+
        |                         |                         |
        |  1. Auth Request        |                         |
        |------------------------>|                         |
        |                         |                         |
        |  2. JWT Token           |                         |
        |<------------------------|                         |
        |                         |                         |
        |  3. API Call + JWT      |                         |
        |-------------------------------------------------->|
        |                         |                         |
        |  4. Validate JWT        |<------------------------|
        |                         |                         |
        |  5. Response            |                         |
        |<--------------------------------------------------|
```

## Instructions

### Step 1: Secure OAuth2 Implementation

```typescript
// Secure token management
interface TokenConfig {
  clientId: string;
  clientSecret: string;
  hubUrl: string;
  scope: string;
}

class SecureTokenManager {
  private token: string | null = null;
  private tokenExpiry: Date | null = null;
  private refreshPromise: Promise<string> | null = null;

  constructor(private config: TokenConfig) {}

  async getToken(): Promise<string> {
    // Return cached token if valid
    if (this.isTokenValid()) {
      return this.token!;
    }

    // Prevent concurrent refresh requests
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.refreshToken();
    try {
      const token = await this.refreshPromise;
      return token;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async refreshToken(): Promise<string> {
    const response = await fetch(`${this.config.hubUrl}/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
        scope: this.config.scope
      })
    });

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status}`);
    }

    const data = await response.json();
    this.token = data.access_token;
    // Set expiry with 60-second buffer
    this.tokenExpiry = new Date(Date.now() + (data.expires_in - 60) * 1000);

    return this.token;
  }

  private isTokenValid(): boolean {
    return this.token !== null &&
           this.tokenExpiry !== null &&
           this.tokenExpiry > new Date();
  }

  // Securely clear tokens
  clearTokens(): void {
    this.token = null;
    this.tokenExpiry = null;
  }
}
```

### Step 2: JWT Validation

```typescript
// Validate JWT tokens (for webhook receivers or internal services)
import jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

interface JWTValidationConfig {
  issuer: string;
  audience: string;
  jwksUri: string;
}

class JWTValidator {
  private jwksClient: jwksClient.JwksClient;
  private keyCache: Map<string, string> = new Map();

  constructor(private config: JWTValidationConfig) {
    this.jwksClient = jwksClient({
      jwksUri: config.jwksUri,
      cache: true,
      cacheMaxAge: 600000, // 10 minutes
      rateLimit: true
    });
  }

  async validateToken(token: string): Promise<jwt.JwtPayload> {
    const decoded = jwt.decode(token, { complete: true });
    if (!decoded || !decoded.header.kid) {
      throw new Error('Invalid token format');
    }

    const publicKey = await this.getSigningKey(decoded.header.kid);

    return new Promise((resolve, reject) => {
      jwt.verify(
        token,
        publicKey,
        {
          issuer: this.config.issuer,
          audience: this.config.audience,
          algorithms: ['RS256']
        },
        (err, payload) => {
          if (err) {
            reject(new Error(`Token validation failed: ${err.message}`));
          } else {
            resolve(payload as jwt.JwtPayload);
          }
        }
      );
    });
  }

  private async getSigningKey(kid: string): Promise<string> {
    if (this.keyCache.has(kid)) {
      return this.keyCache.get(kid)!;
    }

    const key = await this.jwksClient.getSigningKey(kid);
    const publicKey = key.getPublicKey();
    this.keyCache.set(kid, publicKey);
    return publicKey;
  }
}
```

### Step 3: Configure API Roles

```yaml
# API Role Configuration in Guidewire Cloud Console
# Navigate to: Identity & Access > API Roles

# Service Account Role Assignment
service_accounts:
  integration-service:
    roles:
      - name: PolicyCenter
        permissions:
          - endpoint: /account/v1/accounts
            operations: [GET, POST, PATCH]
          - endpoint: /job/v1/submissions
            operations: [GET, POST]
          - endpoint: /policy/v1/policies
            operations: [GET]

      - name: ClaimCenter
        permissions:
          - endpoint: /claim/v1/claims
            operations: [GET, POST]
          - endpoint: /fnol/v1/fnol
            operations: [POST]

  readonly-service:
    roles:
      - name: PolicyCenter
        permissions:
          - endpoint: /account/v1/accounts
            operations: [GET]
          - endpoint: /policy/v1/policies
            operations: [GET]
```

### Step 4: Secure Gosu Coding

```gosu
// Secure Gosu coding practices
package gw.security

uses gw.api.util.Logger
uses gw.api.system.PLSecurityRules

class SecureCodingPractices {
  private static final var LOG = Logger.forCategory("Security")

  // Input validation
  static function validateInput(input : String, maxLength : int = 255) : String {
    if (input == null) {
      throw new IllegalArgumentException("Input cannot be null")
    }

    // Remove potentially dangerous characters
    var sanitized = input
      .replaceAll("[<>\"'%;)(&+]", "")
      .trim()

    if (sanitized.length() > maxLength) {
      throw new IllegalArgumentException("Input exceeds maximum length")
    }

    return sanitized
  }

  // SQL Injection Prevention - Always use Query API
  // BAD: String concatenation
  static function findAccountBad(accountNumber : String) : Account {
    // NEVER DO THIS - SQL Injection vulnerability!
    // var sql = "SELECT * FROM Account WHERE AccountNumber = '" + accountNumber + "'"
    return null
  }

  // GOOD: Use Query API with parameterized queries
  static function findAccountGood(accountNumber : String) : Account {
    return Query.make(Account)
      .compare(Account#AccountNumber, Equals, validateInput(accountNumber))
      .select()
      .AtMostOneRow
  }

  // Sensitive data handling
  static function maskSSN(ssn : String) : String {
    if (ssn == null || ssn.length() < 4) {
      return "***-**-****"
    }
    return "***-**-" + ssn.substring(ssn.length() - 4)
  }

  // Audit logging for sensitive operations
  static function auditSecurityEvent(
    action : String,
    resource : String,
    success : boolean,
    details : String = null
  ) {
    var user = gw.api.web.SessionUtil.CurrentUser
    var message = "SECURITY_AUDIT: action=${action}, resource=${resource}, " +
                  "user=${user.PublicID}, success=${success}"
    if (details != null) {
      message += ", details=${details}"
    }

    if (success) {
      LOG.info(message)
    } else {
      LOG.warn(message)
    }
  }

  // Check permissions before operations
  static function checkPermission(permission : String) {
    if (!PLSecurityRules.hasPermission(permission)) {
      auditSecurityEvent("ACCESS_DENIED", permission, false)
      throw new SecurityException("Permission denied: ${permission}")
    }
  }
}
```

### Step 5: Data Encryption

```gosu
// Encrypt sensitive data at rest
package gw.security.encryption

uses javax.crypto.Cipher
uses javax.crypto.spec.SecretKeySpec
uses javax.crypto.spec.IvParameterSpec
uses java.util.Base64
uses gw.api.util.Logger

class DataEncryption {
  private static final var LOG = Logger.forCategory("Encryption")
  private static final var ALGORITHM = "AES/CBC/PKCS5Padding"
  private static final var KEY_ALGORITHM = "AES"

  private var _secretKey : SecretKeySpec
  private var _iv : IvParameterSpec

  construct(keyBase64 : String, ivBase64 : String) {
    var keyBytes = Base64.getDecoder().decode(keyBase64)
    var ivBytes = Base64.getDecoder().decode(ivBase64)

    _secretKey = new SecretKeySpec(keyBytes, KEY_ALGORITHM)
    _iv = new IvParameterSpec(ivBytes)
  }

  function encrypt(plainText : String) : String {
    try {
      var cipher = Cipher.getInstance(ALGORITHM)
      cipher.init(Cipher.ENCRYPT_MODE, _secretKey, _iv)
      var encrypted = cipher.doFinal(plainText.getBytes("UTF-8"))
      return Base64.getEncoder().encodeToString(encrypted)
    } catch (e : Exception) {
      LOG.error("Encryption failed", e)
      throw new SecurityException("Encryption failed", e)
    }
  }

  function decrypt(encryptedText : String) : String {
    try {
      var cipher = Cipher.getInstance(ALGORITHM)
      cipher.init(Cipher.DECRYPT_MODE, _secretKey, _iv)
      var decoded = Base64.getDecoder().decode(encryptedText)
      var decrypted = cipher.doFinal(decoded)
      return new String(decrypted, "UTF-8")
    } catch (e : Exception) {
      LOG.error("Decryption failed", e)
      throw new SecurityException("Decryption failed", e)
    }
  }
}

// Usage for PII storage
class PIIHandler {
  private static var _encryption = new DataEncryption(
    ScriptParameters.EncryptionKey,
    ScriptParameters.EncryptionIV
  )

  static function storeSSN(contact : Contact, ssn : String) {
    contact.EncryptedSSN = _encryption.encrypt(ssn)
    // Clear unencrypted field if it exists
    contact.SSN = null
  }

  static function retrieveSSN(contact : Contact) : String {
    if (contact.EncryptedSSN != null) {
      return _encryption.decrypt(contact.EncryptedSSN)
    }
    return null
  }
}
```

### Step 6: Secure API Endpoints

```typescript
// Secure API middleware
import { Request, Response, NextFunction } from 'express';

interface SecurityContext {
  userId: string;
  roles: string[];
  permissions: string[];
  tenantId: string;
}

// Extract and validate security context
async function securityMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      res.status(401).json({ error: 'Missing authorization header' });
      return;
    }

    const token = authHeader.substring(7);
    const validator = new JWTValidator({
      issuer: process.env.GW_HUB_URL!,
      audience: process.env.GW_CLIENT_ID!,
      jwksUri: `${process.env.GW_HUB_URL}/.well-known/jwks.json`
    });

    const payload = await validator.validateToken(token);

    // Attach security context to request
    (req as any).securityContext = {
      userId: payload.sub,
      roles: payload.roles || [],
      permissions: payload.permissions || [],
      tenantId: payload.tenant_id
    } as SecurityContext;

    next();
  } catch (error) {
    console.error('Authentication failed:', error);
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// Role-based access control middleware
function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const context = (req as any).securityContext as SecurityContext;

    if (!context) {
      res.status(401).json({ error: 'Not authenticated' });
      return;
    }

    const hasRole = roles.some(role => context.roles.includes(role));
    if (!hasRole) {
      res.status(403).json({
        error: 'Forbidden',
        requiredRoles: roles,
        userRoles: context.roles
      });
      return;
    }

    next();
  };
}

// Usage
app.get('/api/policies',
  securityMiddleware,
  requireRole('policy_read', 'policy_admin'),
  async (req, res) => {
    // Handle request
  }
);
```

## Security Checklist

| Category | Check | Status |
|----------|-------|--------|
| Authentication | OAuth2 client credentials flow | Required |
| Authentication | JWT token validation | Required |
| Authentication | Token refresh before expiry | Required |
| Authorization | API roles configured | Required |
| Authorization | Least privilege principle | Required |
| Data Protection | PII encryption at rest | Required |
| Data Protection | TLS 1.2+ in transit | Required |
| Input Validation | All inputs sanitized | Required |
| Logging | Security events audited | Required |
| Secrets | No hardcoded credentials | Required |
