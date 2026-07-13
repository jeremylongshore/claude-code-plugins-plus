# Docker Compose Setup

## Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
    deploy:
      replicas: 2

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - REDIS_HOST=redis
      - KLINGAI_API_KEY=${KLINGAI_API_KEY}
    depends_on:
      - redis
    deploy:
      replicas: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api

volumes:
  redis_data:
```
