# All Plugins Now 100% Free

**Date:** December 26, 2025
**Version:** 4.4.0

## Summary

All 264 plugins in the Claude Code Plugins marketplace are now completely free to use. We've replaced every paid API dependency with free, self-hosted, or open-source alternatives.

## What Changed

Previously, some plugins required paid API subscriptions:
- Financial data APIs (Alpha Vantage, paid tiers)
- Blockchain RPC endpoints (Alchemy, Infura paid tiers)
- Cloud AI services (OpenAI, paid tiers)
- Automation platforms (Zapier, Make paid tiers)

**Now:**
- Financial plugins use Yahoo Finance, SEC EDGAR (free)
- Crypto plugins use public RPCs (Ankr, dRPC, Chainstack free tiers)
- AI plugins support Ollama (local, free)
- Automation plugins support n8n (self-hosted, free)

## No Breaking Changes

Existing workflows continue to work. The paid API options remain available for users who prefer them, but free alternatives are now the documented default.

## Affected Plugins

- `market-price-tracker` - Now uses free exchange APIs
- `market-movers-scanner` - Now uses free crypto APIs
- `defi-yield-optimizer` - Now uses public blockchain data
- `crypto-portfolio-tracker` - Now uses free APIs
- `ai-sdk-agents` - Now supports Ollama
- `make-scenario-builder` - Now supports n8n
- `geepers-agents` - Now supports Ollama

## Install the CLI

```bash
pnpm add -g @intentsolutionsio/ccpi
ccpi list
```

## Questions?

Open a discussion at https://github.com/jeremylongshore/claude-code-plugins/discussions

---

*This announcement addresses Discussion #148 and the community request for transparency about API costs.*
