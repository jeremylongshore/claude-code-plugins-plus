---
name: cursor-usage-analytics
description: |
  Track and analyze Cursor usage metrics. Triggers on "cursor analytics",
  "cursor usage", "cursor metrics", "cursor reporting", "cursor dashboard".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Usage Analytics

## Analytics Overview

### Available Metrics (Business/Enterprise)
```
User Metrics:
- Active users (daily/weekly/monthly)
- User engagement levels
- Feature adoption rates
- Usage patterns by team

AI Metrics:
- Completions generated
- Completions accepted/rejected
- Chat messages sent
- Composer operations
- Model usage breakdown

Cost Metrics:
- API usage by model
- Cost per user
- Cost trends
- Budget utilization
```

### Accessing Analytics
```
Admin Dashboard > Analytics

Views:
- Overview dashboard
- User details
- Team breakdown
- Time-based trends
- Export options
```

## Key Metrics

### Completion Metrics
```
Completion Acceptance Rate:
= Accepted completions / Total completions × 100

Target: 40-60% is healthy
Low (<20%): May indicate poor context/rules
High (>80%): May indicate over-reliance

Completions per User:
Track productivity gains
Compare across teams
```

### Chat Metrics
```
Chat Sessions per Day:
- Average messages per session
- Time spent in chat
- Resolution rate

Useful queries:
- How many questions answered
- Code generated from chat
- Follow-up question rate
```

### Composer Metrics
```
Composer Usage:
- Operations per week
- Files modified per operation
- Apply rate (accepted vs rejected)
- Multi-file vs single-file edits
```

## Dashboard Views

### Executive Summary
```
┌─────────────────────────────────────────────────────────┐
│  CURSOR USAGE - EXECUTIVE SUMMARY                       │
├─────────────────────────────────────────────────────────┤
│  Active Users: 127/150 (85%)     │  Cost: $3,200/mo    │
│  Completions: 45,000 this month  │  Per User: $25.20   │
│  Acceptance Rate: 52%            │  Trend: ↓ 5%        │
├─────────────────────────────────────────────────────────┤
│  Top Features:                   │  Growth:            │
│  1. Tab Completion (78%)         │  Users: +12% MoM    │
│  2. Chat (65%)                   │  Usage: +23% MoM    │
│  3. Composer (34%)               │  Efficiency: +18%   │
└─────────────────────────────────────────────────────────┘
```

### Team Breakdown
```
Team Analytics View:

Engineering:
- Users: 45
- Avg completions/day: 120
- Primary model: GPT-4 Turbo
- Top use case: Code generation

Design:
- Users: 12
- Avg completions/day: 40
- Primary model: GPT-4
- Top use case: CSS/styling

Data Science:
- Users: 8
- Avg completions/day: 85
- Primary model: Claude
- Top use case: Python/analysis
```

### Individual User Metrics
```
User Detail View:

Username: developer@company.com
Role: Member
Last Active: 2 hours ago

30-Day Stats:
- Completions: 2,450
- Acceptance Rate: 58%
- Chat Sessions: 145
- Composer Uses: 23

Model Preferences:
- GPT-4 Turbo: 65%
- GPT-3.5: 30%
- Claude: 5%

Active Hours: 9am-6pm EST
```

## Custom Reports

### Creating Reports
```
Admin > Analytics > Custom Reports

Report Types:
- Usage summary (daily/weekly/monthly)
- User activity
- Cost breakdown
- Feature adoption
- Team comparison
```

### Scheduled Reports
```
Automate reporting:

1. Create report template
2. Set schedule (daily/weekly/monthly)
3. Add recipients
4. Choose format (PDF/CSV/Email)
5. Enable delivery

Example schedules:
- Weekly usage summary to managers
- Monthly cost report to finance
- Daily activity to team leads
```

### Export Options
```
Export formats:
- CSV (raw data)
- PDF (formatted report)
- JSON (API integration)

Export via:
- Dashboard download
- Scheduled export
- API endpoint
```

## Analytics API

### API Access
```bash
# Get usage summary
curl -X GET "https://api.cursor.com/v1/analytics/summary" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Available Endpoints
```
GET /analytics/summary
- Overall usage metrics

GET /analytics/users
- Per-user breakdown

GET /analytics/teams
- Team-level metrics

GET /analytics/features
- Feature adoption data

GET /analytics/costs
- Cost breakdown
```

### Integration Examples
```python
# Python integration
import requests

def get_cursor_analytics(start_date, end_date):
    response = requests.get(
        "https://api.cursor.com/v1/analytics/summary",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )
    return response.json()

# Use in dashboards, reports, etc.
```

## Benchmarking

### Industry Benchmarks
```
Typical ranges:

Completion Acceptance Rate:
- Low: < 30%
- Average: 40-55%
- High: > 60%

Daily Active Users:
- Low: < 50% of licenses
- Average: 60-75%
- High: > 80%

Features Used:
- Basic: Tab completion only
- Intermediate: + Chat
- Advanced: + Composer + Rules
```

### Internal Benchmarking
```
Compare teams:
- By department
- By experience level
- By project type
- Over time

Identify:
- Top performers (share practices)
- Training opportunities
- Underutilized features
```

## Optimization Insights

### Low Acceptance Rate
```
Causes & Solutions:

Poor context:
→ Improve .cursorrules
→ Better indexing setup

Wrong model:
→ Switch to more appropriate model
→ Adjust per-task settings

Lack of training:
→ Conduct workshops
→ Share best practices
```

### Underutilization
```
Signs:
- Low daily active users
- Only basic features used
- High cost per completion

Solutions:
- Training sessions
- Share success stories
- Optimize onboarding
- Gamify adoption
```

### High Costs
```
Investigation:
- Which models are expensive?
- Who are top users?
- What's the ROI?

Optimization:
- Default to cheaper models
- Set usage guidelines
- Implement budgets
- Track productivity gains
```

## Privacy & Compliance

### Data Collected
```
Analytics tracks:
- Usage patterns (aggregated)
- Feature adoption
- Performance metrics
- Cost data

Does NOT track:
- Code content
- Chat conversations
- Personal data beyond email
```

### Compliance Features
```
GDPR:
- Data export capability
- Deletion support
- Consent management

SOC 2:
- Audit logs
- Access controls
- Data retention policies
```

## Best Practices

### Regular Review
```
Weekly:
- Check active user trends
- Monitor unusual patterns
- Review top users

Monthly:
- Full analytics review
- Cost analysis
- Feature adoption check
- Generate reports

Quarterly:
- Deep dive analysis
- ROI calculation
- Strategy adjustment
- Benchmark comparison
```

### Acting on Insights
```
Data → Action:

Low adoption → Training program
High costs → Model optimization
Feature gaps → Targeted workshops
Power users → Champions program
```
