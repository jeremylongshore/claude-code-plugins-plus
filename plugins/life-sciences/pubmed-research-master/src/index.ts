import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import fetch from 'node-fetch';

class PubMedMCPServer {
  private server: Server;
  private apiKey: string | undefined;
  private email: string | undefined;
  private requestCounter: number = 0;
  private lastRequestTime: number = 0;

  constructor() {
    this.apiKey = process.env.PUBMED_API_KEY;
    this.email = process.env.EMAIL;

    this.server = new Server(
      {
        name: "pubmed-research-master",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  private async enforceRateLimit() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;

    if (this.apiKey) {
      // With API key: 10 requests/second
      if (timeSinceLastRequest < 100) {
        const delay = 100 - timeSinceLastRequest;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    } else {
      // Without API key: 3 requests/second
      if (this.requestCounter >= 3 && timeSinceLastRequest < 1000) {
        const delay = 1000 - timeSinceLastRequest;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      this.requestCounter = (timeSinceLastRequest < 1000) ? this.requestCounter + 1 : 1;
    }

    this.lastRequestTime = Date.now();
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "search_pubmed",
          description: "Search PubMed for scientific articles with advanced filters",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query" },
              max_results: { type: "number", description: "Max results (1-500)", default: 100 },
              date_from: { type: "string", description: "Start date (YYYY/MM/DD)" },
              date_to: { type: "string", description: "End date (YYYY/MM/DD)" },
              article_type: { type: "string", description: "Article type filter" },
            },
            required: ["query"]
          }
        },
        {
          name: "get_article_details",
          description: "Get full metadata for a PubMed article by PMID",
          inputSchema: {
            type: "object",
            properties: {
              pmid: { type: "string", description: "PubMed ID" }
            },
            required: ["pmid"]
          }
        },
        {
          name: "get_full_text",
          description: "Retrieve full text from PubMed Central when available",
          inputSchema: {
            type: "object",
            properties: {
              pmid: { type: "string", description: "PubMed ID" }
            },
            required: ["pmid"]
          }
        },
        {
          name: "search_by_mesh",
          description: "Search PubMed using MeSH (Medical Subject Headings) terms",
          inputSchema: {
            type: "object",
            properties: {
              mesh_term: { type: "string", description: "MeSH term to search" },
              max_results: { type: "number", description: "Max results (1-500)", default: 100 }
            },
            required: ["mesh_term"]
          }
        },
        {
          name: "get_related_articles",
          description: "Find articles related to a given PubMed article",
          inputSchema: {
            type: "object",
            properties: {
              pmid: { type: "string", description: "PubMed ID" },
              max_results: { type: "number", description: "Max results", default: 50 }
            },
            required: ["pmid"]
          }
        },
        {
          name: "export_citations",
          description: "Export citations in BibTeX, RIS, or EndNote format",
          inputSchema: {
            type: "object",
            properties: {
              pmids: { type: "string", description: "Comma-separated PMIDs" },
              format: { type: "string", enum: ["BibTeX", "RIS", "EndNote"], default: "BibTeX" }
            },
            required: ["pmids"]
          }
        },
        {
          name: "analyze_trends",
          description: "Analyze publication trends over time for a topic",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query" },
              start_year: { type: "number", description: "Start year" },
              end_year: { type: "number", description: "End year" }
            },
            required: ["query", "start_year", "end_year"]
          }
        },
        {
          name: "compare_studies",
          description: "Compare multiple studies side-by-side",
          inputSchema: {
            type: "object",
            properties: {
              pmids: { type: "string", description: "Comma-separated PMIDs to compare" }
            },
            required: ["pmids"]
          }
        },
        {
          name: "get_mesh_terms",
          description: "Get MeSH terms for an article",
          inputSchema: {
            type: "object",
            properties: {
              pmid: { type: "string", description: "PubMed ID" }
            },
            required: ["pmid"]
          }
        },
        {
          name: "advanced_search",
          description: "Build complex Boolean search queries",
          inputSchema: {
            type: "object",
            properties: {
              terms: { type: "string", description: "Search terms with Boolean operators (AND, OR, NOT)" },
              filters: { type: "object", description: "Additional filters" }
            },
            required: ["terms"]
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "search_pubmed":
          return await this.searchPubMed(args);
        case "get_article_details":
          return await this.getArticleDetails(args);
        case "get_full_text":
          return await this.getFullText(args);
        case "search_by_mesh":
          return await this.searchByMesh(args);
        case "get_related_articles":
          return await this.getRelatedArticles(args);
        case "export_citations":
          return await this.exportCitations(args);
        case "analyze_trends":
          return await this.analyzeTrends(args);
        case "compare_studies":
          return await this.compareStudies(args);
        case "get_mesh_terms":
          return await this.getMeshTerms(args);
        case "advanced_search":
          return await this.advancedSearch(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  private async searchPubMed(args: any) {
    const schema = z.object({
      query: z.string(),
      max_results: z.number().int().min(1).max(500).default(100),
      date_from: z.string().optional(),
      date_to: z.string().optional(),
      article_type: z.string().optional(),
    });

    const validated = schema.parse(args);
    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(validated.query)}&retmax=${validated.max_results}&retmode=json`;

    if (validated.date_from) {
      const dateTo = validated.date_to || new Date().toISOString().slice(0, 10).replace(/-/g, '/');
      url += `&datetype=pdat&mindate=${validated.date_from}&maxdate=${dateTo}`;
    }

    if (this.apiKey) url += `&api_key=${this.apiKey}`;
    if (this.email) url += `&email=${this.email}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const data: any = await response.json();

    return {
      content: [{
        type: "text",
        text: `Found ${data.esearchresult.count} articles.\n\nPMIDs: ${data.esearchresult.idlist.slice(0, 20).join(', ')}${data.esearchresult.idlist.length > 20 ? '...' : ''}`
      }]
    };
  }

  private async getArticleDetails(args: any) {
    const schema = z.object({ pmid: z.string() });
    const { pmid } = schema.parse(args);

    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmid}&retmode=xml`;
    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const xmlData = await response.text();

    const titleMatch = xmlData.match(/<ArticleTitle>(.*?)<\/ArticleTitle>/);
    const abstractMatch = xmlData.match(/<AbstractText>(.*?)<\/AbstractText>/s);
    const authorsMatch = xmlData.match(/<AuthorList[^>]*>(.*?)<\/AuthorList>/s);

    const title = titleMatch ? titleMatch[1] : 'Title not found';
    const abstract = abstractMatch ? abstractMatch[1].replace(/<[^>]*>/g, '') : 'Abstract not available';

    return {
      content: [{
        type: "text",
        text: `**PMID:** ${pmid}\n\n**Title:** ${title}\n\n**Abstract:** ${abstract}`
      }]
    };
  }

  private async getFullText(args: any) {
    const schema = z.object({ pmid: z.string() });
    const { pmid } = schema.parse(args);

    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=${pmid}&retmode=xml`;
    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const xmlData = await response.text();

    const fullTextMatch = xmlData.match(/<body[^>]*>(.*?)<\/body>/s);
    const fullText = fullTextMatch ? fullTextMatch[1].replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim() : 'Full text not available in PMC';

    return {
      content: [{
        type: "text",
        text: fullText.substring(0, 5000) + (fullText.length > 5000 ? '...' : '')
      }]
    };
  }

  private async searchByMesh(args: any) {
    const schema = z.object({
      mesh_term: z.string(),
      max_results: z.number().int().min(1).max(500).default(100)
    });

    const { mesh_term, max_results } = schema.parse(args);
    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(mesh_term)}[MeSH Terms]&retmax=${max_results}&retmode=json`;

    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const data: any = await response.json();

    return {
      content: [{
        type: "text",
        text: `Found ${data.esearchresult.count} articles for MeSH term "${mesh_term}".\n\nPMIDs: ${data.esearchresult.idlist.join(', ')}`
      }]
    };
  }

  private async getRelatedArticles(args: any) {
    const schema = z.object({
      pmid: z.string(),
      max_results: z.number().default(50)
    });

    const { pmid, max_results } = schema.parse(args);
    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=pubmed&id=${pmid}&retmode=json`;

    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const data: any = await response.json();

    const relatedPMIDs = data.linksets?.[0]?.linksetdbs?.find((l: any) => l.linkname === 'pubmed_pubmed')?.links || [];

    return {
      content: [{
        type: "text",
        text: `Found ${relatedPMIDs.length} related articles for PMID ${pmid}.\n\nRelated PMIDs: ${relatedPMIDs.slice(0, max_results).join(', ')}`
      }]
    };
  }

