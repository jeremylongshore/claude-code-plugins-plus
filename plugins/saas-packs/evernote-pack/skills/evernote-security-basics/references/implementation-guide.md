# Evernote Security Basics - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Credential Security

### Step 1: Environment Variables

```bash
EVERNOTE_CONSUMER_KEY=your-consumer-key
EVERNOTE_CONSUMER_SECRET=your-consumer-secret
EVERNOTE_SANDBOX=true

.env
.env.local
.env.*.local
*.pem
*.key
```

```javascript
// config/evernote.js
require('dotenv').config();

const config = {
  consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
  consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
  sandbox: process.env.EVERNOTE_SANDBOX === 'true'
};

// Validate required credentials at startup
const required = ['consumerKey', 'consumerSecret'];
for (const key of required) {
  if (!config[key]) {
    throw new Error(`Missing required config: ${key}`);
  }
}

module.exports = Object.freeze(config);
```

### Step 2: Secret Manager Integration

```javascript
// For production, use a secret manager

// AWS Secrets Manager
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

async function getEvernoteSecrets() {
  const client = new SecretsManagerClient({ region: 'us-east-1' });

  const response = await client.send(
    new GetSecretValueCommand({
      SecretId: 'evernote/api-credentials'
    })
  );

  return JSON.parse(response.SecretString);
}

// Google Secret Manager
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');

async function getSecretFromGCP(secretName) {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/my-project/secrets/${secretName}/versions/latest`
  });
  return version.payload.data.toString('utf8');
}
```

### Step 3: Secure Token Storage

```javascript
// services/token-store.js

/**
 * Never store tokens in:
 * - Plain text files
 * - Client-side storage (localStorage, cookies without httpOnly)
 * - Source code
 * - Log files
 */

class SecureTokenStore {
  constructor(encryptionKey) {
    this.crypto = require('crypto');
    this.algorithm = 'aes-256-gcm';
    this.key = this.deriveKey(encryptionKey);
  }

  deriveKey(password) {
    return this.crypto.scryptSync(password, 'salt', 32);
  }

  encrypt(token) {
    const iv = this.crypto.randomBytes(16);
    const cipher = this.crypto.createCipheriv(this.algorithm, this.key, iv);

    let encrypted = cipher.update(token, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return {
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }

  decrypt(encryptedData) {
    const decipher = this.crypto.createDecipheriv(
      this.algorithm,
      this.key,
      Buffer.from(encryptedData.iv, 'hex')
    );

    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));

    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

module.exports = SecureTokenStore;
```


## OAuth Security

### Step 4: Secure OAuth Implementation

```javascript
// routes/oauth.js
const express = require('express');
const Evernote = require('evernote');
const crypto = require('crypto');

const router = express.Router();

// Generate CSRF token
function generateCSRFToken() {
  return crypto.randomBytes(32).toString('hex');
}

// Initiate OAuth with CSRF protection
router.get('/auth/evernote', (req, res) => {
  // Generate and store CSRF token
  const csrfToken = generateCSRFToken();
  req.session.csrfToken = csrfToken;

  const client = new Evernote.Client({
    consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
    consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
    sandbox: process.env.EVERNOTE_SANDBOX === 'true'
  });

  // Include CSRF token in callback URL
  const callbackUrl = `${process.env.APP_URL}/auth/evernote/callback?csrf=${csrfToken}`;

  client.getRequestToken(callbackUrl, (error, oauthToken, oauthTokenSecret) => {
    if (error) {
      console.error('OAuth request token error:', error);
      return res.status(500).json({ error: 'Failed to initiate authentication' });
    }

    // Store tokens securely in session
    req.session.oauthToken = oauthToken;
    req.session.oauthTokenSecret = oauthTokenSecret;
    req.session.oauthTimestamp = Date.now();

    res.redirect(client.getAuthorizeUrl(oauthToken));
  });
});

// Handle OAuth callback with validation
router.get('/auth/evernote/callback', (req, res) => {
  // Validate CSRF token
  if (req.query.csrf !== req.session.csrfToken) {
    return res.status(403).json({ error: 'Invalid CSRF token' });
  }

  // Check OAuth request timeout (5 minutes)
  const timeout = 5 * 60 * 1000;
  if (Date.now() - req.session.oauthTimestamp > timeout) {
    return res.status(400).json({ error: 'OAuth request expired' });
  }

  // Validate required parameters
  if (!req.query.oauth_verifier) {
    return res.status(400).json({ error: 'Missing oauth_verifier' });
  }

  const client = new Evernote.Client({
    consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
    consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
    sandbox: process.env.EVERNOTE_SANDBOX === 'true'
  });

  client.getAccessToken(
    req.session.oauthToken,
    req.session.oauthTokenSecret,
    req.query.oauth_verifier,
    (error, accessToken, accessTokenSecret, results) => {
      if (error) {
        console.error('OAuth access token error:', error);
        return res.status(500).json({ error: 'Failed to complete authentication' });
      }

      // Clear OAuth session data
      delete req.session.oauthToken;
      delete req.session.oauthTokenSecret;
      delete req.session.oauthTimestamp;
      delete req.session.csrfToken;

      // Store access token securely
      // DO NOT log the token
      req.session.evernoteToken = accessToken;
      req.session.evernoteExpires = parseInt(results.edam_expires);

      res.redirect('/dashboard');
    }
  );
});

module.exports = router;
```

### Step 5: Session Security

```javascript
// config/session.js
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const { createClient } = require('redis');

const redisClient = createClient({
  url: process.env.REDIS_URL
});

redisClient.connect().catch(console.error);

module.exports = session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,
  name: 'sessionId', // Don't use default 'connect.sid'
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS only in production
    httpOnly: true, // Prevent XSS access
    sameSite: 'lax', // CSRF protection
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
});
```


## Input Validation

### Step 6: Validate User Input

```javascript
// utils/validators.js

