# PubMed Research Master

> Complete PubMed research toolkit with 10 MCP tools, offline caching, and citation management

**Why This is Better than Anthropic's Claude for Life Sciences:**
- ✅ **Open Source** - MIT licensed, fork and customize freely
- ✅ **Self-Hosted** - Your data stays on your machine
- ✅ **Free** - No paid tiers, works with PubMed's free API
- ✅ **Offline Support** - SQLite caching for research without internet
- ✅ **Complete Workflows** - 10 integrated tools vs single-purpose connectors
- ✅ **Easy Installation** - 30 seconds via Claude Code marketplace

---

## Features

### 10 MCP Tools

1. **search_pubmed** - Advanced search with filters (date, article type, MeSH terms)
2. **get_article_details** - Full article metadata by PMID
3. **get_full_text** - PMC full-text when available
4. **search_by_mesh** - Medical Subject Heading taxonomy search
5. **get_related_articles** - Citation network expansion
6. **export_citations** - BibTeX, RIS, EndNote formats
7. **track_search_history** - SQLite persistence for offline access
8. **analyze_trends** - Publication trends over time
9. **compare_studies** - Side-by-side study comparison
10. **generate_summary** - AI-powered article synthesis

### Agent Skills

- **Literature Review Automator** (9.6KB) - Activates on "review the literature on..."
- Comprehensive multi-phase workflows
- Automatic query construction and optimization
- Citation network analysis
- Research gap identification

### Rate Limiting

- Without API key: 3 requests/second (compliant with NCBI)
- With API key: 10 requests/second
- Automatic rate limit enforcement
- Request queuing and retry logic

### Offline Caching

- Local SQLite database (pubmed_cache.db)
- Automatic caching of all searches
- Article details persisted locally
- Search history tracking
- Works without internet after first fetch

---

## Installation

### Prerequisites

- Claude Code installed
- Node.js 20+ and pnpm
- (Optional) NCBI API key for higher rate limits

### Quick Install

```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install plugin
/plugin install pubmed-research-master@claude-code-plugins-plus
```

### Manual Build

```bash
cd plugins/life-sciences/pubmed-research-master/
pnpm install
pnpm build
```

---

## Configuration

### API Key (Optional but Recommended)

Get a free API key from NCBI: https://www.ncbi.nlm.nih.gov/account/settings/

Set environment variables:
```bash
export PUBMED_API_KEY="your-api-key-here"
export EMAIL="your@email.com"
```

Or add to `.env` file in the plugin directory:
```env
PUBMED_API_KEY=your_key_here
EMAIL=your@email.com
```

### MCP Server Configuration

The plugin runs as an MCP server. Configuration in `.claude-plugin/mcp/server.json`:

```json
{
  "mcpServers": {
    "pubmed-research": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {
        "PUBMED_API_KEY": "",
        "EMAIL": ""
      }
    }
  }
}
```

---

## Usage Examples

### Example 1: Basic Literature Search

```
User: "Search PubMed for CRISPR gene editing in cancer therapy from 2023-2025"

MCP Tool Called: search_pubmed
Parameters: {
  query: "CRISPR gene editing cancer therapy",
  max_results: 100,
  date_from: "2023/01/01",
  date_to: "2025/12/31"
}

Result: Found 1,247 articles. PMIDs: 38123456, 38123457, 38123458...
```

### Example 2: Agent Skill Activation

```
User: "Review the literature on immunotherapy for glioblastoma"

Agent Skill: Literature Review Automator (auto-activates)

Workflow:
1. Constructs optimized PubMed query
2. Searches with filters (last 5 years, Clinical Trials + Reviews)
3. Retrieves top 100 articles
4. Analyzes publication trends
5. Identifies key researchers
6. Maps citation networks
7. Synthesizes findings into structured review
```

### Example 3: Export Citations

```
User: "Export these PMIDs as BibTeX: 38123456, 38123457, 38123458"

MCP Tool Called: export_citations
Parameters: {
  pmids: "38123456,38123457,38123458",
  format: "BibTeX"
}

Result: (BibTeX formatted citations ready for LaTeX)
```

### Example 4: Trend Analysis

```
User: "Show me publication trends for mRNA vaccines from 2015-2025"

MCP Tool Called: analyze_trends
Parameters: {
  query: "mRNA vaccines",
  start_year: 2015,
  end_year: 2025
}

Result: 2015: 23, 2016: 31, 2017: 45, 2018: 67, 2019: 89, 2020: 456, 2021: 1234, 2022: 987, 2023: 876, 2024: 1098, 2025: 543
```

### Example 5: Compare Studies

```
User: "Compare these three studies side-by-side: 38123456, 38123457, 38123458"

MCP Tool Called: compare_studies
Parameters: { pmids: "38123456,38123457,38123458" }

Result: Detailed comparison with titles, authors, dates, key findings
```

