---
name: flyio-hello-world
description: |
  Deploy your first app to Fly.io with flyctl launch and the Machines API.
  Use when starting a new Fly.io project, deploying a container globally,
  or testing edge compute deployment.
  Trigger: "fly.io hello world", "fly launch", "deploy to fly.io", "first fly app".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(curl:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Hello World

## Overview

Deploy a minimal app to Fly.io using `fly launch`. Fly.io runs Docker containers on Firecracker microVMs across 30+ regions worldwide. Two paths: `flyctl` CLI (simple) or Machines API (programmatic).

## Instructions

### Step 1: Launch with flyctl

```bash
# Create a new directory with a Dockerfile
mkdir fly-hello && cd fly-hello

cat > Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY server.js .
EXPOSE 3000
CMD ["node", "server.js"]
EOF

cat > server.js << 'EOF'
const http = require('http');
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    message: 'Hello from Fly.io!',
    region: process.env.FLY_REGION,
    app: process.env.FLY_APP_NAME,
  }));
});
server.listen(3000, () => console.log('Listening on :3000'));
EOF

# Launch — creates app, generates fly.toml, deploys
fly launch --name hello-fly --region iad --now
```

### Step 2: Verify Deployment

```bash
# Check status
fly status

# Open in browser
fly open

# View logs
fly logs

# Test with cURL
curl https://hello-fly.fly.dev/
# {"message":"Hello from Fly.io!","region":"iad","app":"hello-fly"}
```

### Step 3: Deploy via Machines API

```typescript
const FLY_API = 'https://api.machines.dev';
const headers = {
  'Authorization': `Bearer ${process.env.FLY_API_TOKEN}`,
  'Content-Type': 'application/json',
};

// Create an app
const app = await fetch(`${FLY_API}/v1/apps`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    app_name: 'hello-api',
    org_slug: 'personal',
  }),
}).then(r => r.json());

// Create a machine in the app
const machine = await fetch(`${FLY_API}/v1/apps/hello-api/machines`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    region: 'iad',
    config: {
      image: 'nginx:alpine',
      services: [{
        ports: [{ port: 443, handlers: ['tls', 'http'] }],
        protocol: 'tcp',
        internal_port: 80,
      }],
      guest: { cpu_kind: 'shared', cpus: 1, memory_mb: 256 },
    },
  }),
}).then(r => r.json());

console.log(`Machine ${machine.id} created in ${machine.region}`);
```

## Output

```
Machine e784079f004d86 created in iad
App URL: https://hello-api.fly.dev
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `No machines in group` | App exists but no machines | Run `fly deploy` or create via API |
| `Could not find image` | Docker build failed | Check Dockerfile, run `docker build .` locally |
| `Region not available` | Invalid region code | Use `fly platform regions` to list valid codes |
| `Insufficient resources` | Org quota reached | Check `fly orgs show` or upgrade plan |

## Resources

- [Fly Launch](https://fly.io/docs/reference/fly-launch/)
- [Deploy an App](https://fly.io/docs/launch/deploy/)
- [Machines API](https://fly.io/docs/machines/api/machines-resource/)

## Next Steps

Proceed to `flyio-local-dev-loop` for development workflow setup.
