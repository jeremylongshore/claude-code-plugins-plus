# Intercom Enterprise RBAC — Worked Examples

End-to-end scenarios that combine the building blocks from
`references/implementation.md`.

## Example 1: Gate a delete endpoint behind role permissions

An agent should never be able to hard-delete a contact. Wire the
`requirePermission` middleware so only owners reach the handler.

```typescript
// Only "owner" carries "contacts:delete" in ROLE_PERMISSIONS
app.delete(
  "/api/contacts/:id",
  requirePermission("contacts:delete"),
  deleteContactHandler
);

// An agent hitting this endpoint gets:
// 403 { error: "Forbidden", message: "Missing permission: contacts:delete",
//       required: "contacts:delete", currentRole: "agent" }
```

## Example 2: Install a public app for a new customer workspace

```typescript
// 1. Send the customer to the consent screen
const state = crypto.randomUUID();
const authUrl = getAuthUrl(state);           // persist `state` to verify on callback
// redirect(authUrl)

// 2. On the callback, verify state, then exchange the code
const { token } = await exchangeCode(req.query.code as string);

// 3. Persist one token per workspace for multi-tenant access
const auth: WorkspaceAuth = {
  workspaceId: req.query.workspace_id as string,
  token,
  installedAt: new Date(),
  installedBy: req.user.email,
};
await db.workspaceAuth.upsert(auth);
```

## Example 3: Route + audit a sensitive assignment in one flow

```typescript
// Route a billing question to the billing team, then record the action
await routeConversation("conv-9001", "admin-42", "billing");

await auditAdminAction({
  timestamp: new Date().toISOString(),
  adminId: "admin-42",
  adminEmail: "lead@acme.com",
  action: "conversations:assign",
  resource: "conversation",
  resourceId: "conv-9001",
  success: true,
});
// The "settings"/"delete" branch would also emit a [AUDIT] console warning.
```
