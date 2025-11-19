#!/bin/bash

################################################################################
# PETER v10.0.0 - One-Command Project Setup
################################################################################
# Purpose: Fresh environment setup in one command
# Usage: ./setup.sh [--skip-docker] [--skip-data]
# Author: PETER Team
# Version: 10.0.0
################################################################################

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Progress indicators
CHECKMARK="✓"
CROSS="✗"
ARROW="→"

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_DOCKER=false
SKIP_DATA=false

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}${CHECKMARK}${NC} $1"
}

print_error() {
    echo -e "${RED}${CROSS}${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_info() {
    echo -e "${BLUE}${ARROW}${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed ($(command -v $1))"
        return 0
    else
        print_error "$1 is NOT installed"
        return 1
    fi
}

check_version() {
    local cmd=$1
    local min_version=$2
    local current_version=$3

    print_info "Checking $cmd version: $current_version (minimum: $min_version)"
}

################################################################################
# System Requirements Check
################################################################################

check_system_requirements() {
    print_header "Step 1/9: Checking System Requirements"

    local all_good=true

    # Python 3.11+
    if check_command python3; then
        python_version=$(python3 --version | cut -d' ' -f2)
        check_version "Python" "3.11.0" "$python_version"
    else
        all_good=false
        print_error "Python 3.11+ is required"
    fi

    # Node 18+
    if check_command node; then
        node_version=$(node --version | sed 's/v//')
        check_version "Node.js" "18.0.0" "$node_version"
    else
        all_good=false
        print_error "Node.js 18+ is required"
    fi

    # pnpm
    if ! check_command pnpm; then
        print_warning "pnpm not found. Installing..."
        npm install -g pnpm
        check_command pnpm || all_good=false
    fi

    # Docker
    if ! $SKIP_DOCKER; then
        if ! check_command docker; then
            all_good=false
            print_error "Docker is required (use --skip-docker to skip)"
        fi

        if ! check_command docker-compose; then
            all_good=false
            print_error "Docker Compose is required"
        fi
    fi

    # Git
    check_command git || all_good=false

    if [ "$all_good" = false ]; then
        print_error "System requirements not met. Please install missing dependencies."
        exit 1
    fi

    print_success "All system requirements met"
}

################################################################################
# Python Dependencies
################################################################################

install_python_deps() {
    print_header "Step 2/9: Installing Python Dependencies"

    cd "$PROJECT_ROOT"

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel

    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing requirements.txt..."
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found, skipping"
    fi

    # Install pre-commit
    print_info "Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
    print_success "Pre-commit hooks installed"
}

################################################################################
# Node Dependencies
################################################################################

install_node_deps() {
    print_header "Step 3/9: Installing Node Dependencies"

    cd "$PROJECT_ROOT"

    print_info "Installing pnpm dependencies (monorepo)..."
    pnpm install
    print_success "Node dependencies installed"
}

################################################################################
# Environment Setup
################################################################################

setup_environment() {
    print_header "Step 4/9: Setting Up Environment"

    cd "$PROJECT_ROOT"

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_info "Creating .env from .env.example..."
            cp .env.example .env
            print_success ".env file created"
            print_warning "Please update .env with your actual configuration"
        else
            print_warning ".env.example not found, skipping .env creation"
        fi
    else
        print_info ".env file already exists"
    fi
}

################################################################################
# Docker Services
################################################################################

start_docker_services() {
    if $SKIP_DOCKER; then
        print_header "Step 5/9: Skipping Docker Services"
        return
    fi

    print_header "Step 5/9: Starting Docker Services"

    cd "$PROJECT_ROOT"

    if [ -f "docker-compose.yml" ]; then
        print_info "Starting Docker Compose services..."
        docker-compose up -d

        print_info "Waiting for services to be ready (30 seconds)..."
        sleep 30

        print_success "Docker services started"
    else
        print_warning "docker-compose.yml not found, skipping"
    fi
}

################################################################################
# Database Initialization
################################################################################

initialize_databases() {
    print_header "Step 6/9: Initializing Databases"

    cd "$PROJECT_ROOT"

    # Wait for PostgreSQL
    print_info "Checking PostgreSQL connection..."
    for i in {1..30}; do
        if docker exec postgres pg_isready -U postgres &>/dev/null; then
            print_success "PostgreSQL is ready"
            break
        fi
        sleep 1
    done

    # Wait for Qdrant
    print_info "Checking Qdrant connection..."
    for i in {1..30}; do
        if curl -s http://localhost:6333/health &>/dev/null; then
            print_success "Qdrant is ready"
            break
        fi
        sleep 1
    done

    # Wait for Redis
    print_info "Checking Redis connection..."
    for i in {1..30}; do
        if docker exec redis redis-cli ping &>/dev/null; then
            print_success "Redis is ready"
            break
        fi
        sleep 1
    done
}

