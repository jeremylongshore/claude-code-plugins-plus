# Intercom Reference Architecture — Usage Examples

These examples wire together the services defined in
[implementation.md](implementation.md). They invoke only methods that already
exist in that walkthrough — no new API surface — so you can copy them once the
client and service layers are in place.

## Sync a CRM user into Intercom

Uses `ContactsService.syncFromCRM` (search-before-create, so it is idempotent).

```typescript
import { ContactsService } from "./services/contacts.service";

const contacts = new ContactsService();

const contact = await contacts.syncFromCRM({
  id: "crm_8842",
  email: "ada@example.com",
  name: "Ada Lovelace",
  plan: "enterprise",
  company: "Analytical Engines Ltd",
});

console.log(`Synced contact ${contact.id}`);
```

## Reply to and close a conversation

Uses `ConversationsService.replyAsAdmin` then `closeWithMessage`.

```typescript
import { ConversationsService } from "./services/conversations.service";

const conversations = new ConversationsService();

await conversations.replyAsAdmin(conversationId, adminId, "Thanks for reaching out — fixed now.");
await conversations.closeWithMessage(conversationId, adminId, "Resolved. Reopen anytime.");
```

## Page through every matching contact

`searchAll` is an async generator, so large result sets stream without holding
every page in memory.

```typescript
const contacts = new ContactsService();

for await (const contact of contacts.searchAll({
  field: "custom_attributes.plan",
  operator: "=",
  value: "enterprise",
})) {
  console.log(contact.email);
}
```

## Publish a Help Center article

Uses `ArticlesService.createArticle`. It defaults to `draft`; pass
`state: "published"` to go live.

```typescript
import { ArticlesService } from "./services/articles.service";

const articles = new ArticlesService();

await articles.createArticle({
  title: "Resetting your password",
  body: "<p>Go to Settings → Security → Reset password.</p>",
  authorId: adminId,
  state: "published",
});
```
