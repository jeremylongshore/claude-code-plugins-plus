# Examples

## Example 1: Minimal Backend API Spec

A focused spec for a single-domain API with clear scope boundaries and
mandatory QA testing.

```markdown
# Sprint 1: Authentication API

## Goal
Add email/password authentication with JWT tokens and refresh token rotation.

## Scope
### In Scope
- POST /auth/register (email + password, validate format)
- POST /auth/login (return access + refresh tokens)
- POST /auth/refresh (rotate refresh token, issue new access token)
- POST /auth/logout (invalidate refresh token)
- Password hashing with bcrypt (min 10 rounds)
- JWT access token (15min expiry, HS256)
- Refresh token stored in database (7-day expiry)

### Out of Scope
- OAuth providers (Google, GitHub, Apple)
- Password reset flow
- Email verification
- Rate limiting (separate sprint)
- Admin user management

## Testing
- QA: required
- UI Testing: skip
- UI Testing Mode: automated
```

**Why this works:**

- Goal is one sentence describing the deliverable
- In Scope lists every endpoint with its behavior
- Out of Scope prevents agent drift toward OAuth or email flows
- QA is required (API endpoints need automated tests)
- UI Testing is skipped (no frontend changes)

## Example 2: Frontend-Only Spec with Manual UI Testing

A spec for visual UI changes where automated E2E tests cannot easily
verify the result and manual inspection is needed.

```markdown
# Sprint 5: Dark Mode Support

## Goal
Add dark mode with system preference detection and manual toggle.

## Scope
### In Scope
- CSS custom properties for all color tokens (light and dark variants)
- Dark mode toggle button in the header nav
- System preference detection via prefers-color-scheme media query
- Persist user preference in localStorage
- Smooth transition animation between themes (200ms)
- Update all existing components to use color tokens instead of hardcoded values

### Out of Scope
- New components or layouts
- API changes
- Database changes
- Third-party theme libraries

## Testing
- QA: skip
- UI Testing: required
- UI Testing Mode: manual
```

**Why manual testing is appropriate here:**

- Visual correctness (contrast, readability) requires human eyes
- Theme transitions need subjective quality assessment
- System preference detection needs OS-level interaction
- QA is skipped because there are no API or logic changes

## Example 3: Full-Stack Feature Spec

A spec covering both backend and frontend work with parallel agent execution
and both QA and automated UI testing.

```markdown
# Sprint 3: Product Search

## Goal
Full-text product search with type-ahead suggestions and faceted filtering.

## Scope
### In Scope
- **Backend:**
  - POST /api/search (full-text query with filters, pagination)
  - GET /api/search/facets (available filter options with counts)
  - Elasticsearch integration for indexing and querying
  - Product indexing triggered on create/update/delete
- **Frontend:**
  - Search bar with debounced type-ahead (300ms)
  - Facet sidebar with checkbox filters (category, price range, rating)
  - Search results grid with pagination (20 items per page)
  - Empty state when no results match
  - Loading skeleton during search execution
- **Shared:**
  - SearchRequest and SearchResponse TypeScript interfaces
  - FacetGroup type definition for filter categories

### Out of Scope
- Search analytics or query logging
- Saved searches or search history
- Autocomplete from external suggestion APIs
- Image search or visual similarity
- Search result caching (handle in a performance sprint)

## Testing
- QA: required
- UI Testing: required
- UI Testing Mode: automated
```

**Why this works:**

- Scope is partitioned by domain (Backend / Frontend / Shared)
- Each agent gets a clear boundary
- Shared types are called out so both agents reference the same contract
- Both QA and UI testing are required (backend logic + frontend interactions)

## Example 4: Iterative Spec After First Iteration

A spec that has been narrowed based on iteration 1 results. Completed items
are removed and only remaining work and fixes are listed.

**Original specs.md (before sprint):**

