# Gemini Pro: Claude for Life Sciences Plugin Pack Generator

**Context:** Anthropic just announced "Claude for Life Sciences" (Oct 20, 2025) - their first industry-vertical using Model Context Protocol (MCP) to integrate with Benchling, PubMed, 10x Genomics, and Synapse.org.

**Your Mission:** Generate comprehensive Claude Code plugin packs tailored for life sciences researchers that complement and extend Claude for Life Sciences capabilities.

---

## 🎯 Requirements

### Plugin Pack Structure
Each plugin pack MUST include:
1. **MCP Server** (TypeScript/Node.js) - Executable tool integration
2. **Agent Skills** (SKILL.md) - Auto-activation based on context
3. **Slash Commands** - Manual workflow triggers
4. **Agents** - Specialized sub-agents for complex tasks
5. **README.md** - Comprehensive documentation with examples

### Quality Standards
- **Agent Skills:** 8,000-14,000 bytes (17x larger than Anthropic's 500-byte examples)
- **Multi-phase workflows:** Analysis → Execution → Validation
- **Code examples:** Include runnable code snippets
- **Error handling:** Comprehensive error scenarios
- **YAML frontmatter:** Valid for all markdown files

---

## 📋 Plugin Packs to Generate

### 1. **PubMed Research Assistant Pack**

**MCP Server Capabilities:**
```typescript
// Tools to implement:
- search_pubmed(query, max_results, filters)
- get_article_details(pmid)
- get_full_text(pmid)  // When available
- search_by_mesh_terms(mesh_terms[])
- get_related_articles(pmid, max_results)
- export_citations(pmids[], format)  // BibTeX, RIS, etc.
- track_search_history()
```

**Agent Skills (SKILL.md):**
- Literature Review Automator
- Systematic Review Planner
- Citation Network Analyzer
- Research Gap Identifier

**Slash Commands:**
- `/pubmed-search` - Interactive PubMed search
- `/literature-review` - Generate literature review outline
- `/citation-export` - Export citations in multiple formats
- `/mesh-explorer` - Explore MeSH term relationships

**Sub-Agents:**
- `systematic-review-agent` - PRISMA-compliant reviews
- `citation-analyzer-agent` - Citation network analysis
- `research-synthesis-agent` - Synthesize findings across papers

**Key Features:**
- Rate limiting compliance (NCBI E-utilities: 3 req/s without API key, 10 req/s with key)
- SQLite caching for offline access
- Full abstract retrieval with MeSH terms
- PMC full-text search when available

---

### 2. **Lab Data Integration Pack**

**MCP Server Capabilities:**
```typescript
// Benchling-style lab data management:
- query_experiments(filters, date_range)
- get_assay_results(experiment_id)
- search_protocols(keywords)
- get_sample_metadata(sample_id)
- export_dataset(query, format)  // CSV, JSON, Excel
- validate_data_schema(data, schema)
```

**Agent Skills:**
- Experiment Data Analyzer
- Quality Control Automator
- Protocol Optimizer
- Sample Tracking Assistant

**Slash Commands:**
- `/query-lab-data` - Interactive data queries
- `/qc-check` - Quality control analysis
- `/protocol-search` - Find relevant protocols
- `/export-results` - Export experimental data

**Integration Points:**
- CSV/Excel file parsing
- JSON schema validation
- Statistical analysis (basic stats)
- Data visualization recommendations

---

### 3. **Regulatory Compliance Pack**

**MCP Server Capabilities:**
```typescript
// FDA/EMA regulatory tools:
- validate_submission(document, regulation_type)
- check_compliance(data, standard)  // GLP, GCP, GMP
- generate_report_template(report_type)
- track_regulatory_changes(jurisdiction)
- audit_trail_generator(actions[])
```

**Agent Skills:**
- FDA Submission Preparer
- GLP Compliance Checker
- Audit Trail Generator
- Regulatory Document Reviewer

**Slash Commands:**
- `/validate-submission` - Check regulatory compliance
- `/generate-template` - Create compliant templates
- `/audit-trail` - Generate audit documentation
- `/compliance-check` - Verify GxP compliance

**Key Standards Supported:**
- FDA 21 CFR Part 11 (Electronic Records)
- ICH Guidelines (E6, E8, E9)
- GLP/GCP/GMP standards
- ALCOA+ principles

---

### 4. **Bioinformatics Analysis Pack**

**MCP Server Capabilities:**
```typescript
// Genomics and proteomics tools:
- align_sequences(sequences[], algorithm)
- blast_search(sequence, database)
- annotate_genome(sequence, organism)
- analyze_expression_data(data, method)
- pathway_analysis(gene_list[], database)
- protein_structure_predict(sequence)
```

**Agent Skills:**
- Sequence Alignment Specialist
- Gene Expression Analyzer
- Pathway Enrichment Expert
- Protein Structure Predictor

**Slash Commands:**
- `/align-sequences` - Sequence alignment
- `/blast-search` - BLAST database search
- `/pathway-analysis` - Gene pathway enrichment
- `/protein-predict` - Protein structure prediction

**Integration with:**
- NCBI BLAST
- UniProt
- KEGG pathways
- PDB (Protein Data Bank)

---

### 5. **Clinical Trials Management Pack**

**MCP Server Capabilities:**
```typescript
// ClinicalTrials.gov integration:
- search_trials(condition, phase, status)
- get_trial_details(nct_id)
- analyze_enrollment_trends(conditions[])
- compare_protocols(nct_ids[])
- export_trial_data(filters, format)
- track_trial_updates(nct_ids[])
```

**Agent Skills:**
- Trial Design Consultant
- Enrollment Predictor
- Protocol Comparator
- Site Selection Advisor

**Slash Commands:**
- `/find-trials` - Search clinical trials
- `/analyze-protocol` - Protocol analysis
- `/enrollment-forecast` - Predict enrollment rates
- `/compare-trials` - Compare trial designs

---

### 6. **Scientific Writing Assistant Pack**

**MCP Server Capabilities:**
```typescript
// Writing and publishing tools:
- check_manuscript(text, journal_guidelines)
- suggest_journals(manuscript, field)
- format_references(citations[], style)
- check_plagiarism(text)
- generate_abstract(full_text, max_words)
- create_graphical_abstract(key_points[])
```

**Agent Skills:**
- Manuscript Structurer
- Journal Recommender
- Citation Formatter
- Abstract Optimizer

**Slash Commands:**
- `/format-manuscript` - Format for target journal
- `/suggest-journals` - Find suitable journals
- `/optimize-abstract` - Improve abstract clarity
- `/format-citations` - Format references (APA, Vancouver, etc.)

---

## 🏗️ Implementation Template

### MCP Server Structure (TypeScript)
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

class LifeSciencesMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "plugin-name-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "tool_name",
          description: "What this tool does",
          inputSchema: {
            type: "object",
            properties: {
              param1: { type: "string", description: "Parameter description" },
            },
            required: ["param1"],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) =>
      this.handleToolCall(request)
    );
  }

  private async handleToolCall(request: any) {
    // Tool implementation
  }
}
```

### Agent Skills Format (SKILL.md)
```markdown
---
name: Skill Name Here
description: |
  Automatic activation when user mentions: [trigger phrases].
  This skill handles [specific capability] with multi-phase workflow.
