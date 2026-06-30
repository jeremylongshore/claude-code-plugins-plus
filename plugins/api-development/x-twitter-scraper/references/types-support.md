# Xquik TypeScript Types: Support

```typescript

interface SupportTicket {
  id: string;
  subject: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

interface SupportMessage {
  id: string;
  body: string;
  sender: string;
  createdAt: string;
}

interface CreateTicketRequest {
  subject: string;
  body: string;
}

```
