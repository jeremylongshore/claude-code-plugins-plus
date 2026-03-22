---
name: replit-install-auth
description: |
  Set up a Replit project with .replit + replit.nix configuration, Secrets, and Replit Auth.
  Use when creating a new Replit App, configuring Nix packages, managing secrets,
  or adding user authentication with Replit Auth.
  Trigger with phrases like "setup replit", "replit auth", "replit nix config",
  "replit secrets", "configure replit", "new replit project".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(nix:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, authentication, nix, secrets, configuration]

---
# Replit Install & Auth

## Overview
Set up a Replit App from scratch: configure `.replit` and `replit.nix`, manage Secrets (AES-256 encrypted environment variables), and integrate Replit Auth for zero-setup user authentication with Google, GitHub, Apple, X, and Email login.

## Prerequisites
- Replit account (Free, Core, or Teams plan)
- Replit App created from template, GitHub import, or blank
- For Auth: deployed app on `.replit.app` or custom domain

## Instructions

### Step 1: Configure `.replit` File
```toml
# .replit — controls run behavior, deployment, and environment
entrypoint = "index.ts"
run = "npm start"

# Nix modules provide language runtimes
modules = ["nodejs-20:v8-20230920-bd784b9"]

[nix]
channel = "stable-24_05"

[env]
NODE_ENV = "development"
PORT = "3000"

[deployment]
run = ["sh", "-c", "npm start"]
deploymentTarget = "autoscale"
build = ["sh", "-c", "npm run build"]
ignorePorts = [3001]

[unitTest]
language = "nodejs"

[packager]
language = "nodejs"
  [packager.features]
  packageSearch = true
  guessImports = true

[gitHubImport]
requiredFiles = [".replit", "replit.nix"]
```

### Step 2: Configure `replit.nix`
```nix
# replit.nix — system-level dependencies via Nix
{ pkgs }: {
  deps = [
    pkgs.nodejs-20_x
    pkgs.nodePackages.typescript-language-server
    pkgs.nodePackages.pnpm
    pkgs.postgresql
    pkgs.python311
    pkgs.python311Packages.pip
  ];
}
```

After editing `replit.nix`, reload the shell for changes to take effect.

### Step 3: Configure Secrets
Secrets are encrypted with AES-256 at rest and TLS in transit. Two scopes:
- **App-level**: specific to one Replit App
- **Account-level**: shared across all your Apps

```markdown
Via UI:
1. Click the lock icon (Secrets) in the left sidebar
2. Add key-value pairs:
   - DATABASE_URL = postgresql://...
   - API_KEY = sk-...
   - JWT_SECRET = your-jwt-secret

Via code — validate at startup:
```

```typescript
// src/config.ts
function requireSecrets(keys: string[]): Record<string, string> {
  const missing = keys.filter(k => !process.env[k]);
  if (missing.length > 0) {
    console.error(`Missing secrets: ${missing.join(', ')}`);
    console.error('Add them in the Secrets tab (lock icon in sidebar)');
    process.exit(1);
  }
  return Object.fromEntries(keys.map(k => [k, process.env[k]!]));
}

const config = requireSecrets(['DATABASE_URL', 'JWT_SECRET']);
```

Secrets sync automatically between Workspace and Deployments. Replit's Secret Scanner warns if you paste API keys directly into code files.

### Step 4: Add Replit Auth
Replit Auth provides zero-setup authentication. Users log in with Google, GitHub, Apple, X, or Email. Replit handles sessions via cookies, password resets, and user management.

**Express.js integration:**
```typescript
// src/auth.ts
import express from 'express';

const app = express();

// Replit Auth injects these headers on authenticated requests
interface ReplitUser {
  id: string;        // X-Replit-User-Id
  name: string;      // X-Replit-User-Name
  bio: string;       // X-Replit-User-Bio
  url: string;       // X-Replit-User-Url
  image: string;     // X-Replit-User-Profile-Image
  roles: string;     // X-Replit-User-Roles
  teams: string;     // X-Replit-User-Teams
}

function getReplitUser(req: express.Request): ReplitUser | null {
  const id = req.headers['x-replit-user-id'] as string;
  if (!id) return null;
  return {
    id,
    name: req.headers['x-replit-user-name'] as string,
    bio: req.headers['x-replit-user-bio'] as string,
    url: req.headers['x-replit-user-url'] as string,
    image: req.headers['x-replit-user-profile-image'] as string,
    roles: req.headers['x-replit-user-roles'] as string,
    teams: req.headers['x-replit-user-teams'] as string,
  };
}

// Auth middleware
function requireAuth(req: express.Request, res: express.Response, next: express.NextFunction) {
  const user = getReplitUser(req);
  if (!user) return res.status(401).json({ error: 'Not authenticated' });
  (req as any).user = user;
  next();
}

// Client-side: GET /__replauthuser returns current user info
// Login: direct user to Replit's login page for your app
```

**Flask integration:**
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_replit_user():
    user_id = request.headers.get('X-Replit-User-Id')
    if not user_id:
        return None
    return {
        'id': user_id,
        'name': request.headers.get('X-Replit-User-Name', ''),
        'roles': request.headers.get('X-Replit-User-Roles', ''),
        'teams': request.headers.get('X-Replit-User-Teams', ''),
        'image': request.headers.get('X-Replit-User-Profile-Image', ''),
    }

@app.route('/api/profile')
def profile():
    user = get_replit_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify(user)
```

### Step 5: Verify Setup
```typescript
// test-setup.ts — run to verify everything works
const checks = {
  nix: process.version,  // should show Node version
  secrets: !!process.env.DATABASE_URL,
  replSlug: process.env.REPL_SLUG,
  replOwner: process.env.REPL_OWNER,
  replId: process.env.REPL_ID,
};
console.log('Replit Setup Verification:', checks);
```

Built-in environment variables available in every Repl:
| Variable | Description |
|----------|-------------|
| `REPL_SLUG` | Your Repl's name/slug |
| `REPL_OWNER` | Owner username |
| `REPL_ID` | Unique Repl identifier |
| `REPL_IDENTITY` | PASETO token signed by Replit infra |
| `REPLIT_DB_URL` | Key-value database endpoint |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Module not found` | Nix package missing | Add to `replit.nix` deps, reload shell |
| `EACCES permission` | Wrong file permissions | Check `.replit` run command syntax |
| `Secret undefined` | Not set in Secrets tab | Add via sidebar lock icon |
| Auth headers empty | Not deployed / local dev | Auth only works on deployed `.replit.app` URLs |
| `channel not found` | Invalid Nix channel | Use `stable-24_05` or check Nix channels list |

## Resources
- [Replit App Configuration](https://docs.replit.com/replit-app/configuration)
- [Using Nix with Replit](https://docs.replit.com/programming-ide/nix-on-replit)
- [Replit Secrets](https://docs.replit.com/replit-workspace/workspace-features/secrets)
- [Replit Auth](https://docs.replit.com/replit-workspace/replit-auth)

## Next Steps
Proceed to `replit-hello-world` for a working starter app, or `replit-deploy-integration` to deploy.