```markdown
# Sprint 2: User Dashboard

## Goal
Build a user dashboard showing recent activity, notifications, and account settings.

## Scope
### In Scope
- Activity feed (last 30 days, paginated)
- Notification center (unread count badge, mark-as-read)
- Account settings page (name, email, avatar upload)
- Responsive layout (mobile, tablet, desktop)

### Out of Scope
- Admin dashboard
- Real-time WebSocket updates
- Email notification preferences

## Testing
- QA: required
- UI Testing: required
- UI Testing Mode: automated
```

**Updated specs.md (after iteration 1, 2 items remaining):**

```markdown
# Sprint 2: User Dashboard (Iteration 2)

## Goal
Fix remaining issues from iteration 1.

## Scope
### In Scope
- **Fix: Notification mark-as-read** — PATCH /api/notifications/:id returns 500
  when notification is already read. Should return 200 with no-op behavior.
- **Fix: Avatar upload** — Upload succeeds but the avatar URL in the profile
  response still shows the old URL. Cache invalidation missing after upload.

### Completed (DO NOT re-implement)
- Activity feed: working, 12/12 tests passing
- Notification listing + unread count: working, 8/8 tests passing
- Account settings (name, email): working, 6/6 tests passing
- Responsive layout: all breakpoints verified

### Out of Scope
- Same as iteration 1

## Testing
- QA: required
- UI Testing: required
- UI Testing Mode: automated
```

**Why iterative narrowing matters:**

- Removes completed work so agents do not re-implement it
- Explicitly describes the two bugs with expected vs actual behavior
- "Completed" section tells agents what NOT to touch
- Iteration converges faster because scope shrinks each round

## Example 5: Infrastructure Sprint (No UI Testing)

A spec for DevOps/infrastructure work that needs automated validation
but has no user-facing UI.

```markdown
# Sprint 7: CI/CD Pipeline

## Goal
Automated build, test, and deploy pipeline with staging and production environments.

## Scope
### In Scope
- GitHub Actions workflow: lint → test → build → deploy
- Docker multi-stage build (builder + runtime stages)
- Staging environment deployment on push to develop branch
- Production deployment on push to main branch (manual approval gate)
- Environment-specific secrets via GitHub Secrets
- Deployment health check (HTTP 200 on /health within 60 seconds)
- Rollback procedure documented in DEPLOYMENT.md

### Out of Scope
- Monitoring and alerting setup
- Log aggregation
- Performance testing
- CDN configuration
- Database migration automation

## Testing
- QA: required
- UI Testing: skip
- UI Testing Mode: automated
```

## Example 6: Spec with Specific Technical Constraints

When the spec must dictate implementation choices to ensure consistency
with existing architecture.

```markdown
# Sprint 8: WebSocket Real-Time Chat

## Goal
Real-time chat for project collaboration with channel support and presence tracking.

## Scope
### In Scope
- WebSocket server using Socket.io v4 (must match existing ws infra)
- Channel join/leave with presence indicators
- Message broadcasting within channels
- Message persistence to PostgreSQL via existing Drizzle ORM setup
- Typing indicator (show "user is typing..." for 3 seconds after last keystroke)
- Message delivery confirmation (sent → delivered → read receipts)
- Reconnection with message backfill (last 50 messages on rejoin)

### Out of Scope
- File attachments in messages
- Message reactions or threads
- Voice/video calls
- Push notifications to mobile
- Message search

## Technical Constraints
- Must use Socket.io v4 (not raw WebSockets or alternatives like Pusher)
- Must use existing PostgreSQL + Drizzle ORM stack (no new databases)
- Must use existing auth middleware for WebSocket handshake validation
- Message ordering must be guaranteed via server-side timestamps

## Testing
- QA: required
- UI Testing: required
- UI Testing Mode: manual
```

**Why constraints are valuable:**

- Prevents agents from choosing a different WebSocket library
- Ensures new code integrates with existing database stack
- Manual UI testing because real-time interactions are hard to automate reliably

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
