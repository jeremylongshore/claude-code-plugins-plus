---
name: create-mock-server
description: Create a mock API server for testing
shortcut: mock
---
# Create Mock API Server

Generate production-grade mock API servers from OpenAPI specifications with realistic fake data, stateful operations, and customizable response scenarios. Perfect for frontend development, integration testing, and API prototyping without backend dependencies.

## Design Decisions

This command generates mock servers using Express.js with faker-js for realistic data generation. The implementation prioritizes:

1. **OpenAPI-First Approach**: Generates endpoints directly from OpenAPI/Swagger specs to ensure contract compliance
2. **Stateful Mode**: Optional in-memory persistence allows testing CRUD workflows with realistic state management
3. **Scenario-Based Responses**: Conditional logic based on request parameters enables testing edge cases
4. **Network Realism**: Built-in latency simulation and error injection mimic production API behavior

**Alternatives Considered:**
- JSON Server (limited to simple CRUD, no OpenAPI support)
- Mockoon (GUI-based, not scriptable)
- WireMock (Java-based, heavier dependency)
- Prism (excellent OpenAPI support but less flexible for custom scenarios)

## When to Use This Command

**USE WHEN:**
- Developing frontend features before backend APIs are ready
- Testing error handling and edge cases without affecting production
- Creating reproducible test scenarios for QA and CI/CD
- Demonstrating API functionality to stakeholders
- Validating OpenAPI specifications with working examples
- Load testing frontend without backend infrastructure

**DON'T USE WHEN:**
- You need real business logic or database interactions
- Testing actual backend performance (use staging environment)
- Security testing (mocks bypass authentication layers)
- Integration testing with third-party services
- Production traffic routing (mocks are development tools only)

## Prerequisites

**Required:**
- Node.js 18+ installed
- OpenAPI 3.0+ specification file (YAML or JSON)
- Basic understanding of RESTful API concepts
- Port availability (default: 3000)

**Optional:**
- Docker for containerized deployment
- Postman/Insomnia for API testing
- curl or httpie for command-line testing

**Install Dependencies:**
```bash
npm install express @faker-js/faker swagger-parser cors
npm install --save-dev nodemon @types/express
```

## Step-by-Step Process

### Step 1: Prepare OpenAPI Specification
Ensure your OpenAPI spec is valid and contains response schemas with examples:
```bash
# Validate OpenAPI spec
npx swagger-cli validate openapi.yaml
```

### Step 2: Generate Mock Server Structure
Command analyzes the OpenAPI spec and generates:
- Express route handlers for each endpoint
- Response schemas with faker.js mappings
- Middleware for CORS, logging, error handling
- Optional stateful storage layer

### Step 3: Configure Mock Behavior
Customize mock server with:
- Response delay ranges (simulate network latency)
- Error injection rates (test error handling)
- Stateful mode (enable in-memory persistence)
- Custom scenario rules (conditional responses)

### Step 4: Start Mock Server
Launch the generated server with hot-reload:
```bash
npm run dev  # Development mode with nodemon
npm start    # Production mode
```

### Step 5: Test and Iterate
Verify mock endpoints match OpenAPI contract:
```bash
# Test generated endpoints
curl http://localhost:3000/api/users
curl -X POST http://localhost:3000/api/users -d '{"name":"John"}'
```

## Output Format

The command generates a complete Node.js project:

```
mock-server/
├── server.js              # Express server entry point
├── routes/                # Generated route handlers
│   ├── users.js          # User resource endpoints
│   ├── products.js       # Product resource endpoints
│   └── orders.js         # Order resource endpoints
├── middleware/            # Request/response middleware
│   ├── cors.js           # CORS configuration
│   ├── logger.js         # Request logging
│   └── errorHandler.js   # Error handling
├── data/                  # Stateful mode storage
│   ├── store.js          # In-memory data store
│   └── seed.js           # Initial data seeding
├── scenarios/             # Custom response logic
│   └── conditionalLogic.js
├── config/
│   └── server.config.js  # Server configuration
├── package.json           # Dependencies and scripts
├── .env.example          # Environment variables template
└── README.md             # Generated documentation
```

## Code Examples

