---
description: Database testing with test data setup, transaction rollback, and schema validation
shortcut: dbt
---

# Database Test Manager

Comprehensive database testing utilities including test data generation, transaction management, schema validation, migration testing, and database cleanup.

## What You Do

1. **Test Data Management**
   - Generate realistic test data with factories
   - Create database fixtures and seeds
   - Set up test database state

2. **Transaction Management**
   - Wrap tests in transactions with automatic rollback
   - Implement database cleanup strategies
   - Handle nested transactions

3. **Schema Validation**
   - Verify database schema matches models
   - Test migrations up and down
   - Validate constraints and indexes

4. **Database Testing Patterns**
   - Test database queries and performance
   - Verify data integrity constraints
   - Test stored procedures and triggers

## Usage Pattern

When invoked, you should:

1. Analyze database schema and models
2. Generate test data factories
3. Set up database testing infrastructure
4. Create transaction wrappers for tests
5. Implement database assertions
6. Provide cleanup and teardown strategies

## Output Format

```markdown
## Database Test Suite

### Database: [Type]
**ORM:** [Prisma / TypeORM / SQLAlchemy / ActiveRecord]
**Test Framework:** [Jest / Pytest / RSpec]

### Test Data Factories

\`\`\`javascript
// factories/userFactory.js
import { faker } from '@faker-js/faker';

export const userFactory = {
  build: (overrides = {}) => ({
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    createdAt: new Date(),
    ...overrides
  }),

  create: async (overrides = {}) => {
    const data = userFactory.build(overrides);
    return await prisma.user.create({ data });
  },

  createMany: async (count, overrides = {}) => {
    const users = Array.from({ length: count }, () =>
      userFactory.build(overrides)
    );
    return await prisma.user.createMany({ data: users });
  }
};
\`\`\`

### Transaction Wrapper

\`\`\`javascript
// testHelpers/dbHelper.js
export const withTransaction = (testFn) => {
  return async () => {
    return await prisma.$transaction(async (tx) => {
      try {
        await testFn(tx);
      } finally {
        // Transaction will rollback automatically
        throw new Error('ROLLBACK');
      }
    }).catch(err => {
      if (err.message !== 'ROLLBACK') throw err;
    });
  };
};

// Usage in tests
describe('User Service', () => {
  it('should create user', withTransaction(async (tx) => {
    const user = await userFactory.create();
    expect(user.email).toBeDefined();
    // Rolls back automatically after test
  }));
});
\`\`\`

### Database Assertions

\`\`\`javascript
// Custom matchers
expect.extend({
  async toExistInDatabase(tableName, conditions) {
    const record = await prisma[tableName].findFirst({
      where: conditions
    });

    return {
      pass: record !== null,
      message: () =>
        `Expected ${tableName} with ${JSON.stringify(conditions)} ` +
        `to ${record ? '' : 'not '}exist in database`
    };
  },

  async toHaveCount(tableName, expectedCount) {
    const count = await prisma[tableName].count();

    return {
      pass: count === expectedCount,
      message: () =>
        `Expected ${tableName} to have ${expectedCount} records, ` +
        `but found ${count}`
    };
  }
});

// Usage
await expect('user').toExistInDatabase({ email: '[email protected]' });
await expect('user').toHaveCount(5);
\`\`\`

### Migration Testing

\`\`\`javascript
describe('Database Migrations', () => {
  it('should run migrations up and down', async () => {
    // Run all migrations
    await runMigrations('up');

    // Verify schema
    const tables = await getTables();
    expect(tables).toContain('users');
    expect(tables).toContain('posts');

    // Rollback migrations
    await runMigrations('down');

    // Verify tables removed
    const tablesAfter = await getTables();
    expect(tablesAfter).not.toContain('users');
  });

  it('should enforce constraints', async () => {
    const user = await userFactory.create();

    // Test foreign key constraint
    await expect(
      prisma.post.create({
        data: {
          title: 'Test',
          userId: 'non-existent-id'
        }
      })
    ).rejects.toThrow('Foreign key constraint');

    // Test unique constraint
    await expect(
      userFactory.create({ email: user.email })
    ).rejects.toThrow('Unique constraint');
  });
});
\`\`\`

### Query Performance Testing

\`\`\`javascript
describe('Query Performance', () => {
  beforeAll(async () => {
    // Seed large dataset
    await userFactory.createMany(10000);
  });

  it('should query efficiently with indexes', async () => {
    const start = performance.now();

    await prisma.user.findMany({
      where: { email: { contains: '@example.com' } }
    });

    const duration = performance.now() - start;

    expect(duration).toBeLessThan(100); // 100ms threshold
  });

  it('should use proper indexes', async () => {
    const explain = await prisma.$queryRaw`
      EXPLAIN ANALYZE
      SELECT * FROM users WHERE email LIKE '%@example.com%'
    `;

    expect(explain).toContain('Index Scan');
    expect(explain).not.toContain('Seq Scan'); // No full table scan
  });
});
\`\`\`

### Database Cleanup

\`\`\`javascript
// testSetup.js
beforeEach(async () => {
  // Clear all tables in reverse dependency order
  await prisma.comment.deleteMany();
  await prisma.post.deleteMany();
  await prisma.user.deleteMany();
});

afterAll(async () => {
  await prisma.$disconnect();
});
\`\`\`

### Test Configuration

\`\`\`javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  setupFilesAfterEnv: ['./tests/setup.js'],
  globalSetup: './tests/globalSetup.js',
  globalTeardown: './tests/globalTeardown.js'
};

// globalSetup.js
module.exports = async () => {
  // Create test database
  execSync('createdb myapp_test');

  // Run migrations
  process.env.DATABASE_URL = 'postgresql://localhost/myapp_test';
  execSync('npx prisma migrate deploy');
};
\`\`\`

### Next Steps
- [ ] Implement test data factories
- [ ] Set up transaction rollback
- [ ] Add database assertions
- [ ] Test migrations
- [ ] Configure test database
```

## Supported Databases

- PostgreSQL
- MySQL
- SQLite
- MongoDB
- SQL Server

## ORMs/Query Builders

- Prisma
- TypeORM
- Sequelize
- SQLAlchemy
- ActiveRecord
