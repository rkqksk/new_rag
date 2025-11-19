#!/usr/bin/env bash
# System health check script

echo "🏥 System Health Check"
echo "====================="
echo ""

check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url" > /dev/null; then
        echo "✅ $name - healthy"
    else
        echo "❌ $name - unhealthy"
    fi
}

# Check API
check_service "API" "http://localhost:8001/health"

# Check Web
check_service "Web" "http://localhost:3000"

# Check database
if docker ps | grep -q postgres; then
    echo "✅ PostgreSQL - running"
else
    echo "❌ PostgreSQL - not running"
fi

# Check Redis
if docker ps | grep -q redis; then
    echo "✅ Redis - running"
else
    echo "❌ Redis - not running"
fi

# Check Qdrant
if docker ps | grep -q qdrant; then
    echo "✅ Qdrant - running"
else
    echo "❌ Qdrant - not running"
fi

echo ""
echo "System status check complete"
