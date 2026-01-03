# perplexity-citation-handling

> Parse and display citations from Perplexity responses

## Directory Structure

```
perplexity-citation-handling/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── citation_parser.py      # Citation extraction and parsing
    ├── citation_display.tsx    # React component for citation display
    ├── link_validator.py       # Validate citation URLs
    └── citation_styles.css     # Styling for citation display
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with citation handling patterns |
| `citation_parser.py` | Python | Extract and parse citations from responses |
| `citation_display.tsx` | React/TSX | UI component for displaying citations |
| `link_validator.py` | Python | Validate citation URLs are accessible |
| `citation_styles.css` | CSS | Styling for citation presentation |

## Summary

**Category:** onboarding
**Target Audience:** Developer processing search results
**Trigger Phrases:** `perplexity citations`, `perplexity sources`, `perplexity references`, `show perplexity sources`

### What This Skill Does

This skill teaches citation handling from Perplexity responses:

- Understanding the citations array structure
- Extracting source URLs and metadata
- Linking inline references to citations
- Displaying citations in user interfaces
- Validating citation accessibility

### Technical Success Criteria

- Citations extracted, parsed, and displayed correctly
- Inline references linked to source citations
- Citation URLs validated and formatted

### Business Success Criteria

- User trust through transparent source attribution
- Professional presentation of research results
- Compliance with attribution requirements

## Related Skills

- `perplexity-hello-world` - Basic response parsing
- `perplexity-response-validation` - Validating response quality
- `perplexity-research-workflows` - Using citations in research