const validator = {
  /**
   * Validate note title
   */
  noteTitle(title) {
    if (!title || typeof title !== 'string') {
      throw new Error('Note title is required');
    }

    // Max 255 characters
    if (title.length > 255) {
      throw new Error('Note title must be 255 characters or less');
    }

    // No control characters
    if (/[\x00-\x1f]/.test(title)) {
      throw new Error('Note title contains invalid characters');
    }

    return title.trim();
  },

  /**
   * Validate notebook name
   */
  notebookName(name) {
    if (!name || typeof name !== 'string') {
      throw new Error('Notebook name is required');
    }

    if (name.length > 100) {
      throw new Error('Notebook name must be 100 characters or less');
    }

    return name.trim();
  },

  /**
   * Validate tag name
   */
  tagName(name) {
    if (!name || typeof name !== 'string') {
      throw new Error('Tag name is required');
    }

    if (name.length > 100) {
      throw new Error('Tag name must be 100 characters or less');
    }

    // Tags cannot start with #
    if (name.startsWith('#')) {
      throw new Error('Tag name cannot start with #');
    }

    return name.trim();
  },

  /**
   * Validate GUID format
   */
  guid(guid) {
    if (!guid || typeof guid !== 'string') {
      throw new Error('GUID is required');
    }

    // Evernote GUIDs are typically UUID format
    const guidPattern = /^[a-f0-9-]{36}$/i;
    if (!guidPattern.test(guid)) {
      throw new Error('Invalid GUID format');
    }

    return guid;
  },

  /**
   * Sanitize ENML content
   */
  enmlContent(content) {
    if (!content || typeof content !== 'string') {
      throw new Error('Content is required');
    }

    // Remove potentially dangerous elements
    let sanitized = content
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<iframe[^>]*>[\s\S]*?<\/iframe>/gi, '')
      .replace(/<object[^>]*>[\s\S]*?<\/object>/gi, '')
      .replace(/<embed[^>]*>/gi, '')
      .replace(/<form[^>]*>[\s\S]*?<\/form>/gi, '');

    // Remove event handlers
    sanitized = sanitized.replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, '');

    // Remove javascript: URLs
    sanitized = sanitized.replace(/javascript:/gi, '');

    return sanitized;
  }
};

module.exports = validator;
```

### Step 7: Secure Logging

```javascript
// utils/secure-logger.js

