---
name: seed-data
description: Generate realistic test data and seed scripts
---
# Data Seeder Generator

Generate realistic, consistent test data for database seeding.

## Seeding Strategies

1. **Faker Libraries**: Use Faker.js, Faker (Python) for realistic data
2. **Relational Integrity**: Maintain foreign key relationships
3. **Realistic Distributions**: Natural data patterns
4. **Configurable Volume**: Control record counts
5. **Idempotent Seeds**: Safe to run multiple times

## Example Seeder (Node.js/TypeORM)

```typescript
import { faker } from '@faker-js/faker';

export class UserSeeder {
  async run() {
    const users = [];
    for (let i = 0; i < 100; i++) {
      users.push({
        email: faker.internet.email(),
        firstName: faker.person.firstName(),
        lastName: faker.person.lastName(),
        createdAt: faker.date.past()
      });
    }
    await User.save(users);
  }
}
```

## When Invoked

Generate seed scripts with realistic data for testing and development.
