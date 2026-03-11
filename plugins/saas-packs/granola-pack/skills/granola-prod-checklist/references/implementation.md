# Granola Production Checklist - Implementation Details

## Security Configuration
```markdown
## Security Setup
- [ ] SSO configured (Business/Enterprise)
- [ ] 2FA enforced for all users
- [ ] Password policy defined
- [ ] IP allowlisting configured (if required)
- [ ] Data residency settings verified
- [ ] DPA signed (GDPR requirement)
- [ ] Audit logging enabled
```

## Integration Setup
```markdown
## Required Integrations
- [ ] Calendar integration (Google/Outlook)
- [ ] Communication (Slack/Teams)
- [ ] Documentation (Notion/Confluence)
- [ ] CRM (HubSpot/Salesforce) if applicable
- [ ] Task management (Linear/Jira) if applicable
- [ ] Zapier workflows configured
```

## Training Plan
```markdown
Week 1:
- [ ] Admin training (2 hours)
- [ ] Power user training (1 hour)

Week 2:
- [ ] General user training (30 min)
- [ ] Q&A sessions scheduled

Ongoing:
- [ ] Monthly tips newsletter
- [ ] Quarterly feature updates
```

## Pilot Program
```markdown
## Pilot Phase (Recommended)
- [ ] Select 5-10 pilot users
- [ ] Define success metrics
- [ ] Set 2-week pilot duration
- [ ] Collect feedback daily
- [ ] Address issues before full rollout
- [ ] Document lessons learned
```

## Workspace Configuration
```markdown
- [ ] Workspace name and branding set
- [ ] Default sharing permissions configured
- [ ] Data retention policy defined
- [ ] Auto-recording preferences set
- [ ] Template library created
- [ ] Default note format selected
```

## Admin Controls
```markdown
- [ ] User roles defined
- [ ] Permission groups created
- [ ] External sharing policy set
- [ ] Integration permissions controlled
- [ ] Audit log retention configured
```

## Technical Requirements

### Desktop Requirements
- macOS 12 (Monterey) or later
- Windows 10 (1903) or later
- 8 GB RAM minimum (16 GB recommended)
- 500 MB free disk space
- Stable internet (5 Mbps+)

### Network Configuration
Allow outbound HTTPS to:
- api.granola.ai
- app.granola.ai
- storage.granola.ai
- auth.granola.ai

Ports: 443 (HTTPS required), 80 (redirect only)

### MDM/Deployment
```markdown
- [ ] MSI/PKG package available
- [ ] Silent install tested
- [ ] Auto-update policy set
- [ ] Configuration profile created
- [ ] Deployment script verified
```

## Go-Live Sequence

### Day Before Launch
- [ ] All users provisioned
- [ ] Welcome emails scheduled
- [ ] Support team briefed
- [ ] Status page monitored
- [ ] Rollback plan documented

### Launch Day
- [ ] Send welcome emails
- [ ] Enable user access
- [ ] Monitor adoption metrics
- [ ] Staff support channel
- [ ] Track first-meeting success

### Week 1 Post-Launch
- [ ] Daily adoption metrics review
- [ ] Quick wins shared internally
- [ ] Issues triaged within 4 hours
- [ ] User feedback collected

## Success Metrics

### Adoption KPIs
| Metric | Target | Measurement |
|--------|--------|-------------|
| User activation | 80% in Week 1 | First meeting recorded |
| Daily active users | 60% | Weekly average |
| Meetings captured | 70% of eligible | Automatic detection |
| Integration usage | 50% | Using at least one |

### Quality KPIs
| Metric | Target | Measurement |
|--------|--------|-------------|
| Note satisfaction | 4.0/5.0 | User rating |
| Transcription accuracy | 95% | Spot check |
| Support tickets | < 5% of users | Weekly |
| Uptime | 99.9% | Status page |

## Ongoing Operations
```markdown
Daily:
- [ ] Monitor status page
- [ ] Review support queue

Weekly:
- [ ] Adoption metrics review
- [ ] User feedback triage

Monthly:
- [ ] Feature update review
- [ ] Usage report generation
- [ ] Billing reconciliation
```
