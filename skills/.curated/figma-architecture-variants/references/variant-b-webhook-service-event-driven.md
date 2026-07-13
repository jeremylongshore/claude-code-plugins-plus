# Variant B: Webhook Service (Event-Driven)

Deep-dive reference for the `figma-architecture-variants` skill — extracted from the 'Variant B: Webhook Service (Event-Driven)' step of the workflow.

**Use case:** Auto-sync on file save, Slack notifications, build triggers

```
  ┌─────────────┐
  │ Figma Cloud  │
  │ FILE_UPDATE  │──── Webhook V2 ────┐
  │ FILE_COMMENT │                    │
  └──────────────┘                    │
                                      ▼
                               ┌──────────────┐
                               │ Your Service  │
                               │ (Vercel/Fly)  │
                               ├──────────────┤
                               │ /webhooks     │ ← Verify passcode
                               │ /health       │
                               │ /api/tokens   │
                               └──────┬───────┘
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Token    │ │ Slack    │ │ CI       │
                    │ Rebuild  │ │ Notify   │ │ Trigger  │
                    └──────────┘ └──────────┘ └──────────┘
```

```typescript
// Minimal webhook service (Express)
const app = express();
app.post('/webhooks/figma', express.json(), verifyPasscode, (req, res) => {
  res.status(200).json({ received: true });
  processEvent(req.body); // async
});
app.get('/health', healthCheck);
app.listen(process.env.PORT || 3000);
```

**Pros:** Real-time, event-driven, no polling waste
**Cons:** Requires hosting, HTTPS endpoint, webhook management

---

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
