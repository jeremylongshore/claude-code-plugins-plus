# Life Sciences MCP Connectors Research & Implementation Plan

**Date:** 2025-10-20
**Purpose:** Comprehensive research for building Claude Code life sciences plugins that compete with Anthropic's Claude for Life Sciences
**Status:** Research Complete - Ready for Implementation

---

## Executive Summary

Anthropic announced **Claude for Life Sciences** on October 20, 2025 - their first industry-vertical product using Model Context Protocol (MCP) to integrate with scientific tools. This research document provides everything needed to build **superior life sciences plugins** for the Claude Code marketplace that researchers will actually want to use.

**Why We'll Be Better:**
- ✅ Open source (MIT/Apache-2.0) - Anyone can use, modify, contribute
- ✅ Self-hosted option - Researchers control their own data
- ✅ Free tier friendly (Vertex AI Gemini) - Accessible to all researchers
- ✅ Claude Code marketplace - Easy installation, no special access needed
- ✅ Multi-tool integration - Solve complete workflows, not just pieces
- ✅ Comprehensive Agent Skills (8,000+ bytes) - Actually useful automation
- ✅ Better documentation - Real examples researchers can follow
- ✅ Community-driven - Researchers can request features and contribute

---

## Anthropic's Claude for Life Sciences - Learning from Their Approach

### Announced Features (Oct 20, 2025)

**Official Integrations:**
1. **Benchling** - Lab data management platform (via MCP)
2. **PubMed** - Medical literature database (NCBI E-utilities)
3. **10x Genomics** - Single-cell sequencing platform
4. **Synapse.org** - Collaborative research data platform (Sage Bionetworks)

**Capabilities:**
- Literature reviews in minutes (previously took days)
- Hypothesis development with source citations
- Data analysis with traceability
- Regulatory submission drafting
- One-click access to underlying scientific data
- Automatic permission and audit log carryover

**Partnerships:**
- Implementation: Caylent, KPMG, Deloitte
- Cloud providers: AWS, Google Cloud

**Access:** Claude for Life Sciences ecosystem (limited/controlled access)

---

## Model Context Protocol (MCP) - Technical Foundation

### Architecture

**Client-Server Model:**
```
┌─────────────────┐
│   Claude Code   │ ← MCP Client (Host)
│   (Desktop App) │
└────────┬────────┘
         │ JSON-RPC 2.0 over stdio
         ├──────────────┬──────────────┬─────────────┐
         ▼              ▼              ▼             ▼
    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
    │ PubMed │    │  10x   │    │Synapse │    │Benchling│
    │  MCP   │    │Genomics│    │  MCP   │    │  MCP    │
    │ Server │    │  MCP   │    │ Server │    │ Server  │
    └────────┘    └────────┘    └────────┘    └────────┘
```

**JSON-RPC 2.0 Messages:**
- **Requests**: Include string/integer ID (not null), must be unique per session
- **Responses**: Match request ID
- **Notifications**: No response expected

**MCP Specification:** modelcontextprotocol.io/specification/2025-03-26

### Core Primitives

**Servers Provide (3 primitives):**
1. **Tools** - Executable functions (search, analyze, export)
2. **Resources** - Data access (articles, datasets, protocols)
3. **Prompts** - Structured templates for LLM interactions

**Clients Provide (2 primitives):**
1. **Roots** - Workspace context
2. **Sampling** - LLM inference requests

### Tools Implementation

```typescript
// Tools discovery
Request: tools/list
Response: {
  tools: [{
    name: "search_pubmed",  // 1-128 chars, ASCII only
    description: "Search PubMed database",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        max_results: { type: "number" }
      },
      required: ["query"]
    }
  }]
}

// Tool execution
Request: tools/call
Params: { name: "search_pubmed", arguments: {...} }
Response: { content: [...], isError: false }
```

### Resources Implementation

```typescript
// Resource listing
Request: resources/list
Response: {
  resources: [{
    uri: "pubmed://articles/PMID123456",
    name: "Article title",
    mimeType: "application/json"
  }]
}

// Resource reading
Request: resources/read
Params: { uri: "pubmed://articles/PMID123456" }
Response: { contents: [...] }
```

### SDKs Available

- **TypeScript**: `@modelcontextprotocol/sdk` (official, actively maintained)
- **Python**: `mcp` package (official)
- **Java**: Community SDK
- **C#**: Community SDK

**We use:** TypeScript SDK v0.7.0+ (matches our existing MCP plugins)

---

## Scientific Platform APIs - Integration Details

### 1. PubMed / NCBI E-utilities

