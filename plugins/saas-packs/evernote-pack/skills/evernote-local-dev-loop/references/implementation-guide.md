# Evernote Local Dev Loop - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Project Structure

```bash
mkdir evernote-project && cd evernote-project
npm init -y
npm install evernote dotenv nodemon express express-session

mkdir -p src/{routes,services,utils}
touch src/index.js src/evernote-client.js .env .env.example
```

```
evernote-project/
├── src/
│   ├── index.js              # Express server entry
│   ├── evernote-client.js    # Evernote client wrapper
│   ├── routes/
│   │   └── oauth.js          # OAuth routes
│   ├── services/
│   │   └── notes.js          # Note operations
│   └── utils/
│       └── enml.js           # ENML helpers
├── .env                      # Local environment
├── .env.example              # Template
└── package.json
```

### Step 2: Environment Configuration

```bash
EVERNOTE_CONSUMER_KEY=your-consumer-key
EVERNOTE_CONSUMER_SECRET=your-consumer-secret
EVERNOTE_SANDBOX=true
EVERNOTE_DEV_TOKEN=your-sandbox-dev-token
SESSION_SECRET=dev-session-secret-change-in-prod
PORT=3000
NODE_ENV=development
```

```bash
EVERNOTE_CONSUMER_KEY=
EVERNOTE_CONSUMER_SECRET=
EVERNOTE_SANDBOX=true
EVERNOTE_DEV_TOKEN=
SESSION_SECRET=
PORT=3000
NODE_ENV=development
```

### Step 3: Evernote Client Wrapper

```javascript
// src/evernote-client.js
const Evernote = require('evernote');

class EvernoteService {
  constructor(accessToken) {
    this.client = new Evernote.Client({
      token: accessToken,
      sandbox: process.env.EVERNOTE_SANDBOX === 'true'
    });
    this._noteStore = null;
    this._userStore = null;
  }

  // Lazy-load NoteStore
  get noteStore() {
    if (!this._noteStore) {
      this._noteStore = this.client.getNoteStore();
    }
    return this._noteStore;
  }

  // Lazy-load UserStore
  get userStore() {
    if (!this._userStore) {
      this._userStore = this.client.getUserStore();
    }
    return this._userStore;
  }

  // Create client for OAuth flow
  static createOAuthClient() {
    return new Evernote.Client({
      consumerKey: process.env.EVERNOTE_CONSUMER_KEY,
      consumerSecret: process.env.EVERNOTE_CONSUMER_SECRET,
      sandbox: process.env.EVERNOTE_SANDBOX === 'true'
    });
  }

  // Quick dev client using developer token
  static createDevClient() {
    if (!process.env.EVERNOTE_DEV_TOKEN) {
      throw new Error('EVERNOTE_DEV_TOKEN not set - get one from sandbox.evernote.com');
    }
    return new EvernoteService(process.env.EVERNOTE_DEV_TOKEN);
  }
}

module.exports = EvernoteService;
```

### Step 4: ENML Utility Helpers

```javascript
// src/utils/enml.js

const ENML_HEADER = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">`;

/**
 * Wrap content in valid ENML structure
 */
function wrapInENML(content) {
  return `${ENML_HEADER}
<en-note>
${content}
</en-note>`;
}

/**
 * Convert plain text to ENML
 */
function textToENML(text) {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>');

  return wrapInENML(`<div>${escaped}</div>`);
}

/**
 * Convert Markdown to basic ENML (simplified)
 */
function markdownToENML(markdown) {
  let html = markdown
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold and italic
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.+?)\*/g, '<i>$1</i>')
    // Links
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>')
    // Lists (simplified)
    .replace(/^- (.+)$/gm, '<div>• $1</div>')
    // Line breaks
    .replace(/\n\n/g, '</div><div>')
    .replace(/\n/g, '<br/>');

  return wrapInENML(`<div>${html}</div>`);
}

/**
 * Create todo checkbox
 */
function createTodo(text, checked = false) {
  return `<en-todo checked="${checked}"/> ${text}<br/>`;
}

/**
 * Validate ENML has required structure
 */
