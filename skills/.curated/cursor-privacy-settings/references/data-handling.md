# Data Handling

## Data Handling

### What Data is Processed

```
When Privacy Mode OFF:

Sent to AI:
- Code in context (selected/open files)
- Chat messages
- File contents for @-mentions
- Project structure (for indexing)

NOT sent:
- Full codebase (only indexed locally)
- Credentials (if properly excluded)
- Binary files
- Files in .cursorignore
```

### Data Retention

```
Cursor's data policy:
- Code not stored long-term
- Conversations not used for training (Business/Enterprise)
- Logs retained temporarily for debugging
- Indexing data stored locally only

AI Provider policies:
- OpenAI: No training on API data
- Anthropic: No training on API data
- Check current policies for specifics
```