**Official Documentation:** https://www.ncbi.nlm.nih.gov/books/NBK25501/

**Rate Limits:**
- Without API key: 3 requests/second
- With API key: 10 requests/second
- Best practice: Limit large jobs to weekends or 9 PM-5 AM ET weekdays

**API Key Management:**
- Create in My NCBI Account Settings → API Key Management
- Include in all requests: `&api_key=YOUR_KEY`

**Key E-utilities:**

```bash
# 1. ESearch - Search and retrieve UIDs
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?
  db=pubmed&
  term=cancer+therapy&
  retmax=100&
  retmode=json&
  api_key=YOUR_KEY

# 2. EFetch - Retrieve full records
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?
  db=pubmed&
  id=12345678,87654321&
  retmode=xml&
  api_key=YOUR_KEY

# 3. ESummary - Get document summaries
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?
  db=pubmed&
  id=12345678&
  retmode=json&
  api_key=YOUR_KEY

# 4. ELink - Find related articles
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?
  dbfrom=pubmed&
  db=pubmed&
  id=12345678&
  api_key=YOUR_KEY

# 5. EPost - Upload large ID lists to server
# Returns WebEnv and QueryKey for batch operations
```

**Best Practices:**
- Use Entrez History (EPost) for large batch operations
- Download 500 records per EFetch request (max efficiency)
- Include `&email=your@email.com` for NCBI to contact if issues
- Cache results locally (SQLite) to reduce API calls
- Handle XML and JSON response formats

**Data Available:**
- Abstract text
- MeSH terms (Medical Subject Headings)
- Authors and affiliations
- Publication dates
- Journal information
- PMC full-text links (when available)
- Citation counts
- Related articles

### 2. 10x Genomics Cloud Analysis

**Platform:** https://cloud.10xgenomics.com/

**Key Workflows:**
1. **Normalization (SCTransform) and Batch Correction (Harmony)**
   - Input: Individual Loupe (.cloupe) files per sample
   - Output: Normalized gene expression matrices

2. **Cell Ranger Aggregation (aggr) Pipeline**
   - Combines multiple samples
   - Normalizes read depths
   - Generates integrated datasets

3. **Graph-based and K-means Clustering**
   - Automatic cell type identification
   - Dimensionality reduction (t-SNE, UMAP)
   - Marker gene detection

**Integration Capabilities:**
- Natural language workflow execution (via MCP)
- Cloud-scale analysis (90 minutes typical runtime)
- Free tier available
- Integration with Seurat, Azimuth, SingleR, CellTypist
- Export formats: Seurat objects, HDF5, CSV, Loupe files

**Analysis Pipeline:**
```
Raw FASTQ → Cell Ranger → Feature-Barcode Matrix →
Normalization → Clustering → Cell Type ID → Visualization
```

**API Access:**
- Cloud Analysis API (requires authentication)
- Cell Ranger command-line tools
- Loupe Browser integration
- Export to community tools

### 3. Synapse.org (Sage Bionetworks)

**Platform:** https://www.synapse.org/

**Scale:**
- 3+ petabytes of biomedical data
- 20,000+ projects
- 100,000+ user accounts

**Python Client:**
```python
import synapseclient
syn = synapseclient.login('username', 'password')

# Query datasets
results = syn.tableQuery("SELECT * FROM syn12345678 WHERE age > 50")

# Download files
entity = syn.get('syn87654321')

# Upload data
file = synapseclient.File('data.csv', parent='syn12345678')
syn.store(file)
```

**SynapseChat (AI Integration):**
- AI-powered dataset search
- Automatic dataset summarization
- Cross-dataset connection discovery
- Natural language queries

**Research Areas:**
- Neurodegeneration (Alzheimer's, Parkinson's)
- Cancer genomics
- Rare diseases
- Mental health research

**Data Types:**
- Genomic sequences
- Clinical trial data
- Imaging data
- Electronic health records
- Omics data (proteomics, metabolomics)

### 4. Benchling (Lab Data Management)

**Platform:** https://www.benchling.com/

**MCP Integration (Anthropic Partnership):**
- One-click traceability to source data
- Automatic permission inheritance
- Audit log continuity
- Seamless data queries from Claude

**Core Capabilities:**
- Electronic lab notebook (ELN)
- Lab inventory management
- Workflow automation
- Protocol management
- Sample tracking
- Assay data capture

**Data Types:**
- Experiment results
- Assay data (qPCR, ELISA, Western blots)
- DNA/protein sequences
- Sample metadata
- Protocol versions
- Quality control data

**API Considerations:**
- Proprietary platform (requires Benchling account)
- Enterprise-focused (not free tier friendly)
- **Our alternative:** Generic lab data integration (CSV, Excel, JSON)

