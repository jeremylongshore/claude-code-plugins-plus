# Testing Configuration

## Testing Configuration

The Testing section controls which testing agents run.

### Options

| Setting | Values | Meaning |
|---------|--------|---------|
| QA | required / optional / skip | API and unit tests |
| UI Testing | required / optional / skip | Browser-based E2E tests |
| UI Testing Mode | automated / manual | Auto-run or user-driven |

### When to Use Each

**QA: required**

- New API endpoints
- Business logic changes
- Data validation rules

**QA: skip**

- Frontend-only changes
- Documentation updates
- Configuration changes

**UI Testing: required**

- User-facing features
- Form submissions
- Navigation flows

**UI Testing Mode: manual**

- Complex interactions
- Visual verification needed
- Exploratory testing

**UI Testing Mode: automated**

- Regression testing
- Standard CRUD flows
- Repeatable scenarios
