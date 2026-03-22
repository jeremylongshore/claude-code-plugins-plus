---
name: navan-core-workflow-a
description: |
  Execute Navan primary workflow: Travel Booking & Management.
  Trigger: "navan travel booking & management", "primary navan workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan — Travel Booking & Management

## Overview
Primary workflow for Navan integration.

## Instructions

### Step 1: Search Flights
```typescript
const flights = await client.flights.search({
  origin: 'SFO', destination: 'JFK',
  departure_date: '2026-05-01',
  return_date: '2026-05-05',
  travelers: 1,
  cabin_class: 'economy',
  policy_check: true  // Validate against company travel policy
});

flights.results.forEach(f =>
  console.log(`${f.airline} ${f.flight_number}: $${f.price} | ${f.duration} | ${f.policy_compliant ? 'IN POLICY' : 'OUT OF POLICY'}`)
);
```

### Step 2: Book Trip
```typescript
const booking = await client.bookings.create({
  flight_id: flights.results[0].id,
  traveler: { employee_id: 'emp_123', name: 'Jane Smith', email: 'jane@company.com' },
  cost_center: 'engineering',
  project_code: 'PROJ-456',
  approver_id: 'mgr_789'
});
console.log(`Booking: ${booking.id} | Status: ${booking.status}`);
```

### Step 3: Track Trips
```typescript
const activeTrips = await client.trips.list({
  status: 'active',
  department: 'engineering'
});
activeTrips.forEach(t =>
  console.log(`${t.traveler.name}: ${t.origin} → ${t.destination} | ${t.dates}`)
);
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-core-workflow-b`.
