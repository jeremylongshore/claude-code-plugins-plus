---
description: Generate production-ready Express.js REST API with TypeScript and auth
shortcut: eas
category: backend
difficulty: intermediate
estimated_time: 5-10 minutes
---

# Express API Scaffold

Generates a complete Express.js REST API boilerplate with TypeScript, authentication, database integration, and testing setup.

## What This Command Does

**Generated Project:**
-  Express.js with TypeScript
-  JWT authentication
-  Database integration (Prisma or TypeORM)
-  Input validation (Zod)
-  Error handling middleware
-  Rate limiting & security (Helmet, CORS)
-  Testing setup (Jest + Supertest)
-  Docker configuration
-  Example CRUD endpoints

**Output:** Complete API project ready for development

**Time:** 5-10 minutes

---

## Usage

```bash
# Generate full Express API
/express-api-scaffold "Task Management API"

# Shortcut
/eas "E-commerce API"

# With specific database
/eas "Blog API" --database postgresql

# With authentication type
/eas "Social API" --auth jwt --database mongodb
```

---

## Example Output

**Input:**
```
/eas "Task Management API" --database postgresql
```

**Generated Project Structure:**
```
task-api/
├── src/
│   ├── controllers/        # Request handlers
│   │   ├── auth.controller.ts
│   │   └── task.controller.ts
│   ├── middleware/         # Express middleware
│   │   ├── auth.middleware.ts
│   │   ├── error.middleware.ts
│   │   └── validation.middleware.ts
│   ├── models/            # Database models
│   │   └── task.model.ts
│   ├── routes/            # API routes
│   │   ├── auth.routes.ts
│   │   └── task.routes.ts
│   ├── services/          # Business logic
│   │   ├── auth.service.ts
│   │   └── task.service.ts
│   ├── utils/             # Utilities
│   │   ├── jwt.util.ts
│   │   └── password.util.ts
│   ├── config/            # Configuration
│   │   └── database.ts
│   ├── types/             # TypeScript types
│   │   └── express.d.ts
│   ├── app.ts             # Express app setup
│   └── server.ts          # Server entry point
├── tests/
│   ├── auth.test.ts
│   └── task.test.ts
├── prisma/
│   └── schema.prisma      # Database schema
├── .env.example
├── .gitignore
├── package.json
├── tsconfig.json
├── jest.config.js
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Generated Files

### 1. **src/server.ts** (Entry Point)

```typescript
import app from './app'
import { config } from './config'

const PORT = process.env.PORT || 3000

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
  console.log(`Environment: ${process.env.NODE_ENV}`)
})
```

### 2. **src/app.ts** (Express Setup)

```typescript
import express, { Application } from 'express'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import rateLimit from 'express-rate-limit'

import authRoutes from './routes/auth.routes'
import taskRoutes from './routes/task.routes'
import { errorHandler } from './middleware/error.middleware'
import { notFoundHandler } from './middleware/notFound.middleware'

const app: Application = express()

// Security middleware
app.use(helmet())
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true
}))

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests, please try again later'
})
app.use('/api/', limiter)

// Parsing middleware
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined'))
}

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// Routes
app.use('/api/auth', authRoutes)
app.use('/api/tasks', taskRoutes)

// Error handling
app.use(notFoundHandler)
app.use(errorHandler)

export default app
```

### 3. **src/controllers/auth.controller.ts**

```typescript
import { Request, Response, NextFunction } from 'express'
import { AuthService } from '../services/auth.service'
import { ApiError } from '../utils/ApiError'

const authService = new AuthService()

export class AuthController {
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      const { email, password, name } = req.body

      const result = await authService.register({ email, password, name })

