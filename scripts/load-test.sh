#!/usr/bin/env bash
# Load testing script using Apache Bench

set -e

echo "🔥 Load Testing"
echo "==============="
echo ""

# Configuration
API_URL=${API_URL:-"http://localhost:8001"}
CONCURRENT=${CONCURRENT:-50}
REQUESTS=${REQUESTS:-1000}

# Check if ab (Apache Bench) is installed
if ! command -v ab > /dev/null; then
    echo "⚠️  Apache Bench (ab) not found. Installing..."
    sudo apt-get update && sudo apt-get install -y apache2-utils || {
        echo "❌ Failed to install Apache Bench"
        echo "   Install manually: sudo apt-get install apache2-utils"
        exit 1
    }
fi

# Create reports directory
mkdir -p reports/load-tests

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="reports/load-tests/load-test-$TIMESTAMP.txt"

echo "Configuration:"
echo "  URL: $API_URL"
echo "  Concurrent: $CONCURRENT"
echo "  Total Requests: $REQUESTS"
echo ""

# Test 1: Health endpoint
echo "📊 Testing Health Endpoint..."
ab -n $REQUESTS -c $CONCURRENT -g reports/load-tests/health-$TIMESTAMP.tsv \
    "$API_URL/health" > reports/load-tests/health-$TIMESTAMP.txt 2>&1

HEALTH_RPS=$(grep "Requests per second" reports/load-tests/health-$TIMESTAMP.txt | awk '{print $4}')
HEALTH_TIME=$(grep "Time per request.*mean" reports/load-tests/health-$TIMESTAMP.txt | head -1 | awk '{print $4}')

echo "   ✅ RPS: $HEALTH_RPS"
echo "   ✅ Avg Response Time: ${HEALTH_TIME}ms"
echo ""

# Test 2: Search endpoint (POST)
echo "📊 Testing Search Endpoint..."

# Create POST data file
cat > /tmp/search-data.json <<EOF
{"query":"test product","top_k":5}
EOF

ab -n $REQUESTS -c $CONCURRENT \
    -p /tmp/search-data.json \
    -T "application/json" \
    -g reports/load-tests/search-$TIMESTAMP.tsv \
    "$API_URL/api/v1/search/" > reports/load-tests/search-$TIMESTAMP.txt 2>&1 || {
    echo "   ⚠️  Search endpoint test failed (server might not be running)"
}

if [ -f "reports/load-tests/search-$TIMESTAMP.txt" ]; then
    SEARCH_RPS=$(grep "Requests per second" reports/load-tests/search-$TIMESTAMP.txt | awk '{print $4}')
    SEARCH_TIME=$(grep "Time per request.*mean" reports/load-tests/search-$TIMESTAMP.txt | head -1 | awk '{print $4}')
    echo "   ✅ RPS: $SEARCH_RPS"
    echo "   ✅ Avg Response Time: ${SEARCH_TIME}ms"
fi

echo ""

# Generate summary report
cat > $REPORT_FILE <<EOF
LOAD TEST REPORT
================
Timestamp: $(date -Iseconds)
Configuration:
  - URL: $API_URL
  - Concurrent Requests: $CONCURRENT
  - Total Requests: $REQUESTS

RESULTS:
--------

Health Endpoint (/health):
  - Requests per second: $HEALTH_RPS
  - Average response time: ${HEALTH_TIME}ms

Search Endpoint (/api/v1/search/):
  - Requests per second: $SEARCH_RPS
  - Average response time: ${SEARCH_TIME}ms

ANALYSIS:
---------
$(if (( $(echo "$HEALTH_RPS > 1000" | bc -l) )); then
    echo "✅ Health endpoint performance: EXCELLENT"
else
    echo "⚠️  Health endpoint performance: Needs optimization"
fi)

$(if (( $(echo "$SEARCH_TIME < 100" | bc -l) )); then
    echo "✅ Search response time: EXCELLENT"
elif (( $(echo "$SEARCH_TIME < 500" | bc -l) )); then
    echo "⚠️  Search response time: ACCEPTABLE"
else
    echo "❌ Search response time: CRITICAL - Optimization required"
fi)

Detailed results: reports/load-tests/
EOF

echo "📄 Summary Report:"
cat $REPORT_FILE

echo ""
echo "✅ Load testing complete!"
echo "   Full reports: $REPORT_FILE"

# Cleanup
rm -f /tmp/search-data.json
