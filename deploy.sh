#!/bin/bash
# Production Deployment Script

set -e

echo "=========================================="
echo "RAG Enterprise - Deployment Script"
echo "=========================================="
echo ""

# Load environment
ENV="${1:-production}"
echo "Environment: $ENV"
echo ""

# Step 1: Prerequisites
echo "=== Step 1: Check Prerequisites ==="
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "ERROR: docker-compose not installed"; exit 1; }
echo "✓ Docker available"
echo "✓ docker-compose available"
echo ""

# Step 2: Configuration
echo "=== Step 2: Configuration ==="
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with production values"
    exit 1
fi
echo "✓ .env file exists"
echo ""

# Step 3: Build images
echo "=== Step 3: Build Docker Images ==="
docker-compose build
echo "✓ Images built"
echo ""

# Step 4: Start services
echo "=== Step 4: Start Services ==="
docker-compose up -d
echo "✓ Services started"
echo ""

# Step 5: Wait for services
echo "=== Step 5: Wait for Services ==="
echo "Waiting for Qdrant..."
until curl -s http://localhost:6333/health > /dev/null; do
    sleep 2
done
echo "✓ Qdrant ready"

echo "Waiting for Redis..."
until redis-cli ping > /dev/null 2>&1; do
    sleep 2
done
echo "✓ Redis ready"

echo "Waiting for PostgreSQL..."
until pg_isready -h localhost -p 5432 > /dev/null 2>&1; do
    sleep 2
done
echo "✓ PostgreSQL ready"

echo "Waiting for API..."
until curl -s http://localhost:8001/health/live > /dev/null; do
    sleep 2
done
echo "✓ API ready"
echo ""

# Step 6: Run migrations (if any)
echo "=== Step 6: Database Setup ==="
if [ -f "sql/analytics_schema.sql" ]; then
    echo "Running database migrations..."
    docker-compose exec -T postgres psql -U postgres -d rag_enterprise < sql/analytics_schema.sql
    echo "✓ Migrations complete"
fi
echo ""

# Step 7: Health check
echo "=== Step 7: Health Check ==="
./test_system.sh
echo ""

# Step 8: Summary
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Frontend:  http://localhost:8080"
echo "  - API:       http://localhost:8001"
echo "  - API Docs:  http://localhost:8001/api/v1/docs"
echo "  - Qdrant:    http://localhost:6333"
echo "  - Redis:     localhost:6379"
echo "  - Postgres:  localhost:5432"
echo ""
echo "Logs: docker-compose logs -f"
echo "Stop: docker-compose down"
echo ""
