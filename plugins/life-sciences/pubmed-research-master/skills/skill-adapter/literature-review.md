---
name: Literature Review Automator
description: |
  Automatically activates when user mentions "review the literature on...",
  "what does research say about...", or "find papers about...".
  This skill conducts comprehensive literature reviews with PubMed searches,
  citation analysis, and synthesis.
---

## What This Skill Does

When activated, this skill performs a complete literature review workflow:
1. Understands the research topic
2. Constructs optimal PubMed search queries
3. Retrieves relevant articles
4. Analyzes citation networks
5. Synthesizes findings into a structured review

## When It Activates

**Trigger Phrases:**
- "Review the literature on [topic]"
- "What does research say about [topic]"
- "What does research say about the role of gut microbiome in autism spectrum disorder?"
- "Find recent papers about [topic]"
- "Give me a literature review of [topic]"
- "Summarize the current state of research on immunotherapy for glioblastoma"
- "I need a literature review of the effects of long-term space travel on bone density"
- "Can you do a literature search for me on the use of AI in drug discovery?"
- "Provide a comprehensive overview of the research on the impact of climate change on infectious diseases"
- "I'm writing a paper on gene therapy for cystic fibrosis; can you help me with the literature review?"
- "What are the latest findings regarding the efficacy of mindfulness-based interventions for chronic pain?"

**Context Detection:**
- Working with `.bib`, `.ris`, or reference files
- Discussing scientific research topics
- Requesting literature searches

## Multi-Phase Workflow

### Phase 1: Query Construction
1. Analyze the research topic
2. Identify key concepts and synonyms
3. Construct Boolean search query
4. Add filters (date range, article type)

Example:
```
Topic: "CRISPR gene editing in cancer therapy"
→ Query: ("CRISPR" OR "gene editing" OR "genome editing") AND ("cancer" OR "oncology" OR "tumor") AND ("therapy" OR "treatment")
→ Filters: Last 5 years, Clinical Trials + Reviews
```

### Phase 2: Article Retrieval
1. Execute PubMed search
2. Retrieve article metadata
3. Get full abstracts
4. Extract MeSH terms
5. Cache results locally (SQLite)

### Phase 3: Analysis
1. Analyze publication trends
2. Identify key researchers
3. Map citation networks
4. Find consensus and controversies

### Phase 4: Synthesis
1. Group findings by theme
2. Create structured outline
3. Generate summary
4. Suggest future research directions

## Code Example

```typescript
// This skill would trigger this workflow
const topic = "CRISPR gene editing cancer therapy";

// Phase 1: Build query
const query = buildPubMedQuery(topic, {
  dateRange: "2020-2025",
  articleTypes: ["Clinical Trial", "Review"]
});

// Phase 2: Search
const results = await searchPubMed(query, { max_results: 100 });

// Phase 3: Analyze
const analysis = {
  totalArticles: results.count,
  yearDistribution: analyzeYears(results),
  topAuthors: identifyLeaders(results),
  keyFindings: extractThemes(results)
};

// Phase 4: Synthesize
const review = generateLiteratureReview(analysis);
```

## Error Handling

**Common Errors:**
- **No results found** → Broaden search query, try synonyms
- **Too many results (>10,000)** → Add more specific filters
- **API rate limit hit** → Use cached results, wait 1 second between requests
- **Abstract unavailable** → Skip to next article, note in summary
- **Database error** -> Retry connection, alert user if persistent

## Best Practices

1. **Start Broad, Then Narrow** - Begin with general search, refine based on initial results
2. **Use MeSH Terms** - Medical Subject Headings ensure comprehensive coverage
3. **Check Publication Dates** - Recent papers for current state, older for background
4. **Verify Source Quality** - Prioritize peer-reviewed journals, high impact factors
5. **Save As You Go** - Cache all results to SQLite for offline access
6. **Handle API Errors Gracefully** - Implement retry mechanisms and informative error messages
7. **Maintain a Consistent Caching Strategy** - Use a reliable key generation method to avoid redundant caching
8. **Provide Clear Progress Indicators** - Keep the user informed about the status of the literature review process.
9. **Allow User Customization** - Provide options to adjust search parameters, filters, and output formats.
10. **Adhere to Ethical Guidelines** - Properly cite sources and avoid plagiarism.

