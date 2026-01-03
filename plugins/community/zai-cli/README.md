# ZAI CLI

**Z.AI vision, search, reader, and GitHub exploration via CLI and MCP.**

## Features

- **Vision**: Image/video analysis, OCR, UI-to-code, error diagnosis (GLM-4.6V)
- **Search**: Real-time web search with domain/recency filtering
- **Reader**: Web page to markdown extraction
- **Repo**: GitHub code search and reading via ZRead
- **Tools**: MCP tool discovery and raw calls
- **Code**: TypeScript tool chaining

## Installation

```bash
# Set your API key
export Z_AI_API_KEY="your-api-key"

# Get a key at: https://z.ai/manage-apikey/apikey-list
```

## Quick Start

```bash
# Analyze an image
npx zai-cli vision analyze ./screenshot.png "What errors do you see?"

# Search the web
npx zai-cli search "React 19 new features" --count 5

# Read a web page
npx zai-cli read https://docs.example.com/api

# Explore a GitHub repo
npx zai-cli repo search facebook/react "server components"

# Check setup
npx zai-cli doctor
```

## Usage

Simply describe what you need - ZAI activates when you:
- Need image or video analysis
- Want to search the web in real-time
- Need to read a webpage as markdown
- Want to explore GitHub repositories

## Author

**Numman Ali** - [@numman-ali](https://github.com/numman-ali)

## Resources

- [n-skills Marketplace](https://github.com/numman-ali/n-skills)

## License

Apache-2.0
