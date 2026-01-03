# Architecture Review Workflow

> BMAD-compatible workflow for reviewing Claude Code plugin architecture

## Overview

This workflow guides you through reviewing plugin architecture using Architect, Security, and Reviewer agents. Identifies issues, security concerns, and improvement opportunities.

## Prerequisites

- Existing plugin codebase
- Access to plugin.json and source files
- Understanding of review criteria

## Phase 1: Analysis (Architect Agent)

### 1.1 Structure Analysis

```
As the Architect agent, analyze structure:

1. Review plugin.json manifest
2. Map component relationships
3. Identify architectural patterns
4. Document data flows
```

### 1.2 Analysis Checklist

**Plugin Structure**
- [ ] plugin.json is valid and complete
- [ ] Directory structure follows conventions
- [ ] Commands are properly organized
- [ ] Skills follow 2025 schema

**Code Organization**
- [ ] Clear separation of concerns
- [ ] Minimal coupling between components
- [ ] Consistent naming conventions
- [ ] Appropriate abstraction levels

**Dependencies**
- [ ] Minimal external dependencies
- [ ] No vulnerable dependencies
- [ ] Proper version pinning
- [ ] License compatibility

### 1.3 Architecture Map

Create visual or textual map:

```
plugin/
├── .claude-plugin/
│   └── plugin.json      [Manifest - defines entry points]
├── commands/
│   └── *.md             [User-invoked slash commands]
├── skills/
│   └── */SKILL.md       [Auto-activated capabilities]
├── agents/
│   └── *.md             [Specialized AI personas]
└── hooks/
    └── hooks.json       [Event-driven automation]
```

---

## Phase 2: Security Review (Security Agent)

### 2.1 Security Scan

```
As the Security agent, review for:

1. Input validation gaps
2. Command injection risks
3. Data exposure issues
4. Permission escalation
```

### 2.2 Security Checklist

**Input Handling**
- [ ] All user inputs validated
- [ ] Path traversal prevented
- [ ] Command injection blocked
- [ ] SQL/NoSQL injection prevented

**Data Security**
- [ ] No hardcoded secrets
- [ ] Sensitive data not logged
- [ ] Proper data sanitization
- [ ] Secure storage patterns

**Permissions**
- [ ] Minimal tool access in skills
- [ ] Appropriate file system access
- [ ] Network access justified
- [ ] No privilege escalation

**MCP Security** (if applicable)
- [ ] Tool inputs validated with Zod
- [ ] Error messages don't leak info
- [ ] Rate limiting considered
- [ ] Auth tokens secured

### 2.3 Security Findings Template

```markdown
## Security Finding

**Severity**: Critical / High / Medium / Low
**Location**: [file:line]
**Issue**: [description]
**Risk**: [potential impact]
**Recommendation**: [fix approach]
**References**: [OWASP, CWE, etc.]
```

---

## Phase 3: Review & Recommendations (Reviewer Agent)

### 3.1 Quality Assessment

```
As the Reviewer agent, assess:

1. Code quality and maintainability
2. Documentation completeness
3. Test coverage
4. Performance considerations
```

### 3.2 Quality Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Cyclomatic complexity | < 10 | | |
| Documentation coverage | > 80% | | |
| Test coverage | > 70% | | |
| Dependency freshness | < 6 months | | |

### 3.3 Review Report Template

```markdown
# Architecture Review Report

## Summary
- **Plugin**: [name]
- **Version**: [version]
- **Reviewer**: [agent/person]
- **Date**: [date]
- **Overall Rating**: [1-5 stars]

## Findings

### Critical Issues
1. [Issue with recommendation]

### Improvements Recommended
1. [Improvement suggestion]

### Strengths
1. [What's working well]

## Architecture Score

| Category | Score (1-5) | Notes |
|----------|-------------|-------|
| Structure | | |
| Security | | |
| Maintainability | | |
| Performance | | |
| Documentation | | |

## Action Items

- [ ] [Immediate action]
- [ ] [Short-term improvement]
- [ ] [Long-term consideration]
```

---

## Outputs

After completing this workflow:

1. **architecture-map.md** - Component relationships
2. **security-findings.md** - Security issues and risks
3. **review-report.md** - Complete assessment
4. **action-items.md** - Prioritized improvements

## Integration with MCP Servers

| Server | Use Case |
|--------|----------|
| project-health-auditor | Automated metrics |
| conversational-api-debugger | API review |
| domain-memory-agent | Store findings |

## Quick Review Commands

```bash
# Run automated health check
/project-health check

# Analyze complexity
/project-health complexity

# Security scan
/security scan
```

---

*Part of Claude Code Plugins Marketplace - https://claudecodeplugins.io/*
