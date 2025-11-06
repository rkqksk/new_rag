#!/bin/bash
# Optimized deployment script for RAG Enterprise
# Uses modular library functions for better maintainability

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source library functions
source "$SCRIPT_DIR/lib/colors.sh"
source "$SCRIPT_DIR/lib/docker.sh"
source "$SCRIPT_DIR/lib/health.sh"

# Configuration
ENVIRONMENT="${1:-development}"
COMPOSE_FILE="docker-compose.yml"

# Override compose file for production
if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# Main deployment function
main() {
    cd "$PROJECT_ROOT"

    print_header "RAG Enterprise Deployment - ${ENVIRONMENT}"

    # Step 1: Check prerequisites
    print_section "Step 1: Checking Prerequisites"
    check_docker_prerequisites || exit 1

    # Step 2: Build images
    print_section "Step 2: Building Docker Images"
    build_images "$COMPOSE_FILE" || exit 1

    # Step 3: Start services
    print_section "Step 3: Starting Services"
    start_services "$COMPOSE_FILE" || exit 1

    # Step 4: Wait for services to be healthy
    print_section "Step 4: Waiting for Services"
    sleep 5  # Give services time to start
    check_all_infrastructure || exit 1

    # Step 5: Run migrations (if production)
    if [ "$ENVIRONMENT" = "production" ]; then
        print_section "Step 5: Running Database Migrations"
        if [ -f "sql/analytics_schema.sql" ]; then
            print_info "Applying analytics schema..."
            PGPASSWORD="${POSTGRES_PASSWORD}" psql -h localhost -U postgres -d rag_enterprise -f sql/analytics_schema.sql > /dev/null 2>&1 || print_warning "Migration failed (may already exist)"
        fi
    fi

    # Success summary
    print_header "Deployment Successful! 🚀"
    echo ""
    echo "Services are running:"
    echo "  • API:       http://localhost:8001"
    echo "  • Docs:      http://localhost:8001/api/v1/docs"
    echo "  • Qdrant UI: http://localhost:6333/dashboard"
    echo "  • Frontend:  http://localhost:8080 (run separately)"
    echo ""
    echo "Next steps:"
    echo "  1. Test system:    ./scripts/test-optimized.sh"
    echo "  2. View logs:      docker-compose logs -f"
    echo "  3. Stop services:  docker-compose down"
    echo ""
}

# Run main function
main "$@"