      res.status(201).json({
        data: {
          user: result.user,
          token: result.token
        }
      })
    } catch (error) {
      next(error)
    }
  }

  async login(req: Request, res: Response, next: NextFunction) {
    try {
      const { email, password } = req.body

      const result = await authService.login(email, password)

      res.json({
        data: {
          user: result.user,
          token: result.token
        }
      })
    } catch (error) {
      next(error)
    }
  }

  async getProfile(req: Request, res: Response, next: NextFunction) {
    try {
      const userId = req.user!.id

      const user = await authService.getUserById(userId)

      res.json({ data: user })
    } catch (error) {
      next(error)
    }
  }
}
```

### 4. **src/middleware/auth.middleware.ts**

```typescript
import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'
import { ApiError } from '../utils/ApiError'

interface JwtPayload {
  userId: string
  email: string
}

declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string
        email: string
      }
    }
  }
}

export function authenticate(req: Request, res: Response, next: NextFunction) {
  try {
    const authHeader = req.headers.authorization

    if (!authHeader?.startsWith('Bearer ')) {
      throw new ApiError(401, 'No token provided')
    }

    const token = authHeader.split(' ')[1]

    const decoded = jwt.verify(
      token,
      process.env.JWT_SECRET!
    ) as JwtPayload

    req.user = {
      id: decoded.userId,
      email: decoded.email
    }

    next()
  } catch (error) {
    if (error instanceof jwt.JsonWebTokenError) {
      next(new ApiError(401, 'Invalid token'))
    } else {
      next(error)
    }
  }
}
```

### 5. **src/middleware/error.middleware.ts**

```typescript
import { Request, Response, NextFunction } from 'express'
import { ApiError } from '../utils/ApiError'
import { ZodError } from 'zod'

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  console.error('Error:', err)

  // Handle known API errors
  if (err instanceof ApiError) {
    return res.status(err.statusCode).json({
      error: {
        code: err.name,
        message: err.message,
        ...(err.details && { details: err.details })
      }
    })
  }

  // Handle validation errors (Zod)
  if (err instanceof ZodError) {
    return res.status(400).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Validation failed',
        details: err.errors.map(e => ({
          field: e.path.join('.'),
          message: e.message
        }))
      }
    })
  }

  // Handle unexpected errors
  res.status(500).json({
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: process.env.NODE_ENV === 'production'
        ? 'An unexpected error occurred'
        : err.message
    }
  })
}
```

### 6. **src/routes/task.routes.ts**

```typescript
import { Router } from 'express'
import { TaskController } from '../controllers/task.controller'
import { authenticate } from '../middleware/auth.middleware'
import { validate } from '../middleware/validation.middleware'
import { createTaskSchema, updateTaskSchema } from '../schemas/task.schema'

const router = Router()
const taskController = new TaskController()

// All routes require authentication
router.use(authenticate)

router.get('/', taskController.list)
router.post('/', validate(createTaskSchema), taskController.create)
router.get('/:id', taskController.getById)
router.patch('/:id', validate(updateTaskSchema), taskController.update)
router.delete('/:id', taskController.delete)

export default router
```

### 7. **src/services/task.service.ts**

```typescript
import { PrismaClient } from '@prisma/client'
import { ApiError } from '../utils/ApiError'

const prisma = new PrismaClient()

export class TaskService {
  async create(userId: string, data: { title: string; description?: string }) {
    return await prisma.task.create({
      data: {
        ...data,
        userId
      }
    })
  }

  async findAll(userId: string) {
    return await prisma.task.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' }
    })
  }

  async findById(id: string, userId: string) {
    const task = await prisma.task.findUnique({
      where: { id }
    })

    if (!task) {
      throw new ApiError(404, 'Task not found')
    }

    if (task.userId !== userId) {
      throw new ApiError(403, 'Access denied')
    }

    return task
  }

  async update(id: string, userId: string, data: Partial<{ title: string; description: string; completed: boolean }>) {
    await this.findById(id, userId) // Check ownership

    return await prisma.task.update({
      where: { id },
      data
    })
  }

  async delete(id: string, userId: string) {
    await this.findById(id, userId) // Check ownership

    await prisma.task.delete({
      where: { id }
    })
  }
}
```

### 8. **prisma/schema.prisma** (Database Schema)

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  password  String
  name      String
  tasks     Task[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("users")
}

model Task {
  id          String   @id @default(uuid())
  title       String
  description String?
  completed   Boolean  @default(false)
  userId      String
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([userId])
  @@map("tasks")
}
```

