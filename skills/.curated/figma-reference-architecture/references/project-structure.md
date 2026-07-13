# Step 1: Project Structure

Deep-dive reference for the `figma-reference-architecture` skill — extracted from the 'Step 1: Project Structure' step of the workflow.

```
figma-integration/
├── src/
│   ├── figma/
│   │   ├── client.ts           # Typed REST API wrapper
│   │   ├── types.ts            # Figma API response types
│   │   ├── errors.ts           # FigmaApiError, FigmaRateLimitError
│   │   ├── cache.ts            # LRU cache for API responses
│   │   └── walker.ts           # Node tree traversal utilities
│   ├── services/
│   │   ├── token-extractor.ts  # Design token extraction
│   │   ├── asset-exporter.ts   # Image/icon export pipeline
│   │   ├── comment-syncer.ts   # Comment sync to Slack/Jira
│   │   └── variable-syncer.ts  # Variables API sync (Enterprise)
│   ├── webhooks/
│   │   ├── handler.ts          # Webhook event router
│   │   ├── verify.ts           # Passcode verification
│   │   └── processors/
│   │       ├── file-update.ts  # FILE_UPDATE handler
│   │       ├── comment.ts      # FILE_COMMENT handler
│   │       └── library.ts      # LIBRARY_PUBLISH handler
│   ├── api/
│   │   ├── health.ts           # Health check endpoint
│   │   ├── tokens.ts           # Token API endpoint
│   │   └── assets.ts           # Asset download endpoint
│   └── index.ts
├── scripts/
│   ├── extract-tokens.mjs      # CLI: extract tokens from Figma
│   ├── export-icons.mjs        # CLI: export icons from Figma
│   └── setup-webhooks.mjs      # CLI: create/manage webhooks
├── output/
│   ├── tokens.css              # Generated CSS custom properties
│   ├── tokens.json             # Generated JSON tokens
│   └── icons/                  # Exported SVG/PNG icons
├── tests/
│   ├── fixtures/               # Saved Figma API responses
│   └── *.test.ts
├── .env.example
└── package.json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