---

## Our Plugin Pack Architecture - Superior to Anthropic

### Plugin Pack #1: PubMed Research Assistant

**File Structure:**
```
life-sciences-pubmed-research/
├── .claude-plugin/
│   ├── plugin.json           # Metadata
│   └── mcp/
│       └── server.json       # MCP server config
├── src/
│   └── index.ts              # MCP server (TypeScript)
├── skills/
│   └── skill-adapter/
│       ├── literature-review.md       # 8,000+ bytes
│       ├── systematic-review.md       # 8,000+ bytes
│       ├── citation-network.md        # 8,000+ bytes
│       └── research-gap-finder.md     # 8,000+ bytes
├── commands/
│   ├── pubmed-search.md
│   ├── literature-review.md
│   ├── citation-export.md
│   └── mesh-explorer.md
├── agents/
│   ├── systematic-review-agent.md     # PRISMA-compliant
│   └── citation-analyzer-agent.md
├── package.json
├── tsconfig.json
├── README.md
└── LICENSE (MIT)
```

**MCP Tools to Implement (10 tools):**
1. `search_pubmed` - Search with filters (date, article type, MeSH)
2. `get_article_details` - Full article metadata by PMID
3. `get_full_text` - PMC full-text when available
4. `search_by_mesh` - Medical Subject Heading taxonomy search
5. `get_related_articles` - Citation network expansion
6. `export_citations` - BibTeX, RIS, EndNote formats
7. `track_search_history` - SQLite persistence
8. `analyze_trends` - Publication trends over time
9. `compare_studies` - Side-by-side comparison
10. `generate_summary` - AI-powered literature synthesis

**Agent Skills (4 skills, 8,000+ bytes each):**
- **Literature Review Automator**: Triggered by "review the literature on...", "what does research say about..."
- **Systematic Review Planner**: PRISMA guidelines, inclusion/exclusion criteria, quality assessment
- **Citation Network Analyzer**: Impact factor, citation counts, researcher networks
- **Research Gap Identifier**: Finds underexplored areas, suggests future research

**Slash Commands (5):**
- `/pubmed-search` - Interactive search builder
- `/literature-review` - Generate structured review outline
- `/citation-export` - Multi-format export wizard
- `/mesh-explorer` - Browse MeSH hierarchy
- `/research-trends` - Visualize publication trends

**Key Features:**
- SQLite caching for offline research
- Rate limit compliance (10 req/s with API key)
- Automatic retries with exponential backoff
- Citation deduplication
- MeSH term suggestions
- Full abstract retrieval
- PMC full-text when available

### Plugin Pack #2: 10x Genomics Single Cell Analysis

**MCP Tools (8 tools):**
1. `analyze_single_cell` - Run Cell Ranger pipeline
2. `normalize_expression` - SCTransform normalization
3. `batch_correction` - Harmony integration
4. `cluster_cells` - Graph-based clustering
5. `identify_cell_types` - Automated annotation
6. `run_differential_expression` - Find marker genes
7. `visualize_umap` - Generate UMAP plots
8. `export_seurat` - Export to Seurat/Scanpy formats

**Agent Skills (3 skills):**
- **Single Cell Workflow Orchestrator**: Multi-step pipeline automation
- **Cell Type Identifier**: Automated annotation with confidence scores
- **Quality Control Analyst**: Filter low-quality cells, doublets

**Integration Points:**
- 10x Cloud Analysis API
- Local Cell Ranger execution
- Seurat/Scanpy compatibility
- Loupe Browser export

### Plugin Pack #3: Synapse Data Platform Connector

**MCP Tools (7 tools):**
1. `search_datasets` - Natural language dataset discovery
2. `query_synapse` - SQL-like queries on Synapse tables
3. `download_dataset` - Bulk data download with progress
4. `get_dataset_metadata` - Comprehensive metadata retrieval
5. `find_related_datasets` - Cross-study discovery
6. `chat_with_data` - SynapseChat integration
7. `create_project` - New Synapse project creation

**Agent Skills (3 skills):**
- **Dataset Discovery Assistant**: Find relevant datasets across 3PB
- **Cross-Study Analyzer**: Connect findings across projects
- **Data Downloader**: Batch download with authentication

### Plugin Pack #4: Lab Data Integration (Benchling Alternative)

