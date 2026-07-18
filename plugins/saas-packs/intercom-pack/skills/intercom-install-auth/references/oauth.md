# OAuth Setup, API Versioning & Scopes

Deep reference for public-app OAuth, API version pinning, and the OAuth scope
matrix. The main `SKILL.md` covers the common access-token path; use this file
when building a **public app** that accesses other workspaces.

## OAuth Setup (Public Apps)

For apps that access other workspaces, configure OAuth:

```typescript
// Step 1: Redirect user to Intercom authorization
const authUrl = `https://app.intercom.com/oauth?client_id=${CLIENT_ID}&state=${STATE}`;

// Step 2: Exchange code for token at your callback endpoint
async function handleOAuthCallback(code: string): Promise<string> {
  const response = await fetch("https://api.intercom.io/auth/eagle/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: process.env.INTERCOM_CLIENT_ID,
      client_secret: process.env.INTERCOM_CLIENT_SECRET,
      code,
    }),
  });

  const data = await response.json();
  return data.token; // Use this token for API calls
}

// Step 3: Initialize client with OAuth token
const client = new IntercomClient({ token: oauthToken });
```

## API Versioning

Specify the API version header to pin behavior:

```typescript
const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// All requests use Bearer token in Authorization header:
// Authorization: Bearer YOUR_TOKEN
// Intercom-Version: 2.11
```

The current stable API version is **2.11**. The SDK handles this automatically.

## OAuth Scopes Reference

| Scope | Access Granted |
|-------|---------------|
| Read admins | List workspace admins |
| Read/write contacts | Create, update, search contacts |
| Read/write conversations | Manage conversations and replies |
| Read/write messages | Send outbound messages |
| Read/write articles | Manage Help Center content |
| Read/write tags | Tag contacts, companies, conversations |
| Read/write events | Submit and read data events |
| Read/write companies | Manage company records |
