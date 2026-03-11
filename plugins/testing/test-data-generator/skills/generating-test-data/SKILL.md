---
name: generating-test-data
description: |
  Generate realistic test data including edge cases and boundary conditions.
  Use when creating realistic fixtures or edge case test data.
  Trigger with phrases like "generate test data", "create fixtures", or "setup test database".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:data-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Test Data Generator

## Overview

Generate realistic, type-safe test data including fixtures, factory functions, seed datasets, and edge case values. Supports Faker.js, Factory Bot patterns, Fishery (TypeScript factories), pytest fixtures, and database seed scripts. Produces deterministic data with reproducible seeds for consistent test runs while covering boundary conditions, unicode, and adversarial inputs.

## Prerequisites

- Data generation library installed (Faker.js/@faker-js/faker, Fishery, factory-boy for Python, or JavaFaker)
- Database schema or TypeScript/Python type definitions for the data models
- Test framework with fixture support (Jest, pytest, JUnit)
- Seed management for reproducible random data (`faker.seed()`)
- Database client for seed data insertion (if generating database fixtures)

## Instructions

1. Read the project's data models, TypeScript interfaces, database schemas, or ORM definitions to understand the shape of all entities.
2. For each entity, create a factory function that produces a valid default instance:
   - Use Faker methods matched to field semantics (e.g., `faker.person.fullName()` for names, `faker.internet.email()` for emails).
   - Provide sensible defaults for required fields.
   - Allow overrides via a partial parameter for test-specific customization.
   - Set a deterministic seed for reproducibility (`faker.seed(12345)`).
3. Generate edge case data variants for each entity:
   - **Empty values**: Empty strings, null, undefined, empty arrays.
   - **Boundary values**: Maximum string length, integer overflow, zero, negative numbers.
   - **Unicode and i18n**: Names with accents, CJK characters, RTL text, emoji.
   - **Adversarial inputs**: SQL injection strings, XSS payloads, excessively long strings.
   - **Temporal edge cases**: Leap years, timezone boundaries, epoch zero, far-future dates.
4. Create relationship factories that build connected entity graphs:
   - A user factory that also creates associated addresses and orders.
   - Configurable depth to avoid infinite recursion.
   - Lazy evaluation for optional relationships.
5. Generate database seed files for integration tests:
   - SQL insert scripts or ORM seed functions.
   - Idempotent operations (use `ON CONFLICT` or `INSERT IF NOT EXISTS`).
   - Separate seed sets for different test scenarios (empty state, populated state, edge cases).
6. Write fixture files in JSON, YAML, or TypeScript for static test data:
   - Group fixtures by test scenario.
   - Include both valid and invalid data sets.
7. Validate generated data against the schema to ensure factories remain in sync with model changes.

## Output

- Factory function files (one per entity) in `test/factories/` or `tests/factories/`
- Edge case data collections covering boundaries and adversarial inputs
- Database seed scripts for integration test environments
- JSON/YAML fixture files for static test data
- Factory index file exporting all factories for easy test imports

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Factory produces invalid data | Schema changed but factory not updated | Add a validation step that runs the factory output through the schema validator |
| Duplicate unique values | Faker generates collisions in small datasets | Use sequential IDs or append a counter; increase Faker's unique retry limit |
| Database seed fails on foreign key | Seed insertion order violates referential integrity | Sort seed operations topologically by dependency; disable FK checks during seeding |
| Factory recursion overflow | Circular relationships (User -> Order -> User) | Limit relationship depth; use lazy references; break cycles with ID-only references |
| Non-deterministic test failures | Random seed not set consistently | Call `faker.seed()` in `beforeAll` or at factory module level; document seed values |

## Examples

**TypeScript factory with Fishery:**
```typescript
import { Factory } from 'fishery';
import { faker } from '@faker-js/faker';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
  createdAt: Date;
}

export const userFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  name: faker.person.fullName(),
  email: faker.internet.email(),
  role: 'user',
  createdAt: faker.date.past(),
}));

// Usage:
const user = userFactory.build();
const admin = userFactory.build({ role: 'admin' });
const users = userFactory.buildList(10);
```

**pytest fixture factory:**
```python
import pytest
from faker import Faker

fake = Faker()
Faker.seed(42)

@pytest.fixture
def make_user():
    def _make_user(**overrides):
        defaults = {
            "name": fake.name(),
            "email": fake.email(),
            "age": fake.random_int(min=18, max=99),
        }
        return {**defaults, **overrides}
    return _make_user

def test_user_validation(make_user):
    user = make_user(age=17)
    assert validate_age(user) is False
```

**Edge case data collection:**
```typescript
export const edgeCases = {
  strings: ['', ' ', '\t\n', 'a'.repeat(10000), '<script>alert(1)</script>',
            "Robert'); DROP TABLE users;--", '\u0000null\u0000byte'],
  numbers: [0, -0, -1, Number.MAX_SAFE_INTEGER, NaN, Infinity, -Infinity],
  dates: [new Date(0), new Date('2024-02-29'), new Date('9999-12-31')],
};
```

## Resources

- Faker.js: https://fakerjs.dev/
- Fishery (TypeScript factories): https://github.com/thoughtbot/fishery
- factory_boy (Python): https://factoryboy.readthedocs.io/
- Chance.js: https://chancejs.com/
- Test data management patterns: https://martinfowler.com/bliki/ObjectMother.html
