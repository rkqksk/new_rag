#!/usr/bin/env bash
# =============================================================================
# RAG Enterprise Deployment Automation Script
# =============================================================================
# Production-ready deployment script with comprehensive safety checks.
#
# Usage:
#   ./scripts/deploy.sh <environment> [version]
#   ./scripts/deploy.sh backup <environment> <timestamp>
#
# Environments: staging, production
# Version: Docker image tag (default: latest)
#
# Features:
#   - Pre-deployment validation
#   - Automatic backup creation
#   - Database migration execution
#   - Service deployment
#   - Health check validation
#   - Automatic rollback on failure
#   - Comprehensive logging
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="${PROJECT_ROOT}/logs/deploy-$(date +%Y%m%d-%H%M%S).log"
readonly BACKUP_DIR="${PROJECT_ROOT}/backups"
readonly DEPLOYMENT_TIMEOUT=600  # 10 minutes

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'  # No Color

# -----------------------------------------------------------------------------
# Logging Functions
# -----------------------------------------------------------------------------

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "${GREEN}✓${NC}" "$@"
}

log_warn() {
    log "WARN" "${YELLOW}⚠${NC}" "$@"
}

log_error() {
    log "ERROR" "${RED}✗${NC}" "$@"
}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

usage() {
    cat <<EOF
Usage: $0 <command> [options]

Commands:
    deploy <environment> [version]    Deploy to environment
    backup <environment> <timestamp>  Create backup only
    validate <environment>            Validate environment setup

Environments:
    staging      Staging environment
    production   Production environment

Examples:
    $0 deploy staging v1.2.3
    $0 deploy production latest
    $0 backup production 20250119-120000
    $0 validate staging

EOF
    exit 1
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    local required_tools=("kubectl" "helm" "aws" "jq" "curl")

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done

    log_info "All prerequisites satisfied"
}

validate_environment() {
    local env="$1"

    if [[ ! "$env" =~ ^(staging|production)$ ]]; then
        log_error "Invalid environment: $env (must be staging or production)"
        exit 1
    fi

    log_info "Environment validated: $env"
}

# -----------------------------------------------------------------------------
# Backup Functions
# -----------------------------------------------------------------------------

create_backup() {
    local env="$1"
    local timestamp="${2:-$(date +%Y%m%d-%H%M%S)}"

    log_info "Creating backup for $env environment..."

    mkdir -p "$BACKUP_DIR"

    local backup_file="${BACKUP_DIR}/backup-${env}-${timestamp}.tar.gz"

    # Backup PostgreSQL database
    log_info "Backing up PostgreSQL database..."
    kubectl exec -n "$env" deployment/rag-api -- \
        pg_dump -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        > "${BACKUP_DIR}/db-${env}-${timestamp}.sql"

    # Backup Qdrant collections
    log_info "Backing up Qdrant collections..."
    kubectl exec -n "$env" deployment/rag-api -- \
        python -c "
from qdrant_client import QdrantClient
import json

client = QdrantClient(host='qdrant', port=6333)
collections = client.get_collections()

with open('/tmp/qdrant-backup.json', 'w') as f:
    json.dump([c.dict() for c in collections.collections], f)
" || log_warn "Qdrant backup failed (non-critical)"

    # Backup Kubernetes configurations
    log_info "Backing up Kubernetes configurations..."
    kubectl get all -n "$env" -o yaml > "${BACKUP_DIR}/k8s-${env}-${timestamp}.yaml"

    # Create consolidated backup archive
    tar -czf "$backup_file" -C "$BACKUP_DIR" \
        "db-${env}-${timestamp}.sql" \
        "k8s-${env}-${timestamp}.yaml" \
        2>/dev/null || true

    # Verify backup
    if [[ -f "$backup_file" ]]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_info "Backup created successfully: $backup_file ($size)"
        echo "$backup_file"
    else
        log_error "Backup creation failed"
        exit 1
    fi

    # Cleanup old backups (keep last 10)
    find "$BACKUP_DIR" -name "backup-${env}-*.tar.gz" -type f | \
        sort -r | tail -n +11 | xargs -r rm -f
    log_info "Cleaned up old backups (keeping last 10)"
}

# -----------------------------------------------------------------------------
# Database Migration Functions
# -----------------------------------------------------------------------------

