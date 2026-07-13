# API Authentication Examples

## JWT Authentication Middleware (Express)

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      type: 'https://api.example.com/errors/missing-token',
      title: 'Authentication Required',
      status: 401,
      detail: 'No Bearer token provided in Authorization header'
    });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(401).json({
        type: 'https://api.example.com/errors/invalid-token',
        title: 'Invalid Token',
        status: 401,
        detail: err.name === 'TokenExpiredError'
          ? 'Token has expired, please refresh'
          : 'Token signature is invalid'
      });
    }
    req.user = user;
    next();
  });
}
```

## Login with JWT + Refresh Token Rotation

```javascript
// routes/auth.js
const bcrypt = require('bcrypt');
const crypto = require('crypto');

app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await db.users.findByEmail(email);

  if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
    return res.status(401).json({ detail: 'Invalid credentials' });
  }

  const accessToken = jwt.sign(
    { sub: user.id, roles: user.roles, scopes: user.scopes },
    process.env.JWT_SECRET,
    { expiresIn: '15m', algorithm: 'HS256' }
  );

  const refreshToken = crypto.randomBytes(64).toString('hex');
  const refreshHash = crypto.createHash('sha256').update(refreshToken).digest('hex');

  await db.refreshTokens.create({
    userId: user.id,
    tokenHash: refreshHash,
    expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
  });

  res.json({ accessToken, refreshToken, expiresIn: 900 });
});

app.post('/auth/refresh', async (req, res) => {
  const { refreshToken } = req.body;
  const tokenHash = crypto.createHash('sha256').update(refreshToken).digest('hex');
  const stored = await db.refreshTokens.findByHash(tokenHash);

  if (!stored || stored.expiresAt < new Date()) {
    return res.status(401).json({ detail: 'Invalid or expired refresh token' });
  }

  await db.refreshTokens.delete(stored.id);

  const newRefreshToken = crypto.randomBytes(64).toString('hex');
  const newHash = crypto.createHash('sha256').update(newRefreshToken).digest('hex');
  await db.refreshTokens.create({
    userId: stored.userId,
    tokenHash: newHash,
    expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
  });

  const accessToken = jwt.sign(
    { sub: stored.userId },
    process.env.JWT_SECRET,
    { expiresIn: '15m' }
  );

  res.json({ accessToken, refreshToken: newRefreshToken, expiresIn: 900 });
});
```

## RBAC Middleware

```javascript
// middleware/rbac.js
function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.some(role => req.user.roles.includes(role))) {
      return res.status(403).json({
        title: 'Insufficient Permissions',
        status: 403,
        detail: `Requires one of: ${roles.join(', ')}`
      });
    }
    next();
  };
}

function requireScope(...scopes) {
  return (req, res, next) => {
    const missing = scopes.filter(s => !req.user?.scopes?.includes(s));
    if (missing.length > 0) {
      return res.status(403).json({ detail: `Missing scopes: ${missing.join(', ')}` });
    }
    next();
  };
}

app.get('/admin/users', authenticateToken, requireRole('admin'), listUsers);
app.delete('/users/:id', authenticateToken, requireScope('write:users'), deleteUser);
```

## API Key Authentication

```javascript
// middleware/apiKey.js
async function authenticateApiKey(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey) return res.status(401).json({ detail: 'X-API-Key header required' });

  const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex');
  const keyRecord = await db.apiKeys.findByHash(keyHash);

  if (!keyRecord || keyRecord.revokedAt) {
    return res.status(401).json({ detail: 'Invalid API key' });
  }

  req.apiKeyScopes = keyRecord.scopes;
  req.apiKeyOwner = keyRecord.userId;
  next();
}

app.post('/api-keys', authenticateToken, requireRole('admin'), async (req, res) => {
  const rawKey = `sk_live_${crypto.randomBytes(32).toString('hex')}`;
  const keyHash = crypto.createHash('sha256').update(rawKey).digest('hex');

  await db.apiKeys.create({
    userId: req.user.sub, keyHash,
    scopes: req.body.scopes, name: req.body.name
  });
  res.status(201).json({ key: rawKey, scopes: req.body.scopes });
});
```

## OAuth 2.0 Client Credentials (Python)

```python
import httpx, time

class OAuth2ClientCredentials:
    def __init__(self, token_url, client_id, client_secret):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._expires_at = 0

    def get_token(self):
        if self._token and time.time() < self._expires_at - 30:
            return self._token
        resp = httpx.post(self.token_url, data={
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        resp.raise_for_status()
        data = resp.json()
        self._token = data['access_token']
        self._expires_at = time.time() + data['expires_in']
        return self._token

auth = OAuth2ClientCredentials('https://auth.example.com/oauth/token', 'client_id', 'secret')
headers = {'Authorization': f'Bearer {auth.get_token()}'}
```

## curl: Testing Authentication

```bash
# Login
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'
# {"accessToken":"eyJhbG...","refreshToken":"a1b2c3...","expiresIn":900}

# Protected route
curl http://localhost:3000/api/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Refresh token
curl -X POST http://localhost:3000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken":"a1b2c3..."}'

# API key access
curl http://localhost:3000/api/analytics -H "X-API-Key: sk_live_abc123..."

# 403 insufficient scope
curl -X DELETE http://localhost:3000/api/users/42 \
  -H "Authorization: Bearer eyJhbG..."
# {"detail":"Missing scopes: write:users"}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
