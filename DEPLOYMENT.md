# RAG Enterprise - Deployment Guide

**Version**: v7.0.0+ | **Status**: Production Ready ✅

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd new_rag

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# Access the application
open http://localhost/
```

---

## Architecture Overview

### Services (17 containers)

| Service | Port(s) | Purpose | Status |
|---------|---------|---------|--------|
| **nginx** | 80, 443 | Reverse proxy & frontend | ✅ Running |
| **api** | 8001 | FastAPI backend | ✅ Running |
| **postgres** | 15432 | Main database | ✅ Healthy |
| **redis** | 16379 | Cache & pub/sub | ✅ Healthy |
| **qdrant** | 16333, 16334 | Vector database | ✅ Running |
| **keycloak** | 8080 | Authentication | ✅ Running |
| **vault** | 8200 | Secrets management | ✅ Running |
| **clickhouse** | 8123, 9000 | Analytics database | ✅ Healthy |
| **kafka** | 9092 | Message broker | ✅ Healthy |
| **zookeeper** | 2181 | Kafka coordination | ✅ Healthy |
| **jaeger** | 16686 | Distributed tracing | ✅ Running |
| **prometheus** | 9090 | Metrics collection | ✅ Running |
| **grafana** | 3000 | Monitoring dashboard | ✅ Running |
| **minio** | 9001, 9002 | Object storage | ✅ Healthy |
| **airflow-webserver** | 8082 | Workflow UI | ✅ Running |
| **airflow-scheduler** | - | Workflow scheduler | ✅ Running |
| **metabase** | 3001 | BI dashboard | ✅ Running |

---

## Environment Configuration

### Required Environment Variables

```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=qdrant
QDRANT_HTTP_PORT=6333

# Ollama (if using)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# CORS
ALLOWED_ORIGINS=http://localhost,http://your-domain.com

# Optional: External URLs for production
# DB_HOST=postgres
# CLICKHOUSE_HOST=clickhouse
# KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

---

## Deployment Steps

### 1. Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api nginx

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### 2. Production Deployment

