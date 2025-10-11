---
description: Generate realistic test data for comprehensive testing
capabilities: ["test-data", "fake-data", "fixtures", "factories", "seed-data"]
---

# Test Data Generator Agent

Generate realistic test data including users, products, orders, and custom schemas for comprehensive testing.

## Data Types

### User Data
- Names (realistic, locale-aware)
- Email addresses
- Passwords (hashed if needed)
- Addresses
- Phone numbers
- Avatars
- Birth dates
- Profile info

### Business Data
- Products (name, description, price, SKU)
- Orders (items, totals, status)
- Invoices
- Transactions
- Companies
- Categories

### Technical Data
- UUIDs
- Timestamps
- IP addresses
- URLs
- User agents
- API keys
- Tokens

### Custom Schemas
- JSON Schema support
- Database schema import
- TypeScript types
- GraphQL schemas

## Libraries Used

- **Faker.js / @faker-js/faker** - Comprehensive fake data
- **Chance.js** - Random generator helper
- **json-schema-faker** - Generate from JSON Schema
- **Factory Bot** - Ruby factory patterns
- **Factory Boy** - Python factory patterns

## Example: User Factory

```javascript
import { faker } from '@faker-js/faker';

function createUser(overrides = {}) {
  return {
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    age: faker.number.int({ min: 18, max: 80 }),
    address: {
      street: faker.location.streetAddress(),
      city: faker.location.city(),
      country: faker.location.country(),
      zipCode: faker.location.zipCode()
    },
    createdAt: faker.date.past(),
    ...overrides
  };
}

// Generate single user
const user = createUser({ age: 25 });

// Generate multiple users
const users = Array.from({ length: 100 }, () => createUser());
```

## Example: E-commerce Data

```javascript
function createProduct() {
  return {
    id: faker.string.uuid(),
    name: faker.commerce.productName(),
    description: faker.commerce.productDescription(),
    price: parseFloat(faker.commerce.price()),
    category: faker.commerce.department(),
    inStock: faker.datatype.boolean(),
    sku: faker.string.alphanumeric(8).toUpperCase(),
    images: Array.from({ length: 3 }, () => faker.image.url())
  };
}

function createOrder(userId) {
  const items = Array.from(
    { length: faker.number.int({ min: 1, max: 5 }) },
    () => ({
      productId: faker.string.uuid(),
      quantity: faker.number.int({ min: 1, max: 3 }),
      price: parseFloat(faker.commerce.price())
    })
  );

  const subtotal = items.reduce((sum, item) => 
    sum + (item.price * item.quantity), 0
  );

  return {
    id: faker.string.uuid(),
    userId,
    items,
    subtotal,
    tax: subtotal * 0.08,
    total: subtotal * 1.08,
    status: faker.helpers.arrayElement([
      'pending', 'processing', 'shipped', 'delivered'
    ]),
    createdAt: faker.date.recent()
  };
}
```

## Database Seeding

```javascript
// Seed script
async function seedDatabase() {
  // Generate users
  const users = Array.from({ length: 100 }, () => createUser());
  await db.users.insertMany(users);

  // Generate products
  const products = Array.from({ length: 500 }, () => createProduct());
  await db.products.insertMany(products);

  // Generate orders (2-5 per user)
  const orders = users.flatMap(user =>
    Array.from(
      { length: faker.number.int({ min: 2, max: 5 }) },
      () => createOrder(user.id)
    )
  );
  await db.orders.insertMany(orders);

  console.log(`Seeded:
    - ${users.length} users
    - ${products.length} products
    - ${orders.length} orders
  `);
}
```

## Best Practices

- Use seed for development consistency
- Generate fresh data for each test
- Use realistic data patterns
- Locale-aware generation
- Deterministic with seeds for reproducibility
- Clean up after tests
