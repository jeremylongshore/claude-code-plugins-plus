# Xquik TypeScript Types: REST API vs MCP Field Naming

The REST API and MCP server use different field names for the same data. Map these when switching between interfaces:

| Type | REST API Field | MCP Field |
|------|---------------|-----------|
| **Monitor** | `username` | `xUsername` |
| **XquikEvent** | `type` | `eventType` |
| **XquikEvent** | `data` | `eventData` |
| **XquikEvent** | `monitorId` | `monitoredAccountId` |
| **UserProfile** | `followers` | `followersCount` |
| **UserProfile** | `following` | `followingCount` |
| **FollowerCheck** | `isFollowing` / `isFollowedBy` | `following` / `followedBy` |

**MCP `get-user-info` returns a subset** of the full `UserProfile` type. Fields not returned by MCP: `verified`, `location`, `createdAt`, `statusesCount`. Use the REST API `GET /x/users/{id}` for the complete profile.
