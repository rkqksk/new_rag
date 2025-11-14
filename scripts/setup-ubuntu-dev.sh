#!/bin/bash
# =============================================================================
# Ubuntu Development Environment Setup
# =============================================================================
# For Ubuntu 22.04/24.04 LTS
# Sets up complete development environment for RAG Enterprise project
#
# Usage:
#   ./scripts/setup-ubuntu-dev.sh
#
# Version: v1.0.0
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 is installed"
        return 0
    else
        log_warning "$1 is not installed"
        return 1
    fi
}

# =============================================================================
# System Requirements Check
# =============================================================================

check_system() {
    log_info "Checking system requirements..."

    # Check Ubuntu version
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "OS: $NAME $VERSION"

        if [[ "$ID" != "ubuntu" ]]; then
            log_error "This script is designed for Ubuntu. Detected: $ID"
            exit 1
        fi

        VERSION_NUM=$(echo "$VERSION_ID" | cut -d. -f1)
        if [[ "$VERSION_NUM" -lt 22 ]]; then
            log_warning "Ubuntu version $VERSION_ID detected. Recommended: 22.04 or 24.04 LTS"
        fi
    else
        log_error "Cannot detect OS version"
        exit 1
    fi

    # Check architecture
    ARCH=$(uname -m)
    log_info "Architecture: $ARCH"

    if [[ "$ARCH" != "x86_64" && "$ARCH" != "aarch64" ]]; then
        log_warning "Unsupported architecture: $ARCH"
    fi

    # Check available memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    log_info "Total Memory: ${TOTAL_MEM}GB"

    if [[ "$TOTAL_MEM" -lt 4 ]]; then
        log_warning "Low memory detected. Recommended: 8GB+ for full stack"
    fi

    # Check disk space
    DISK_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    log_info "Available Disk Space: ${DISK_SPACE}GB"

    if [[ "$DISK_SPACE" -lt 20 ]]; then
        log_warning "Low disk space. Recommended: 50GB+ for Docker images and data"
    fi

    log_success "System check completed"
}

# =============================================================================
# Install System Dependencies
# =============================================================================

install_system_deps() {
    log_info "Installing system dependencies..."

    sudo apt-get update -qq

    # Essential build tools
    sudo apt-get install -y \
        build-essential \
        cmake \
        pkg-config \
        git \
        curl \
        wget \
        ca-certificates \
        gnupg \
        lsb-release

    # Python build dependencies
    sudo apt-get install -y \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libffi-dev \
        liblzma-dev \
        python3-dev \
        python3-pip

    # PostgreSQL client
    sudo apt-get install -y \
        postgresql-client \
        libpq-dev

    # Redis client
    sudo apt-get install -y redis-tools

    # OpenCV dependencies
    sudo apt-get install -y \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1

    # OCR dependencies
    sudo apt-get install -y \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-kor

    # Network tools
    sudo apt-get install -y \
        net-tools \
        netcat-openbsd \
        iputils-ping

    # Compression tools
    sudo apt-get install -y \
        zip \
        unzip \
        tar \
        gzip

    # Monitoring tools
    sudo apt-get install -y \
        htop \
        iotop \
        iftop

    log_success "System dependencies installed"
}

# =============================================================================
# Install Docker
# =============================================================================

install_docker() {
    if check_command docker; then
        DOCKER_VERSION=$(docker --version)
        log_info "Docker already installed: $DOCKER_VERSION"
        return 0
    fi

    log_info "Installing Docker..."

    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh

    # Add user to docker group
    sudo usermod -aG docker "$USER"

    # Configure Docker daemon
    sudo mkdir -p /etc/docker
    cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}
EOF

    # Start Docker
    sudo systemctl enable docker
    sudo systemctl start docker

    log_success "Docker installed"
    log_warning "Please log out and log back in for docker group changes to take effect"
}

# =============================================================================
# Install Python Tools
# =============================================================================

