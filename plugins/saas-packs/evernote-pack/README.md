# Evernote Skill Pack

> Claude Code skill pack for Evernote Cloud API integration (24 skills)

## Installation

```bash
/plugin install evernote-pack@claude-code-plugins-plus
```

## About Evernote

[Evernote](https://evernote.com) is a note-taking and knowledge management platform with a Thrift-based Cloud API. The API provides access to notes, notebooks, tags, resources (attachments), and search via the NoteStore and UserStore services. Notes use ENML (Evernote Markup Language), a restricted XHTML subset.

**Key facts:**
- Thrift-based API with SDKs for JavaScript, Python, Java, iOS, Android
- Authentication: OAuth 1.0a (developer tokens for sandbox)
- Content format: ENML (XML with DOCTYPE, restricted elements)
- Rate limits: per API key, per user, with `rateLimitDuration` in error response
- Sandbox environment at sandbox.evernote.com
- Developer portal at [dev.evernote.com](https://dev.evernote.com/)

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `evernote-install-auth` | OAuth 1.0a setup, SDK installation, developer tokens |
| `evernote-hello-world` | Create first note with ENML format and NoteStore |
| `evernote-local-dev-loop` | Sandbox testing, Express OAuth server, ENML helpers |
| `evernote-sdk-patterns` | NoteFilter search, attachments, batch ops, error wrapping |
| `evernote-core-workflow-a` | Note creation, ENML formatting, notebook/tag management |
| `evernote-core-workflow-b` | Search grammar, QueryBuilder, pagination, related notes |
| `evernote-common-errors` | EDAMUserException/SystemException/NotFoundException |
| `evernote-debug-bundle` | Request logging, ENML validator, token inspector |
| `evernote-rate-limits` | rateLimitDuration handling, request queuing, batching |
| `evernote-security-basics` | OAuth hardening, AES-256 token encryption, CSRF |
| `evernote-prod-checklist` | Production readiness with verification script |
| `evernote-upgrade-migration` | SDK version upgrades and breaking changes |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `evernote-ci-integration` | GitHub Actions, mocked NoteStore tests |
| `evernote-deploy-integration` | Docker, AWS, GCP deployment patterns |
| `evernote-webhooks-events` | Webhook endpoint, sync state USN tracking |
| `evernote-performance-tuning` | Caching, metadata-only queries, sync chunks |
| `evernote-cost-tuning` | Quota management, resource optimization |
| `evernote-reference-architecture` | Production architecture with sync pipeline |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `evernote-multi-env-setup` | Dev/staging/prod with sandbox and production keys |
| `evernote-observability` | API metrics, latency tracking, quota monitoring |
| `evernote-incident-runbook` | Auth failures, rate limits, sync issues |
| `evernote-data-handling` | ENML processing, sync pipeline, data export |
| `evernote-enterprise-rbac` | Business accounts, shared notebooks, team access |
| `evernote-migration-deep-dive` | Bulk data migration and platform transitions |

## Quick Start

```javascript
const Evernote = require('evernote');

// Initialize with developer token (sandbox)
const client = new Evernote.Client({
  token: process.env.EVERNOTE_DEV_TOKEN,
  sandbox: true,
});

// Create a note
const noteStore = client.getNoteStore();
const note = new Evernote.Types.Note();
note.title = 'Hello from Claude Code';
note.content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><p>Created via the Evernote API!</p></en-note>`;

const created = await noteStore.createNote(note);
console.log('Note GUID:', created.guid);
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| NoteStore | Note, notebook, tag, and resource CRUD |
| UserStore | User accounts and authentication |
| ENML | XML-based content format (restricted XHTML) |
| Resources | File attachments with MD5 hash references |
| USN | Update Sequence Numbers for incremental sync |
| Search Grammar | `notebook:`, `tag:`, `intitle:`, `created:`, `todo:` operators |

## Resources

- [Evernote Developer Portal](https://dev.evernote.com/)
- [API Documentation](https://dev.evernote.com/doc/)
- [NoteStore Reference](https://dev.evernote.com/doc/reference/NoteStore.html)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Search Grammar](https://dev.evernote.com/doc/articles/search_grammar.php)
- [JavaScript SDK](https://github.com/Evernote/evernote-sdk-js)
- [Python SDK](https://github.com/Evernote/evernote-sdk-python)

## License

MIT
