---
description: Generate complete fullstack project structure with all boilerplate
shortcut: ps
category: devops
difficulty: beginner
estimated_time: 5-10 minutes
---

# Project Scaffold

Generates a complete fullstack project structure with frontend, backend, database, authentication, testing, and deployment configuration.

## What This Command Does

**Generated Project:**
- ✅ Frontend (React + TypeScript + Vite)
- ✅ Backend (Express or FastAPI)
- ✅ Database (PostgreSQL + Prisma/SQLAlchemy)
- ✅ Authentication (JWT + OAuth)
- ✅ Testing (Jest/Pytest + E2E)
- ✅ CI/CD (GitHub Actions)
- ✅ Docker setup
- ✅ Documentation

**Output:** Production-ready fullstack application

**Time:** 5-10 minutes

---

## Usage

```bash
# Generate fullstack project
/project-scaffold "Task Management App"

# Shortcut
/ps "E-commerce Platform" --stack react,express,postgresql

# With specific features
/ps "Blog Platform" --features auth,admin,payments,analytics
```

---

## Generated Structure

```
my-app/
├── client/                    # Frontend (React + TypeScript + Vite)
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API services
│   │   ├── context/          # Context providers
│   │   ├── utils/            # Utilities
│   │   ├── types/            # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
│
├── server/                    # Backend (Express + TypeScript)
│   ├── src/
│   │   ├── controllers/      # Request handlers
│   │   ├── services/         # Business logic
│   │   ├── models/           # Database models
│   │   ├── routes/           # API routes
│   │   ├── middleware/       # Express middleware
│   │   ├── utils/            # Utilities
│   │   ├── config/           # Configuration
│   │   ├── app.ts
│   │   └── server.ts
│   ├── tests/
│   ├── prisma/
│   │   └── schema.prisma
│   ├── package.json
│   ├── tsconfig.json
│   └── jest.config.js
│
├── .github/
│   └── workflows/
│       ├── ci.yml            # Continuous Integration
│       └── deploy.yml        # Deployment
│
├── docker-compose.yml         # Development environment
├── Dockerfile                 # Production container
├── .env.example              # Environment template
├── .gitignore
├── README.md
└── package.json              # Root workspace
```

---

## Example: Task Management App

**Frontend (client/src/pages/Dashboard.tsx):**
```tsx
import { useState, useEffect } from 'react'
import { TaskList } from '../components/TaskList'
import { CreateTaskForm } from '../components/CreateTaskForm'
import { useAuth } from '../context/AuthContext'
import { taskService } from '../services/api'

export function Dashboard() {
  const { user } = useAuth()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTasks()
  }, [])

  async function loadTasks() {
    try {
      const data = await taskService.getAll()
      setTasks(data)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateTask(task: CreateTaskInput) {
    const newTask = await taskService.create(task)
    setTasks([newTask, ...tasks])
  }

  async function handleToggleTask(id: string) {
    const updated = await taskService.toggle(id)
    setTasks(tasks.map(t => t.id === id ? updated : t))
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">
        Welcome, {user?.name}
      </h1>

      <CreateTaskForm onSubmit={handleCreateTask} />

      <TaskList
        tasks={tasks}
        onToggle={handleToggleTask}
      />
    </div>
  )
}
```

**Backend (server/src/controllers/task.controller.ts):**
```typescript
import { Request, Response } from 'express'
import { TaskService } from '../services/task.service'

const taskService = new TaskService()

export class TaskController {
  async getAll(req: Request, res: Response) {
    const tasks = await taskService.findAll(req.user!.userId)
    res.json({ data: tasks })
  }

  async create(req: Request, res: Response) {
    const task = await taskService.create(req.user!.userId, req.body)
    res.status(201).json({ data: task })
  }

  async toggle(req: Request, res: Response) {
    const task = await taskService.toggle(req.params.id, req.user!.userId)
    res.json({ data: task })
  }

  async delete(req: Request, res: Response) {
    await taskService.delete(req.params.id, req.user!.userId)
    res.status(204).send()
  }
}
```

---

## Quick Start

**1. Install dependencies:**
```bash
# Install all dependencies (client + server)
npm install

# Or individually
cd client && npm install
cd server && npm install
```

**2. Setup environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

**3. Setup database:**
```bash
cd server
npx prisma migrate dev
npx prisma generate
```

**4. Start development:**
```bash
# Start all services (client, server, database)
docker-compose up

# Or start individually
npm run dev:client   # Frontend on http://localhost:5173
npm run dev:server   # Backend on http://localhost:3000
```

**5. Run tests:**
```bash
npm run test         # All tests
npm run test:client  # Frontend tests
npm run test:server  # Backend tests
```

---

## Stack Options

**Frontend:**
- React + TypeScript + Vite (default)
- Next.js 14 (App Router)
- Vue 3 + TypeScript

**Backend:**
- Express + TypeScript (default)
- FastAPI + Python
- NestJS

**Database:**
- PostgreSQL + Prisma (default)
- MongoDB + Mongoose
- MySQL + TypeORM

**Styling:**
- Tailwind CSS (default)
- CSS Modules
- Styled Components

---

## Included Features

**Authentication:**
- JWT authentication
- OAuth (Google, GitHub)
- Email verification
- Password reset

**Testing:**
- Frontend: Jest + React Testing Library + Cypress
- Backend: Jest + Supertest
- E2E: Playwright

**CI/CD:**
- GitHub Actions workflows
- Automated testing
- Docker build and push
- Deployment to cloud platforms

**Development:**
- Hot reload (frontend + backend)
- Docker development environment
- Database migrations
- Seed data

**Production:**
- Optimized Docker images
- Health checks
- Logging and monitoring
- Environment-based config

---

## Customization

**Add Features:**
```bash
# Add payment processing
/ps --add-feature payments --provider stripe

# Add file uploads
/ps --add-feature uploads --storage s3

# Add email service
/ps --add-feature email --provider sendgrid

# Add admin dashboard
/ps --add-feature admin
```

**Change Stack:**
```bash
# Use Next.js instead of React
/ps --frontend nextjs

# Use FastAPI instead of Express
/ps --backend fastapi

# Use MongoDB instead of PostgreSQL
/ps --database mongodb
```

---

## Deployment

**Vercel (Frontend):**
```bash
cd client
vercel
```

**Railway (Backend):**
```bash
cd server
railway up
```

**Docker (Full Stack):**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Related Commands

- `/express-api-scaffold` - Generate Express API
- `/fastapi-scaffold` - Generate FastAPI
- `/auth-setup` - Authentication boilerplate
- `/env-config-setup` - Environment configuration

---

**Start building immediately. Ship faster. Scale effortlessly.** 🚀
