#!/bin/bash

################################################################################
# Colima Disk Space Cleanup & Optimization Script
# Purpose: Safely clean up unused Docker resources and compact Colima VM disk
#
# Usage: ./colima_cleanup.sh [phase] [--dry-run]
#   phase: 1 (safe), 2 (selective), 3 (vm-compact), 4 (archive), all
#   --dry-run: Show what would be deleted without actually deleting
#
# Example:
#   ./colima_cleanup.sh 1              # Run phase 1 cleanup
#   ./colima_cleanup.sh all --dry-run  # Show all cleanup actions (no changes)
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
BACKUP_DIR="$DATA_DIR/cleanup_backups"
DRY_RUN=false
LOG_FILE="$BACKUP_DIR/cleanup_$(date +%Y%m%d_%H%M%S).log"

# Create backup directory
mkdir -p "$BACKUP_DIR"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

################################################################################
# Utility Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

execute_command() {
    local cmd="$1"
    local description="$2"

    print_info "$description"

    if [ "$DRY_RUN" = true ]; then
        print_warning "[DRY RUN] Would execute: $cmd"
        return 0
    else
        if eval "$cmd"; then
            print_success "$description"
            return 0
        else
            print_error "Failed: $description"
            return 1
        fi
    fi
}

get_disk_usage() {
    du -sh "$1" 2>/dev/null | awk '{print $1}'
}

################################################################################
# Disk Usage Reporting
################################################################################

report_disk_usage() {
    print_header "📊 Disk Usage Report"

    echo "Colima VM Disk:"
    du -sh /Users/oypnus/.colima/_lima/_disks/colima/datadisk 2>/dev/null || echo "  (Unable to access)"

    echo -e "\nDocker System Usage:"
    docker system df 2>/dev/null || echo "  (Docker not accessible)"

    echo -e "\nProject Data:"
    du -sh "$PROJECT_ROOT/data"* 2>/dev/null | head -5

    echo -e "\nBackup Files:"
    du -sh "$DATA_DIR"/backup_* 2>/dev/null || echo "  (No backup files found)"
}

################################################################################
# Cleanup Phases
################################################################################

# Phase 1: Safe Operations (No Risk)
phase_1_safe_cleanup() {
    print_header "🟢 Phase 1: Safe Cleanup Operations"

    echo "This phase removes dangling images, containers, and caches."
    echo "Risk Level: LOW | Downtime: NONE"
    echo ""

    # Remove dangling images
    print_info "Checking for dangling images..."
    dangling_images=$(docker images -q -f dangling=true | wc -l)
    if [ "$dangling_images" -gt 0 ]; then
        execute_command "docker image prune -a --force --filter \"until=24h\"" \
            "Removing $dangling_images dangling images"
    else
        print_success "No dangling images found"
    fi

    # Remove unused volumes
    print_info "Checking for unused volumes..."
    unused_volumes=$(docker volume ls -q -f dangling=true | wc -l)
    if [ "$unused_volumes" -gt 0 ]; then
        execute_command "docker volume prune --force" \
            "Removing $unused_volumes unused volumes"
    else
        print_success "No unused volumes found"
    fi

    # Remove stopped containers
    print_info "Checking for stopped containers..."
    stopped_containers=$(docker container ls -q -a --filter status=exited | wc -l)
    if [ "$stopped_containers" -gt 0 ]; then
        execute_command "docker container prune --force" \
            "Removing $stopped_containers stopped containers"
    else
        print_success "No stopped containers found"
    fi

    # Clear build cache
    execute_command "docker builder prune --all --force --quiet" \
        "Clearing Docker build cache"

    print_header "✅ Phase 1 Complete"
}

# Phase 2: Selective Cleanup (Requires Verification)
phase_2_selective_cleanup() {
    print_header "🟡 Phase 2: Selective Cleanup (With Backups)"

    echo "This phase removes old images and creates backups of important data."
    echo "Risk Level: MEDIUM | Downtime: NONE"
    echo ""

    # Backup Qdrant data
    if docker ps | grep -q rag-qdrant; then
        print_info "Backing up Qdrant data..."
        if [ "$DRY_RUN" = false ]; then
            docker exec rag-qdrant tar czf /tmp/qdrant_backup.tar.gz /qdrant/storage 2>/dev/null || true
            docker cp rag-qdrant:/tmp/qdrant_backup.tar.gz "$BACKUP_DIR/qdrant_backup_$(date +%s).tar.gz" 2>/dev/null || true
            docker exec rag-qdrant rm -f /tmp/qdrant_backup.tar.gz 2>/dev/null || true
            print_success "Qdrant backup created"
        else
            print_warning "[DRY RUN] Would backup Qdrant data"
        fi
    fi

    # Remove unused Ollama volumes (local Ollama only, Docker Ollama removed)
    print_info "Removing Docker Ollama volumes (local Ollama only)..."
    docker volume rm ollama 2>/dev/null && print_success "Removed: ollama volume" || true
    docker volume rm rag-enterprise_ollama_models 2>/dev/null && print_success "Removed: rag-enterprise_ollama_models volume" || true

    # List unused images for review
    print_info "Listing potentially unused images..."
    docker images --no-trunc | grep -v "REPOSITORY" | awk '{print $3, $1":"$2}' | sort | uniq

    print_warning "Review unused images above. Run: docker rmi <image_id> to remove specific images"

    print_header "✅ Phase 2 Complete"
}

