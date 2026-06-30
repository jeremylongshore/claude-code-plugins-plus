# Xquik REST API Endpoints: Support

### Create Ticket

```
POST /support/tickets
```

**Body:** `{ "subject": "...", "body": "..." }`

**Response (201):** `{ id, subject, status, createdAt }`

### List Tickets

```
GET /support/tickets
```

Returns all tickets for the authenticated user.

### Get Ticket

```
GET /support/tickets/{id}
```

Returns ticket with messages.

### Update Ticket

```
PATCH /support/tickets/{id}
```

Update ticket status.

### Reply to Ticket

```
POST /support/tickets/{id}/messages
```

**Body:** `{ "body": "..." }`

Add a message to an existing ticket.

---
