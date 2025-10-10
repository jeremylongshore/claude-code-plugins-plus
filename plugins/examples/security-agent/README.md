# Security Agent Plugin

A specialized security review subagent for identifying vulnerabilities and providing security guidance.

## Installation

```bash
/plugin install security-agent@claude-code-plugins
```

## Usage

The security reviewer agent will automatically activate when you:
- Ask Claude to review code for security issues
- Request a security audit
- Mention security concerns in your prompt

**Manual invocation**:
```
@security-reviewer Please review this authentication code for security vulnerabilities
```

## What It Reviews

- SQL injection vulnerabilities
- Cross-site scripting (XSS)
- Authentication/authorization flaws
- Input validation issues
- Cryptographic weaknesses
- Dependency vulnerabilities
- Secure coding practices

## Output

Provides structured security findings with:
- Severity ratings
- Specific code locations
- Impact assessment
- Remediation guidance
- Secure code examples

## Learning Objectives

This plugin demonstrates:
- Creating specialized subagents
- Defining agent capabilities
- Writing agent prompts
- Agent activation patterns

## Files

- `.claude-plugin/plugin.json` - Plugin manifest
- `agents/security-reviewer.md` - Agent definition

## License

MIT
