# Deployment

OpenGov-Food can be deployed using various methods including Docker, cloud platforms, and traditional server deployments.

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /home/app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R app:app /home/app

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "opengovfood.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  opengovfood:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/opengovfood.db
      - SECRET_KEY=your-production-secret-key
      - ENVIRONMENT=production
    volumes:
      - ./data:/home/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - opengovfood
    restart: unless-stopped
```

### Building and Running

```bash
# Build Docker image
docker build -t opengovfood .

# Run with Docker
docker run -p 8000:8000 -e SECRET_KEY=your-secret-key opengovfood

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f opengovfood
```

## Cloud Deployment

### Heroku

```yaml
# Procfile
web: uvicorn opengovfood.web.app:app --host=0.0.0.0 --port=$PORT
```

```bash
# Deploy to Heroku
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-database-url
git push heroku main
```

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render

```yaml
# render.yaml
services:
  - type: web
    name: opengovfood
    runtime: python3
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn opengovfood.web.app:app --host 0.0.0.0 --port 10000
    envVars:
      - key: SECRET_KEY
        value: your-secret-key
      - key: DATABASE_URL
        value: your-database-url
      - key: ENVIRONMENT
        value: production
```

### AWS

#### Elastic Beanstalk

```python
# .ebextensions/python.config
option_settings:
  aws:elasticbeanstalk:application:environment:
    SECRET_KEY: your-secret-key
    DATABASE_URL: your-database-url
  aws:elasticbeanstalk:container:python:
    WSGIPath: opengovfood.web.app:app
```

#### ECS with Fargate

```yaml
# task-definition.json
{
  "family": "opengovfood",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "opengovfood",
      "image": "your-registry/opengovfood:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "SECRET_KEY", "value": "your-secret-key"},
        {"name": "DATABASE_URL", "value": "your-database-url"},
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/opengovfood",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud

#### Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/project-id/opengovfood
gcloud run deploy --image gcr.io/project-id/opengovfood --platform managed
```

#### App Engine

```yaml
# app.yaml
runtime: python311

env_variables:
  SECRET_KEY: your-secret-key
  DATABASE_URL: your-database-url

handlers:
- url: /.*
  script: auto
```

## Traditional Server Deployment

### System Requirements

- Ubuntu 20.04+ or CentOS 8+
- Python 3.11+
- 2GB RAM minimum
- 10GB disk space

### Ubuntu Deployment

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL (optional)
sudo apt install postgresql postgresql-contrib -y

# Create application user
sudo useradd --create-home --shell /bin/bash opengovfood

# Create application directory
sudo mkdir /opt/opengovfood
sudo chown opengovfood:opengovfood /opt/opengovfood

# Switch to application user
sudo -u opengovfood bash

# Clone repository
cd /opt/opengovfood
git clone https://github.com/your-org/opengovfood.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from opengovfood.core.database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager.initialize())"

# Create environment file
cat > .env << EOF
SECRET_KEY=your-production-secret-key
DATABASE_URL=sqlite+aiosqlite:///./opengovfood.db
ENVIRONMENT=production
EOF

# Exit application user
exit
```

### Systemd Service

```bash
# Create systemd service file
sudo tee /etc/systemd/system/opengovfood.service > /dev/null <<EOF
[Unit]
Description=OpenGov-Food FastAPI Application
After=network.target

[Service]
User=opengovfood
Group=opengovfood
WorkingDirectory=/opt/opengovfood
Environment=PATH=/opt/opengovfood/venv/bin
ExecStart=/opt/opengovfood/venv/bin/uvicorn opengovfood.web.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable opengovfood
sudo systemctl start opengovfood

# Check status
sudo systemctl status opengovfood
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/opengovfood
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/opengovfood/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/opengovfood /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Test renewal
sudo certbot renew --dry-run
```

## Environment Configuration

### Production Environment Variables

```bash
# Application
SECRET_KEY=your-very-long-random-secret-key-here
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/opengovfood

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging
LOG_LEVEL=INFO

# Optional: External services
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your-sentry-dsn
```

### Database Setup

#### PostgreSQL

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE opengovfood;
CREATE USER opengovfood_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE opengovfood TO opengovfood_user;
ALTER USER opengovfood_user CREATEDB;

# Exit PostgreSQL
\q
```

#### SQLite (Simple)

```bash
# SQLite is file-based, just ensure write permissions
sudo chown opengovfood:opengovfood /opt/opengovfood/opengovfood.db
```

## Monitoring and Logging

### Application Monitoring

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    # Return application metrics
    return {
        "uptime": get_uptime(),
        "requests_total": get_request_count(),
        "active_connections": get_active_connections()
    }
```

### Log Aggregation

```python
# Structured logging configuration
import structlog

shared_processors = [
    structlog.stdlib.filter_by_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

if ENVIRONMENT == "production":
    # JSON logging for production
    shared_processors.append(structlog.processors.JSONRenderer())
else:
    # Colored console logging for development
    shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))

structlog.configure(
    processors=shared_processors,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Monitoring Tools

#### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)

    return response

@app.get("/metrics")
def metrics():
    return generate_latest()
```

#### Sentry Error Tracking

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[
        FastAPIIntegration(),
        SqlalchemyIntegration(),
    ],
    environment=ENVIRONMENT,
    traces_sample_rate=1.0,
)
```

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -U opengovfood_user -h localhost opengovfood > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite backup (simple file copy)
cp /opt/opengovfood/opengovfood.db /opt/opengovfood/backup/opengovfood_$(date +%Y%m%d_%H%M%S).db
```