### Example 1: OpenAPI Spec-Based Mock Generation

**Input OpenAPI Spec (openapi.yaml):**
```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: List all users
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Create a user
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserInput'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
  /api/users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        firstName:
          type: string
        lastName:
          type: string
        avatar:
          type: string
          format: uri
        createdAt:
          type: string
          format: date-time
    UserInput:
      type: object
      required:
        - email
        - firstName
        - lastName
      properties:
        email:
          type: string
          format: email
        firstName:
          type: string
        lastName:
          type: string
```

**Command Usage:**
```bash
# Generate mock server from OpenAPI spec
/create-mock-server \
  --spec openapi.yaml \
  --output ./mock-api \
  --port 3000 \
  --delay 100-300
```

**Generated routes/users.js:**
```javascript
import express from 'express';
import { faker } from '@faker-js/faker';
import { applyDelay } from '../middleware/delay.js';

const router = express.Router();

// Generate realistic fake user
function generateUser() {
  return {
    id: faker.string.uuid(),
    email: faker.internet.email(),
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
    avatar: faker.image.avatar(),
    createdAt: faker.date.past().toISOString()
  };
}

// GET /api/users - List all users
router.get('/users', applyDelay, (req, res) => {
  const count = parseInt(req.query.limit) || 10;
  const users = Array.from({ length: count }, generateUser);

  res.json({
    data: users,
    pagination: {
      total: count,
      page: 1,
      limit: count
    }
  });
});

// POST /api/users - Create user
router.post('/users', applyDelay, (req, res) => {
  const { email, firstName, lastName } = req.body;

  // Validation
  if (!email || !firstName || !lastName) {
    return res.status(400).json({
      error: 'Missing required fields',
      required: ['email', 'firstName', 'lastName']
    });
  }

  const newUser = {
    id: faker.string.uuid(),
    email,
    firstName,
    lastName,
    avatar: faker.image.avatar(),
    createdAt: new Date().toISOString()
  };

  res.status(201).json(newUser);
});

// GET /api/users/:id - Get user by ID
router.get('/users/:id', applyDelay, (req, res) => {
  const { id } = req.params;

  // Simulate 404 for specific IDs
  if (id === '00000000-0000-0000-0000-000000000000') {
    return res.status(404).json({
      error: 'User not found',
      id
    });
  }

  const user = {
    ...generateUser(),
    id // Use the requested ID
  };

  res.json(user);
});

export default router;
```

**Generated server.js:**
```javascript
import express from 'express';
import cors from 'cors';
import { config } from './config/server.config.js';
import logger from './middleware/logger.js';
import errorHandler from './middleware/errorHandler.js';
import usersRouter from './routes/users.js';

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(logger);

// Routes
app.use('/api', usersRouter);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || config.port;
app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log(`API documentation: http://localhost:${PORT}/api-docs`);
});
```

### Example 2: Stateful Mock Server with CRUD Operations

**Command Usage:**
```bash
# Generate stateful mock server with persistent data
/create-mock-server \
  --spec openapi.yaml \
  --output ./mock-api \
  --stateful \
  --seed 50 \
  --port 3000
```

**Generated data/store.js (In-Memory Database):**
```javascript
import { faker } from '@faker-js/faker';

class MockStore {
  constructor() {
    this.collections = {
      users: new Map(),
      products: new Map(),
      orders: new Map()
    };
    this.idCounters = {
      users: 1,
      products: 1,
      orders: 1
    };
  }

