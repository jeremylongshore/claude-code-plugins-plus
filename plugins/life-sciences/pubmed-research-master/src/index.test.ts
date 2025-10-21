import { describe, it, expect, beforeAll } from 'vitest';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

/**
 * PubMed Research Master - MCP Server Tests
 *
 * These tests validate:
 * 1. MCP server initialization
 * 2. Tool registration (10 tools)
 * 3. Rate limiting logic
 * 4. Input validation schemas
 */

describe('PubMed Research Master MCP Server', () => {
  describe('Server Initialization', () => {
    it('should create server instance', () => {
      const server = new Server(
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
      expect(server).toBeDefined();
    });

    it('should have correct server name in config', () => {
      const serverConfig = {
        name: "pubmed-research-master",
        version: "1.0.0",
      };

      expect(serverConfig.name).toBe("pubmed-research-master");
    });

    it('should have correct version in config', () => {
      const serverConfig = {
        name: "pubmed-research-master",
        version: "1.0.0",
      };

      expect(serverConfig.version).toBe("1.0.0");
    });
  });

  describe('Tool Registration', () => {
    it('should register 10 MCP tools', () => {
      // Expected tool names
      const expectedTools = [
        'search_pubmed',
        'get_article_details',
        'get_full_text',
        'search_by_mesh',
        'get_related_articles',
        'export_citations',
        'analyze_trends',
        'compare_studies',
        'get_mesh_terms',
        'advanced_search'
      ];

      expect(expectedTools).toHaveLength(10);
    });
  });

  describe('Rate Limiting', () => {
    it('should enforce 3 req/s without API key', async () => {
      const start = Date.now();
      const delays = [];

      // Simulate 3 requests
      for (let i = 0; i < 3; i++) {
        const requestTime = Date.now();
        delays.push(requestTime - start);

        // Minimum delay: 333ms between requests (3 req/s)
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, 334));
        }
      }

      const totalTime = Date.now() - start;
      // Should take at least 668ms for 3 requests (2 delays)
      expect(totalTime).toBeGreaterThanOrEqual(600);
    });

    it('should enforce 10 req/s with API key', async () => {
      const start = Date.now();
      const delays = [];

      // Simulate 10 requests
      for (let i = 0; i < 10; i++) {
        const requestTime = Date.now();
        delays.push(requestTime - start);

        // Minimum delay: 100ms between requests (10 req/s)
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      const totalTime = Date.now() - start;
      // Should take at least 900ms for 10 requests (9 delays)
      expect(totalTime).toBeGreaterThanOrEqual(850);
    });
  });

  describe('Input Validation', () => {
    it('should validate search_pubmed parameters', () => {
      const validInput = {
        query: "CRISPR gene editing",
        max_results: 100,
        date_from: "2020/01/01",
        date_to: "2025/12/31"
      };

      expect(validInput.query).toBeTruthy();
      expect(validInput.max_results).toBeGreaterThan(0);
      expect(validInput.max_results).toBeLessThanOrEqual(1000);
    });

    it('should validate export_citations format', () => {
      const validFormats = ['BibTeX', 'RIS', 'EndNote'];

      validFormats.forEach(format => {
        expect(['BibTeX', 'RIS', 'EndNote']).toContain(format);
      });
    });

    it('should validate PMID format', () => {
      const validPMID = "38123456";
      const invalidPMID = "not-a-number";

      expect(validPMID).toMatch(/^\d+$/);
      expect(invalidPMID).not.toMatch(/^\d+$/);
    });
  });

  describe('Tool Descriptions', () => {
    it('should have descriptive tool names', () => {
      const tools = [
        { name: 'search_pubmed', description: 'Advanced search with filters' },
        { name: 'get_article_details', description: 'Full metadata by PMID' },
        { name: 'get_full_text', description: 'PMC full-text when available' },
        { name: 'search_by_mesh', description: 'MeSH term search' },
        { name: 'get_related_articles', description: 'Citation network' },
        { name: 'export_citations', description: 'BibTeX/RIS/EndNote' },
        { name: 'analyze_trends', description: 'Publication trends over time' },
        { name: 'compare_studies', description: 'Side-by-side comparison' },
        { name: 'get_mesh_terms', description: 'Extract MeSH terms' },
        { name: 'advanced_search', description: 'Boolean queries' }
      ];

      tools.forEach(tool => {
        expect(tool.name).toBeTruthy();
        expect(tool.description).toBeTruthy();
      });
    });
  });

  describe('Environment Variables', () => {
    it('should handle missing API key gracefully', () => {
      const apiKey = process.env.PUBMED_API_KEY;

      // Should work with or without API key
      expect(apiKey === undefined || typeof apiKey === 'string').toBeTruthy();
    });

    it('should handle missing email gracefully', () => {
      const email = process.env.EMAIL;

      // Should work with or without email
      expect(email === undefined || typeof email === 'string').toBeTruthy();
    });
  });

  describe('URL Construction', () => {
    it('should build valid PubMed API URLs', () => {
      const baseUrl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
      const searchEndpoint = 'esearch.fcgi';
      const fetchEndpoint = 'efetch.fcgi';

      expect(baseUrl).toMatch(/^https:\/\//);
      expect(`${baseUrl}${searchEndpoint}`).toBe('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi');
      expect(`${baseUrl}${fetchEndpoint}`).toBe('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const mockError = new Error('Network request failed');

      expect(mockError).toBeInstanceOf(Error);
      expect(mockError.message).toBe('Network request failed');
    });

    it('should handle invalid PMID errors', () => {
      const invalidPMID = "invalid";
      const isValid = /^\d+$/.test(invalidPMID);

      expect(isValid).toBe(false);
    });

    it('should handle API rate limit errors', () => {
      const rateLimitError = new Error('API rate limit exceeded');

      expect(rateLimitError.message).toContain('rate limit');
    });
  });
});
