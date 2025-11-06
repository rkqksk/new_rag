#!/bin/bash
# Health check utilities for infrastructure components
# Source this file: source scripts/lib/health.sh

# Check if Qdrant is healthy
check_qdrant() {
    local host="${1:-localhost}"
    local port="${2:-6333}"
    local max_attempts="${3:-30}"

    print_info "Checking Qdrant at $host:$port..."

    for i in $(seq 1 $max_attempts); do
        if curl -sf "http://$host:$port/health" > /dev/null 2>&1; then
            print_success "Qdrant is healthy"
            return 0
        fi
        [ $i -eq $max_attempts ] && break
        sleep 1
    done

    print_error "Qdrant health check failed after $max_attempts attempts"
    return 1
}

# Check if Redis is healthy
check_redis() {
    local host="${1:-localhost}"
    local port="${2:-6379}"

    print_info "Checking Redis at $host:$port..."

    if redis-cli -h "$host" -p "$port" ping > /dev/null 2>&1; then
        print_success "Redis is healthy"
        return 0
    else
        print_error "Redis health check failed"
        return 1
    fi
}

# Check if PostgreSQL is healthy
check_postgres() {
    local host="${1:-localhost}"
    local port="${2:-5432}"
    local user="${3:-postgres}"
    local db="${4:-rag_enterprise}"

    print_info "Checking PostgreSQL at $host:$port..."

    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$host" -p "$port" -U "$user" -d "$db" -c '\q' > /dev/null 2>&1; then
        print_success "PostgreSQL is healthy"
        return 0
    else
        print_error "PostgreSQL health check failed"
        return 1
    fi
}

# Check if API is healthy
check_api() {
    local host="${1:-localhost}"
    local port="${2:-8001}"
    local max_attempts="${3:-30}"

    print_info "Checking API at http://$host:$port..."

    for i in $(seq 1 $max_attempts); do
        if curl -sf "http://$host:$port/health/live" > /dev/null 2>&1; then
            print_success "API is healthy"
            return 0
        fi
        [ $i -eq $max_attempts ] && break
        sleep 1
    done

    print_error "API health check failed after $max_attempts attempts"
    return 1
}

# Check all infrastructure components
check_all_infrastructure() {
    local failed=0

    print_header "Infrastructure Health Check"

    check_qdrant || ((failed++))
    check_redis || ((failed++))
    check_postgres || ((failed++))
    check_api || ((failed++))

    if [ $failed -eq 0 ]; then
        print_success "All infrastructure components are healthy"
        return 0
    else
        print_error "$failed component(s) failed health check"
        return 1
    fi
}
