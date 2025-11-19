#!/usr/bin/env bash
# Performance benchmark script

set -e

echo "⚡ Performance Benchmarks"
echo "========================="
echo ""

# Create reports directory
mkdir -p reports/performance

# Function to format time
format_time() {
    local seconds=$1
    printf "%.2fs" "$seconds"
}

# 1. Build Time Benchmark
echo "📦 Build Time Benchmark..."
BUILD_START=$(date +%s)
pnpm --filter "./packages/*" build > /dev/null 2>&1
pnpm --filter "./apps/web" build > /dev/null 2>&1
BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))
echo "   Build Time: $(format_time $BUILD_TIME)"

# 2. Bundle Size Analysis
echo ""
echo "📊 Bundle Size Analysis..."
if [ -d "apps/web/.next" ]; then
    BUNDLE_SIZE=$(du -sh apps/web/.next/static | cut -f1)
    echo "   Static Bundle: $BUNDLE_SIZE"
fi

# 3. API Response Time (requires server running)
echo ""
echo "🌐 API Response Time..."
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' http://localhost:8001/health)
    echo "   Health Endpoint: ${RESPONSE_TIME}s"

    # Test search endpoint
    SEARCH_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' \
        -X POST http://localhost:8001/api/v1/search/ \
        -H "Content-Type: application/json" \
        -d '{"query":"test","top_k":5}')
    echo "   Search Endpoint: ${SEARCH_TIME}s"
else
    echo "   ⚠️  API not running - skipping response time tests"
fi

# 4. Test Execution Time
echo ""
echo "🧪 Test Execution Time..."
TEST_START=$(date +%s)
pytest tests/ -q --tb=no > /dev/null 2>&1 || true
TEST_END=$(date +%s)
TEST_TIME=$((TEST_END - TEST_START))
echo "   Backend Tests: $(format_time $TEST_TIME)"

# 5. Database Query Performance (if DB is running)
echo ""
echo "💾 Database Query Performance..."
if docker ps | grep -q postgres; then
    QUERY_TIME=$(docker exec postgres psql -U postgres -c "EXPLAIN ANALYZE SELECT 1;" | grep "Execution Time" | grep -oE '[0-9]+\.[0-9]+')
    echo "   Simple Query: ${QUERY_TIME}ms"
else
    echo "   ⚠️  PostgreSQL not running - skipping DB tests"
fi

# 6. Memory Usage
echo ""
echo "🧠 Memory Usage..."
if command -v free > /dev/null; then
    MEMORY=$(free -h | awk 'NR==2{printf "   Used: %s / Total: %s (%.2f%%)", $3,$2,$3*100/$2}')
    echo "$MEMORY"
fi

# Generate JSON report
cat > reports/performance/benchmark-$(date +%Y%m%d-%H%M%S).json <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "build_time_seconds": $BUILD_TIME,
  "test_time_seconds": $TEST_TIME,
  "bundle_size": "$BUNDLE_SIZE",
  "api_health_response_time": "$RESPONSE_TIME",
  "api_search_response_time": "$SEARCH_TIME"
}
EOF

echo ""
echo "✅ Benchmark complete!"
echo "   Reports saved to: reports/performance/"
