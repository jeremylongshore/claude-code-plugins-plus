# Supabase Rate Limits & Quotas by Tier and Surface

Every Supabase project has per-surface limits that differ by plan. Know these numbers before you architect.

**API Request Limits**

| Metric | Free | Pro | Enterprise |
|--------|------|-----|------------|
| Requests per minute (RPM) | 500 | 5,000 | Unlimited (custom) |
| Requests per day (RPD) | 50,000 | 1,000,000 | Unlimited (custom) |

**Auth Rate Limits**

| Endpoint | Free | Pro |
| ---------- | ------ | ----- |
| Signup | 30/hour per IP | Higher (configurable) |
| Sign-in (password) | 30/hour per IP | Higher (configurable) |
| Magic link / OTP | 4/hour per user | Configurable |
| Token refresh | 360/hour | 360/hour |

Auth limits are per-IP and per-user. Configure custom limits in Dashboard > Authentication > Rate Limits.

**Storage Bandwidth**

| Metric | Free | Pro |
| -------- | ------ | ----- |
| Storage size | 1 GB | 100 GB |
| Bandwidth | 2 GB/month | 250 GB/month |
| Max file size | 50 MB | 5 GB |
| Upload rate | Shared with API RPM | Shared with API RPM |

**Realtime Connections**

| Metric | Free | Pro |
| -------- | ------ | ----- |
| Concurrent connections | 200 | 500 |
| Messages per second | 100 | 500 |
| Channel joins | Shared with connection limit | Shared |

**Edge Functions**

| Metric | Free | Pro |
| -------- | ------ | ----- |
| Invocations/month | 500,000 | 2,000,000 |
| Execution time | 150s wall / 50ms CPU | 150s wall / 2s CPU |
| Memory | 256 MB | 256 MB |

**Database Connections**

| Mode | Free | Pro |
|------|------|-----|
| Direct connections | 60 | 100+ |
| Pooled connections (Supavisor) | 200 | 1,500+ |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