  // Generic CRUD operations
  create(collection, data) {
    const id = data.id || String(this.idCounters[collection]++);
    const record = {
      ...data,
      id,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    this.collections[collection].set(id, record);
    return record;
  }

  findAll(collection, filters = {}) {
    const records = Array.from(this.collections[collection].values());

    // Apply filters
    return records.filter(record => {
      return Object.entries(filters).every(([key, value]) => {
        if (value === undefined) return true;
        return String(record[key]).toLowerCase().includes(String(value).toLowerCase());
      });
    });
  }

  findById(collection, id) {
    return this.collections[collection].get(id) || null;
  }

  update(collection, id, data) {
    const existing = this.findById(collection, id);
    if (!existing) return null;

    const updated = {
      ...existing,
      ...data,
      id, // Prevent ID change
      updatedAt: new Date().toISOString()
    };
    this.collections[collection].set(id, updated);
    return updated;
  }

  delete(collection, id) {
    const record = this.findById(collection, id);
    if (!record) return false;
    return this.collections[collection].delete(id);
  }

  count(collection) {
    return this.collections[collection].size;
  }

  clear(collection) {
    this.collections[collection].clear();
  }

  // Seed data
  seed(collection, count, generator) {
    for (let i = 0; i < count; i++) {
      this.create(collection, generator());
    }
  }
}

// Singleton instance
export const store = new MockStore();
```

**Generated data/seed.js:**
```javascript
import { faker } from '@faker-js/faker';
import { store } from './store.js';

export function seedDatabase() {
  console.log('Seeding database...');

  // Seed users
  store.seed('users', 50, () => ({
    email: faker.internet.email(),
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
    avatar: faker.image.avatar(),
    role: faker.helpers.arrayElement(['user', 'admin', 'moderator']),
    status: faker.helpers.arrayElement(['active', 'inactive', 'suspended'])
  }));

  // Seed products
  store.seed('products', 100, () => ({
    name: faker.commerce.productName(),
    description: faker.commerce.productDescription(),
    price: parseFloat(faker.commerce.price()),
    category: faker.commerce.department(),
    inStock: faker.datatype.boolean(),
    sku: faker.string.alphanumeric(8).toUpperCase(),
    image: faker.image.urlLoremFlickr({ category: 'product' })
  }));

  // Seed orders
  const users = store.findAll('users');
  const products = store.findAll('products');

  store.seed('orders', 200, () => {
    const user = faker.helpers.arrayElement(users);
    const orderItems = faker.helpers.arrayElements(products, { min: 1, max: 5 });
    const total = orderItems.reduce((sum, item) => sum + item.price, 0);

    return {
      userId: user.id,
      items: orderItems.map(item => ({
        productId: item.id,
        quantity: faker.number.int({ min: 1, max: 5 }),
        price: item.price
      })),
      total: parseFloat(total.toFixed(2)),
      status: faker.helpers.arrayElement(['pending', 'processing', 'shipped', 'delivered', 'cancelled']),
      shippingAddress: {
        street: faker.location.streetAddress(),
        city: faker.location.city(),
        state: faker.location.state(),
        zip: faker.location.zipCode(),
        country: faker.location.country()
      }
    };
  });

  console.log(`Seeded ${store.count('users')} users`);
  console.log(`Seeded ${store.count('products')} products`);
  console.log(`Seeded ${store.count('orders')} orders`);
}
```

**Stateful routes/users.js:**
```javascript
import express from 'express';
import { store } from '../data/store.js';
import { applyDelay } from '../middleware/delay.js';

const router = express.Router();

// GET /api/users - List with filtering and pagination
router.get('/users', applyDelay, (req, res) => {
  const { search, role, status, page = 1, limit = 20 } = req.query;

  // Apply filters
  const filters = {};
  if (search) filters.firstName = search; // Partial match
  if (role) filters.role = role;
  if (status) filters.status = status;

  const allUsers = store.findAll('users', filters);

  // Pagination
  const pageNum = parseInt(page);
  const limitNum = parseInt(limit);
  const startIndex = (pageNum - 1) * limitNum;
  const endIndex = startIndex + limitNum;
  const paginatedUsers = allUsers.slice(startIndex, endIndex);

  res.json({
    data: paginatedUsers,
    pagination: {
      total: allUsers.length,
      page: pageNum,
      limit: limitNum,
      totalPages: Math.ceil(allUsers.length / limitNum)
    }
  });
});

// POST /api/users - Create with validation
router.post('/users', applyDelay, (req, res) => {
  const { email, firstName, lastName, role = 'user' } = req.body;

  if (!email || !firstName || !lastName) {
    return res.status(400).json({
      error: 'Validation failed',
      details: {
        email: !email ? 'Email is required' : null,
        firstName: !firstName ? 'First name is required' : null,
        lastName: !lastName ? 'Last name is required' : null
      }
    });
  }

  // Check for duplicate email
  const existing = store.findAll('users').find(u => u.email === email);
  if (existing) {
    return res.status(409).json({
      error: 'User with this email already exists',
      existingId: existing.id
    });
  }

  const newUser = store.create('users', {
    email,
    firstName,
    lastName,
    role,
    status: 'active',
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${email}`
  });

  res.status(201).json(newUser);
});

// GET /api/users/:id - Get by ID
router.get('/users/:id', applyDelay, (req, res) => {
  const user = store.findById('users', req.params.id);

  if (!user) {
    return res.status(404).json({
      error: 'User not found',
      id: req.params.id
    });
  }

  res.json(user);
});

// PUT /api/users/:id - Update
router.put('/users/:id', applyDelay, (req, res) => {
  const { email, firstName, lastName, role, status } = req.body;

  const updated = store.update('users', req.params.id, {
    email,
    firstName,
    lastName,
    role,
    status
  });

  if (!updated) {
    return res.status(404).json({
      error: 'User not found',
      id: req.params.id
    });
  }

  res.json(updated);
});

// DELETE /api/users/:id
router.delete('/users/:id', applyDelay, (req, res) => {
  const deleted = store.delete('users', req.params.id);

  if (!deleted) {
    return res.status(404).json({
      error: 'User not found',
      id: req.params.id
    });
  }

  res.status(204).send();
});

export default router;
```

### Example 3: Dynamic Response Scenarios with Conditional Logic

**Command Usage:**
```bash
# Generate mock server with custom scenarios
/create-mock-server \
  --spec openapi.yaml \
  --output ./mock-api \
  --scenarios \
  --error-rate 5 \
  --port 3000
```

**Generated scenarios/conditionalLogic.js:**
```javascript
/**
 * Scenario-based response logic for realistic API behavior
 */

// Simulate different response scenarios based on request data
export const scenarios = {

  // Payment processing scenarios
  payment: {
    // Test card numbers trigger specific responses
    testCards: {
      '4242424242424242': { status: 'success', message: 'Payment approved' },
      '4000000000000002': { status: 'declined', message: 'Card declined' },
      '4000000000009995': { status: 'error', message: 'Insufficient funds' },
      '4000000000000069': { status: 'error', message: 'Card expired' },
      '4000000000000127': { status: 'error', message: 'Incorrect CVC' }
    },

    handler: (cardNumber, amount) => {
      // Check test cards
      if (scenarios.payment.testCards[cardNumber]) {
        return scenarios.payment.testCards[cardNumber];
      }

      // Amount-based scenarios
      if (amount > 10000) {
        return {
          status: 'pending',
          message: 'Large transaction requires manual review',
          reviewId: `REV-${Date.now()}`
        };
      }

      // Random 5% failure rate for realistic testing
      if (Math.random() < 0.05) {
        return {
          status: 'error',
          message: 'Payment gateway timeout',
          retryable: true
        };
      }

      return {
        status: 'success',
        message: 'Payment approved',
        transactionId: `TXN-${Date.now()}`
      };
    }
  },

  // Authentication scenarios
  auth: {
    // Test credentials
    testUsers: {
      'admin@example.com': { password: 'admin123', role: 'admin', mfaEnabled: true },
      'user@example.com': { password: 'user123', role: 'user', mfaEnabled: false },
      'locked@example.com': { password: 'locked123', locked: true },
      'expired@example.com': { password: 'expired123', passwordExpired: true }
    },

    handler: (email, password) => {
      const user = scenarios.auth.testUsers[email];

      if (!user) {
        return {
          status: 401,
          error: 'Invalid credentials'
        };
      }

      if (user.locked) {
        return {
          status: 403,
          error: 'Account locked due to multiple failed login attempts',
          unlockTime: new Date(Date.now() + 3600000).toISOString()
        };
      }

      if (user.passwordExpired) {
        return {
          status: 403,
          error: 'Password expired',
          passwordResetRequired: true
        };
      }

      if (user.password !== password) {
        return {
          status: 401,
          error: 'Invalid credentials',
          attemptsRemaining: 3
        };
      }

      if (user.mfaEnabled) {
        return {
          status: 200,
          mfaRequired: true,
          mfaToken: `MFA-${Date.now()}`
        };
      }

      return {
        status: 200,
        token: `JWT-${Date.now()}`,
        user: { email, role: user.role }
      };
    }
  },

  // Rate limiting scenarios
  rateLimit: {
    requestCounts: new Map(),

    handler: (clientId, limit = 100, window = 60000) => {
      const now = Date.now();
      const key = `${clientId}-${Math.floor(now / window)}`;

      const count = scenarios.rateLimit.requestCounts.get(key) || 0;
      scenarios.rateLimit.requestCounts.set(key, count + 1);

      // Clean old entries
      for (const [k, v] of scenarios.rateLimit.requestCounts.entries()) {
        if (k.split('-')[1] < Math.floor((now - window * 2) / window)) {
          scenarios.rateLimit.requestCounts.delete(k);
        }
      }

      if (count >= limit) {
        return {
          status: 429,
          error: 'Rate limit exceeded',
          retryAfter: Math.ceil((window - (now % window)) / 1000),
          limit,
          remaining: 0
        };
      }

      return {
        status: 200,
        limit,
        remaining: limit - count - 1,
        reset: Math.floor((now + window) / 1000)
      };
    }
  },

  // Error injection for testing
  errorInjection: {
    handler: (errorRate = 0.05) => {
      const rand = Math.random();

      if (rand < errorRate * 0.2) {
        return { status: 500, error: 'Internal server error' };
      }

      if (rand < errorRate * 0.4) {
        return { status: 503, error: 'Service temporarily unavailable', retryAfter: 30 };
      }

      if (rand < errorRate * 0.6) {
        return { status: 504, error: 'Gateway timeout' };
      }

      if (rand < errorRate) {
        return { status: 502, error: 'Bad gateway' };
      }

      return null; // No error
    }
  },

  // Conditional responses based on headers
  headerBased: {
    handler: (headers) => {
      // API version handling
      if (headers['api-version'] === '1.0') {
        return { format: 'legacy', deprecationWarning: true };
      }

      // Feature flags
      const features = (headers['x-features'] || '').split(',');
      const enabledFeatures = {};
      features.forEach(f => {
        enabledFeatures[f.trim()] = true;
      });

      // A/B testing
      const variant = headers['x-variant'] || 'control';

      return {
        format: 'current',
        features: enabledFeatures,
        variant
      };
    }
  }
};

// Middleware to apply scenarios
export function applyScenarios(req, res, next) {
  // Add scenario helpers to request
  req.scenarios = scenarios;

  // Add error injection
  const injectedError = scenarios.errorInjection.handler(
    parseFloat(process.env.ERROR_RATE) || 0.05
  );

  if (injectedError) {
    return res.status(injectedError.status).json(injectedError);
  }

  // Add rate limiting
  const clientId = req.ip || req.headers['x-client-id'] || 'anonymous';
  const rateLimitResult = scenarios.rateLimit.handler(clientId);

  res.set({
    'X-RateLimit-Limit': rateLimitResult.limit,
    'X-RateLimit-Remaining': rateLimitResult.remaining,
    'X-RateLimit-Reset': rateLimitResult.reset
  });

  if (rateLimitResult.status === 429) {
    res.set('Retry-After', rateLimitResult.retryAfter);
    return res.status(429).json({
      error: rateLimitResult.error,
      retryAfter: rateLimitResult.retryAfter
    });
  }

  next();
}
```

**Using scenarios in routes/payments.js:**
```javascript
import express from 'express';
import { scenarios } from '../scenarios/conditionalLogic.js';
import { applyDelay } from '../middleware/delay.js';

const router = express.Router();

// POST /api/payments
router.post('/payments', applyDelay, (req, res) => {
  const { cardNumber, amount, currency = 'USD' } = req.body;

  // Validation
  if (!cardNumber || !amount) {
    return res.status(400).json({
      error: 'Missing required fields',
      required: ['cardNumber', 'amount']
    });
  }

  // Apply payment scenario logic
  const result = scenarios.payment.handler(cardNumber, amount);

  const response = {
    ...result,
    amount,
    currency,
    timestamp: new Date().toISOString()
  };

  // Set status code based on result
  const statusCode = result.status === 'success' ? 200 :
                     result.status === 'pending' ? 202 :
                     result.status === 'declined' ? 402 : 400;

  res.status(statusCode).json(response);
});

// POST /api/auth/login
router.post('/auth/login', applyDelay, (req, res) => {
  const { email, password } = req.body;

  const result = scenarios.auth.handler(email, password);

  res.status(result.status).json(result);
});

export default router;
```

## Configuration Options

### Command-Line Flags

```bash
/create-mock-server [OPTIONS]

OPTIONS:
  --spec <file>           OpenAPI specification file (YAML/JSON)
                          Required. Supports OpenAPI 3.0+ and Swagger 2.0

  --output <directory>    Output directory for generated server
                          Default: ./mock-server

  --port <number>         Server port
                          Default: 3000

  --delay <range>         Response delay range in milliseconds
                          Format: "min-max" (e.g., "100-300")
                          Default: "50-150"

  --stateful              Enable stateful mode with in-memory persistence
                          Default: false (stateless)

  --seed <number>         Number of records to seed per collection (stateful mode)
                          Default: 20

  --scenarios             Enable conditional response scenarios
                          Default: false

  --error-rate <percent>  Error injection rate (0-100)
                          Default: 0 (no errors)

  --cors                  Enable CORS with permissive settings
                          Default: true

  --log-level <level>     Logging verbosity: error, warn, info, debug
                          Default: info

  --hot-reload            Enable hot-reload with nodemon
                          Default: true for dev mode

EXAMPLES:
  # Basic stateless mock
  /create-mock-server --spec api.yaml --port 3000

  # Stateful with 100 seed records
  /create-mock-server --spec api.yaml --stateful --seed 100

  # With error injection and scenarios
  /create-mock-server --spec api.yaml --scenarios --error-rate 10 --delay 200-500

  # Production-like config
  /create-mock-server --spec api.yaml --delay 50-200 --log-level warn --no-hot-reload
```

### Environment Variables

Create `.env` file in generated project:

```bash
# Server configuration
PORT=3000
NODE_ENV=development
LOG_LEVEL=info

# Mock behavior
STATEFUL_MODE=true
ERROR_RATE=0.05
MIN_DELAY=100
MAX_DELAY=300

# CORS settings
CORS_ORIGIN=*
CORS_CREDENTIALS=false

# Data seeding
SEED_USERS=50
SEED_PRODUCTS=100
SEED_ORDERS=200

# Feature flags
ENABLE_SCENARIOS=true
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60000

# Authentication (for protected mock endpoints)
API_KEY=mock-api-key-12345
REQUIRE_AUTH=false
```

## Error Handling

### Common Errors and Solutions

**1. OpenAPI Spec Validation Failed**
```
Error: Invalid OpenAPI specification
  - Missing required field: info.version
  - Invalid path parameter syntax
```
**Solution:**
```bash
# Validate spec first
npx swagger-cli validate openapi.yaml

# Check for common issues:
# - Missing required fields (info, paths)
# - Invalid references ($ref)
# - Incorrect schema syntax
```

**2. Port Already in Use**
```
Error: listen EADDRINUSE: address already in use :::3000
```
**Solution:**
```bash
# Find process using port
lsof -i :3000

# Kill process or use different port
/create-mock-server --spec api.yaml --port 3001
```

**3. Faker.js Schema Mapping Failed**
```
Warning: Could not map schema type 'customType' to faker method
```
**Solution:**
- Add custom mapping in generated `config/faker-mappings.js`
- Or use default faker method as fallback
```javascript
// Custom mapping example
const customMappings = {
  'ipAddress': () => faker.internet.ip(),
  'macAddress': () => faker.internet.mac(),
  'customType': () => faker.string.alphanumeric(10)
};
```

**4. Stateful Store Memory Limit**
```
Error: JavaScript heap out of memory
```
**Solution:**
```bash
# Increase Node.js heap size
NODE_OPTIONS="--max-old-space-size=4096" npm start

# Or reduce seed count
/create-mock-server --spec api.yaml --stateful --seed 50
```

**5. CORS Issues in Browser**
```
Access to fetch at 'http://localhost:3000' has been blocked by CORS policy
```
**Solution:**
```javascript
// Generated CORS config already permissive, but can customize:
// middleware/cors.js
export const corsOptions = {
  origin: process.env.CORS_ORIGIN || '*',
  credentials: process.env.CORS_CREDENTIALS === 'true',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key']
};
```

## Best Practices

### DO:
1. Always validate OpenAPI spec before generating mock server
2. Use stateful mode for testing complex CRUD workflows
3. Set realistic delay ranges (100-300ms) to catch race conditions
4. Enable error injection (5-10%) to test error handling
5. Seed sufficient data (50+ records) for pagination testing
6. Use scenario-based responses for authentication and payments
7. Add request logging for debugging
8. Version your OpenAPI spec alongside mock server
9. Document test scenarios in README
10. Use Docker for consistent mock server deployment

### DON'T:
1. Don't rely on mocks for performance testing (no real database)
2. Don't commit generated node_modules to version control
3. Don't expose mock servers to public internet (development only)
4. Don't use real production data in mock servers
5. Don't skip response schema validation
6. Don't hardcode test data (use faker.js for variety)
7. Don't forget to update mocks when API spec changes
8. Don't use mocks as production API substitutes

### TIPS:
- Use `--seed` generously for realistic datasets
- Combine `--delay` with `--error-rate` for chaos testing
- Create separate mock configs for different test scenarios
- Use Docker Compose for multi-service mock environments
- Add health check endpoint for orchestration tools
- Export Postman collection from generated server for QA
- Use Git tags to version mock server with API spec versions

## Related Commands

- `/validate-openapi` - Validate OpenAPI specification before mocking
- `/test-api-endpoints` - Test generated mock endpoints automatically
- `/generate-api-client` - Generate SDK clients from same OpenAPI spec
- `/api-load-test` - Load test mock server to verify performance
- `/create-api-docs` - Generate interactive documentation from OpenAPI spec
- `/api-contract-test` - Validate mock responses match OpenAPI contract

## Performance Considerations

### Mock Server Performance
- **Stateless Mode**: Handles 1000+ req/sec on modest hardware
- **Stateful Mode**: 500-800 req/sec with in-memory store (10k records)
- **With Delay Simulation**: Throughput = 1000 / avg_delay_ms requests/sec
- **Memory Usage**: ~50MB base, +5MB per 10k seeded records

### Optimization Tips
1. Use stateless mode for high-concurrency tests
2. Reduce seed count if memory is constrained
3. Disable logging in production mode (`LOG_LEVEL=error`)
4. Use Redis for stateful storage beyond 100k records
5. Enable clustering for multi-core utilization:
```javascript
// server.js with clustering
import cluster from 'cluster';
import os from 'os';

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
} else {
  // Start Express server
  app.listen(PORT);
}
```

### Monitoring Mock Performance
```bash
# Request latency
curl -w "@curl-format.txt" http://localhost:3000/api/users

# Concurrent requests
ab -n 1000 -c 10 http://localhost:3000/api/users

# Memory usage
NODE_ENV=production node --inspect server.js
# Visit chrome://inspect for profiling
```

## Security Notes for Mock Data

### Important Security Warnings
1. **Never use production data** - Mocks should use synthetic data only
2. **No real credentials** - All passwords, API keys, tokens should be fake
3. **No PII leakage** - Use faker.js to generate realistic but fake personal data
4. **Disable in production** - Mock servers are development tools only
5. **Network isolation** - Bind to localhost or use Docker networks

### Secure Mock Configuration
```javascript
// config/security.js
export const securityConfig = {
  // Bind to localhost only (not 0.0.0.0)
  host: process.env.HOST || '127.0.0.1',

  // Disable in production
  enabled: process.env.NODE_ENV !== 'production',

  // Optional API key for mock server access
  apiKey: process.env.MOCK_API_KEY,

  // Rate limiting
  rateLimit: {
    windowMs: 60000,
    max: 100
  }
};

// Middleware
if (securityConfig.apiKey) {
  app.use((req, res, next) => {
    const providedKey = req.headers['x-api-key'];
    if (providedKey !== securityConfig.apiKey) {
      return res.status(401).json({ error: 'Invalid API key' });
    }
    next();
  });
}
```

### Data Sanitization
```javascript
// Ensure no real data leaks
import { faker } from '@faker-js/faker';

faker.seed(12345); // Reproducible fake data

// Sanitize any user input
function sanitizeForMock(data) {
  return {
    ...data,
    email: faker.internet.email(),
    phone: faker.phone.number(),
    ssn: 'XXX-XX-' + faker.string.numeric(4),
    creditCard: '****-****-****-' + faker.string.numeric(4)
  };
}
```

## Troubleshooting Guide

### Issue: Mock server not starting
**Symptoms:** Port binding errors, module not found
**Diagnosis:**
```bash
# Check port availability
netstat -an | grep 3000

# Check Node version
node --version  # Should be 18+

# Check dependencies
npm list
```
**Resolution:**
- Kill process on port: `kill -9 $(lsof -t -i:3000)`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Use different port: `PORT=3001 npm start`

### Issue: OpenAPI spec not generating routes
**Symptoms:** No routes registered, empty routes folder
**Diagnosis:**
```bash
# Validate OpenAPI spec
npx swagger-cli validate openapi.yaml

# Check for required fields
jq '.paths' openapi.yaml
```
**Resolution:**
- Ensure `paths` section exists with at least one endpoint
- Check `$ref` references are valid
- Verify schema components are defined

### Issue: Faker.js generating same data
**Symptoms:** Identical data on each request
**Diagnosis:** Seed is set globally
**Resolution:**
```javascript
// Remove global seed or set per-request
// Bad:
faker.seed(12345); // At module level

// Good:
function generateUser() {
  faker.seed(Date.now() + Math.random()); // Unique seed
  return { ... };
}
```

### Issue: Stateful store losing data
**Symptoms:** Data disappears on server restart
**Diagnosis:** In-memory store is ephemeral
**Resolution:**
```javascript
// Add persistence to disk
import fs from 'fs';

class PersistentStore extends MockStore {
  constructor(filename = 'mock-data.json') {
    super();
    this.filename = filename;
    this.load();
  }

  save() {
    const data = {
      users: Array.from(this.collections.users.entries()),
      products: Array.from(this.collections.products.entries())
    };
    fs.writeFileSync(this.filename, JSON.stringify(data, null, 2));
  }

  load() {
    if (fs.existsSync(this.filename)) {
      const data = JSON.parse(fs.readFileSync(this.filename, 'utf8'));
      this.collections.users = new Map(data.users);
      this.collections.products = new Map(data.products);
    }
  }
}

// Save on changes
router.post('/users', (req, res) => {
  const user = store.create('users', req.body);
  store.save(); // Persist to disk
  res.json(user);
});
```

### Issue: CORS errors in production
**Symptoms:** Browser blocks requests
**Diagnosis:** CORS origin mismatch
**Resolution:**
```javascript
// Whitelist specific origins
const corsOptions = {
  origin: (origin, callback) => {
    const whitelist = [
      'http://localhost:3000',
      'https://app.example.com'
    ];
    if (!origin || whitelist.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  }
};

app.use(cors(corsOptions));
```

## Version History

### v1.2.0 (Current)
- Added scenario-based conditional responses
- Implemented rate limiting simulation
- Enhanced error injection with configurable rates
- Added persistent storage option for stateful mode
- Improved OpenAPI 3.1 support

### v1.1.0
- Added stateful mode with in-memory CRUD operations
- Implemented data seeding with faker.js
- Added pagination and filtering support
- Enhanced delay simulation with configurable ranges

### v1.0.0
- Initial release with OpenAPI 3.0 support
- Basic stateless mock generation
- Faker.js integration for realistic data
- Express.js server generation
- CORS and logging middleware

### Planned Features (v1.3.0)
- WebSocket mock support
- GraphQL mock generation
- Redis-backed stateful storage
- Request/response recording for replay
- Docker Compose generation
- Postman collection export
- OpenAPI 3.1 webhooks support
