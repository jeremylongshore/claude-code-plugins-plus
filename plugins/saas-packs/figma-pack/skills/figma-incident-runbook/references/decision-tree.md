# Step 2: Decision Tree

Deep-dive reference for the `figma-incident-runbook` skill — extracted from the 'Step 2: Decision Tree' step of the workflow.

```
API returning errors?
├── 403 Forbidden
│   ├── Token expired (>90 days) → Rotate PAT immediately
│   ├── Wrong scopes → Regenerate with correct scopes
│   └── File not shared → Check file permissions
│
├── 429 Rate Limited
│   ├── Retry-After < 60s → Wait and retry automatically
│   ├── Retry-After > 300s → Reduce request volume
│   └── X-Figma-Rate-Limit-Type: low → Consider upgrading plan
│
├── 404 Not Found
│   ├── File deleted → Check with file owner
│   ├── Wrong file key → Verify FIGMA_FILE_KEY
│   └── API path wrong → Check endpoint documentation
│
├── 500/503 Server Error
│   ├── status.figma.com shows incident → Wait for resolution
│   ├── Intermittent → Retry with backoff
│   └── Persistent → Contact Figma support
│
└── Network Error (ECONNREFUSED, timeout)
    ├── DNS resolution failing → Check DNS config
    ├── Firewall blocking → Verify outbound HTTPS to api.figma.com
    └── TLS error → Check Node.js version (18+ required)
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