class SecureLogger {
  constructor() {
    this.sensitivePatterns = [
      /S=s\d+:U=[^:]+:[^:]+:[a-f0-9]+/gi, // Evernote tokens
      /oauth_token=[^&]+/gi,
      /oauth_token_secret=[^&]+/gi,
      /consumer_secret=[^&]+/gi,
      /password=[^&]+/gi,
      /api_key=[^&]+/gi
    ];
  }

  sanitize(data) {
    if (typeof data === 'string') {
      let sanitized = data;
      for (const pattern of this.sensitivePatterns) {
        sanitized = sanitized.replace(pattern, '[REDACTED]');
      }
      return sanitized;
    }

    if (typeof data === 'object' && data !== null) {
      const sanitized = Array.isArray(data) ? [] : {};

      for (const [key, value] of Object.entries(data)) {
        const lowerKey = key.toLowerCase();

        if (lowerKey.includes('token') ||
            lowerKey.includes('secret') ||
            lowerKey.includes('password') ||
            lowerKey.includes('key')) {
          sanitized[key] = '[REDACTED]';
        } else {
          sanitized[key] = this.sanitize(value);
        }
      }

      return sanitized;
    }

    return data;
  }

  log(level, message, data = null) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data: data ? this.sanitize(data) : undefined
    };

    console[level === 'error' ? 'error' : 'log'](JSON.stringify(entry));
  }

  info(message, data) {
    this.log('info', message, data);
  }

  error(message, data) {
    this.log('error', message, data);
  }

  warn(message, data) {
    this.log('warn', message, data);
  }
}

module.exports = new SecureLogger();
```


## Token Lifecycle

### Step 8: Token Expiration Handling

```javascript
// services/token-manager.js

class TokenManager {
  constructor(options = {}) {
    this.refreshThresholdDays = options.refreshThresholdDays || 30;
  }

  /**
   * Check if token needs refresh (approaching expiration)
   */
  needsRefresh(expirationTimestamp) {
    const now = Date.now();
    const expiresAt = expirationTimestamp;
    const thresholdMs = this.refreshThresholdDays * 24 * 60 * 60 * 1000;

    return (expiresAt - now) < thresholdMs;
  }

  /**
   * Check if token is expired
   */
  isExpired(expirationTimestamp) {
    return Date.now() > expirationTimestamp;
  }

  /**
   * Calculate days until expiration
   */
  daysUntilExpiration(expirationTimestamp) {
    const ms = expirationTimestamp - Date.now();
    return Math.floor(ms / (24 * 60 * 60 * 1000));
  }

  /**
   * Token status summary
   */
  getStatus(expirationTimestamp) {
    const daysLeft = this.daysUntilExpiration(expirationTimestamp);

    return {
      expiresAt: new Date(expirationTimestamp),
      daysUntilExpiration: daysLeft,
      isExpired: this.isExpired(expirationTimestamp),
      needsRefresh: this.needsRefresh(expirationTimestamp),
      status: this.isExpired(expirationTimestamp) ? 'EXPIRED' :
              daysLeft < 7 ? 'CRITICAL' :
              daysLeft < 30 ? 'WARNING' : 'OK'
    };
  }
}

module.exports = TokenManager;
```


## Security Checklist

```markdown


## Pre-Production Security Checklist

### Credentials
- [ ] API keys stored in environment variables or secret manager
- [ ] No credentials in source code
- [ ] .env files in .gitignore
- [ ] Different credentials for dev/staging/production

### OAuth
- [ ] CSRF protection implemented
- [ ] OAuth state parameter validated
- [ ] Request token timeout enforced
- [ ] Secure session storage (Redis, database)

### Sessions
- [ ] HttpOnly cookies enabled
- [ ] Secure flag enabled in production
- [ ] SameSite attribute set
- [ ] Session timeout configured

### Data Protection
- [ ] Tokens encrypted at rest
- [ ] Sensitive data not logged
- [ ] Input validation on all user data
- [ ] ENML content sanitized

### Transport
- [ ] HTTPS enforced in production
- [ ] TLS 1.2+ required
- [ ] Certificate validation enabled

### Error Handling
- [ ] No sensitive data in error messages
- [ ] Generic error messages to users
- [ ] Detailed errors only in secure logs
```
