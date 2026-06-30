# Xquik TypeScript Types: MCP: get-user-info

```typescript

interface McpUserInfo {
  username: string;           // X username (without @)
  name: string;               // Display name
  description: string;        // User bio text
  followersCount: number;     // Number of followers
  followingCount: number;     // Number of accounts followed
  profilePicture: string;     // Profile picture URL
  // Not returned: verified, location, createdAt, statusesCount
  // Use REST GET /x/users/{id} for the full profile
}

```
