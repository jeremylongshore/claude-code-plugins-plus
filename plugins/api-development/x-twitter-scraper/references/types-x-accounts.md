# Xquik TypeScript Types: X Accounts (Connected)

```typescript

interface ConnectedXAccount {
  id: string;                 // Unique account ID
  username: string;           // X username
  displayName?: string;       // Display name on X
  isActive: boolean;          // Whether the connection is active
  createdAt: string;          // ISO 8601 timestamp
}

// Connecting an X account is done by the user in the Xquik dashboard,
// not through this skill. The skill never handles X login material.

```
