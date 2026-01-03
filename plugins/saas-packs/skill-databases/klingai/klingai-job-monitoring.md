# klingai-job-monitoring

> Monitor and track Kling AI video generation jobs

## Directory Structure

```
klingai-job-monitoring/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 job_tracker.py          # Job tracking implementation
    ├── 🐍 status_dashboard.py     # Dashboard data generation
    └── 🐍 alerting.py             # Alert configuration
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with job monitoring guide |
| `job_tracker.py` | 🐍 Python | Track multiple concurrent jobs |
| `status_dashboard.py` | 🐍 Python | Generate dashboard metrics |
| `alerting.py` | 🐍 Python | Configure alerts for job failures |

## Summary

**Category:** operations
**Target Audience:** Developer managing multiple jobs
**Trigger Phrases:** `klingai monitor`, `kling ai job status`, `track klingai jobs`, `klingai dashboard`

### What This Skill Does

This skill establishes job monitoring for Kling AI video generation. It covers:

- Multi-job tracking with status management
- Real-time status polling and updates
- Dashboard metrics and visualizations
- Alerting on job failures or delays
- Historical job data and analytics
- Progress tracking for batch operations

### Technical Success Criteria

- Real-time job status tracking and alerting
- Dashboard displaying job metrics
- Historical data for analysis

### Business Success Criteria

- Operational visibility into video generation
- Proactive issue detection through alerts
- Data-driven capacity planning

## Related Skills

- `klingai-batch-processing` - Batch job monitoring
- `klingai-webhook-config` - Event-driven status updates
- `klingai-usage-analytics` - Advanced analytics
