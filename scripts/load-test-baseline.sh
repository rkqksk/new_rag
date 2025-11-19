#!/bin/bash

################################################################################
# Load Testing Script for v10.0.0 Performance Baseline
#
# Purpose: Measure API performance under various load conditions
# Usage: ./scripts/load-test-baseline.sh [light|medium|heavy|stress|all]
# Output: JSON results in reports/load-test-results.json
#
# Dependencies:
#   - curl (for API testing)
#   - Python 3.11+ with requests library
#   - Docker (for service health checks)
#
# Author: Claude Code
# Date: 2025-11-19
# Version: 1.0.0
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8001}"
REPORTS_DIR="/home/rkqksk/projects/new_rag/reports"
RESULTS_FILE="${REPORTS_DIR}/load-test-results.json"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${REPORTS_DIR}/load-test-${TIMESTAMP}.log"

# Test scenarios
LIGHT_CONCURRENT=10
LIGHT_REQUESTS=1000

MEDIUM_CONCURRENT=50
MEDIUM_REQUESTS=5000

HEAVY_CONCURRENT=100
HEAVY_REQUESTS=10000

STRESS_CONCURRENT=500
STRESS_REQUESTS=50000

################################################################################
# Utility Functions
################################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

################################################################################
# Health Check Functions
################################################################################

check_prerequisites() {
    log "Checking prerequisites..."

    # Check curl
    if ! command -v curl &> /dev/null; then
        error "curl is not installed. Please install it first."
        exit 1
    fi
    success "curl found"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    success "Python 3 found ($(python3 --version))"

    # Check Python requests library
    if ! python3 -c "import requests" 2>/dev/null; then
        warn "Python requests library not found. Installing..."
        python3 -m pip install requests --quiet
    fi
    success "Python requests library available"

    # Check jq for JSON parsing (optional)
    if command -v jq &> /dev/null; then
        success "jq found (for pretty JSON output)"
    else
        warn "jq not found (optional, install for prettier output)"
    fi
}

check_services() {
    log "Checking service health..."

    # Check API
    if curl -s "${API_URL}/health/ready" > /dev/null 2>&1; then
        success "API is running at ${API_URL}"
    else
        error "API is not responding at ${API_URL}"
        error "Please start the API first: docker-compose up -d api"
        exit 1
    fi

    # Check PostgreSQL
    if docker exec new_rag-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then
        success "PostgreSQL is ready"
    else
        warn "PostgreSQL is not ready (some tests may fail)"
    fi

    # Check Redis
    if docker exec new_rag-redis-1 redis-cli ping > /dev/null 2>&1; then
        success "Redis is ready"
    else
        warn "Redis is not ready (caching tests may fail)"
    fi

    # Check Qdrant
    if curl -s http://localhost:16333/collections > /dev/null 2>&1; then
        success "Qdrant is ready"
    else
        warn "Qdrant is not ready (vector search tests may fail)"
    fi
}

################################################################################
# Simple Load Testing (using curl)
################################################################################

run_simple_load_test() {
    local endpoint=$1
    local method=$2
    local concurrent=$3
    local requests=$4
    local payload=$5
    local description=$6

    log "Running: $description"
    log "  Endpoint: ${method} ${endpoint}"
    log "  Concurrent: ${concurrent}, Total Requests: ${requests}"

    # Create results file
    local results_file="/tmp/load_test_results_$$.txt"
    > "$results_file"

    local start_time=$(date +%s.%N)

    # Run concurrent requests
    for i in $(seq 1 $concurrent); do
        (
            local count=$((requests / concurrent))
            for j in $(seq 1 $count); do
                local request_start=$(date +%s.%N)

                if [ "$method" = "POST" ]; then
                    response=$(curl -s -w "\n%{http_code}\n%{time_total}" -X POST \
                        -H "Content-Type: application/json" \
                        -d "$payload" \
                        "${API_URL}${endpoint}" 2>/dev/null)
                else
                    response=$(curl -s -w "\n%{http_code}\n%{time_total}" \
                        "${API_URL}${endpoint}" 2>/dev/null)
                fi

                local status_code=$(echo "$response" | tail -2 | head -1)
                local time_total=$(echo "$response" | tail -1)

                echo "${status_code},${time_total}" >> "$results_file"
            done
        ) &
    done

    # Wait for all background jobs
    wait

    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc)

    # Analyze results
    analyze_results "$results_file" "$requests" "$total_time" "$description"

    rm -f "$results_file"
}