### 9. **tests/task.test.ts** (Integration Tests)

```typescript
import request from 'supertest'
import app from '../src/app'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

describe('Task API', () => {
  let authToken: string
  let userId: string

  beforeAll(async () => {
    // Create test user and get token
    const res = await request(app)
      .post('/api/auth/register')
      .send({
        email: '[email protected]',
        password: 'password123',
        name: 'Test User'
      })

    authToken = res.body.data.token
    userId = res.body.data.user.id
  })

  afterAll(async () => {
    // Cleanup
    await prisma.task.deleteMany({ where: { userId } })
    await prisma.user.delete({ where: { id: userId } })
    await prisma.$disconnect()
  })

  describe('POST /api/tasks', () => {
    it('should create a new task', async () => {
      const res = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          title: 'Test Task',
          description: 'Test description'
        })

      expect(res.status).toBe(201)
      expect(res.body.data).toHaveProperty('id')
      expect(res.body.data.title).toBe('Test Task')
    })

    it('should require authentication', async () => {
      const res = await request(app)
        .post('/api/tasks')
        .send({ title: 'Test' })

      expect(res.status).toBe(401)
    })
  })

  describe('GET /api/tasks', () => {
    it('should list user tasks', async () => {
      const res = await request(app)
        .get('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)

      expect(res.status).toBe(200)
      expect(Array.isArray(res.body.data)).toBe(true)
    })
  })
})
```

### 10. **package.json**

```json
{
  "name": "task-api",
  "version": "1.0.0",
  "scripts": {
    "dev": "ts-node-dev --respawn --transpile-only src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "format": "prettier --write \"src/**/*.ts\"",
    "db:migrate": "prisma migrate dev",
    "db:push": "prisma db push",
    "db:generate": "prisma generate"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5",
    "morgan": "^1.10.0",
    "bcrypt": "^5.1.1",
    "jsonwebtoken": "^9.0.2",
    "zod": "^3.22.4",
    "@prisma/client": "^5.8.0",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.6",
    "@types/cors": "^2.8.17",
    "@types/morgan": "^1.9.9",
    "@types/bcrypt": "^5.0.2",
    "@types/jsonwebtoken": "^9.0.5",
    "@types/jest": "^29.5.11",
    "@types/supertest": "^6.0.2",
    "typescript": "^5.3.3",
    "ts-node-dev": "^2.0.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.1",
    "supertest": "^6.3.3",
    "prisma": "^5.8.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.1"
  }
}
```

---

## Features

**Security:**
- Helmet.js for HTTP headers
- CORS with configurable origins
- Rate limiting (100 req/15min)
- JWT authentication
- Password hashing (bcrypt)
- Input validation (Zod)

**Database:**
- Prisma ORM with TypeScript
- Automatic migrations
- Type-safe queries
- Supports PostgreSQL, MySQL, SQLite

**Testing:**
- Jest + Supertest
- Integration tests
- Coverage reporting
- Test database isolation

**Development:**
- Hot reload (ts-node-dev)
- TypeScript with strict mode
- ESLint + Prettier
- Environment variables

**Production:**
- Docker support
- Health check endpoint
- Error logging
- Graceful shutdown

---

## Getting Started

**1. Install dependencies:**
```bash
npm install
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database URL and secrets
```

**3. Run database migrations:**
```bash
npm run db:migrate
```

**4. Start development server:**
```bash
npm run dev
```

**5. Run tests:**
```bash
npm test
```

---

## Related Commands

- `/fastapi-scaffold` - Generate FastAPI boilerplate
- Backend Architect (agent) - Architecture review
- API Builder (agent) - API design guidance

---

**Build production-ready APIs. Ship faster. Scale confidently.** 
