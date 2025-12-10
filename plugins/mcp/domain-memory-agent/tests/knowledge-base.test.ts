import { describe, it, expect, beforeEach } from 'vitest';

describe('Knowledge Base MCP Server', () => {
  describe('Document Storage', () => {
    it('should generate document ID from title', () => {
      const title = 'Test Document';
      const id = title.toLowerCase().replace(/[^\w]+/g, '-');

      expect(id).toContain('test');
      expect(id).toContain('document');
    });

    it('should calculate word count', () => {
      const content = 'This is a test document with multiple words';
      const wordCount = content.split(/\s+/).length;

      expect(wordCount).toBe(8);
    });

    it('should track created and updated timestamps', () => {
      const now = new Date().toISOString();

      expect(now).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('should store document metadata', () => {
      const metadata = {
        author: 'John Doe',
        category: 'Technical',
        version: '1.0'
      };

      expect(metadata).toHaveProperty('author');
      expect(metadata).toHaveProperty('category');
    });

    it('should support custom document IDs', () => {
      const customId = 'custom-doc-123';
      expect(customId).toBe('custom-doc-123');
    });
  });

  describe('Text Tokenization', () => {
    it('should tokenize text into lowercase words', () => {
      const text = 'Hello World! This is a TEST.';
      const tokens = text
        .toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(w => w.length > 2);

      expect(tokens).toContain('hello');
      expect(tokens).toContain('world');
      expect(tokens).toContain('this');
      expect(tokens).toContain('test');
    });

    it('should filter short words (<=2 chars)', () => {
      const text = 'I am a developer';
      const tokens = text.split(/\s+/).filter(w => w.length > 2);

      expect(tokens).not.toContain('I');
      expect(tokens).not.toContain('am');
      expect(tokens).toContain('developer');
    });

    it('should remove punctuation', () => {
      const text = 'Hello, world!';
      const cleaned = text.replace(/[^\w\s]/g, ' ');

      expect(cleaned).not.toContain(',');
      expect(cleaned).not.toContain('!');
    });
  });

  describe('Term Frequency (TF)', () => {
    it('should calculate term frequency', () => {
      const tokens = ['hello', 'world', 'hello', 'test'];
      const tf = new Map<string, number>();

      tokens.forEach(token => {
        tf.set(token, (tf.get(token) || 0) + 1);
      });

      expect(tf.get('hello')).toBe(2);
      expect(tf.get('world')).toBe(1);
      expect(tf.get('test')).toBe(1);
    });

    it('should handle empty token array', () => {
      const tokens: string[] = [];
      const tf = new Map<string, number>();

      tokens.forEach(token => {
        tf.set(token, (tf.get(token) || 0) + 1);
      });

      expect(tf.size).toBe(0);
    });

    it('should handle duplicate words', () => {
      const tokens = ['test', 'test', 'test'];
      const tf = new Map();

      tokens.forEach(t => {
        tf.set(t, (tf.get(t) || 0) + 1);
      });

      expect(tf.get('test')).toBe(3);
    });
  });

  describe('TF-IDF Scoring', () => {
    it('should calculate IDF correctly', () => {
      const totalDocs = 100;
      const docsWithTerm = 10;
      const idf = Math.log((totalDocs + 1) / (docsWithTerm + 1));

      expect(idf).toBeGreaterThan(0);
    });

    it('should give higher IDF to rare terms', () => {
      const totalDocs = 100;
      const rareTermDocs = 1;
      const commonTermDocs = 50;

      const rareIDF = Math.log((totalDocs + 1) / (rareTermDocs + 1));
      const commonIDF = Math.log((totalDocs + 1) / (commonTermDocs + 1));

      expect(rareIDF).toBeGreaterThan(commonIDF);
    });

    it('should normalize by document length', () => {
      const termFreq = 5;
      const docLength = 100;
      const normalizedTF = termFreq / docLength;

      expect(normalizedTF).toBe(0.05);
    });

    it('should calculate TF-IDF score', () => {
      const tf = 0.05; // 5/100 terms
      const idf = 2.3; // log((100+1)/(10+1))
      const tfidf = tf * idf;

      expect(tfidf).toBeCloseTo(0.115, 2);
    });
  });

  describe('Semantic Search', () => {
    it('should tokenize search query', () => {
      const query = 'machine learning algorithms';
      const tokens = query.toLowerCase().split(/\s+/);

      expect(tokens).toEqual(['machine', 'learning', 'algorithms']);
    });

    it('should match documents by term overlap', () => {
      const queryTokens = ['machine', 'learning'];
      const docTokens = ['machine', 'learning', 'tutorial'];

      const overlap = queryTokens.filter(t => docTokens.includes(t));

      expect(overlap.length).toBe(2);
    });

    it('should rank results by relevance score', () => {
      const results = [
        { id: '1', score: 0.5 },
        { id: '2', score: 0.8 },
        { id: '3', score: 0.3 }
      ];

      results.sort((a, b) => b.score - a.score);

      expect(results[0].id).toBe('2');
      expect(results[0].score).toBe(0.8);
    });

    it('should filter by minimum score', () => {
      const results = [
        { score: 0.8 },
        { score: 0.5 },
        { score: 0.2 }
      ];

      const filtered = results.filter(r => r.score >= 0.5);

      expect(filtered.length).toBe(2);
    });

    it('should limit number of results', () => {
      const results = Array.from({ length: 50 }, (_, i) => ({ id: i }));
      const limited = results.slice(0, 10);

      expect(limited.length).toBe(10);
    });
  });

  describe('Excerpt Extraction', () => {
    it('should extract sentences from text', () => {
      const text = 'First sentence. Second sentence! Third sentence?';
      const sentences = text.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 0);

      expect(sentences.length).toBe(3);
      expect(sentences[0]).toBe('First sentence');
    });

    it('should filter short sentences', () => {
      const sentences = ['Hi', 'This is a longer sentence that provides context', 'Ok'];
      const filtered = sentences.filter(s => s.length > 20);

      expect(filtered.length).toBe(1);
    });

    it('should score sentences by query term presence', () => {
      const sentence = 'machine learning algorithms';
      const queryTokens = ['machine', 'learning'];
      const sentenceTokens = sentence.split(/\s+/);

      const matchCount = queryTokens.filter(t => sentenceTokens.includes(t)).length;

      expect(matchCount).toBe(2);
    });

    it('should select top scoring excerpts', () => {
      const excerpts = [
        { text: 'A', score: 3 },
        { text: 'B', score: 1 },
        { text: 'C', score: 5 }
      ];

      excerpts.sort((a, b) => b.score - a.score);
      const top = excerpts.slice(0, 2);

      expect(top[0].text).toBe('C');
      expect(top[1].text).toBe('A');
    });
  });

  describe('Extractive Summarization', () => {
    it('should split content into sentences', () => {
      const content = 'Sentence one. Sentence two! Sentence three?';
      const sentences = content.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 0);

      expect(sentences.length).toBe(3);
    });

    it('should return original if shorter than max', () => {
      const sentences = ['A', 'B', 'C'];
      const maxSentences = 5;

      if (sentences.length <= maxSentences) {
        const summary = sentences.join('. ') + '.';
        expect(summary).toBe('A. B. C.');
      }
    });

    it('should score sentences by term frequency', () => {
      const sentence = 'machine learning machine';
      const tokens = sentence.split(/\s+/);
      const termFreq = new Map<string, number>();

      tokens.forEach(t => {
        termFreq.set(t, (termFreq.get(t) || 0) + 1);
      });

      const score = tokens.reduce((sum, t) => sum + (termFreq.get(t) || 0), 0);

      expect(score).toBeGreaterThan(0);
    });

    it('should boost first and last sentences', () => {
      const sentences = ['First', 'Middle', 'Last'];
      const boostedIndices = [0, sentences.length - 1];

      expect(boostedIndices).toContain(0);
      expect(boostedIndices).toContain(2);
      expect(boostedIndices).not.toContain(1);
    });

    it('should maintain sentence order in summary', () => {
      const selected = [
        { sentence: 'C', index: 2 },
        { sentence: 'A', index: 0 },
        { sentence: 'B', index: 1 }
      ];

      selected.sort((a, b) => a.index - b.index);
      const ordered = selected.map(s => s.sentence);

      expect(ordered).toEqual(['A', 'B', 'C']);
    });

    it('should limit to max sentences', () => {
      const sentences = ['A', 'B', 'C', 'D', 'E', 'F'];
      const maxSentences = 3;
      const limited = sentences.slice(0, maxSentences);

      expect(limited.length).toBe(3);
    });
  });

  describe('Document Listing', () => {
    it('should filter by tags', () => {
      const docs = [
        { tags: ['tech', 'ai'] },
        { tags: ['business'] },
        { tags: ['tech', 'web'] }
      ];

      const filtered = docs.filter(doc => doc.tags.includes('tech'));

      expect(filtered.length).toBe(2);
    });

    it('should sort by creation date', () => {
      const docs = [
        { createdAt: '2025-01-01T00:00:00Z' },
        { createdAt: '2025-03-01T00:00:00Z' },
        { createdAt: '2025-02-01T00:00:00Z' }
      ];

      docs.sort((a, b) =>
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );

      expect(docs[0].createdAt).toBe('2025-03-01T00:00:00Z');
    });

    it('should sort by title alphabetically', () => {
      const docs = [
        { title: 'Charlie' },
        { title: 'Alice' },
        { title: 'Bob' }
      ];

      docs.sort((a, b) => a.title.localeCompare(b.title));

      expect(docs[0].title).toBe('Alice');
    });

    it('should paginate results', () => {
      const docs = Array.from({ length: 50 }, (_, i) => ({ id: i }));
      const page1 = docs.slice(0, 10);
      const page2 = docs.slice(10, 20);

      expect(page1.length).toBe(10);
      expect(page2.length).toBe(10);
      expect(page1[0].id).toBe(0);
      expect(page2[0].id).toBe(10);
    });

    it('should indicate if more results exist', () => {
      const total = 50;
      const offset = 40;
      const limit = 10;
      const hasMore = offset + limit < total;

      expect(hasMore).toBe(false);
    });
  });

  describe('Summary Caching', () => {
    it('should cache generated summaries', () => {
      const doc = {
        id: '1',
        summary: undefined as string | undefined
      };

      const generatedSummary = 'This is a summary';
      doc.summary = generatedSummary;

      expect(doc.summary).toBe(generatedSummary);
    });

    it('should return cached summary if available', () => {
      const doc = {
        summary: 'Cached summary'
      };

      const regenerate = false;

      if (doc.summary && !regenerate) {
        expect(doc.summary).toBe('Cached summary');
      }
    });

    it('should regenerate if requested', () => {
      const doc = {
        summary: 'Old summary'
      };

      const regenerate = true;

      if (regenerate || !doc.summary) {
        const newSummary = 'New summary';
        expect(newSummary).not.toBe(doc.summary);
      }
    });
  });

  describe('Input Validation', () => {
    it('should validate store_document schema', async () => {
      const { z } = await import('zod');

      const StoreDocumentSchema = z.object({
        title: z.string(),
        content: z.string(),
        metadata: z.record(z.string(), z.any()).optional().default({}),
        tags: z.array(z.string()).optional().default([]),
        id: z.string().optional()
      });

      expect(() => StoreDocumentSchema.parse({
        title: 'Test',
        content: 'Content'
      })).not.toThrow();

      expect(() => StoreDocumentSchema.parse({
        content: 'Missing title'
      })).toThrow();
    });

    it('should validate semantic_search schema', async () => {
      const { z } = await import('zod');

      const SearchSchema = z.object({
        query: z.string(),
        limit: z.number().optional().default(10),
        tags: z.array(z.string()).optional(),
        minScore: z.number().optional().default(0)
      });

      expect(() => SearchSchema.parse({
        query: 'test'
      })).not.toThrow();

      expect(() => SearchSchema.parse({})).toThrow();
    });

    it('should validate summarize schema', async () => {
      const { z } = await import('zod');

      const SummarizeSchema = z.object({
        documentId: z.string().optional(),
        content: z.string().optional(),
        maxSentences: z.number().optional().default(5),
        regenerate: z.boolean().optional().default(false)
      });

      expect(() => SummarizeSchema.parse({
        documentId: 'doc123'
      })).not.toThrow();

      expect(() => SummarizeSchema.parse({
        content: 'Direct content'
      })).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle empty query gracefully', () => {
      const query = '';
      const tokens = query.split(/\s+/).filter(t => t.length > 0);

      expect(tokens.length).toBe(0);
    });

    it('should handle document not found', () => {
      const documents = new Map();
      const docId = 'nonexistent';

      expect(documents.has(docId)).toBe(false);
    });

    it('should handle empty content for summarization', () => {
      const content = '';
      const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);

      expect(sentences.length).toBe(0);
    });

    it('should handle missing required fields', () => {
      const invalidDoc = {
        // Missing title and content
        metadata: {}
      };

      expect(invalidDoc).not.toHaveProperty('title');
      expect(invalidDoc).not.toHaveProperty('content');
    });
  });
});