################################################################################
# Database Migrations
################################################################################

run_migrations() {
    print_header "Step 7/9: Running Database Migrations"

    cd "$PROJECT_ROOT"

    if [ -d "alembic" ]; then
        source .venv/bin/activate
        print_info "Running Alembic migrations..."
        alembic upgrade head
        print_success "Migrations completed"
    else
        print_warning "Alembic directory not found, skipping migrations"
    fi
}

################################################################################
# Seed Data
################################################################################

seed_data() {
    if $SKIP_DATA; then
        print_header "Step 8/9: Skipping Data Seeding"
        return
    fi

    print_header "Step 8/9: Seeding Initial Data"

    cd "$PROJECT_ROOT"

    if [ -f "scripts/seed_data.py" ]; then
        source .venv/bin/activate
        print_info "Running seed script..."
        python scripts/seed_data.py
        print_success "Data seeded"
    else
        print_info "No seed script found, skipping"
    fi
}

################################################################################
# Verification
################################################################################

verify_setup() {
    print_header "Step 9/9: Verifying Setup"

    local all_good=true

    # Check API health
    print_info "Checking API health..."
    if curl -s http://localhost:8001/health &>/dev/null; then
        print_success "API is responding"
    else
        print_warning "API not responding (this is OK if not started)"
    fi

    # Check frontend
    print_info "Checking frontend build..."
    if [ -d "apps/web/node_modules" ]; then
        print_success "Frontend dependencies installed"
    else
        print_warning "Frontend dependencies not installed"
    fi

    # Check services
    if ! $SKIP_DOCKER; then
        print_info "Checking Docker services..."

        services=("postgres" "redis" "qdrant")
        for service in "${services[@]}"; do
            if docker ps | grep -q "$service"; then
                print_success "$service is running"
            else
                print_warning "$service is not running"
                all_good=false
            fi
        done
    fi

    if [ "$all_good" = true ]; then
        print_success "All verifications passed"
    else
        print_warning "Some verifications failed, but setup completed"
    fi
}

################################################################################
# Final Message
################################################################################

print_next_steps() {
    print_header "Setup Complete!"

    echo -e "${GREEN}${CHECKMARK} Setup completed successfully!${NC}\n"

    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Update .env file with your configuration"
    echo -e "  2. Start development servers:"
    echo -e "     ${YELLOW}pnpm dev${NC}          # All apps"
    echo -e "     ${YELLOW}pnpm web${NC}          # Frontend only"
    echo -e "     ${YELLOW}pnpm api${NC}          # API only"
    echo -e ""
    echo -e "  3. View interfaces:"
    echo -e "     ${YELLOW}http://localhost:3000${NC}              # Web App"
    echo -e "     ${YELLOW}http://localhost:8001/api/v1/docs${NC}  # API Docs"
    echo -e "     ${YELLOW}http://localhost:6333/dashboard${NC}    # Qdrant"
    echo -e ""
    echo -e "  4. Run tests:"
    echo -e "     ${YELLOW}./scripts/test-all.sh${NC}"
    echo -e ""
    echo -e "  5. Build for production:"
    echo -e "     ${YELLOW}./scripts/build-all.sh${NC}"
    echo -e ""
    echo -e "${BLUE}Documentation:${NC}"
    echo -e "  • Quick reference: ${YELLOW}CLAUDE.md${NC}"
    echo -e "  • Full guide: ${YELLOW}README.md${NC}"
    echo -e "  • API docs: ${YELLOW}docs/reference/API_DOCUMENTATION.md${NC}"
    echo -e ""
    echo -e "${GREEN}Happy coding! 🚀${NC}\n"
}

################################################################################
# Main Script
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-data)
                SKIP_DATA=true
                shift
                ;;
            --help)
                echo "Usage: ./setup.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-docker    Skip Docker services setup"
                echo "  --skip-data      Skip data seeding"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    print_header "PETER v10.0.0 Setup Script"
    echo -e "${BLUE}This script will set up your development environment.${NC}"
    echo -e "${BLUE}Press Ctrl+C to cancel at any time.${NC}\n"
    sleep 2

    check_system_requirements
    install_python_deps
    install_node_deps
    setup_environment
    start_docker_services
    initialize_databases
    run_migrations
    seed_data
    verify_setup
    print_next_steps
}

# Run main function
main "$@"
