# Skill: Docker — Official Best Practices
# Source: docs.docker.com/develop/develop-images/dockerfile_best-practices/

## Dockerfile Principles
- Use official slim base images: `python:3.12-slim`, `node:20-alpine`.
- Multi-stage builds: build stage compiles/installs, final stage copies only artifacts.
- Order layers from least-to-most-frequently-changed: OS packages → pip install → app code.
- Pin versions explicitly: `FROM python:3.12.3-slim`.

## Layer Efficiency
```dockerfile
# Good — single RUN reduces layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install deps before copying code (cache hit on rebuild)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

## Security
- Never run as root: `RUN adduser --disabled-password app && USER app`
- Never bake secrets into image — use env vars or secrets at runtime.
- `.dockerignore`: exclude `.git`, `__pycache__`, `.env`, `*.log`, `node_modules`.
- Scan images: `docker scout cves <image>` or `trivy image <image>`.

## Runtime & Compose
```yaml
# docker-compose.yml essentials
services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}   # from host env, not hardcoded
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      retries: 3
```

## Key Commands
```bash
docker build -t app:latest --no-cache .
docker run --rm -p 8000:8000 --env-file .env app:latest
docker system prune -f        # clean dangling images/containers
docker logs -f <container>    # tail logs
```