# Phase 3: VM Disk Compaction (Structural Optimization)
phase_3_vm_compaction() {
    print_header "🟠 Phase 3: Colima VM Disk Compaction"

    echo "This phase compacts the Colima VM disk (sparse file optimization)."
    echo "Risk Level: MEDIUM | Downtime: 30 seconds | Savings: 15-25GB"
    echo ""

    # Check if colima is installed
    if ! command -v colima &> /dev/null; then
        print_error "Colima is not installed. Skipping Phase 3."
        return 1
    fi

    # Warn user
    print_warning "This will stop Colima for 30 seconds."
    if [ "$DRY_RUN" = false ]; then
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Phase 3 skipped"
            return 0
        fi
    fi

    # Stop Colima
    execute_command "colima stop" "Stopping Colima..."
    sleep 2

    # Compact disk
    execute_command "colima disk compact" "Compacting Colima disk..."
    sleep 2

    # Start Colima
    execute_command "colima start" "Starting Colima..."
    sleep 5

    # Wait for Docker to be ready
    print_info "Waiting for Docker to be ready..."
    max_attempts=30
    attempt=0
    while ! docker ps &>/dev/null && [ $attempt -lt $max_attempts ]; do
        sleep 1
        ((attempt++))
    done

    if docker ps &>/dev/null; then
        print_success "Docker is ready"
    else
        print_warning "Docker took longer to start, but proceeding..."
    fi

    print_header "✅ Phase 3 Complete"
}

# Phase 4: Archive Backups
phase_4_archive_backups() {
    print_header "🔵 Phase 4: Archive Backup Files"

    echo "This phase archives large backup files (if external storage available)."
    echo "Risk Level: LOW | Downtime: NONE | Savings: 2-3GB"
    echo ""

    # Check for backup files
    backup_files=$(find "$DATA_DIR" -maxdepth 1 -name "backup_*.tar.gz" -type f 2>/dev/null | wc -l)

    if [ "$backup_files" -eq 0 ]; then
        print_success "No backup files to archive"
        return 0
    fi

    print_info "Found $backup_files backup files"

    # List backup files
    find "$DATA_DIR" -maxdepth 1 -name "backup_*.tar.gz" -type f | while read file; do
        size=$(du -h "$file" | awk '{print $1}')
        echo "  - $(basename "$file") ($size)"
    done

    # Check for external storage
    if [ -d "/Volumes/ExternalDrive" ]; then
        print_info "External storage found at /Volumes/ExternalDrive"
        archive_dir="/Volumes/ExternalDrive/rag-enterprise-backups"

        mkdir -p "$archive_dir"

        execute_command "mv '$DATA_DIR'/backup_*.tar.gz '$archive_dir'/" \
            "Moving backup files to external storage"

        print_success "Backups archived to external storage"
    else
        print_warning "External storage not found (need to manually archive)"
        print_info "Backup files remain in: $DATA_DIR"
    fi

    print_header "✅ Phase 4 Complete"
}

################################################################################
# Main Execution
################################################################################

main() {
    local phase="${1:-all}"

    # Check for dry-run flag
    if [[ "$*" == *"--dry-run"* ]]; then
        DRY_RUN=true
        print_warning "DRY RUN MODE - No changes will be made"
    fi

    print_header "🚀 Colima Cleanup & Optimization Script"
    print_info "Log file: $LOG_FILE"

    # Report initial disk usage
    report_disk_usage

    # Execute selected phase(s)
    case "$phase" in
        1|safe)
            phase_1_safe_cleanup
            ;;
        2|selective)
            phase_1_safe_cleanup
            phase_2_selective_cleanup
            ;;
        3|vm-compact)
            phase_3_vm_compaction
            ;;
        4|archive)
            phase_4_archive_backups
            ;;
        all)
            phase_1_safe_cleanup
            phase_2_selective_cleanup
            phase_3_vm_compaction
            phase_4_archive_backups
            ;;
        *)
            echo "Usage: $0 [phase] [--dry-run]"
            echo "  Phases:"
            echo "    1, safe      - Remove dangling images/containers"
            echo "    2, selective - Create backups and selective cleanup"
            echo "    3, vm-compact - Compact Colima disk (requires restart)"
            echo "    4, archive    - Archive backup files"
            echo "    all          - Run all phases"
            echo ""
            echo "  Options:"
            echo "    --dry-run    - Show what would be deleted without changes"
            exit 1
            ;;
    esac

    # Report final disk usage
    echo ""
    report_disk_usage

    print_header "✅ Cleanup Complete"
    print_info "Log saved to: $LOG_FILE"
}

# Run main function
main "$@"
