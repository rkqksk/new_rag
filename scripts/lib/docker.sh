#!/bin/bash
# Docker utilities for container management
# Source this file: source scripts/lib/docker.sh

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        return 1
    fi

    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        return 1
    fi

    print_success "Docker is available"
    return 0
}

# Check if docker-compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed"
        return 1
    fi

    print_success "docker-compose is available"
    return 0
}

# Start Docker services
start_services() {
    local compose_file="${1:-docker-compose.yml}"

    print_info "Starting Docker services from $compose_file..."

    if docker-compose -f "$compose_file" up -d; then
        print_success "Docker services started"
        return 0
    else
        print_error "Failed to start Docker services"
        return 1
    fi
}

# Stop Docker services
stop_services() {
    local compose_file="${1:-docker-compose.yml}"

    print_info "Stopping Docker services..."

    if docker-compose -f "$compose_file" down; then
        print_success "Docker services stopped"
        return 0
    else
        print_error "Failed to stop Docker services"
        return 1
    fi
}

# Show Docker service status
show_status() {
    print_header "Docker Service Status"
    docker-compose ps
}

# Show Docker service logs
show_logs() {
    local service="${1:-}"
    local lines="${2:-50}"

    if [ -z "$service" ]; then
        docker-compose logs --tail="$lines"
    else
        docker-compose logs --tail="$lines" "$service"
    fi
}

# Build Docker images
build_images() {
    local compose_file="${1:-docker-compose.yml}"

    print_info "Building Docker images..."

    if docker-compose -f "$compose_file" build; then
        print_success "Docker images built successfully"
        return 0
    else
        print_error "Failed to build Docker images"
        return 1
    fi
}

# Check prerequisites for Docker deployment
check_docker_prerequisites() {
    local failed=0

    print_header "Checking Docker Prerequisites"

    check_docker || ((failed++))
    check_docker_compose || ((failed++))

    # Check for .env file
    if [ ! -f .env ]; then
        print_error ".env file not found"
        print_info "Please create .env from .env.example"
        ((failed++))
    else
        print_success ".env file found"
    fi

    # Check available disk space (need at least 10GB)
    local available_gb=$(df -BG . | awk 'NR==2 {print $4}' | tr -d 'G')
    if [ "$available_gb" -lt 10 ]; then
        print_warning "Low disk space: ${available_gb}GB available (10GB recommended)"
    else
        print_success "Sufficient disk space: ${available_gb}GB available"
    fi

    if [ $failed -eq 0 ]; then
        print_success "All Docker prerequisites met"
        return 0
    else
        print_error "$failed prerequisite(s) not met"
        return 1
    fi
}
