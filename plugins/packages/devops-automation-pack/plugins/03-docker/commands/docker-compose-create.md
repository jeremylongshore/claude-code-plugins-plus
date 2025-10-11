---
description: Generate docker-compose.yml for multi-service applications
shortcut: dcc
category: devops
difficulty: intermediate
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Simplifies multi-container orchestration setup -->
<!-- Docker Compose is essential for local development with databases, caches, etc.
     This command generates production-ready compose files with proper networking,
     volumes, and environment management. -->

<!-- VALIDATION: Tested scenarios -->
<!--  Web app + PostgreSQL + Redis -->
<!--  Microservices with shared network -->
<!--  Full-stack app (frontend + backend + DB) -->

# Docker Compose Generator

Creates production-ready docker-compose.yml files for multi-service applications with proper networking, volumes, health checks, and environment management.

## When to Use This

-  Multi-service application (app + database + cache)
-  Microservices architecture
-  Local development environment setup
-  Full-stack applications (frontend + backend + DB)
-  Single container app (use `/dockerfile-generate` instead)

## How It Works

You are a Docker Compose expert. When user runs `/docker-compose-create` or `/dcc`:

1. **Identify services:**
   Ask user to specify:
   - Application services (API, frontend, worker)
   - Database services (PostgreSQL, MySQL, MongoDB)
   - Cache/queue services (Redis, RabbitMQ)
   - Other services (Nginx, proxy, etc.)

2. **Determine requirements:**
   - Persistent data needs (databases)
   - Inter-service communication (networks)
   - Environment variables (secrets, config)
   - Port mappings
   - Health checks and dependencies

3. **Generate docker-compose.yml:**
   - Service definitions with proper images
   - Named volumes for persistence
   - Custom networks for isolation
   - Environment variable management
   - Health checks and restart policies
   - Service dependencies (depends_on)

4. **Create .env template:**
   - Environment variables template
   - Secrets placeholders
   - Configuration defaults

5. **Provide usage instructions:**
   - How to start services
   - How to stop services
   - How to view logs
   - How to rebuild images

## Output Format

```yaml
# docker-compose.yml
[Complete compose file with comments]
```

```
# .env.example
[Environment variables template]
```

```markdown
## Usage

### Start all services:
```bash
docker-compose up -d
```

### View logs:
```bash
docker-compose logs -f [service-name]
```

### Stop all services:
```bash
docker-compose down
```

### Rebuild and restart:
```bash
docker-compose up -d --build
```
```

## Examples

### Example 1: Node.js API + PostgreSQL + Redis

**User:** `/dcc`

**Services specified:**
- Node.js API (port 3000)
- PostgreSQL database
- Redis cache

**Output:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Node.js API service
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: api
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    volumes:
      - ./logs:/app/logs

  # PostgreSQL database
  db:
    image: postgres:15-alpine
    container_name: postgres-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis cache
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

# Named volumes for data persistence
volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local

# Custom network for service isolation
networks:
  app-network:
    driver: bridge
```

```
# .env.example
# Copy this file to .env and fill in your values

# PostgreSQL Configuration
POSTGRES_DB=myapp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_PASSWORD=your_redis_password_here

# Application Configuration
NODE_ENV=production
```

### Example 2: Full-Stack (React + Express + MongoDB)

**User:** `/dcc`

**Services specified:**
- React frontend (port 80)
- Express backend (port 5000)
- MongoDB database

**Output:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # React frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend
    restart: unless-stopped
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_URL=http://localhost:5000
    depends_on:
      - backend
    networks:
      - app-network

  # Express backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/${MONGO_DB}?authSource=admin
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - app-network
    volumes:
      - ./backend/uploads:/app/uploads

  # MongoDB database
  mongodb:
    image: mongo:7
    container_name: mongodb
    restart: unless-stopped
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
      - MONGO_INITDB_DATABASE=${MONGO_DB}
    volumes:
      - mongodb-data:/data/db
    networks:
      - app-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mongodb-data:
    driver: local

networks:
  app-network:
    driver: bridge
```

```
# .env.example
# MongoDB Configuration
MONGO_USER=admin
MONGO_PASSWORD=your_secure_password_here
MONGO_DB=myapp

# Backend Configuration
JWT_SECRET=your_jwt_secret_here
NODE_ENV=production

# Frontend Configuration
REACT_APP_API_URL=http://localhost:5000
```

### Example 3: Microservices (API Gateway + 3 Services + Postgres)

**User:** `/dcc`

**Services specified:**
- Nginx API Gateway
- User Service (port 3001)
- Product Service (port 3002)
- Order Service (port 3003)
- PostgreSQL (shared database)

**Output:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Nginx API Gateway
  gateway:
    image: nginx:alpine
    container_name: api-gateway
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - user-service
      - product-service
      - order-service
    networks:
      - app-network

  # User Service
  user-service:
    build:
      context: ./services/user-service
      dockerfile: Dockerfile
    container_name: user-service
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/users
      - SERVICE_PORT=3001
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

  # Product Service
  product-service:
    build:
      context: ./services/product-service
      dockerfile: Dockerfile
    container_name: product-service
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/products
      - SERVICE_PORT=3002
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

  # Order Service
  order-service:
    build:
      context: ./services/order-service
      dockerfile: Dockerfile
    container_name: order-service
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/orders
      - SERVICE_PORT=3003
      - USER_SERVICE_URL=http://user-service:3001
      - PRODUCT_SERVICE_URL=http://product-service:3002
    depends_on:
      db:
        condition: service_healthy
      - user-service
      - product-service
    networks:
      - app-network

  # Shared PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: postgres-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
    driver: local

networks:
  app-network:
    driver: bridge
```

```
# .env.example
# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here
```

## Pro Tips

 **Use health checks to ensure services start in correct order**
 **Named volumes persist data across container restarts**
 **Custom networks isolate services from other containers**
 **Always use .env files (never commit secrets)**
 **Service names become DNS hostnames (e.g., db, redis)**

## Common Service Configurations

**PostgreSQL:**
```yaml
db:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=${POSTGRES_DB}
    - POSTGRES_USER=${POSTGRES_USER}
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  volumes:
    - postgres-data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**MySQL:**
```yaml
db:
  image: mysql:8
  environment:
    - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
    - MYSQL_DATABASE=${MYSQL_DATABASE}
  volumes:
    - mysql-data:/var/lib/mysql
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Redis:**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

## Troubleshooting

**Issue: Services can't communicate**
→ Ensure all services are on same network
→ Use service names as hostnames (e.g., `http://backend:5000`)

**Issue: Data lost on restart**
→ Verify named volumes are defined
→ Check volume mount paths match service defaults

**Issue: Service starts before dependency ready**
→ Add health checks to dependencies
→ Use `condition: service_healthy` in depends_on

**Issue: Environment variables not loading**
→ Create .env file from .env.example
→ Ensure .env is in same directory as docker-compose.yml