analyze_results() {
    local results_file=$1
    local total_requests=$2
    local total_time=$3
    local description=$4

    python3 << EOF
import json
import statistics

# Read results
times = []
status_codes = {"200": 0, "201": 0, "400": 0, "404": 0, "500": 0, "other": 0}

with open("$results_file", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            parts = line.split(",")
            if len(parts) == 2:
                status, time_val = parts
                times.append(float(time_val) * 1000)  # Convert to ms

                # Count status codes
                if status in status_codes:
                    status_codes[status] += 1
                else:
                    status_codes["other"] += 1

if not times:
    print("No valid results")
    exit(1)

# Calculate statistics
mean = statistics.mean(times)
median = statistics.median(times)
stdev = statistics.stdev(times) if len(times) > 1 else 0
min_time = min(times)
max_time = max(times)

# Percentiles
sorted_times = sorted(times)
p50 = sorted_times[int(len(sorted_times) * 0.50)]
p75 = sorted_times[int(len(sorted_times) * 0.75)]
p90 = sorted_times[int(len(sorted_times) * 0.90)]
p95 = sorted_times[int(len(sorted_times) * 0.95)]
p99 = sorted_times[int(len(sorted_times) * 0.99)]

# Requests per second
total_time = float("$total_time")
rps = $total_requests / total_time if total_time > 0 else 0

# Success rate
successful = status_codes.get("200", 0) + status_codes.get("201", 0)
success_rate = (successful / $total_requests) * 100 if $total_requests > 0 else 0

# Print results
print("\n" + "="*60)
print("Test: $description")
print("="*60)
print(f"Total Requests: $total_requests")
print(f"Total Time: {total_time:.2f}s")
print(f"Requests/sec: {rps:.2f}")
print(f"Success Rate: {success_rate:.1f}%")
print()
print("Latency (ms):")
print(f"  Mean:   {mean:.2f}")
print(f"  Median: {median:.2f}")
print(f"  StdDev: {stdev:.2f}")
print(f"  Min:    {min_time:.2f}")
print(f"  Max:    {max_time:.2f}")
print()
print("Percentiles (ms):")
print(f"  p50: {p50:.2f}")
print(f"  p75: {p75:.2f}")
print(f"  p90: {p90:.2f}")
print(f"  p95: {p95:.2f}")
print(f"  p99: {p99:.2f}")
print()
print("Status Codes:")
for code, count in sorted(status_codes.items()):
    if count > 0:
        print(f"  {code}: {count}")
print("="*60)

# Save JSON results
result = {
    "test": "$description",
    "timestamp": "$(date -Iseconds)",
    "requests": {
        "total": $total_requests,
        "successful": successful,
        "success_rate": success_rate
    },
    "throughput": {
        "requests_per_second": rps,
        "total_time_seconds": total_time
    },
    "latency_ms": {
        "mean": mean,
        "median": median,
        "stddev": stdev,
        "min": min_time,
        "max": max_time,
        "p50": p50,
        "p75": p75,
        "p90": p90,
        "p95": p95,
        "p99": p99
    },
    "status_codes": status_codes
}

# Append to results file
try:
    with open("$RESULTS_FILE", "r") as f:
        results = json.load(f)
except:
    results = {"tests": []}

results["tests"].append(result)

with open("$RESULTS_FILE", "w") as f:
    json.dump(results, f, indent=2)

EOF
}

################################################################################
# Python-based Load Testing (for POST requests with complex payloads)
################################################################################

run_python_load_test() {
    local endpoint=$1
    local method=$2
    local concurrent=$3
    local requests=$4
    local description=$5

    log "Running (Python): $description"

    python3 << EOF
import asyncio
import aiohttp
import time
import statistics
import json
from datetime import datetime

async def make_request(session, url, method="GET", json_data=None):
    start = time.time()
    try:
        if method == "POST":
            async with session.post(url, json=json_data) as response:
                data = await response.text()
                status = response.status
        else:
            async with session.get(url) as response:
                data = await response.text()
                status = response.status

        elapsed = (time.time() - start) * 1000  # Convert to ms
        return {"status": status, "time": elapsed, "error": None}
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return {"status": 0, "time": elapsed, "error": str(e)}

async def worker(session, url, method, json_data, num_requests, results):
    for _ in range(num_requests):
        result = await make_request(session, url, method, json_data)
        results.append(result)

async def run_load_test():
    url = "${API_URL}${endpoint}"
    method = "$method"
    concurrent = $concurrent
    total_requests = $requests

    # Prepare payload
    if method == "POST":
        if "$endpoint" == "/api/v1/search/":
            json_data = {"query": "PET 용기", "top_k": 5}
        elif "$endpoint" == "/api/v1/qa/":
            json_data = {"question": "50ml PET 용기의 사양은?", "context_chunks": 5}
        else:
            json_data = {}
    else:
        json_data = None

    requests_per_worker = total_requests // concurrent
    results = []

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        workers = [
            worker(session, url, method, json_data, requests_per_worker, results)
            for _ in range(concurrent)
        ]
        await asyncio.gather(*workers)

    end_time = time.time()
    total_time = end_time - start_time

    # Analyze results
    times = [r["time"] for r in results]
    statuses = [r["status"] for r in results]
    errors = [r for r in results if r["error"]]

    if not times:
        print("No results")
        return

    mean = statistics.mean(times)
    median = statistics.median(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    min_time = min(times)
    max_time = max(times)

    sorted_times = sorted(times)
    p50 = sorted_times[int(len(sorted_times) * 0.50)]
    p95 = sorted_times[int(len(sorted_times) * 0.95)]
    p99 = sorted_times[int(len(sorted_times) * 0.99)]

    rps = total_requests / total_time
    successful = sum(1 for s in statuses if 200 <= s < 300)
    success_rate = (successful / total_requests) * 100

    # Print results
    print()
    print("=" * 60)
    print("Test: $description")
    print("=" * 60)
    print(f"Total Requests: {total_requests}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests/sec: {rps:.2f}")
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    print("Latency (ms):")
    print(f"  Mean:   {mean:.2f}")
    print(f"  Median: {median:.2f}")
    print(f"  StdDev: {stdev:.2f}")
    print(f"  Min:    {min_time:.2f}")
    print(f"  Max:    {max_time:.2f}")
    print()
    print("Percentiles (ms):")
    print(f"  p50: {p50:.2f}")
    print(f"  p95: {p95:.2f}")
    print(f"  p99: {p99:.2f}")
    print()
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error['error']}")
    print("=" * 60)

    # Save results
    result = {
        "test": "$description",
        "timestamp": datetime.now().isoformat(),
        "requests": {
            "total": total_requests,
            "successful": successful,
            "success_rate": success_rate
        },
        "throughput": {
            "requests_per_second": rps,
            "total_time_seconds": total_time
        },
        "latency_ms": {
            "mean": mean,
            "median": median,
            "stddev": stdev,
            "min": min_time,
            "max": max_time,
            "p50": p50,
            "p95": p95,
            "p99": p99
        },
        "errors": len(errors)
    }

    try:
        with open("$RESULTS_FILE", "r") as f:
            results_data = json.load(f)
    except:
        results_data = {"tests": []}

    results_data["tests"].append(result)

    with open("$RESULTS_FILE", "w") as f:
        json.dump(results_data, f, indent=2)

asyncio.run(run_load_test())
EOF
}

################################################################################
# Test Scenarios
################################################################################

run_light_load() {
    log "Starting LIGHT LOAD test..."

    run_simple_load_test \
        "/health/ready" \
        "GET" \
        $LIGHT_CONCURRENT \
        $LIGHT_REQUESTS \
        "" \
        "Light Load - Health Endpoint"

    run_python_load_test \
        "/api/v1/search/" \
        "POST" \
        $LIGHT_CONCURRENT \
        500 \
        "Light Load - Search Endpoint"
}

run_medium_load() {
    log "Starting MEDIUM LOAD test..."

    run_python_load_test \
        "/api/v1/search/" \
        "POST" \
        $MEDIUM_CONCURRENT \
        $MEDIUM_REQUESTS \
        "Medium Load - Search Endpoint"

    run_simple_load_test \
        "/api/v1/products/?limit=20" \
        "GET" \
        $MEDIUM_CONCURRENT \
        2000 \
        "" \
        "Medium Load - Products Endpoint"
}

run_heavy_load() {
    log "Starting HEAVY LOAD test..."

    warn "This may take several minutes and impact system performance"

    run_python_load_test \
        "/api/v1/search/" \
        "POST" \
        $HEAVY_CONCURRENT \
        $HEAVY_REQUESTS \
        "Heavy Load - Search Endpoint"
}

run_stress_test() {
    log "Starting STRESS TEST..."

    error "⚠️  WARNING: This will heavily stress the system!"
    error "    Press Ctrl+C within 5 seconds to cancel..."
    sleep 5

    run_python_load_test \
        "/health/ready" \
        "GET" \
        $STRESS_CONCURRENT \
        $STRESS_REQUESTS \
        "Stress Test - Maximum Throughput"
}

################################################################################
# Reporting
################################################################################

generate_summary_report() {
    log "Generating summary report..."

    if [ ! -f "$RESULTS_FILE" ]; then
        error "No results file found"
        return
    fi

    python3 << 'EOF'
import json
import sys

try:
    with open("${RESULTS_FILE}", "r") as f:
        data = json.load(f)
except Exception as e:
    print(f"Error reading results: {e}")
    sys.exit(1)

tests = data.get("tests", [])
if not tests:
    print("No test results found")
    sys.exit(1)

print()
print("=" * 80)
print(" " * 20 + "LOAD TEST SUMMARY REPORT")
print("=" * 80)
print()

for test in tests:
    print(f"Test: {test['test']}")
    print(f"  Timestamp: {test['timestamp']}")
    print(f"  Total Requests: {test['requests']['total']}")
    print(f"  Success Rate: {test['requests']['success_rate']:.1f}%")
    print(f"  Throughput: {test['throughput']['requests_per_second']:.2f} req/s")
    print(f"  Latency (p50/p95/p99): {test['latency_ms']['p50']:.0f}/{test['latency_ms']['p95']:.0f}/{test['latency_ms']['p99']:.0f} ms")
    print()

print("=" * 80)
print()
print(f"Full results saved to: ${RESULTS_FILE}")
print(f"Test log saved to: ${LOG_FILE}")
print()
EOF

    success "Summary report generated"
}

################################################################################
# Main Function
################################################################################

main() {
    local test_type=${1:-all}

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║        Load Testing Script - v10.0.0 Performance Baseline      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Prerequisites
    check_prerequisites
    check_services

    # Initialize results file
    echo '{"tests": []}' > "$RESULTS_FILE"

    # Run tests based on argument
    case $test_type in
        light)
            run_light_load
            ;;
        medium)
            run_medium_load
            ;;
        heavy)
            run_heavy_load
            ;;
        stress)
            run_stress_test
            ;;
        all)
            run_light_load
            sleep 5
            run_medium_load
            sleep 5
            run_heavy_load
            ;;
        *)
            error "Unknown test type: $test_type"
            echo ""
            echo "Usage: $0 [light|medium|heavy|stress|all]"
            echo ""
            echo "Test Types:"
            echo "  light   - 10 concurrent, 1000 requests"
            echo "  medium  - 50 concurrent, 5000 requests"
            echo "  heavy   - 100 concurrent, 10000 requests"
            echo "  stress  - 500 concurrent, 50000 requests (⚠️  WARNING)"
            echo "  all     - Run light, medium, and heavy (default)"
            echo ""
            exit 1
            ;;
    esac

    # Generate summary
    generate_summary_report

    success "Load testing complete!"
    echo ""
}

# Run main function
main "$@"