**MCP Tools (9 tools):**
1. `import_lab_data` - CSV, Excel, JSON parsing
2. `query_experiments` - Filter by date, researcher, assay type
3. `get_assay_results` - Extract specific assay data
4. `validate_data_schema` - Quality checks
5. `export_dataset` - Multiple format export
6. `calculate_statistics` - Basic stats (mean, SD, p-values)
7. `generate_report` - PDF/HTML reports
8. `track_samples` - Sample inventory management
9. `version_protocols` - Protocol change tracking

**Agent Skills (4 skills):**
- **Experiment Data Analyzer**: Statistical analysis automation
- **Quality Control Automator**: Detect outliers, anomalies
- **Protocol Optimizer**: Suggest protocol improvements
- **Sample Tracker**: Inventory management assistant

**Why We Don't Use Benchling API:**
- Proprietary/expensive platform
- Not accessible to most researchers
- We provide open-source alternative supporting common formats

### Plugin Pack #5: Regulatory Compliance Assistant

**MCP Tools (8 tools):**
1. `validate_submission` - FDA/EMA compliance checks
2. `check_glp_compliance` - Good Laboratory Practice validation
3. `generate_audit_trail` - 21 CFR Part 11 compliant logs
4. `create_report_template` - IND, NDA, BLA templates
5. `track_regulatory_changes` - Monitor guideline updates
6. `verify_data_integrity` - ALCOA+ principles check
7. `generate_statistical_report` - ICH E9 compliant stats
8. `export_regulatory_package` - Complete submission bundle

**Agent Skills (4 skills):**
- **FDA Submission Preparer**: IND/NDA/BLA guidance
- **GLP Compliance Checker**: Laboratory practice validation
- **Audit Trail Generator**: 21 CFR Part 11 automation
- **Regulatory Document Reviewer**: Completeness checks

**Supported Standards:**
- FDA 21 CFR Part 11 (Electronic Records)
- ICH E6 (Good Clinical Practice)
- ICH E8 (Clinical Trial Design)
- ICH E9 (Statistical Principles)
- GLP/GCP/GMP compliance
- ALCOA+ data integrity

### Plugin Pack #6: Scientific Writing Assistant

**MCP Tools (10 tools):**
1. `check_manuscript` - Journal guideline compliance
2. `suggest_journals` - Match manuscript to journals
3. `format_references` - APA, Vancouver, AMA, Chicago
4. `check_readability` - Flesch-Kincaid scores
5. `optimize_abstract` - Structured abstract formatting
6. `generate_graphical_abstract` - Key points extraction
7. `detect_plagiarism` - Similarity checking
8. `analyze_impact` - Predict citation potential
9. `create_cover_letter` - Journal-specific templates
10. `track_revisions` - Manuscript version control

**Agent Skills (4 skills):**
- **Manuscript Structurer**: IMRaD format optimization
- **Journal Recommender**: Impact factor, scope matching
- **Citation Formatter**: Multi-style bibliography generation
- **Abstract Optimizer**: Clarity and completeness

---

## Implementation Strategy Using Vertex AI Gemini

### Why Vertex AI Gemini 2.5 Flash (Free Tier)

**Cost Advantages:**
- Free tier: 1,500 requests/day
- Flash model: Fast responses (< 2s)
- Large context: 1M tokens
- API requests: 15 RPM free tier

**vs. Anthropic's Approach:**
- They use proprietary Claude models (paid)
- We use Google's free tier (accessible)
- Same quality outputs for plugin generation

### Generation Workflow

```bash
# Step 1: Create comprehensive generation prompt
# (Already have in 000-docs/082-RL-PROP-life-sciences-plugins.md)

# Step 2: Use Vertex AI to generate each plugin pack
python3 scripts/skills-generate-vertex-safe.py \
  --plugin-type life-sciences \
  --pack-name pubmed-research \
  --output plugins/life-sciences/

# Step 3: Build and validate MCP servers
cd plugins/life-sciences/pubmed-research/
pnpm install
pnpm build
pnpm test

# Step 4: Test locally via Claude Code
/plugin marketplace add ~/000-projects/claude-code-plugins
/plugin install pubmed-research@claude-code-plugins-plus

# Step 5: Deploy to marketplace
# Update .claude-plugin/marketplace.extended.json
pnpm run sync-marketplace
```

### Quality Assurance Checklist

For each plugin pack:
- [ ] MCP server implements all tools (TypeScript)
- [ ] Agent Skills are 8,000+ bytes each
- [ ] All markdown files have valid YAML frontmatter
- [ ] Comprehensive README with examples
- [ ] MIT License included
- [ ] plugin.json complete with metadata
- [ ] package.json with correct dependencies
- [ ] Local testing successful
- [ ] Error handling implemented
- [ ] Rate limiting compliant
- [ ] Security best practices followed

---

