# Granola Performance Tuning - Implementation Details

## Audio Quality Hierarchy
```
Transcription Accuracy
        ^
[Professional Microphone] 98%
        ^
[Quality Headset Mic] 95%
        ^
[Laptop Built-in Mic] 85%
        ^
[Phone Speaker] 70%
```

## Microphone Recommendations
- Budget (~$50): Blue Snowball iCE, Fifine K669
- Mid-Range (~$100): Blue Yeti, Rode NT-USB Mini, Audio-Technica AT2020USB+
- Professional (~$200+): Shure MV7, Elgato Wave:3, Rode PodMic + interface

## Room Optimization Checklist
- [ ] Close windows to reduce outside noise
- [ ] Turn off fans, AC if possible
- [ ] Use soft surfaces (carpet, curtains)
- [ ] Position away from keyboard clicks
- [ ] Mute when not speaking

## Meeting Best Practices for Accuracy
1. State names when addressing people: "Sarah, what do you think about..."
2. Summarize decisions verbally: "So we're agreed: deadline is Friday."
3. Spell out technical terms: "The API endpoint, A-P-I..."
4. Avoid crosstalk - one person speaking at a time
5. Use clear action item language: "Action item: Mike will review the PR by Thursday."

## Template Optimization

### Effective Template Structure
```markdown
# Meeting Template: Sprint Planning

## Agenda (Pre-filled)
-

## Context
[Add links to relevant docs]

## Discussion Notes
[AI-enhanced during meeting]

## Decisions
- [ ] Decision 1: [Clear statement]

## Action Items
Format: - [ ] What (@who, by when)

## Follow-up
Next meeting: [date]
```

### Template Impact
| Practice | Reason | Impact |
|----------|--------|--------|
| Use headers | Better AI parsing | +20% accuracy |
| Pre-fill context | Reduces ambiguity | +15% relevance |
| Standard formats | Consistent output | +10% usability |
| Action item format | Auto-extraction | +25% detection |

## Processing Speed Expectations
```
Meeting Duration -> Processing Time
15 minutes -> 1-2 minutes
30 minutes -> 2-3 minutes
60 minutes -> 3-5 minutes
120 minutes -> 5-8 minutes
```

## Integration Performance

### Zapier Optimization
1. Use Instant triggers (not polling)
2. Minimize steps in Zap
3. Avoid unnecessary filters
4. Use multi-step Zaps efficiently

### Batch Processing
```yaml
Schedule: Every 30 minutes
Process:
  - Collect all new notes
  - Batch update Notion
  - Single Slack summary
  - Aggregate CRM updates
```

## Accuracy Improvement Over Time
1. Correct errors when you see them (AI learns)
2. Use consistent terminology (builds vocabulary)
3. Identify speakers (improves attribution)
4. Regular editing (provides feedback loop)

## Custom Vocabulary
Add to meeting intros:
"We'll discuss the OAuth2 implementation, that's O-Auth-Two, and the GraphQL API, spelled G-R-A-P-H-Q-L..."

Common terms to spell out: Acronyms (API, SDK, CI/CD), product names, unusual name spellings.

## Weekly Performance Review
```markdown
Monday:
- [ ] Review last week's meeting notes
- [ ] Note common transcription errors
- [ ] Identify improvement opportunities
- [ ] Adjust templates if needed
```
