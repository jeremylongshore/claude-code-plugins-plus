# Severity Level Reference

## S1 — Critical

**Definition:** System-down, active data loss, or confirmed security breach requiring immediate response.

**Indicators:**
- Production system completely unavailable
- Active data corruption or loss
- Confirmed security exploitation in progress
- No workaround exists
- Affects all or most users

**Response:** Immediate — all hands on deck

**Examples:**
- SQL injection actively being exploited
- Database corruption causing data loss
- Authentication bypass allowing unauthorized access
- Complete service outage

## S2 — High

**Definition:** Major functionality broken or security vulnerability with high exploitability requiring urgent resolution.

**Indicators:**
- Core feature non-functional
- Security vulnerability with known exploit path
- Data integrity at risk but not actively compromised
- Workaround exists but is impractical for most users

**Response:** Within 4 hours

**Examples:**
- Payment processing failing for subset of users
- XSS vulnerability in user input fields
- API rate limiting completely broken
- User sessions not expiring properly

## S3 — Medium

**Definition:** Degraded functionality with reasonable workaround available, scheduled for normal fix cycle.

**Indicators:**
- Feature works but with reduced capability
- Security issue with limited scope or low exploitability
- Workaround is available and practical
- Affects a subset of users or use cases

**Response:** Within 24 hours

**Examples:**
- Search results occasionally missing items
- CSRF token not rotating on session refresh
- Export feature produces incorrect formatting
- Mobile layout broken on specific device

## S4 — Low

**Definition:** Minor issue, cosmetic defect, or enhancement request for the backlog.

**Indicators:**
- Cosmetic or UI inconsistency
- Documentation error
- Enhancement request
- Edge case with minimal user impact

**Response:** Backlog prioritization

**Examples:**
- Typo in error message
- Button color inconsistent with design system
- Feature request for additional export format
- Tooltip text truncated on hover