#### Prerequisites
- Docker & Docker Compose installed
- Domain name configured (for HTTPS)
- Firewall rules configured
- SSL certificates (Let's Encrypt recommended)

#### Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd new_rag

# 2. Configure environment
cp .env.example .env
nano .env  # Set production values

# 3. Configure nginx for your domain
nano nginx.conf
# - Replace server_name with your domain
# - Uncomment HTTPS configuration
# - Add SSL certificate paths

# 4. Set up SSL certificates (Let's Encrypt)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 5. Start services
docker-compose up -d

# 6. Verify deployment
curl https://your-domain.com/health/live
```

---

## Remote Access Configuration

### Option 1: Direct Public Access

1. **Update docker-compose.yml**
   - Nginx already bound to 0.0.0.0:80 and 0.0.0.0:443
   - Accessible from any network interface

2. **Firewall Configuration**
   ```bash
   # Allow HTTP/HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **DNS Configuration**
   - Point your domain to server IP
   - Add A record: `your-domain.com` → `your.server.ip`

### Option 2: SSH Tunnel (Development)

```bash
# From local machine
ssh -L 8080:localhost:80 user@your-server

# Access at http://localhost:8080
```

### Option 3: Tailscale/Zerotier (Secure Private Network)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Access via Tailscale IP
# http://100.x.x.x/
```

---

## Nginx Reverse Proxy

### Current Configuration

- **Frontend**: Static files served from `/usr/share/nginx/html`
- **API**: Proxied to `http://api:8001/api/`
- **WebSocket**: `http://api:8001/socket.io/`
- **Keycloak**: Proxied to `http://keycloak:8080/auth/`
- **Health**: `http://api:8001/health/`

### SSL/HTTPS Setup

```nginx
# nginx.conf (HTTPS section)
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... (same location blocks)
}
```

---

## Frontend API Endpoints

All frontend pages now use relative URLs that work through nginx:

```javascript
// API calls (automatically proxied)
const API_BASE = '/api/v1';

// Examples
fetch('/api/v1/debug/system-info')
fetch('/health/live')
fetch('/socket.io/')  // WebSocket
```

---

## Monitoring & Health Checks

### Health Endpoints

```bash
# Liveness (is API running?)
curl http://localhost/health/live

# Readiness (is API ready?)
curl http://localhost/health/ready

# System info
curl http://localhost/api/v1/debug/system-info
```

### Monitoring Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **Metabase**: http://localhost:3001

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using port 80
sudo lsof -i :80
sudo kill -9 <PID>

# Or change nginx port in docker-compose.yml
ports:
  - "8080:80"  # Access at http://localhost:8080
```

#### 2. Backend Unhealthy

```bash
# Check API logs
docker-compose logs api --tail=50

# Restart API
docker-compose restart api

# Check dependencies
docker-compose ps postgres redis qdrant
```

#### 3. Frontend Not Loading

```bash
# Check nginx logs
docker-compose logs nginx --tail=50

# Verify frontend files exist
ls -la frontend/

# Restart nginx
docker-compose restart nginx
```

#### 4. CORS Errors

```bash
# Check CORS configuration in app/main.py
# Ensure allowed_origins includes your domain

# Restart API after changes
docker-compose restart api
```

---

## Security Checklist

### Before Production Deployment

- [ ] Change default passwords (Postgres, Redis, Grafana, etc.)
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall (only expose 80/443)
- [ ] Set secure POSTGRES_PASSWORD in .env
- [ ] Restrict Prometheus/Grafana access (add auth or IP whitelist)
- [ ] Enable authentication for Keycloak admin console
- [ ] Review and update ALLOWED_ORIGINS for CORS
- [ ] Set up backup strategy for databases
- [ ] Configure log rotation
- [ ] Set up monitoring alerts

---

## Backup & Recovery

### Database Backup

```bash
# Postgres
docker-compose exec postgres pg_dump -U postgres rag_enterprise > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres rag_enterprise < backup.sql
```

### Vector Database Backup

```bash
# Qdrant
docker-compose exec qdrant /bin/sh -c "cd /qdrant/storage && tar czf - ." > qdrant_backup.tar.gz

# Restore
docker-compose down
gunzip -c qdrant_backup.tar.gz | docker-compose exec -T qdrant tar xzf - -C /qdrant/storage
docker-compose up -d
```

---

## Performance Tuning

### Docker Resource Limits

```yaml
# docker-compose.yml
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

### Nginx Caching

Already configured in nginx.conf:
- Static assets: 1 year cache
- HTML: No cache
- API: No cache

---

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost/ | See frontend/README.md |
| **API Docs** | http://localhost/api/v1/docs | N/A |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | N/A |
| **Jaeger** | http://localhost:16686 | N/A |
| **Metabase** | http://localhost:3001 | First-time setup |
| **Airflow** | http://localhost:8082 | admin/admin |
| **MinIO** | http://localhost:9002 | minioadmin/minioadmin |
| **Keycloak** | http://localhost:8080 | admin/admin |

---

## Next Steps

1. ✅ **System is running** - All 17 services operational
2. ✅ **Frontend deployed** - Accessible at http://localhost/
3. ✅ **API connected** - Backend proxied through nginx
4. ✅ **Remote access ready** - Configure DNS and SSL for production

### For Production:

```bash
# 1. Get SSL certificate
sudo certbot --nginx -d your-domain.com

# 2. Update nginx.conf with domain

# 3. Restart nginx
docker-compose restart nginx

# 4. Test
curl https://your-domain.com/health/live
```

---

**Questions?** Check `docs/` for detailed guides or open an issue.

**Status**: ✅ Ready for deployment
**Last Updated**: 2025-11-14
