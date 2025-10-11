---
description: Generate Docker Compose configurations
---

# Docker Compose Generator

Generate production-ready Docker Compose files with best practices.

## Configuration Patterns

1. **Multi-Service Architecture**: Define all services with dependencies
2. **Environment Variables**: Use .env files for configuration
3. **Volume Management**: Persistent data and named volumes
4. **Network Configuration**: Custom networks for service isolation
5. **Health Checks**: Service health monitoring
6. **Resource Limits**: CPU and memory constraints

## Example Docker Compose (Full Stack)

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://api:4000
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "4000:4000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./api/logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
    networks:
      - app-network
      - db-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - db-network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - api
    networks:
      - app-network

volumes:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
  db-network:
    driver: bridge
```

## Best Practices Included

- Service dependencies with health checks
- Named volumes for data persistence
- Custom networks for isolation
- Resource limits for stability
- Environment variable management
- Multi-stage builds support
- Health check configurations
- Logging and monitoring ready

## When Invoked

Generate complete Docker Compose configurations based on application architecture requirements.
