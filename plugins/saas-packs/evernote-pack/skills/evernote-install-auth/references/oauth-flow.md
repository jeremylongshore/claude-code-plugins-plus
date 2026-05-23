# Evernote OAuth Flow Implementation

## Step-by-Step OAuth 1.0a Flow

### Get Request Token and Redirect

```javascript
const callbackUrl = 'http://localhost:3000/oauth/callback';

client.getRequestToken(callbackUrl, (error, oauthToken, oauthTokenSecret) => {
  if (error) {
    console.error('Failed to get request token:', error);
    return;
  }

  // Store tokens in session (required for callback)
  req.session.oauthToken = oauthToken;
  req.session.oauthTokenSecret = oauthTokenSecret;

  // Redirect user to Evernote authorization page
  const authorizeUrl = client.getAuthorizeUrl(oauthToken);
  res.redirect(authorizeUrl);
});
```

### Handle OAuth Callback

```javascript
app.get('/oauth/callback', (req, res) => {
  const oauthVerifier = req.query.oauth_verifier;

  client.getAccessToken(
    req.session.oauthToken,
    req.session.oauthTokenSecret,
    oauthVerifier,
    (error, oauthAccessToken, oauthAccessTokenSecret, results) => {
      if (error) {
        console.error('Failed to get access token:', error);
        return res.status(500).send('Authentication failed');
      }

      // Store access token securely (valid for 1 year by default)
      req.session.accessToken = oauthAccessToken;

      // Token expiration included in results.edam_expires
      console.log('Token expires:', new Date(parseInt(results.edam_expires)));

      res.redirect('/dashboard');
    }
  );
});
```

### Verify Authenticated Connection

```javascript
const authenticatedClient = new Evernote.Client({
  token: req.session.accessToken,
  sandbox: true
});

const userStore = authenticatedClient.getUserStore();
const noteStore = authenticatedClient.getNoteStore();

userStore.getUser().then(user => {
  console.log('Authenticated as:', user.username);
  console.log('User ID:', user.id);
}).catch(err => {
  console.error('Authentication verification failed:', err);
});
```

## Development Tokens (Sandbox Only)

For development, use a Developer Token instead of the full OAuth flow:

1. Create a sandbox account at https://sandbox.evernote.com
2. Get a Developer Token from https://sandbox.evernote.com/api/DeveloperToken.action
3. Use directly without OAuth:

```javascript
const client = new Evernote.Client({
  token: process.env.EVERNOTE_DEV_TOKEN,
  sandbox: true
});

const noteStore = client.getNoteStore();
```

**Note:** Developer tokens are currently unavailable for production. Use the full OAuth flow for production applications.

## Python OAuth Client

```python
from evernote.api.client import EvernoteClient

client = EvernoteClient(
    consumer_key='your-consumer-key',
    consumer_secret='your-consumer-secret',
    sandbox=True
)
```

## Token Expiration Reference

- Default token validity: **1 year**
- Users can reduce to: 1 day, 1 week, or 1 month
- Expiration timestamp in `edam_expires` parameter
- Implement token refresh before expiration
