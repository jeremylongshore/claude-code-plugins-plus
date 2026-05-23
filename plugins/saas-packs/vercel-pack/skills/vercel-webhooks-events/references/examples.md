## Examples

### Testing Webhooks Locally

```bash
# Use ngrok to expose local server
ngrok http 3000

# Send test webhook
curl -X POST https://your-ngrok-url/webhooks/vercel \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": {}}'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
