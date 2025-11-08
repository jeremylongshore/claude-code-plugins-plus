import { describe, it, expect } from 'vitest';
import { parseSearchResults } from '../src/parser.js';

describe('parseSearchResults', () => {
  describe('empty and invalid inputs', () => {
    it('should handle null results', () => {
      const result = parseSearchResults(null);

      expect(result).toEqual({
        sources: [],
        keyPoints: [],
        detectedPriority: 'normal',
        actionable: false,
        topics: [],
      });
    });

    it('should handle undefined results', () => {
      const result = parseSearchResults(undefined);

      expect(result).toEqual({
        sources: [],
        keyPoints: [],
        detectedPriority: 'normal',
        actionable: false,
        topics: [],
      });
    });

    it('should handle empty array', () => {
      const result = parseSearchResults([]);

      expect(result).toEqual({
        sources: [],
        keyPoints: [],
        detectedPriority: 'normal',
        actionable: false,
        topics: [],
      });
    });
  });

  describe('basic parsing', () => {
    const basicResults = [
      {
        title: 'Test Article',
        url: 'https://example.com/article',
        snippet: 'This is a test snippet',
        score: 0.95,
      },
    ];

    it('should parse single result correctly', () => {
      const result = parseSearchResults(basicResults);

      expect(result.sources).toHaveLength(1);
      expect(result.sources[0]).toEqual({
        title: 'Test Article',
        url: 'https://example.com/article',
        snippet: 'This is a test snippet',
        domain: 'example.com',
        relevance: 0.95,
      });
    });

    it('should limit sources to maxSources option', () => {
      const manyResults = Array.from({ length: 10 }, (_, i) => ({
        title: `Article ${i}`,
        url: `https://example.com/article${i}`,
        snippet: `Snippet ${i}`,
      }));

      const result = parseSearchResults(manyResults, { maxSources: 3 });

      expect(result.sources).toHaveLength(3);
    });

    it('should use default maxSources of 5', () => {
      const manyResults = Array.from({ length: 10 }, (_, i) => ({
        title: `Article ${i}`,
        url: `https://example.com/article${i}`,
        snippet: `Snippet ${i}`,
      }));

      const result = parseSearchResults(manyResults);

      expect(result.sources).toHaveLength(5);
    });

    it('should handle results without score', () => {
      const noScoreResults = [
        {
          title: 'Article',
          url: 'https://example.com',
          snippet: 'Test',
        },
      ];

      const result = parseSearchResults(noScoreResults);

      expect(result.sources[0].relevance).toBe(1.0);
    });

    it('should use "Untitled" for missing title', () => {
      const noTitleResults = [
        {
          url: 'https://example.com',
          snippet: 'Test',
        },
      ];

      const result = parseSearchResults(noTitleResults);

      expect(result.sources[0].title).toBe('Untitled');
    });

    it('should handle missing snippet', () => {
      const noSnippetResults = [
        {
          title: 'Article',
          url: 'https://example.com',
        },
      ];

      const result = parseSearchResults(noSnippetResults);

      expect(result.sources[0].snippet).toBe('');
    });

    it('should use description as fallback for snippet', () => {
      const descriptionResults = [
        {
          title: 'Article',
          url: 'https://example.com',
          description: 'This is a description',
        },
      ];

      const result = parseSearchResults(descriptionResults);

      expect(result.sources[0].snippet).toBe('This is a description');
    });
  });

  describe('URL domain extraction', () => {
    it('should extract domain from standard URL', () => {
      const results = [
        {
          title: 'Test',
          url: 'https://www.example.com/path/to/page',
          snippet: 'Test',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.sources[0].domain).toBe('www.example.com');
    });

    it('should extract domain from http URL', () => {
      const results = [
        {
          title: 'Test',
          url: 'http://example.com/page',
          snippet: 'Test',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.sources[0].domain).toBe('example.com');
    });

    it('should handle invalid URL gracefully', () => {
      const results = [
        {
          title: 'Test',
          url: 'not-a-valid-url',
          snippet: 'Test',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.sources[0].domain).toBe('unknown');
    });

    it('should handle subdomain correctly', () => {
      const results = [
        {
          title: 'Test',
          url: 'https://blog.example.com/post',
          snippet: 'Test',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.sources[0].domain).toBe('blog.example.com');
    });
  });

  describe('key point extraction', () => {
    it('should extract key points with action keywords', () => {
      const results = [
        {
          title: 'Best Practices',
          url: 'https://example.com',
          snippet:
            'You should always validate input. This is important for security. Regular testing is recommended.',
        },
      ];

      const result = parseSearchResults(results, { extractKeyPoints: true });

      expect(result.keyPoints.length).toBeGreaterThan(0);
      expect(result.keyPoints[0]).toHaveProperty('text');
      expect(result.keyPoints[0]).toHaveProperty('source');
      expect(result.keyPoints[0]).toHaveProperty('sourceTitle');
    });

    it('should skip key point extraction when disabled', () => {
      const results = [
        {
          title: 'Best Practices',
          url: 'https://example.com',
          snippet: 'You should always validate input.',
        },
      ];

      const result = parseSearchResults(results, { extractKeyPoints: false });

      expect(result.keyPoints).toEqual([]);
    });

    it('should deduplicate identical key points', () => {
      const results = [
        {
          title: 'Article 1',
          url: 'https://example.com/1',
          snippet:
            'You should always validate input. This is critical for security.',
        },
        {
          title: 'Article 2',
          url: 'https://example.com/2',
          snippet:
            'You should always validate input. Another important point here.',
        },
      ];

      const result = parseSearchResults(results);

      const duplicateTexts = result.keyPoints.filter(
        (kp) => kp.text === 'You should always validate input'
      );

      expect(duplicateTexts.length).toBe(1);
    });

    it('should limit key points to 10', () => {
      const longSnippet = Array.from({ length: 20 }, (_, i) =>
        `This is an important point number ${i} that should be included.`
      ).join(' ');

      const results = [
        {
          title: 'Long Article',
          url: 'https://example.com',
          snippet: longSnippet,
        },
      ];

      const result = parseSearchResults(results);

      expect(result.keyPoints.length).toBeLessThanOrEqual(10);
    });

    it('should filter out short sentences', () => {
      const results = [
        {
          title: 'Article',
          url: 'https://example.com',
          snippet: 'Short. This is important for performance. OK.',
        },
      ];

      const result = parseSearchResults(results);

      const shortPoints = result.keyPoints.filter(
        (kp) => kp.text.length < 20
      );

      expect(shortPoints.length).toBe(0);
    });

    it('should detect "recommend" keyword', () => {
      const results = [
        {
          title: 'Article',
          url: 'https://example.com',
          snippet: 'We recommend using TypeScript for better type safety.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.keyPoints.length).toBeGreaterThan(0);
    });

    it('should detect "best practice" keyword', () => {
      const results = [
        {
          title: 'Article',
          url: 'https://example.com',
          snippet: 'It is best practice to use environment variables.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.keyPoints.length).toBeGreaterThan(0);
    });

    it('should detect "avoid" keyword', () => {
      const results = [
        {
          title: 'Article',
          url: 'https://example.com',
          snippet: 'You should avoid using deprecated APIs in production.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.keyPoints.length).toBeGreaterThan(0);
    });
  });

  describe('priority detection', () => {
    it('should detect urgent priority for security keywords', () => {
      const results = [
        {
          title: 'Critical Security Vulnerability Found',
          url: 'https://example.com',
          snippet: 'This is a critical security issue that needs immediate attention.',
        },
      ];

      const result = parseSearchResults(results, { priorityDetection: true });

      expect(result.detectedPriority).toBe('urgent');
    });

    it('should detect urgent priority for CVE mentions', () => {
      const results = [
        {
          title: 'CVE-2024-1234 Advisory',
          url: 'https://example.com',
          snippet: 'New CVE discovered affecting popular library.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.detectedPriority).toBe('urgent');
    });

    it('should detect urgent priority for deprecated warnings', () => {
      const results = [
        {
          title: 'Breaking Changes',
          url: 'https://example.com',
          snippet: 'This API is deprecated and will be removed soon.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.detectedPriority).toBe('urgent');
    });

    it('should return normal priority for regular content', () => {
      const results = [
        {
          title: 'Introduction to Testing',
          url: 'https://example.com',
          snippet: 'Learn how to write effective tests for your application.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.detectedPriority).toBe('normal');
    });

    it('should skip priority detection when disabled', () => {
      const results = [
        {
          title: 'Critical Security Issue',
          url: 'https://example.com',
          snippet: 'This is urgent and critical.',
        },
      ];

      const result = parseSearchResults(results, { priorityDetection: false });

      expect(result.detectedPriority).toBeNull();
    });

    it('should detect "urgent" keyword', () => {
      const results = [
        {
          title: 'Urgent Update Required',
          url: 'https://example.com',
          snippet: 'An urgent patch is needed.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.detectedPriority).toBe('urgent');
    });

    it('should detect "exploit" keyword', () => {
      const results = [
        {
          title: 'Exploit Discovered',
          url: 'https://example.com',
          snippet: 'New exploit found in the wild.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.detectedPriority).toBe('urgent');
    });
  });

  describe('actionability detection', () => {
    it('should detect actionable content with "how to"', () => {
      const results = [
        {
          title: 'How to Deploy Your Application',
          url: 'https://example.com',
          snippet: 'This guide shows you how to deploy step by step.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.actionable).toBe(true);
    });

    it('should detect actionable content with "tutorial"', () => {
      const results = [
        {
          title: 'Complete Tutorial',
          url: 'https://example.com',
          snippet: 'A comprehensive tutorial on testing.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.actionable).toBe(true);
    });

    it('should detect actionable content with "setup"', () => {
      const results = [
        {
          title: 'Setup Guide',
          url: 'https://example.com',
          snippet: 'Learn how to setup your environment.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.actionable).toBe(true);
    });

    it('should not detect actionability for theoretical content', () => {
      const results = [
        {
          title: 'Theory of Computing',
          url: 'https://example.com',
          snippet: 'This article explores theoretical concepts.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.actionable).toBe(false);
    });

    it('should skip actionability detection when priority detection disabled', () => {
      const results = [
        {
          title: 'How to Guide',
          url: 'https://example.com',
          snippet: 'Step by step tutorial.',
        },
      ];

      const result = parseSearchResults(results, { priorityDetection: false });

      expect(result.actionable).toBe(false);
    });
  });

  describe('topic extraction', () => {
    it('should extract topics from content', () => {
      const results = [
        {
          title: 'Testing JavaScript Applications',
          url: 'https://example.com',
          snippet:
            'Learn about testing JavaScript applications with modern testing frameworks.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.topics).toContain('testing');
      expect(result.topics).toContain('javascript');
    });

    it('should limit topics to 5', () => {
      const results = [
        {
          title: 'Article',
          url: 'https://example.com',
          snippet:
            'programming development software engineering testing deployment automation monitoring performance security reliability scalability',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.topics.length).toBe(5);
    });

    it('should filter out stop words', () => {
      const results = [
        {
          title: 'The Best Guide',
          url: 'https://example.com',
          snippet: 'This is the best guide for your testing needs.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.topics).not.toContain('the');
      expect(result.topics).not.toContain('this');
      expect(result.topics).not.toContain('your');
    });

    it('should filter out short words (4 chars or less)', () => {
      const results = [
        {
          title: 'Test API for Code',
          url: 'https://example.com',
          snippet: 'Use API for your test code.',
        },
      ];

      const result = parseSearchResults(results);

      const shortWords = result.topics.filter((t) => t.length <= 4);

      expect(shortWords.length).toBe(0);
    });

    it('should sort topics by frequency', () => {
      const results = [
        {
          title: 'Testing',
          url: 'https://example.com/1',
          snippet: 'Testing is important. Testing frameworks help with testing.',
        },
        {
          title: 'Testing Again',
          url: 'https://example.com/2',
          snippet: 'More about testing and development.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.topics[0]).toBe('testing');
    });

    it('should handle empty content gracefully', () => {
      const results = [
        {
          title: '',
          url: 'https://example.com',
          snippet: '',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.topics).toEqual([]);
    });

    it('should be case-insensitive', () => {
      const results = [
        {
          title: 'Testing JAVASCRIPT Applications',
          url: 'https://example.com',
          snippet: 'Learn TESTING with JavaScript and testing frameworks.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.topics).toContain('testing');
      expect(result.topics).toContain('javascript');
      expect(result.topics).not.toContain('TESTING');
      expect(result.topics).not.toContain('JAVASCRIPT');
    });
  });

  describe('complex scenarios', () => {
    it('should handle mix of valid and malformed results', () => {
      const mixedResults = [
        {
          title: 'Valid Article',
          url: 'https://example.com/valid',
          snippet: 'This is a valid snippet.',
        },
        {
          // Missing title
          url: 'https://example.com/notitle',
          snippet: 'No title here.',
        },
        {
          title: 'No URL Article',
          // Missing URL will cause domain extraction to fail
          snippet: 'Has title and snippet.',
        },
      ];

      expect(() => parseSearchResults(mixedResults)).not.toThrow();

      const result = parseSearchResults(mixedResults);

      expect(result.sources.length).toBe(3);
    });

    it('should handle all options together', () => {
      const results = [
        {
          title: 'Critical Security: How to Fix CVE-2024-1234',
          url: 'https://security.example.com/advisory',
          snippet:
            'This critical vulnerability must be patched immediately. You should update your dependencies and ensure security.',
          score: 0.99,
        },
      ];

      const result = parseSearchResults(results, {
        maxSources: 10,
        extractKeyPoints: true,
        priorityDetection: true,
      });

      expect(result.sources).toHaveLength(1);
      expect(result.keyPoints.length).toBeGreaterThan(0);
      expect(result.detectedPriority).toBe('urgent');
      expect(result.actionable).toBe(true); // "how to" is an actionable keyword
      expect(result.topics.length).toBeGreaterThan(0);
    });

    it('should handle Unicode characters in content', () => {
      const results = [
        {
          title: 'Guide à la Testing 🚀',
          url: 'https://example.com',
          snippet: 'Important: Always validate émojis and spëcial characters.',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.sources[0].title).toContain('à');
      expect(result.sources[0].title).toContain('🚀');
    });

    it('should handle very long snippets', () => {
      const longSnippet = 'This is important. '.repeat(100);

      const results = [
        {
          title: 'Long Article',
          url: 'https://example.com',
          snippet: longSnippet,
        },
      ];

      expect(() => parseSearchResults(results)).not.toThrow();
    });

    it('should handle results with only whitespace', () => {
      const results = [
        {
          title: '   ',
          url: 'https://example.com',
          snippet: '   \n\t   ',
        },
      ];

      const result = parseSearchResults(results);

      expect(result.sources).toHaveLength(1);
      expect(result.keyPoints).toHaveLength(0);
    });
  });
});