---

## What This Skill Does

Comprehensive explanation of the skill's purpose and capabilities.

## When It Activates

**Trigger Phrases:**
- "I need to [action]"
- "Help me [task]"
- "How do I [question]"

**Context Detection:**
- Working with [specific file types]
- Discussing [specific topics]
- Requesting [specific outputs]

## Multi-Phase Workflow

### Phase 1: Analysis
1. Understand the request
2. Gather required context
3. Validate inputs

### Phase 2: Execution
1. Perform primary task
2. Handle edge cases
3. Generate outputs

### Phase 3: Validation
1. Quality checks
2. Error handling
3. User confirmation

## Code Examples

\`\`\`python
# Example implementation
def example_function():
    # Implementation details
    pass
\`\`\`

## Error Handling

Common errors and solutions:
- **Error 1:** [Description] → [Solution]
- **Error 2:** [Description] → [Solution]

## Best Practices

1. **Principle 1:** Explanation
2. **Principle 2:** Explanation
3. **Principle 3:** Explanation
```

---

## 🎨 Output Requirements

### For Each Plugin Pack Generate:

1. **Complete plugin.json** with all metadata
2. **MCP server implementation** (TypeScript, fully functional)
3. **4-6 Agent Skills** (SKILL.md files, 8,000+ bytes each)
4. **5-8 Slash Commands** (markdown with YAML frontmatter)
5. **2-3 Sub-Agents** for complex workflows
6. **Comprehensive README.md** with:
   - Installation instructions
   - Usage examples
   - API requirements (if any)
   - Configuration guide
   - Troubleshooting section

