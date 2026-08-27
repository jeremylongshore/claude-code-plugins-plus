# Intercom Conversations — Full Implementation Walkthrough

Complete step-by-step code for the full conversation lifecycle: create, reply,
assign, close/snooze, tag, retrieve, and search. Each step is standalone — copy
the block you need. All examples assume the `client` from Step 1.

## Step 1: Create a Conversation

Conversations are created when a contact sends a message.

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// Create conversation from a contact
const conversation = await client.conversations.create({
  from: {
    type: "user",
    id: "6657add46abd0167d9419c3a", // Contact ID
  },
  body: "Hi, I'm having trouble with my billing. Can you help?",
});

console.log(`Conversation ID: ${conversation.conversationId}`);
```

## Step 2: Reply to a Conversation

```typescript
// Admin reply (visible to customer)
await client.conversations.reply({
  conversationId: conversation.conversationId,
  body: "Hi there! I'd be happy to help with billing. What's the issue?",
  type: "admin",
  adminId: "12345", // Your admin ID
});

// Admin note (internal, not visible to customer)
await client.conversations.reply({
  conversationId: conversation.conversationId,
  body: "Customer is on Enterprise plan, checking billing system...",
  type: "note",
  adminId: "12345",
});

// Contact reply
await client.conversations.reply({
  conversationId: conversation.conversationId,
  body: "I was charged twice for this month.",
  type: "user",
  intercomUserId: "6657add46abd0167d9419c3a",
});
```

## Step 3: Assign a Conversation

```typescript
// Assign to a specific admin
await client.conversations.assign({
  conversationId: conversation.conversationId,
  type: "admin",
  adminId: "12345",
  assigneeId: "67890", // Target admin ID
  body: "Assigning to billing specialist",
});

// Assign to a team
await client.conversations.assign({
  conversationId: conversation.conversationId,
  type: "team",
  adminId: "12345",
  assigneeId: "team-billing-123",
  body: "Routing to billing team",
});

// Auto-assign using assignment rules
// POST /conversations/{id}/run_assignment_rules
await fetch(`https://api.intercom.io/conversations/${conversation.conversationId}/run_assignment_rules`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.INTERCOM_ACCESS_TOKEN}`,
    "Content-Type": "application/json",
  },
});
```

## Step 4: Close and Snooze Conversations

```typescript
// Close a conversation (with optional closing message)
await client.conversations.close({
  conversationId: conversation.conversationId,
  adminId: "12345",
  body: "Issue resolved! Let us know if you need anything else.",
});

// Snooze until a specific time
await client.conversations.snooze({
  conversationId: conversation.conversationId,
  adminId: "12345",
  snoozedUntil: Math.floor(Date.now() / 1000) + 86400, // 24 hours from now
});

// Reopen a closed conversation
await client.conversations.open({
  conversationId: conversation.conversationId,
  adminId: "12345",
});
```

## Step 5: Tag Conversations

```typescript
// Tag a conversation
await client.conversations.attachTag({
  conversationId: conversation.conversationId,
  tagId: "tag-billing-issue",
  adminId: "12345",
});

// Remove a tag
await client.conversations.detachTag({
  conversationId: conversation.conversationId,
  tagId: "tag-billing-issue",
  adminId: "12345",
});
```

## Step 6: Retrieve Conversation with Parts

```typescript
const full = await client.conversations.find({
  conversationId: conversation.conversationId,
});

console.log(`State: ${full.state}`);  // "open", "closed", "snoozed"
console.log(`Assignee: ${full.adminAssigneeId}`);
console.log(`Parts: ${full.conversationParts.totalCount}`);

// Iterate conversation parts (messages, notes, assignments)
for (const part of full.conversationParts.conversationParts) {
  console.log(`  [${part.partType}] ${part.author.type}: ${part.body?.substring(0, 50)}`);
}

// Conversation parts include:
// - comment (admin/user messages)
// - note (internal notes)
// - assignment (team/admin assignments)
// - close/open (state changes)
```

## Step 7: List and Filter Conversations

```typescript
// List all conversations
const conversations = await client.conversations.list();

// Search conversations
const searched = await client.conversations.search({
  query: {
    operator: "AND",
    value: [
      { field: "state", operator: "=", value: "open" },
      { field: "admin_assignee_id", operator: "=", value: "12345" },
    ],
  },
  pagination: { per_page: 20 },
  sort: { field: "updated_at", order: "descending" },
});
```

## Conversation States

| State | Description | Transitions |
|-------|-------------|-------------|
| `open` | Active, awaiting action | close, snooze |
| `closed` | Resolved | open |
| `snoozed` | Deferred until timestamp | open (auto or manual) |

## Conversation Part Types

| Part Type | Description | Who Creates |
|-----------|-------------|------------|
| `comment` | Visible message | Admin or contact |
| `note` | Internal-only note | Admin |
| `assignment` | Reassignment record | System or admin |
| `close` | Conversation closed | Admin |
| `open` | Conversation reopened | Admin or contact |