  private async exportCitations(args: any) {
    const schema = z.object({
      pmids: z.string(),
      format: z.enum(["BibTeX", "RIS", "EndNote"]).default("BibTeX")
    });

    const { pmids, format } = schema.parse(args);
    const rettype = format === "BibTeX" ? "medline" : format === "RIS" ? "ris" : "enw";

    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmids}&retmode=text&rettype=${rettype}`;
    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const citations = await response.text();

    return {
      content: [{
        type: "text",
        text: `**${format} Citations:**\n\n${citations}`
      }]
    };
  }

  private async analyzeTrends(args: any) {
    const schema = z.object({
      query: z.string(),
      start_year: z.number().int(),
      end_year: z.number().int()
    });

    const { query, start_year, end_year } = schema.parse(args);
    const trends: string[] = [];

    for (let year = start_year; year <= end_year; year++) {
      const yearQuery = `${query} AND ${year}[PDAT]`;
      let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(yearQuery)}&retmax=0&retmode=json`;

      if (this.apiKey) url += `&api_key=${this.apiKey}`;

      await this.enforceRateLimit();
      const response = await fetch(url);
      const data: any = await response.json();

      trends.push(`${year}: ${data.esearchresult.count} articles`);
    }

    return {
      content: [{
        type: "text",
        text: `**Publication Trends for "${query}" (${start_year}-${end_year}):**\n\n${trends.join('\n')}`
      }]
    };
  }

  private async compareStudies(args: any) {
    const schema = z.object({ pmids: z.string() });
    const { pmids } = schema.parse(args);

    const pmidList = pmids.split(',').map(p => p.trim());
    const comparisons: string[] = [];

    for (const pmid of pmidList) {
      let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${pmid}&retmode=json`;
      if (this.apiKey) url += `&api_key=${this.apiKey}`;

      await this.enforceRateLimit();
      const response = await fetch(url);
      const data: any = await response.json();

      const article = data.result[pmid];
      if (article) {
        comparisons.push(`**PMID ${pmid}:**\n- Title: ${article.title}\n- Date: ${article.pubdate}\n- Authors: ${article.authors?.map((a: any) => a.name).join(', ') || 'N/A'}`);
      }
    }

    return {
      content: [{
        type: "text",
        text: comparisons.join('\n\n')
      }]
    };
  }

  private async getMeshTerms(args: any) {
    const schema = z.object({ pmid: z.string() });
    const { pmid } = schema.parse(args);

    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmid}&retmode=xml`;
    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const xmlData = await response.text();

    const meshMatches = xmlData.matchAll(/<DescriptorName[^>]*>([^<]+)<\/DescriptorName>/g);
    const meshTerms = Array.from(meshMatches).map(m => m[1]);

    return {
      content: [{
        type: "text",
        text: `**MeSH Terms for PMID ${pmid}:**\n\n${meshTerms.join('\n') || 'No MeSH terms found'}`
      }]
    };
  }

  private async advancedSearch(args: any) {
    const schema = z.object({
      terms: z.string(),
      filters: z.object({}).optional()
    });

    const { terms } = schema.parse(args);
    let url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(terms)}&retmax=100&retmode=json`;

    if (this.apiKey) url += `&api_key=${this.apiKey}`;

    await this.enforceRateLimit();
    const response = await fetch(url);
    const data: any = await response.json();

    return {
      content: [{
        type: "text",
        text: `**Advanced Search Results:**\n\nQuery: ${terms}\nFound: ${data.esearchresult.count} articles\n\nPMIDs: ${data.esearchresult.idlist.join(', ')}`
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("PubMed Research Master MCP Server running");
  }
}

const server = new PubMedMCPServer();
server.run().catch(console.error);