### File Structure Per Pack:
```
life-sciences-[pack-name]/
├── .claude-plugin/
│   ├── plugin.json
│   └── mcp/
│       └── server.json
├── src/
│   └── index.ts          # MCP server implementation
├── skills/
│   └── skill-adapter/
│       ├── SKILL-1.md
│       ├── SKILL-2.md
│       └── SKILL-3.md
├── commands/
│   ├── command-1.md
│   ├── command-2.md
│   └── command-3.md
├── agents/
│   ├── agent-1.md
│   └── agent-2.md
├── package.json
├── tsconfig.json
├── README.md
└── LICENSE
```

---

## 🚀 Key Differentiators from Anthropic's Claude for Life Sciences

1. **Open Source:** All our plugins are MIT/Apache-2.0
2. **Self-Hosted:** No vendor lock-in, run on your infrastructure
3. **Extensible:** Developers can fork and customize
4. **Free Tier Friendly:** Designed for Vertex AI free tier
5. **Multi-Platform:** Works with Claude Code, not just Claude.ai
6. **Community-Driven:** Plugin marketplace, not closed ecosystem

---

## 📊 Success Metrics

Each plugin pack should achieve:
- **Installation:** < 2 minutes from marketplace
- **First success:** < 5 minutes to first working example
- **Documentation:** 100% coverage of all tools/skills/commands
- **Error rate:** < 1% failures in common workflows
- **Performance:** Tools respond in < 2s for 95% of calls

---

## 🔒 Security & Compliance

**MUST implement:**
- Input validation on all MCP tool parameters
- Rate limiting to prevent API abuse
- API key encryption (never log keys)
- HIPAA-compliant data handling (where applicable)
- Audit logging for compliance tracking
- Data retention policies

**MUST NOT:**
- Store PHI/PII without encryption
- Log sensitive data
- Hardcode API credentials
- Make unvalidated API calls
- Expose internal system details

---

## 💡 Innovation Areas

Go beyond what Anthropic announced:

1. **Offline-First:** SQLite caching for offline research
2. **Collaboration:** Multi-user experiment tracking
3. **Automation:** Cron-style automated literature monitoring
4. **Visualization:** Generate charts/graphs from data
5. **Export:** Multiple formats (CSV, Excel, JSON, XML, PDF)
6. **Integration:** Connect multiple APIs in single workflow

---

## 📝 Deliverables

Generate **6 complete plugin packs** (listed above) with:
- ✅ Production-ready TypeScript MCP servers
- ✅ High-quality Agent Skills (8,000+ bytes each)
- ✅ Comprehensive slash commands
- ✅ Specialized sub-agents
- ✅ Professional documentation
- ✅ MIT License

**Target:** 6 packs × 15 files/pack = ~90 files total

**Timeline:** Complete in single Gemini Pro generation session

**Quality:** Exceeds Anthropic's 500-byte skill examples by 17x

---

## 🎯 Final Output Format

Generate each plugin pack as a complete, installable Claude Code plugin ready for:
1. Immediate marketplace listing
2. Local testing
3. Production deployment
4. Community contribution

**Make it production-grade, not a proof-of-concept.**

---

**Ready to generate? Start with Pack #1: PubMed Research Assistant Pack**
