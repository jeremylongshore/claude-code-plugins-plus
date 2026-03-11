# Granola Reference Architecture - Implementation Details

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      MEETING ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│  Google Calendar  │  Zoom  │  Microsoft Teams                    │
│         └──────────────┬──────────────┘                         │
│                   ┌────▼────┐                                    │
│                   │ GRANOLA │ (Capture, Transcribe, Summarize)   │
│                   └────┬────┘                                    │
│                   ┌────▼────┐                                    │
│                   │ ZAPIER  │ (Middleware/Routing)               │
│                   └────┬────┘                                    │
│    ┌───────┬──────┬────┴────┬────────┬──────────┐               │
│    Slack  Notion  HubSpot  Linear  Analytics                    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Patterns

### Pattern 1: Standard Meeting
Meeting Ends -> Granola Processes (2 min) -> Zapier Trigger -> Parallel: Slack notify + Notion archive + Linear tasks

### Pattern 2: Client Meeting (external attendee detected)
CRM Path: HubSpot note + Contact update + Deal activity + Follow-up task
Plus Standard Path: Notion archive + Slack notify

### Pattern 3: Executive Meeting (VP+ attendee)
High-Touch Path: Private Notion + EA notification + Action tracking + No public Slack

## Enterprise Multi-Workspace Architecture
```
Enterprise Granola Deployment
├── Corporate Workspace (Executive, Leadership, Board)
├── Engineering Workspace (Sprint Planning, Tech Reviews, Syncs)
├── Sales Workspace (Client Calls, Demos, QBRs)
└── HR Workspace (Interviews, Reviews, Training)
```

### Access Control Matrix
| Workspace | Visibility | Sharing | SSO Group |
|-----------|------------|---------|-----------|
| Corporate | Private | Executive only | exec-team |
| Engineering | Team | Engineering + PM | engineering |
| Sales | Team + CRM | Sales + Success | sales |
| HR | Confidential | HR only | hr-team |

### Integration Per Workspace
```yaml
Corporate: Notion (private), Slack (#exec-team private), No CRM
Engineering: Notion (wiki), Slack (#dev-meetings), Linear (auto-tasks), GitHub
Sales: Notion (playbook), Slack (#sales-updates), HubSpot (full sync)
HR: Notion (confidential), Slack (HR DMs only), Greenhouse (if recruiting)
```

## Security Architecture

### Data Classification
| Data Type | Classification | Handling |
|-----------|---------------|----------|
| Transcripts | Confidential | Encrypted, access-controlled |
| Summaries | Internal | Team-shared |
| Action Items | Internal | Public within org |
| Attendee Names | PII | GDPR compliant |

Encryption: AES-256 at rest, TLS 1.3 in transit. RBAC + SSO access control. Full audit logging.

## Scalability

| Team Size | Meetings/Month | Storage/Year | Plan |
|-----------|---------------|--------------|------|
| 1-10 | 100-500 | 5-25 GB | Pro |
| 10-50 | 500-2500 | 25-125 GB | Business |
| 50-200 | 2500-10000 | 125-500 GB | Enterprise |

### Performance Budgets
| Metric | Target |
|--------|--------|
| Note availability | < 3 min post-meeting |
| Integration latency | < 1 min Zapier to destination |
| Search response | < 500 ms |
| Export time | < 30 sec |

## Disaster Recovery
- Primary: Granola cloud storage
- Secondary: Nightly export to company storage
- Tertiary: Weekly archive to cold storage
- RPO: 24 hours, RTO: 4 hours

### Failover
If Granola unavailable: manual notes during meeting, record with backup tool, transcribe post-meeting, upload when restored.