---

## Real Researcher Workflows

### Systematic Literature Review (PRISMA-Compliant)

1. Define research question
2. Use `search_pubmed` with precise filters
3. Export PMIDs with `export_citations`
4. Use `get_article_details` for each article
5. Track everything with `track_search_history`
6. Analyze trends with `analyze_trends`
7. Generate final report

### Citation Network Discovery

1. Start with seed article PMID
2. Use `get_related_articles` to expand network
3. Identify highly-cited papers
4. Map research landscape
5. Find key opinion leaders

### Manuscript Preparation

1. Search relevant literature
2. Export citations in required format (BibTeX/RIS/EndNote)
3. Import into reference manager
4. Use in manuscript

---

## Offline Support

All searches and article details are automatically cached in `pubmed_cache.db`. This allows:

- Working without internet after first fetch
- Faster repeat searches
- Complete search history
- No redundant API calls

Database location: `./pubmed_cache.db` (created automatically)

---

## API Rate Limits & Best Practices

### NCBI E-utilities Guidelines

- **Without API key:** 3 requests/second max
- **With API key:** 10 requests/second max
- **Weekend/off-hours:** Best time for large jobs (9PM-5AM ET weekdays)

### This Plugin's Implementation

- ✅ Automatic rate limit enforcement
- ✅ Request queuing
- ✅ Exponential backoff on errors
- ✅ Caching to minimize API calls
- ✅ User-friendly error messages

---

## Troubleshooting

### Issue: "Rate limit exceeded"
**Solution:** Get an API key or wait 1 second between requests

### Issue: "No results found"
**Solution:** Broaden your search query, check spelling, try synonyms

### Issue: "Database locked"
**Solution:** Close other instances of the plugin, check file permissions

### Issue: "Cannot connect to PubMed"
**Solution:** Check internet connection, verify NCBI services are up

### Issue: "Full text not available"
**Solution:** Not all articles have PMC full-text, check PubMed Central availability

---

## Development

### Build from Source

```bash
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins/plugins/life-sciences/pubmed-research-master/
pnpm install
pnpm build
```

### Run Tests

```bash
pnpm test
```

### Type Checking

```bash
pnpm typecheck
```

### Development Mode

```bash
pnpm dev
```

---

## Technical Architecture

### MCP Server

- **Protocol:** JSON-RPC 2.0 over stdio
- **SDK:** @modelcontextprotocol/sdk v0.7.0
- **Language:** TypeScript 5.5
- **Runtime:** Node.js 20+

### Database

- **Engine:** SQLite 3
- **Schema:** search_history, article_details tables
- **Size:** Grows with usage, typically < 100MB

### Dependencies

```json
{
  "@modelcontextprotocol/sdk": "^0.7.0",
  "zod": "^3.23.0",
  "node-fetch": "^3.3.0",
  "sqlite": "^5.1.1",
  "sqlite3": "^5.1.7"
}
```

---

## Comparison to Anthropic's Claude for Life Sciences

| Feature | Anthropic | PubMed Research Master |
|---------|-----------|----------------------|
| **Pricing** | Paid tier | Free |
| **Access** | Limited | Public marketplace |
| **License** | Proprietary | MIT (open source) |
| **Hosting** | Cloud only | Self-hosted |
| **PubMed Tools** | 1 (basic search) | 10 (complete toolkit) |
| **Offline** | No | Yes (SQLite caching) |
| **Agent Skills** | ~500 bytes | 9,600+ bytes |
| **Citation Export** | Not available | BibTeX/RIS/EndNote |
| **Trend Analysis** | Not available | Built-in |
| **Customizable** | No | Yes (fork & modify) |

---

## Contributing

We welcome contributions! This is an open-source project.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See `CONTRIBUTING.md` for details.

---

## License

MIT License - see `LICENSE` file

Copyright (c) 2025 Intent Solutions IO

---

## Support

- **GitHub Issues:** https://github.com/jeremylongshore/claude-code-plugins/issues
- **Discussions:** https://github.com/jeremylongshore/claude-code-plugins/discussions
- **Email:** contact@intentsolutions.io

---

## Acknowledgments

- **NCBI E-utilities:** https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **Model Context Protocol:** https://modelcontextprotocol.io/
- **Anthropic Claude:** For inspiring better tools

---

## Version History

- **1.0.0** (2025-10-20) - Initial release
  - 10 MCP tools
  - Literature Review Automator Agent Skill (9.6KB)
  - SQLite offline caching
  - Rate limiting compliance
  - Citation export (BibTeX/RIS/EndNote)

---

**Built with ❤️ for the research community**

*Making scientific literature accessible to everyone*