## How We'll Be Better - Feature Comparison

| Feature | Anthropic's Approach | Our Approach (Better Because...) |
|---------|---------------------|----------------------------------|
| **Pricing** | Paid tier required | Free (Vertex AI free tier) - Democratizes access |
| **Access** | Limited ecosystem | Public marketplace - Anyone can install |
| **License** | Proprietary | MIT / Apache-2.0 - Community can improve |
| **Hosting** | Cloud-only | Self-hosted + Cloud - Researchers own their data |
| **Extensibility** | Closed | Fully forkable - Customize for your lab |
| **Tools per Pack** | Single purpose | Multi-tool integration - Complete workflows |
| **Agent Skills** | ~500 bytes | 8,000+ bytes - Actually automate complex tasks |
| **Offline Support** | No | SQLite caching - Work without internet |
| **Export Formats** | Limited | Comprehensive - Integrates with existing tools |
| **API Integration** | 4 platforms | 6+ plugin packs - More scientific platforms |
| **Community** | Closed beta | Open source - Researchers help each other |
| **Documentation** | Basic | Comprehensive - Real examples that work |
| **Installation** | Special access | `/plugin install` - 30 seconds |

---

## Security & Compliance Considerations

### HIPAA Compliance

**Required for Healthcare Data:**
- Encrypt all PHI at rest and in transit
- Implement audit logging
- User authentication/authorization
- Data retention policies
- Breach notification procedures

**Our Implementation:**
- Use HTTPS for all API calls
- SQLite encryption for local caching
- No PHI logging
- Configurable data retention
- Audit trail generation

### FDA 21 CFR Part 11

**Electronic Records Requirements:**
- Audit trails (who, what, when)
- Electronic signatures
- System validation
- Data integrity (ALCOA+)

**Our Implementation:**
- Comprehensive audit logging
- Timestamped operations
- User tracking
- Data validation checks

### API Key Security

**Best Practices:**
- Never hardcode API keys
- Use environment variables
- Encrypt stored credentials
- Rotate keys regularly
- Monitor for leaks

**Our Implementation:**
```typescript
// Environment variable loading
const PUBMED_API_KEY = process.env.PUBMED_API_KEY;
const SYNAPSE_AUTH_TOKEN = process.env.SYNAPSE_AUTH_TOKEN;

// Secure credential storage (encrypted)
import { encrypt, decrypt } from './crypto';
const storedKey = encrypt(apiKey, masterPassword);
```

---

## Next Steps

### Immediate Actions (This Session)

1. ✅ **Research Complete** - This document
2. ⏳ **Generate Plugin Pack #1** - PubMed Research Assistant
   - Use Vertex AI Gemini 2.5 Flash
   - Generate all MCP tools, Agent Skills, commands, agents
   - 15+ files, production-ready

3. ⏳ **Validate & Test** - Ensure plugin works locally

4. ⏳ **Deploy to Marketplace** - Add to marketplace.extended.json

5. ⏳ **Generate Remaining 5 Packs** - Systematic generation

### Success Metrics

**Per Plugin Pack:**
- Installation time: < 2 minutes
- First working example: < 5 minutes
- Tool response time: < 2s (95th percentile)
- Documentation coverage: 100%
- Error rate: < 1% in common workflows

**Overall Goals:**
- 6 complete plugin packs
- 60+ MCP tools total
- 24+ Agent Skills (8,000+ bytes each)
- 100% marketplace ready
- Superior to Anthropic's offering

---

## Resources & References

### Official Documentation
- Model Context Protocol: https://modelcontextprotocol.io/
- PubMed E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- 10x Genomics Cloud: https://www.10xgenomics.com/
- Synapse Python Client: https://python-docs.synapse.org/
- Vertex AI Gemini: https://cloud.google.com/vertex-ai/docs

### Our Existing Resources
- MCP Server Examples: `plugins/mcp/project-health-auditor/`
- Agent Skills Examples: `plugins/*/skills/skill-adapter/SKILL.md`
- Planning Document: `000-docs/082-RL-PROP-life-sciences-plugins.md`
- Scripts Directory: `scripts/README.md`

### Community Resources
- MCP GitHub: https://github.com/modelcontextprotocol
- MCP Servers Repository: https://github.com/modelcontextprotocol/servers
- Claude Code Docs: https://docs.claude.com/en/docs/claude-code/

---

**Research Completed:** 2025-10-20T22:30:00Z
**Ready for Implementation:** YES
**Next Document:** 099-PM-TASK-life-sciences-plugin-generation.md (implementation tracking)

---

**Timestamp:** 2025-10-20T22:30:00Z