function validateENML(content) {
  const errors = [];

  if (!content.includes('<?xml version="1.0"')) {
    errors.push('Missing XML declaration');
  }
  if (!content.includes('<!DOCTYPE en-note')) {
    errors.push('Missing DOCTYPE declaration');
  }
  if (!content.includes('<en-note>') || !content.includes('</en-note>')) {
    errors.push('Missing <en-note> root element');
  }

  // Check for forbidden elements
  const forbidden = ['<script', '<form', '<input', '<iframe', '<button'];
  forbidden.forEach(tag => {
    if (content.toLowerCase().includes(tag)) {
      errors.push(`Forbidden element: ${tag}`);
    }
  });

  return {
    valid: errors.length === 0,
    errors
  };
}

module.exports = {
  ENML_HEADER,
  wrapInENML,
  textToENML,
  markdownToENML,
  createTodo,
  validateENML
};
```

### Step 5: Express Server with OAuth

```javascript
// src/index.js
require('dotenv').config();
const express = require('express');
const session = require('express-session');
const EvernoteService = require('./evernote-client');

const app = express();

app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { secure: process.env.NODE_ENV === 'production' }
}));

app.use(express.json());

// OAuth initiation
app.get('/auth/evernote', (req, res) => {
  const client = EvernoteService.createOAuthClient();
  const callbackUrl = `http://localhost:${process.env.PORT}/auth/evernote/callback`;

  client.getRequestToken(callbackUrl, (error, oauthToken, oauthTokenSecret) => {
    if (error) {
      console.error('OAuth error:', error);
      return res.status(500).json({ error: 'Failed to get request token' });
    }

    req.session.oauthToken = oauthToken;
    req.session.oauthTokenSecret = oauthTokenSecret;
    res.redirect(client.getAuthorizeUrl(oauthToken));
  });
});

// OAuth callback
app.get('/auth/evernote/callback', (req, res) => {
  const client = EvernoteService.createOAuthClient();

  client.getAccessToken(
    req.session.oauthToken,
    req.session.oauthTokenSecret,
    req.query.oauth_verifier,
    (error, accessToken, accessTokenSecret, results) => {
      if (error) {
        console.error('Access token error:', error);
        return res.status(500).json({ error: 'Failed to get access token' });
      }

      req.session.accessToken = accessToken;
      req.session.evernoteExpires = results.edam_expires;

      res.json({
        success: true,
        message: 'Authenticated successfully',
        expiresAt: new Date(parseInt(results.edam_expires))
      });
    }
  );
});

// Dev endpoint - uses dev token
app.get('/dev/test', async (req, res) => {
  try {
    const evernote = EvernoteService.createDevClient();
    const user = await evernote.userStore.getUser();
    const notebooks = await evernote.noteStore.listNotebooks();

    res.json({
      user: user.username,
      notebookCount: notebooks.length,
      notebooks: notebooks.map(n => ({ name: n.name, guid: n.guid }))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log('Sandbox mode:', process.env.EVERNOTE_SANDBOX === 'true');
  console.log('Dev endpoints:');
  console.log(`  GET /dev/test - Test with dev token`);
  console.log(`  GET /auth/evernote - Start OAuth flow`);
});
```

### Step 6: Package.json Scripts

```json
{
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "node --test",
    "test:note": "node -e \"require('./src/test-note.js')\"",
    "lint": "eslint src/"
  }
}
```

### Step 7: Quick Test Script

```javascript
// src/test-note.js
require('dotenv').config();
const EvernoteService = require('./evernote-client');
const { textToENML } = require('./utils/enml');

async function testCreateNote() {
  const evernote = EvernoteService.createDevClient();

  // Create a test note
  const note = new (require('evernote')).Types.Note();
  note.title = `Dev Test - ${new Date().toISOString()}`;
  note.content = textToENML('This is a test note from the dev loop');

  const created = await evernote.noteStore.createNote(note);
  console.log('Created note:', created.guid);

  // Clean up - delete test note
  await evernote.noteStore.deleteNote(created.guid);
  console.log('Deleted test note');

  console.log('Dev loop test passed!');
}

testCreateNote().catch(console.error);
```


## Development Workflow

```bash
npm run dev

curl http://localhost:3000/dev/test

npm run test:note
```


## Sandbox vs Production

| Aspect | Sandbox | Production |
|--------|---------|------------|
| URL | sandbox.evernote.com | www.evernote.com |
| Dev Token | Available | Not available |
| Rate Limits | Same | Same |
| Data | Separate account | Real user data |
| OAuth | Required for apps | Required |