### Automated Backups

```bash
# Create backup script
sudo tee /opt/opengovfood/backup.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/opt/opengovfood/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
cp /opt/opengovfood/opengovfood.db $BACKUP_DIR/opengovfood_$TIMESTAMP.db

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "opengovfood_*.db" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/opengovfood_$TIMESTAMP.db"
EOF

# Make executable and schedule
sudo chmod +x /opt/opengovfood/backup.sh
sudo crontab -e

# Add to crontab (daily at 2 AM)
# 0 2 * * * /opt/opengovfood/backup.sh
```

## Scaling

### Horizontal Scaling

```bash
# Run multiple instances behind load balancer
uvicorn opengovfood.web.app:app --host 0.0.0.0 --port 8000 --workers 4

# Use process manager
gunicorn opengovfood.web.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Load Balancing

```nginx
# Nginx load balancer configuration
upstream opengovfood_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://opengovfood_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Hardening

### Server Security

```bash
# Disable root login
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Use fail2ban for SSH protection
sudo apt install fail2ban -y

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### Application Security

```python
# Security middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com"]
)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
```

## Troubleshooting

### Common Deployment Issues

**Application won't start:**
```bash
# Check logs
sudo journalctl -u opengovfood -f

# Check environment variables
sudo -u opengovfood bash -c "cd /opt/opengovfood && source venv/bin/activate && python -c 'import opengovfood'"

# Check database connection
sudo -u opengovfood bash -c "cd /opt/opengovfood && source venv/bin/activate && python -c 'from opengovfood.core.database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager.test_connection())'"
```

**High memory usage:**
```bash
# Monitor memory usage
ps aux --sort=-%mem | head

# Adjust worker count
# Reduce workers in systemd service
sudo systemctl edit opengovfood
# Change --workers 4 to --workers 2
sudo systemctl restart opengovfood
```

**Slow response times:**
```bash
# Check database performance
sudo -u postgres psql -d opengovfood -c "SELECT * FROM pg_stat_activity;"

# Add database indexes
sudo -u opengovfood bash -c "cd /opt/opengovfood && source venv/bin/activate && alembic upgrade head"

# Enable query logging
# Add to .env: SQLALCHEMY_ECHO=true
```

**SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -text -noout

# Renew certificate
sudo certbot renew

# Check nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

## Performance Optimization

### Database Optimization

```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_item_owner_created ON item (owner_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_item_status ON item (status);

-- Analyze tables
ANALYZE item;
ANALYZE "user";

-- Vacuum for maintenance
VACUUM ANALYZE;
```

### Application Optimization

```python
# Connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# Response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@cache(expire=300)  # 5 minutes
@app.get("/api/v1/items/")
async def get_items():
    # Cached response
    pass

# Background task processing
from fastapi import BackgroundTasks

@app.post("/api/v1/items/")
async def create_item(background_tasks: BackgroundTasks):
    # Quick response
    background_tasks.add_task(process_item_creation)
    return {"message": "Item creation started"}
```

## Maintenance

### Regular Tasks

```bash
# Update application
cd /opt/opengovfood
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart opengovfood

# Database maintenance
sudo -u postgres psql -d opengovfood -c "VACUUM ANALYZE;"

# Log rotation
sudo logrotate /etc/logrotate.d/opengovfood

# Security updates
sudo apt update && sudo apt upgrade -y
```

### Monitoring Scripts

```bash
# Health check script
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ $STATUS -eq 200 ]; then
    echo "Application is healthy"
    exit 0
else
    echo "Application is unhealthy (status: $STATUS)"
    exit 1
fi
```

This comprehensive deployment guide covers everything from simple Docker deployment to complex production setups with monitoring, security, and scaling considerations.