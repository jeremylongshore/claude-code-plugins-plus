# Context Files

The over-50s-health-advisor agent uses local Markdown files to maintain health context, preferences, and session
history. This approach keeps personal health information private and under the user's control.

## Architecture

### Templates (This Repository)

This repository contains template files in `context/templates/`:

- `INITIAL_USER_INFORMATION.md`
- `CLIENT_HEALTH_CONTEXT.md`
- `CLIENT_PREFERENCES.md`
- `SESSION_NOTES.md`
- `SOURCES.md`

These templates provide structure and examples but contain no real user data. When the plugin is installed, the
`SessionStart` hook copies them to `~/.claude/over-50s-health-advisor/templates/` before each session so the agent
can read them without needing to know the version-specific plugin cache location.

### User Context Files

On the first conversation, the agent creates personal context files at:

```text
~/.claude/over-50s-health-advisor/context/
├── INITIAL_USER_INFORMATION.md
├── CLIENT_HEALTH_CONTEXT.md
├── CLIENT_PREFERENCES.md
├── SESSION_NOTES.md
└── SOURCES.md
```

These files contain actual health information and are never committed to version control.
Reinstalling or updating the plugin never touches these files.

## Context File Descriptions

### INITIAL_USER_INFORMATION.md

Basic demographic and goal information:

- Age, sex, primary goals
- Current activity level
- Time and equipment availability
- Initial questions or concerns

### CLIENT_HEALTH_CONTEXT.md

Medical and health history:

- Conditions, medications, surgeries
- Injuries, limitations, contraindications
- Recent lab results or trends
- Healthcare provider information

### CLIENT_PREFERENCES.md

Preferences for guidance:

- Preferred units (imperial/metric)
- Dietary preferences or restrictions
- Exercise preferences
- Communication style preferences

### SESSION_NOTES.md

Chronological log of interactions:

- Date-stamped session summaries
- Key decisions or plans made
- Progress updates
- Questions for follow-up

### SOURCES.md

Curated list of evidence-based resources:

- High-quality sources the agent has cited
- Personal research findings
- Clinician-provided resources

## Required vs Optional Context

**Required** (minimum for personalized guidance):

- `INITIAL_USER_INFORMATION.md`
- `CLIENT_PREFERENCES.md`

**Optional** but strongly recommended:

- `CLIENT_HEALTH_CONTEXT.md`
- `SESSION_NOTES.md`
- `SOURCES.md`

## Privacy and Data Management

- All context files are stored locally on the user's machine
- Files are in plain Markdown format (readable, editable with any text editor)
- The user has full control to view, edit, or delete any information
- No data is sent to external services except when the agent performs web searches (which do not include context files)
- The agent only accesses these files when invoked

## Context Budget Management

The agent aims to keep total context under 2,000 words to ensure efficient processing. The agent will:

- Monitor total word count across all context files at the start of each session
- Archive older SESSION_NOTES entries automatically when approaching the limit
- Request approval before pruning `INITIAL_USER_INFORMATION.md` or `CLIENT_PREFERENCES.md`

## Artifact Ingestion

Lab reports, CSV files, or other documents can be provided for the agent to analyze. The agent will:

- Ask for consent before extracting and storing summaries
- Store only relevant, minimal data in context files
- Reference the artifact and extraction date in `SESSION_NOTES.md` or `CLIENT_HEALTH_CONTEXT.md`

## Editing Context Files

Context files can be edited directly with any text editor. The agent treats edits as authoritative updates.
Common workflows:

```bash
# Add new health information
nano ~/.claude/over-50s-health-advisor/context/CLIENT_HEALTH_CONTEXT.md

# Review past sessions
cat ~/.claude/over-50s-health-advisor/context/SESSION_NOTES.md

# Update preferences
code ~/.claude/over-50s-health-advisor/context/CLIENT_PREFERENCES.md
```