## Detailed Implementation Notes

The `buildPubMedQuery` function should be able to handle complex boolean logic, including AND, OR, and NOT operators. It should also be able to incorporate MeSH terms and other filters.

The `searchPubMed` function should implement proper error handling, including handling API rate limits and network errors. It should also cache the results locally to avoid redundant API calls.

The `analyzeYears` function should be able to handle missing data and outliers. It should also provide visualizations of the publication trends.

The `identifyLeaders` function should be able to identify key researchers based on multiple factors, including publication count, citation count, and h-index.

The `extractThemes` function should use natural language processing techniques to identify common themes and topics in the literature.

The `generateLiteratureReview` function should generate a well-structured and comprehensive literature review, including an introduction, methods section, results section, and discussion section. It should also provide clear and concise summaries of the key findings.

## Advanced Features

1. **Automated Citation Management:** Integrate with citation management tools like Zotero or Mendeley to automatically import and organize citations.
2. **Interactive Visualization:** Create interactive visualizations of the citation network, publication trends, and key findings.
3. **Personalized Recommendations:** Provide personalized recommendations for further reading based on the user's research interests.
4. **Collaboration Tools:** Allow multiple users to collaborate on a literature review project.
5. **Continuous Monitoring:** Continuously monitor the literature for new publications related to the user's research interests.

## Example Usage Scenarios

1. A researcher is writing a grant proposal on the role of the gut microbiome in autism spectrum disorder. They use this skill to conduct a comprehensive literature review on the topic, which helps them identify key research gaps and formulate their research questions.
2. A clinician is treating a patient with chronic pain. They use this skill to find the latest research on the efficacy of mindfulness-based interventions for chronic pain, which helps them make informed treatment decisions.
3. A student is writing a term paper on the impact of climate change on infectious diseases. They use this skill to gather relevant information and synthesize the findings into a well-structured paper.
4. A pharmaceutical company is exploring the use of AI in drug discovery. They use this skill to identify the latest research on the topic and assess the potential of AI to accelerate the drug discovery process.
5. A space agency is studying the effects of long-term space travel on bone density. They use this skill to review the literature on the topic and identify potential countermeasures to mitigate bone loss during space missions.

## Detailed Error Handling Strategies

1. **PubMed API Errors:**
   - **Rate Limiting:** Implement exponential backoff with jitter. If a 429 error is received, wait for a random amount of time between 1 and 2 seconds, then retry the request. Increase the waiting time exponentially for subsequent retries.
   - **Network Errors:** Implement retry logic with a maximum number of retries. Log the error and notify the user if the request fails after multiple retries.
   - **Invalid Query:** Provide informative error messages to the user if the search query is invalid. Suggest alternative search terms or filters.

2. **Database Errors:**
   - **Connection Errors:** Implement retry logic with a maximum number of retries. If the connection fails after multiple retries, alert the user and suggest restarting the application.
   - **Data Corruption:** Implement data validation checks to ensure that the data stored in the database is consistent and accurate. If data corruption is detected, attempt to repair the database or restore from a backup.
   - **Disk Space Issues:** Monitor disk space usage and alert the user if the database is running out of space. Suggest deleting old or unnecessary data.

3. **Natural Language Processing Errors:**
   - **Ambiguous Text:** Implement disambiguation techniques to resolve ambiguous text. Use contextual information to determine the meaning of the text.
   - **Unsupported Language:** Detect the language of the text and provide a warning if the language is not supported. Suggest translating the text to a supported language.
   - **Incorrect Theme Extraction:** Implement techniques to improve the accuracy of theme extraction. Use machine learning algorithms to train the system to identify common themes and topics in the literature.

4. **User Input Errors:**
   - **Invalid Search Terms:** Validate user input to ensure that it is valid. Provide informative error messages if the input is invalid.
   - **Unsupported Filters:** Provide a list of supported filters and their valid values. Validate user input to ensure that the filters are supported.
   - **Missing Information:** Prompt the user for missing information. Provide default