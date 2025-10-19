#!/usr/bin/env bash
# =============================================================================
# RAG Enterprise Rollback Automation Script
# =============================================================================
# Emergency rollback script for deployment failures.
#
# Usage:
#   ./scripts/rollback.sh <environment> [backup_file]
#
# Features:
#   - Find latest backup automatically
#   - Stop current deployment
#   - Restore database from backup
#   - Restore previous deployment
#   - Verify restoration
#   - Notify team
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="${PROJECT_ROOT}/logs/rollback-$(date +%Y%m%d-%H%M%S).log"
readonly BACKUP_DIR="${PROJECT_ROOT}/backups"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

log_info() {
    echo -e "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [INFO] ${GREEN}✓${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [WARN] ${YELLOW}⚠${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [ERROR] ${RED}✗${NC} $*" | tee -a "$LOG_FILE"
}

# -----------------------------------------------------------------------------
# Rollback Functions
# -----------------------------------------------------------------------------

find_latest_backup() {
    local env="$1"

    log_info "Finding latest backup for $env..."

    local backup_file=$(find "$BACKUP_DIR" -name "backup-${env}-*.tar.gz" -type f | sort -r | head -n1)

    if [[ -z "$backup_file" ]]; then
        log_error "No backup found for $env"
        exit 1
    fi

    log_info "Found backup: $backup_file"
    echo "$backup_file"
}

stop_current_deployment() {
    local env="$1"

    log_info "Stopping current deployment..."

    # Scale down to zero
    kubectl scale deployment/rag-api -n "$env" --replicas=0 || {
        log_warn "Failed to scale down deployment (may already be down)"
    }

    log_info "Deployment stopped"
}

restore_database() {
    local env="$1"
    local backup_file="$2"

    log_info "Restoring database from backup..."

    # Extract backup
    local temp_dir=$(mktemp -d)
    tar -xzf "$backup_file" -C "$temp_dir"

    # Find database backup
    local db_backup=$(find "$temp_dir" -name "db-${env}-*.sql" | head -n1)

    if [[ -z "$db_backup" ]]; then
        log_error "Database backup not found in archive"
        rm -rf "$temp_dir"
        exit 1
    fi

    # Restore database
    log_info "Restoring PostgreSQL database..."
    kubectl exec -n "$env" deployment/rag-api -- \
        psql -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$db_backup" || {
        log_error "Database restoration failed"
        rm -rf "$temp_dir"
        exit 1
    }

    # Cleanup
    rm -rf "$temp_dir"

    log_info "Database restored successfully"
}

restore_deployment() {
    local env="$1"

    log_info "Restoring previous deployment..."

    # Rollback Helm release
    helm rollback rag-enterprise -n "$env" || {
        log_error "Helm rollback failed"
        exit 1
    }

    log_info "Helm rollback completed"

    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod \
        -l app=rag-api \
        -n "$env" \
        --timeout=300s || {
        log_error "Pods failed to become ready"
        exit 1
    }

    log_info "Previous deployment restored"
}

verify_restoration() {
    local env="$1"

    log_info "Verifying restoration..."

    local max_attempts=20
    local attempt=0

    local endpoint=$(kubectl get svc rag-api -n "$env" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

    while [[ $attempt -lt $max_attempts ]]; do
        ((attempt++))
        log_info "Verification attempt $attempt/$max_attempts"

        if curl -sf "http://${endpoint}/health/ready" &>/dev/null; then
            log_info "Restoration verified - service is healthy"
            return 0
        fi

        sleep 10
    done

    log_error "Restoration verification failed"
    return 1
}

notify_team() {
    local env="$1"
    local status="$2"

    log_info "Sending notification..."

    # Send Slack notification if webhook is configured
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🔄 Rollback $status\",\"blocks\":[{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"*Rollback $status*\\n*Environment:* $env\\n*Time:* $(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}]}" || {
            log_warn "Failed to send Slack notification"
        }
    fi

    log_info "Notification sent"
}

# -----------------------------------------------------------------------------
# Main Rollback Flow
# -----------------------------------------------------------------------------

rollback() {
    local env="$1"
    local backup_file="${2:-}"

    log_info "==================================================================="
    log_error "INITIATING EMERGENCY ROLLBACK FOR $env"
    log_info "==================================================================="

    # Find backup if not provided
    if [[ -z "$backup_file" ]]; then
        backup_file=$(find_latest_backup "$env")
    fi

    # Stop current deployment
    log_info "Step 1/4: Stopping current deployment..."
    stop_current_deployment "$env"

    # Restore database
    log_info "Step 2/4: Restoring database..."
    restore_database "$env" "$backup_file"

    # Restore deployment
    log_info "Step 3/4: Restoring previous deployment..."
    restore_deployment "$env"

    # Verify restoration
    log_info "Step 4/4: Verifying restoration..."
    if verify_restoration "$env"; then
        log_info "==================================================================="
        log_info "${GREEN}✓ Rollback completed successfully${NC}"
        log_info "==================================================================="
        notify_team "$env" "SUCCESS"
    else
        log_error "==================================================================="
        log_error "Rollback verification failed - manual intervention required"
        log_error "==================================================================="
        notify_team "$env" "FAILED"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

main() {
    mkdir -p "$(dirname "$LOG_FILE")"

    local env="${1:-}"

    if [[ -z "$env" ]]; then
        echo "Usage: $0 <environment> [backup_file]"
        exit 1
    fi

    rollback "$env" "${2:-}"
}

main "$@"
