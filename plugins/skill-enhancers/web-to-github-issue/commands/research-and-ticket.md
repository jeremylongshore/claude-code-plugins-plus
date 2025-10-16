---
name: research-and-ticket
description: Research topic via web search and auto-create GitHub issue with findings
aliases: [rat, ticket-research]
---

# Research and Create GitHub Issue

This command enhances Claude's `web_search` Skill by automatically creating a GitHub issue from research findings.

## Usage

```bash
# Basic usage (uses default repo from config)
research-and-ticket <topic>

# Specify repository
research-and-ticket <topic> --repo owner/repo

# Add custom labels
research-and-ticket <topic> --labels security,urgent

# Assign to team members
research-and-ticket <topic> --assignees user1,user2
```

## Examples

### Technical Research
```bash
research-and-ticket "PostgreSQL indexing best practices"
```

### Security Monitoring
```bash
research-and-ticket "React CVE vulnerabilities 2025" --labels security,urgent
```

### Feature Investigation
```bash
research-and-ticket "Stripe payment features comparison" --labels feature-request
```

## Configuration

Set your GitHub token:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Set default repository (optional):
```bash
# In your .env or shell profile
export GITHUB_DEFAULT_REPO=owner/repo
```

## What It Does

1. **Research Phase**: Uses Claude's `web_search` Skill to find relevant information
2. **Analysis Phase**: Extracts key points, detects priority, identifies actionable items
3. **Creation Phase**: Generates formatted GitHub issue with:
   - Research summary
   - Key findings with source links
   - Related topics
   - Next steps (if actionable)
   - All source references

## Output

The command creates a well-structured GitHub issue with:
- **Title**: Auto-generated based on topic and priority
- **Labels**: Research + custom labels + priority labels
- **Body**: Markdown-formatted with sections for findings, sources, and next steps
- **Links**: All source URLs preserved for reference

## Requirements

- Claude Code with web_search Skill enabled
- GitHub Personal Access Token with `repo` scope
- Node.js 18+ (for @octokit/rest dependency)

## Tips

- Use descriptive topics for better search results
- Add `--labels` to help with issue organization
- Review the created issue and edit if needed
- Use `--assignees` to immediately assign to team members

## Troubleshooting

**Error: GitHub token required**
- Set `GITHUB_TOKEN` environment variable
- Ensure token has `repo` scope

**Error: Repository not found**
- Check repo format: `owner/repo`
- Verify you have access to the repository
- Ensure repository has issues enabled

**No search results found**
- Try broader search terms
- Check internet connectivity
- Ensure web_search Skill is available