run_migrations() {
    local env="$1"

    log_info "Running database migrations for $env..."

    # Dry run first
    log_info "Running migration dry-run..."
    kubectl exec -n "$env" deployment/rag-api -- \
        python -m alembic upgrade head --sql > "${PROJECT_ROOT}/logs/migration-${env}.sql"

    log_info "Migration SQL saved to logs/migration-${env}.sql"

    # Review critical migrations
    if grep -i "DROP\|ALTER\|DELETE" "${PROJECT_ROOT}/logs/migration-${env}.sql" &>/dev/null; then
        log_warn "Critical migration operations detected!"

        if [[ "$env" == "production" ]]; then
            log_warn "Production deployment - please review migration SQL"
            read -p "Continue with migration? (yes/no): " -r
            if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
                log_error "Migration aborted by user"
                exit 1
            fi
        fi
    fi

    # Execute migration
    log_info "Executing migration..."
    if kubectl exec -n "$env" deployment/rag-api -- \
        python -m alembic upgrade head; then
        log_info "Migration completed successfully"
    else
        log_error "Migration failed"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Deployment Functions
# -----------------------------------------------------------------------------

deploy_application() {
    local env="$1"
    local version="${2:-latest}"

    log_info "Deploying RAG Enterprise to $env (version: $version)..."

    # Determine replica count based on environment
    local replicas=2
    if [[ "$env" == "production" ]]; then
        replicas=10
    fi

    # Deploy with Helm
    log_info "Deploying with Helm..."
    helm upgrade --install rag-enterprise "${PROJECT_ROOT}/helm/rag-enterprise" \
        --namespace "$env" \
        --create-namespace \
        --set "image.repository=${REGISTRY}/${IMAGE_NAME}" \
        --set "image.tag=${version}" \
        --set "environment=${env}" \
        --set "replicaCount=${replicas}" \
        --values "${PROJECT_ROOT}/helm/values-${env}.yaml" \
        --wait \
        --timeout "${DEPLOYMENT_TIMEOUT}s" || {
        log_error "Helm deployment failed"
        return 1
    }

    log_info "Helm deployment completed"
}

wait_for_rollout() {
    local env="$1"

    log_info "Waiting for deployment rollout..."

    if kubectl rollout status deployment/rag-api \
        -n "$env" \
        --timeout="${DEPLOYMENT_TIMEOUT}s"; then
        log_info "Rollout completed successfully"
    else
        log_error "Rollout failed or timed out"
        return 1
    fi
}

verify_health() {
    local env="$1"

    log_info "Verifying application health..."

    local max_attempts=30
    local attempt=0

    # Get service endpoint
    local endpoint=$(kubectl get svc rag-api -n "$env" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

    if [[ -z "$endpoint" ]]; then
        log_error "Could not get service endpoint"
        return 1
    fi

    log_info "Service endpoint: $endpoint"

    while [[ $attempt -lt $max_attempts ]]; do
        ((attempt++))
        log_info "Health check attempt $attempt/$max_attempts"

        # Check liveness
        if curl -sf "http://${endpoint}/health/live" &>/dev/null; then
            log_info "Liveness check passed"

            # Check readiness
            if curl -sf "http://${endpoint}/health/ready" &>/dev/null; then
                log_info "Readiness check passed"

                # Verify basic functionality
                if curl -sf "http://${endpoint}/health" | jq -e '.status == "healthy"' &>/dev/null; then
                    log_info "Health verification successful"
                    return 0
                fi
            fi
        fi

        sleep 10
    done

    log_error "Health checks failed after $max_attempts attempts"
    return 1
}

# -----------------------------------------------------------------------------
# Main Deployment Flow
# -----------------------------------------------------------------------------

deploy() {
    local env="$1"
    local version="${2:-latest}"

    log_info "==================================================================="
    log_info "Starting deployment to $env (version: $version)"
    log_info "==================================================================="

    # Validation
    validate_environment "$env"
    check_prerequisites

    # Create backup
    log_info "Step 1/5: Creating backup..."
    local backup_file
    backup_file=$(create_backup "$env")

    # Run migrations
    log_info "Step 2/5: Running database migrations..."
    if ! run_migrations "$env"; then
        log_error "Migration failed, aborting deployment"
        exit 1
    fi

    # Deploy application
    log_info "Step 3/5: Deploying application..."
    if ! deploy_application "$env" "$version"; then
        log_error "Deployment failed, initiating rollback..."
        "${SCRIPT_DIR}/rollback.sh" "$env" "$backup_file"
        exit 1
    fi

    # Wait for rollout
    log_info "Step 4/5: Waiting for rollout..."
    if ! wait_for_rollout "$env"; then
        log_error "Rollout failed, initiating rollback..."
        "${SCRIPT_DIR}/rollback.sh" "$env" "$backup_file"
        exit 1
    fi

    # Verify health
    log_info "Step 5/5: Verifying health..."
    if ! verify_health "$env"; then
        log_error "Health checks failed, initiating rollback..."
        "${SCRIPT_DIR}/rollback.sh" "$env" "$backup_file"
        exit 1
    fi

    log_info "==================================================================="
    log_info "${GREEN}✓ Deployment completed successfully${NC}"
    log_info "==================================================================="
    log_info "Environment: $env"
    log_info "Version: $version"
    log_info "Backup: $backup_file"
    log_info "==================================================================="
}

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

main() {
    # Create logs directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Parse command
    local command="${1:-}"

    case "$command" in
        deploy)
            deploy "${2:-}" "${3:-latest}"
            ;;
        backup)
            create_backup "${2:-}" "${3:-}"
            ;;
        validate)
            validate_environment "${2:-}"
            check_prerequisites
            log_info "Environment validation passed"
            ;;
        *)
            usage
            ;;
    esac
}

# Execute main function
main "$@"
