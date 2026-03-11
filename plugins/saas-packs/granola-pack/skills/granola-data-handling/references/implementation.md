# Granola Data Handling - Implementation Details

## Data Locations
```
Granola Data Storage
├── Cloud Storage (Primary): Notes, Summaries, Transcripts, Metadata
├── Temporary Storage: Audio (processing), Upload queue
└── Local Cache (Device): Recent notes, App settings
```

## Export Formats

### Markdown Export
```markdown
# Meeting Title
**Date:** January 6, 2025
**Duration:** 45 minutes
**Attendees:** Sarah Chen, Mike Johnson

## Summary
[AI-generated summary]

## Action Items
- [ ] Task 1 (@assignee, due: date)

## Transcript
[Full transcript if included]
```

### JSON Export
```json
{
  "export_version": "1.0",
  "export_date": "2025-01-06T15:00:00Z",
  "meetings": [{
    "id": "note_abc123",
    "title": "Sprint Planning",
    "date": "2025-01-06",
    "attendees": [{"name": "Sarah Chen", "email": "sarah@company.com"}],
    "summary": "Discussed Q1 priorities...",
    "action_items": [{"text": "Review PRs", "assignee": "mike", "due": "2025-01-08"}]
  }]
}
```

## Retention Policy Template
```yaml
Default:
  notes: 365 days
  transcripts: 90 days
  audio: delete_after_processing

By Workspace:
  HR: { notes: 730 days, transcripts: 30 days, audio: delete_immediately }
  Sales: { notes: 365 days, transcripts: 90 days, audio: 30 days }
  Engineering: { notes: 180 days, transcripts: 7 days, audio: delete_after_processing }
```

## GDPR Rights Implementation
| Right | Implementation | Process |
|-------|---------------|---------|
| Access | Data export | Self-service export |
| Rectification | Edit notes | User can edit |
| Erasure | Delete account | Settings > Delete |
| Portability | JSON export | Full data download |
| Objection | Opt-out | Don't record specific meetings |

## Subject Access Request (SAR) Process
1. Receive request, verify identity, log with timestamp
2. Search by email across all workspaces including shared notes
3. Export user's data (JSON) with metadata and third-party sharing documentation
4. Deliver within 30 days via secure method in readable format
5. Log response date and store proof of delivery

## Data Deletion Request (Right to Be Forgotten)
1. Verify identity with email confirmation
2. Scope: all personal data, shared notes (mark deleted, retain structure), integration data
3. Execute: delete from primary, delete from backups within 30 days, revoke integrations
4. Confirm with requestor, provide confirmation ID

## DPA Checklist
Granola provides: Standard DPA template, SCCs, sub-processor list, security documentation, breach notification procedures.
Company must: Sign DPA, update privacy policy, obtain consent for recording, train staff.

## CCPA Compliance
Meeting recording notice for invites: "This meeting may be recorded using Granola AI for note-taking purposes. By attending, you consent to recording."

## Data Security
| State | Method | Standard |
|-------|--------|----------|
| At Rest | AES-256 | Industry standard |
| In Transit | TLS 1.3 | Latest protocol |

## Access Controls
| Role | Notes | Transcripts | Audio | Admin |
|------|-------|-------------|-------|-------|
| Owner | RWD | RWD | RD | Full |
| Admin | RW | RW | R | Limited |
| Member | RW | R | - | None |
| Viewer | R | - | - | None |

## Archival Strategy
Monthly: Export notes > 6 months old (JSON), store in company archive (GCS/S3 Glacier), verify integrity, delete from Granola, update archive index. Retention: 7 years.
