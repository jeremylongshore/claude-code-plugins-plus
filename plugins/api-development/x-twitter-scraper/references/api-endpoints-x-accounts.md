# Xquik REST API Endpoints: X Accounts (Connected)

Manage connected X accounts for confirmation-gated write actions.

**Connecting or re-authenticating an X account is done by the user in the Xquik dashboard**, not via this skill. The skill never handles X login material. The agent should direct the user to the dashboard account page when a new account needs to be connected or an existing session needs to be refreshed.

The OpenAPI surface includes dashboard-owned account connection routes:

```
POST /x/accounts
POST /x/account-connection-challenges/{id}/submit
POST /x/accounts/{id}/reauth
POST /x/accounts/bulk-retry
```

Do not call these from this skill. They are listed here only so the skill docs match the public API surface and keep the dashboard-only boundary explicit.

### List X Accounts

```
GET /x/accounts
```

Returns all connected X accounts. Response: `{ accounts: [{ id, username, displayName, isActive, createdAt }] }`.

### Get X Account

```
GET /x/accounts/{id}
```

Returns `{ id, username, displayName, isActive, createdAt }`.

### Disconnect X Account

```
delete request to `/x/accounts/{id}`
```

Permanently removes the account from Xquik. Returns `{ success: true }`. Before calling, confirm with the user.

---
