# Deployment Guide

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Python 3.11+ (for local deployment)
- PostgreSQL 12+ (optional, for production)

## Local Development

### 1. Setup

```bash
# Clone and navigate
git clone <repo-url>
cd smart-task-tracker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env as needed
```

### 2. Run Database Migrations

```bash
# With SQLite (default)
alembic upgrade head

# With PostgreSQL
alembic upgrade head
```

### 3. Start Development Server

```bash
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`

## Docker Deployment

### Quick Start (SQLite)

```bash
# Build and run with SQLite
docker-compose up --build

# Access API
curl http://localhost:8000/health

# Access docs
open http://localhost:8000/docs
```

### With PostgreSQL

```bash
# Start with PostgreSQL profile
docker-compose --profile postgres up --build

# Run migrations inside container
docker exec smart-tracker-app alembic upgrade head
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Remove volumes (careful!)
docker-compose down -v
```

## Production Deployment

### Environment Setup

Update `.env` for production:

```env
DEBUG=false
SECRET_KEY=<generate-strong-random-key>
ALLOWED_ORIGINS=https://your-domain.com
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/app_db
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD_SECONDS=60
```

### Using Docker

```bash
# Build production image
docker build -t smart-task-tracker:latest .

# Run container
docker run -d \
  --name smart-tracker \
  -p 8000:8000 \
  --env-file .env \
  -v tracker_data:/app/data \
  smart-task-tracker:latest
```

### Using Kubernetes

Create a deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smart-task-tracker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smart-task-tracker
  template:
    metadata:
      labels:
        app: smart-task-tracker
    spec:
      containers:
      - name: app
        image: smart-task-tracker:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database_url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret_key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Using Gunicorn

For production ASGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with workers
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  src.app.main:app
```

### Using Nginx as Reverse Proxy

```nginx
upstream app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SSL configuration
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}
```

## Database Setup

### SQLite (Development/Small Deployments)

Already configured by default. Data stored in `./data/tasks.db`

### PostgreSQL (Production)

1. Create database and user:

```sql
CREATE USER tracker_user WITH PASSWORD 'secure_password';
CREATE DATABASE smart_tracker OWNER tracker_user;
GRANT ALL PRIVILEGES ON DATABASE smart_tracker TO tracker_user;
```

2. Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://tracker_user:secure_password@db-host:5432/smart_tracker
```

3. Run migrations:

```bash
alembic upgrade head
```

## Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use HTTPS/TLS for all connections
- [ ] Set `DEBUG=false`
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Use strong database passwords
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Monitor logs and metrics
- [ ] Implement backup strategy
- [ ] Use environment variables for secrets
- [ ] Run security scanning in CI/CD
- [ ] Keep dependencies updated

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# Docker
docker logs smart-tracker-app

# File-based
tail -f logs/app.log
```

### Metrics

Monitor:
- Request response times
- Rate limit violations
- Database connection pool usage
- Error rates
- API endpoint usage

## Backup & Recovery

### SQLite Backup

```bash
# Backup
cp ./data/tasks.db ./data/tasks.db.backup

# Restore
cp ./data/tasks.db.backup ./data/tasks.db
```

### PostgreSQL Backup

```bash
# Backup
pg_dump -U tracker_user smart_tracker > backup.sql

# Restore
psql -U tracker_user smart_tracker < backup.sql
```

## Migration Strategy

### Zero-Downtime Deployments

1. Keep old and new API versions running
2. Gradually shift traffic
3. Monitor error rates
4. Roll back if issues detected

```bash
# Canary deployment
docker service update \
  --image smart-task-tracker:new-version \
  --update-parallelism 1 \
  --update-delay 10s \
  smart-tracker
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs smart-tracker-app

# Verify environment variables
docker inspect smart-tracker-app | grep Env

# Test manually
docker run -it smart-task-tracker:latest /bin/bash
```

### Database connection errors

```bash
# Check PostgreSQL connection
pg_isready -h db-host -p 5432 -U tracker_user

# Test in container
docker exec -it smart-tracker-app \
  python -c "from sqlalchemy import create_engine; print('OK')"
```

### High memory usage

- Reduce number of workers
- Check for memory leaks in logs
- Implement connection pooling limits

## Performance Tuning

### Database

```env
# Connection pool
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
```

### Rate Limiting

```env
RATE_LIMIT_REQUESTS=200  # Increase for higher traffic
RATE_LIMIT_PERIOD_SECONDS=60
```

### Uvicorn Workers

```bash
gunicorn \
  --workers 4 \  # Match CPU cores
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  src.app.main:app
```

## Support

For issues or questions, see:
- [README.md](README.md) - Feature overview
- [TESTING.md](TESTING.md) - Testing guide
- GitHub Issues
