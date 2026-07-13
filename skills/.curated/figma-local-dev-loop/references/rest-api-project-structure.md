# Step 1: REST API Project Structure

Deep-dive reference for the `figma-local-dev-loop` skill — extracted from the 'Step 1: REST API Project Structure' step of the workflow.

```
figma-integration/
├── src/
│   ├── figma-client.ts       # Shared fetch wrapper
│   ├── extract-tokens.ts     # Design token extraction
│   └── export-assets.ts      # Asset export pipeline
├── tests/
│   ├── figma-client.test.ts
│   └── fixtures/             # Saved API responses for offline testing
│       └── sample-file.json
├── .env.local                # FIGMA_PAT, FIGMA_FILE_KEY (git-ignored)
├── .env.example              # Template for team
├── tsconfig.json
└── package.json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