install_python_tools() {
    log_info "Setting up Python environment..."

    # Upgrade pip
    python3 -m pip install --upgrade pip setuptools wheel

    # Install virtualenv
    python3 -m pip install --user virtualenv

    # Install pyenv (optional but recommended)
    if ! check_command pyenv; then
        log_info "Installing pyenv..."
        curl https://pyenv.run | bash

        # Add to shell config
        SHELL_CONFIG="$HOME/.bashrc"
        if [[ "$SHELL" == *"zsh"* ]]; then
            SHELL_CONFIG="$HOME/.zshrc"
        fi

        cat <<'EOF' >> "$SHELL_CONFIG"

# Pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOF

        log_success "pyenv installed. Please restart your shell or run: source $SHELL_CONFIG"
    fi

    log_success "Python tools installed"
}

# =============================================================================
# Install Node.js and pnpm
# =============================================================================

install_nodejs() {
    if check_command node; then
        NODE_VERSION=$(node --version)
        log_info "Node.js already installed: $NODE_VERSION"
    else
        log_info "Installing Node.js..."

        # Install Node.js 20.x LTS
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs

        log_success "Node.js installed"
    fi

    # Install pnpm
    if ! check_command pnpm; then
        log_info "Installing pnpm..."
        npm install -g pnpm
        log_success "pnpm installed"
    fi
}

# =============================================================================
# Setup Project Environment
# =============================================================================

setup_project_env() {
    log_info "Setting up project environment..."

    # Create .env file if not exists
    if [ ! -f .env ]; then
        log_info "Creating .env file from .env.example..."
        cp .env.example .env
        log_warning "Please update .env with your actual configuration"
    fi

    # Create Python virtual environment
    if [ ! -d .venv ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv .venv
        log_success "Virtual environment created"
    fi

    # Activate venv and install dependencies
    log_info "Installing Python dependencies..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate

    # Install Node dependencies
    if [ -f package.json ]; then
        log_info "Installing Node dependencies..."
        pnpm install
    fi

    # Setup git hooks
    if [ -f scripts/install-hooks.sh ]; then
        log_info "Installing git hooks..."
        bash scripts/install-hooks.sh
    fi

    log_success "Project environment setup completed"
}

# =============================================================================
# Configure System Limits
# =============================================================================

configure_system_limits() {
    log_info "Configuring system limits..."

    # Increase file descriptor limits
    cat <<EOF | sudo tee /etc/security/limits.d/99-rag-enterprise.conf
*               soft    nofile          65536
*               hard    nofile          65536
root            soft    nofile          65536
root            hard    nofile          65536
EOF

    # Increase vm.max_map_count for Qdrant
    echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p

    log_success "System limits configured"
}

# =============================================================================
# Setup systemd Service (Optional)
# =============================================================================

setup_systemd_service() {
    log_info "Setting up systemd service..."

    read -p "Do you want to enable auto-start on boot? (y/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping systemd service setup"
        return 0
    fi

    PROJECT_DIR=$(pwd)

    cat <<EOF | sudo tee /etc/systemd/system/rag-enterprise.service
[Unit]
Description=RAG Enterprise Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=$USER

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable rag-enterprise.service

    log_success "Systemd service created and enabled"
}

# =============================================================================
# Main Installation Flow
# =============================================================================

main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     RAG Enterprise - Ubuntu Development Environment Setup     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Run all setup steps
    check_system
    echo ""

    install_system_deps
    echo ""

    install_docker
    echo ""

    install_python_tools
    echo ""

    install_nodejs
    echo ""

    setup_project_env
    echo ""

    configure_system_limits
    echo ""

    setup_systemd_service
    echo ""

    # Final summary
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    Installation Complete! 🎉                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    log_success "Development environment setup completed"
    echo ""
    echo "Next steps:"
    echo "  1. Log out and log back in (for docker group permissions)"
    echo "  2. Update .env file with your configuration"
    echo "  3. Run: docker compose up -d"
    echo "  4. Run: source .venv/bin/activate"
    echo "  5. Access services:"
    echo "     - API: http://localhost:8001/docs"
    echo "     - Grafana: http://localhost:3000"
    echo "     - Jaeger: http://localhost:16686"
    echo ""
    echo "For more information, see:"
    echo "  - README.md"
    echo "  - CLAUDE.md"
    echo "  - docs/guides/LOCAL_SETUP.md"
    echo ""
}

# Run main function
main "$@"
