/**
 * Parse web search results into structured insights
 */
export function parseSearchResults(results, options = {}) {
  const {
    maxSources = 5,
    extractKeyPoints = true,
    priorityDetection = true
  } = options;

  if (!results || results.length === 0) {
    return {
      sources: [],
      keyPoints: [],
      detectedPriority: 'normal',
      actionable: false,
      topics: []
    };
  }

  const topResults = results.slice(0, maxSources);

  const insights = {
    sources: topResults
      .map(result => {
        // Skip results with invalid URLs
        if (!result.url || typeof result.url !== 'string') {
          console.warn('Skipping result with invalid URL:', result);
          return null;
        }

        return {
          title: result.title || 'Untitled',
          url: result.url,
          snippet: result.snippet || result.description || '',
          domain: extractDomain(result.url),
          relevance: result.score || 1.0
        };
      })
      .filter(Boolean), // Remove null entries
    keyPoints: [],
    detectedPriority: null,
    actionable: false,
    topics: []
  };

  if (extractKeyPoints) {
    insights.keyPoints = extractKeyPointsFromSnippets(topResults);
  }

  if (priorityDetection) {
    insights.detectedPriority = detectPriority(topResults);
    insights.actionable = detectActionability(topResults);
  }

  insights.topics = extractTopics(topResults);

  return insights;
}

/**
 * Extract domain from URL safely
 */
function extractDomain(url) {
  try {
    return new URL(url).hostname;
  } catch {
    return 'unknown';
  }
}

/**
 * Extract key points from snippets
 */
function extractKeyPointsFromSnippets(results) {
  const keyPoints = [];

  for (const result of results) {
    const snippet = result.snippet || result.description || '';
    const sentences = snippet.split(/[.!?]+/).filter(s => s.trim().length > 20);

    for (const sentence of sentences) {
      if (isKeyPoint(sentence)) {
        keyPoints.push({
          text: sentence.trim(),
          source: result.url,
          sourceTitle: result.title || 'Source'
        });
      }
    }
  }

  // Deduplicate by text and limit to 10
  return [...new Map(keyPoints.map(kp => [kp.text, kp])).values()].slice(0, 10);
}

/**
 * Check if sentence contains actionable keywords
 */
function isKeyPoint(sentence) {
  const actionKeywords = [
    'should', 'must', 'recommend', 'best practice',
    'important', 'critical', 'essential', 'key',
    'avoid', 'ensure', 'always', 'never',
    'performance', 'security', 'optimize'
  ];

  const lowerSentence = sentence.toLowerCase();
  return actionKeywords.some(keyword => lowerSentence.includes(keyword));
}

/**
 * Detect priority level from content
 */
function detectPriority(results) {
  const urgentKeywords = [
    'urgent', 'critical', 'security', 'vulnerability',
    'cve', 'exploit', 'breaking', 'deprecated',
    'emergency', 'immediate', 'asap'
  ];

  const allText = results
    .map(r => `${r.title || ''} ${r.snippet || r.description || ''}`)
    .join(' ')
    .toLowerCase();

  if (urgentKeywords.some(keyword => allText.includes(keyword))) {
    return 'urgent';
  }

  return 'normal';
}

/**
 * Detect if content is actionable (has implementation guidance)
 */
function detectActionability(results) {
  const actionableKeywords = [
    'how to', 'implementation', 'setup', 'configure',
    'tutorial', 'guide', 'step by step', 'example',
    'install', 'deploy', 'create'
  ];

  const allText = results
    .map(r => `${r.title || ''} ${r.snippet || r.description || ''}`)
    .join(' ')
    .toLowerCase();

  return actionableKeywords.some(keyword => allText.includes(keyword));
}

/**
 * Extract main topics from content
 */
function extractTopics(results) {
  const wordFreq = {};
  const stopWords = new Set(['the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'will', 'your', 'their', 'about', 'which', 'when', 'what', 'where', 'there']);

  for (const result of results) {
    const text = `${result.title || ''} ${result.snippet || result.description || ''}`;
    const words = text.toLowerCase()
      .split(/\W+/)
      .filter(w => w.length > 4 && !stopWords.has(w));

    for (const word of words) {
      wordFreq[word] = (wordFreq[word] || 0) + 1;
    }
  }

  return Object.entries(wordFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word]) => word);
}
