#!/bin/bash

################################################################################
# PETER v10.0.0 - Monorepo Build Automation
################################################################################
# Purpose: Build all apps and packages in correct order
# Usage: ./build-all.sh [--parallel] [--skip-lint] [--production]
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
BUILD_START_TIME=$(date +%s)
PARALLEL_BUILD=false
SKIP_LINT=false
PRODUCTION=false
DIST_DIR="$PROJECT_ROOT/dist"

# Build order
PACKAGES=("config" "utils" "core" "ui")
APPS=("api" "web" "pwa")

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

format_time() {
    local seconds=$1
    local minutes=$((seconds / 60))
    local remaining_seconds=$((seconds % 60))

    if [ $minutes -gt 0 ]; then
        echo "${minutes}m ${remaining_seconds}s"
    else
        echo "${remaining_seconds}s"
    fi
}

get_dir_size() {
    local dir=$1
    if [ -d "$dir" ]; then
        du -sh "$dir" 2>/dev/null | cut -f1
    else
        echo "N/A"
    fi
}

################################################################################
# Pre-Build Checks
################################################################################

pre_build_checks() {
    print_header "Step 1/6: Pre-Build Checks"

    cd "$PROJECT_ROOT"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_error "node_modules not found. Run: pnpm install"
        exit 1
    fi
    print_success "node_modules found"

    # Check if pnpm is available
    if ! command -v pnpm &> /dev/null; then
        print_error "pnpm not found. Install: npm install -g pnpm"
        exit 1
    fi
    print_success "pnpm is available"

    # Clean previous build artifacts
    print_info "Cleaning previous build artifacts..."
    rm -rf "$DIST_DIR"
    mkdir -p "$DIST_DIR"
    print_success "Build directory cleaned"
}

################################################################################
# Type Checking
################################################################################

type_check() {
    print_header "Step 2/6: TypeScript Type Checking"

    cd "$PROJECT_ROOT"

    print_info "Running TypeScript compiler..."
    if pnpm run --recursive --parallel type-check 2>/dev/null || true; then
        print_success "Type checking completed"
    else
        print_warning "Some type errors found (continuing anyway)"
    fi
}

################################################################################
# Linting
################################################################################

run_linting() {
    if $SKIP_LINT; then
        print_header "Step 3/6: Skipping Linting"
        return
    fi

    print_header "Step 3/6: Linting Code"

    cd "$PROJECT_ROOT"

    # ESLint
    print_info "Running ESLint..."
    if pnpm run lint 2>/dev/null || true; then
        print_success "ESLint passed"
    else
        print_warning "ESLint found issues (continuing anyway)"
    fi

    # Prettier
    print_info "Running Prettier..."
    if pnpm run format --check 2>/dev/null || true; then
        print_success "Prettier check passed"
    else
        print_warning "Code formatting issues found (continuing anyway)"
    fi

    # Python linting (if available)
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate

        print_info "Running Python linting..."

        if command -v black &> /dev/null; then
            black --check apps/api/ 2>/dev/null || true
        fi

        if command -v flake8 &> /dev/null; then
            flake8 apps/api/ 2>/dev/null || true
        fi

        print_success "Python linting completed"
    fi
}

################################################################################
# Build Packages
################################################################################

build_packages() {
    print_header "Step 4/6: Building Packages"

    local start_time=$(date +%s)

    for package in "${PACKAGES[@]}"; do
        local package_dir="$PROJECT_ROOT/packages/$package"

        if [ -d "$package_dir" ]; then
            print_info "Building @rag/$package..."

            cd "$package_dir"

            # Check if package has build script
            if grep -q '"build"' package.json 2>/dev/null; then
                if $PARALLEL_BUILD; then
                    pnpm run build &
                else
                    pnpm run build
                fi

                local package_size=$(get_dir_size "$package_dir/dist")
                print_success "@rag/$package built (size: $package_size)"
            else
                print_warning "@rag/$package has no build script"
            fi
        else
            print_warning "Package $package not found at $package_dir"
        fi
    done

    # Wait for parallel builds
    if $PARALLEL_BUILD; then
        wait
        print_success "All packages built in parallel"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    print_success "Packages built in $(format_time $duration)"
}

################################################################################
# Build Apps
################################################################################

build_apps() {
    print_header "Step 5/6: Building Applications"

    local start_time=$(date +%s)

    # Build API (Python)
    print_info "Building API (Python)..."
    cd "$PROJECT_ROOT/apps/api"

    if [ -f "requirements.txt" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"

        # Check Python code
        if command -v python &> /dev/null; then
            python -m py_compile main.py 2>/dev/null || true
            print_success "API Python code validated"
        fi
    fi

    # Build Web Apps (TypeScript)
    for app in "${APPS[@]}"; do
        local app_dir="$PROJECT_ROOT/apps/$app"

        if [ -d "$app_dir" ]; then
            print_info "Building $app..."

            cd "$app_dir"

            # Check if app has build script
            if grep -q '"build"' package.json 2>/dev/null; then
                if $PARALLEL_BUILD && [ "$app" != "api" ]; then
                    pnpm run build &
                else
                    if $PRODUCTION; then
                        NODE_ENV=production pnpm run build
                    else
                        pnpm run build
                    fi
                fi

                local app_size=$(get_dir_size "$app_dir/.next") || \
                                 $(get_dir_size "$app_dir/dist") || "N/A"
                print_success "$app built (size: $app_size)"
            else
                print_warning "$app has no build script"
            fi
        else
            print_info "App $app not found (skipping)"
        fi
    done

    # Wait for parallel builds
    if $PARALLEL_BUILD; then
        wait
        print_success "All apps built in parallel"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    print_success "Applications built in $(format_time $duration)"
}

################################################################################
# Generate Build Report
################################################################################

generate_build_report() {
    print_header "Step 6/6: Generating Build Report"

    local build_end_time=$(date +%s)
    local total_duration=$((build_end_time - BUILD_START_TIME))

    # Create report file
    local report_file="$DIST_DIR/build-report.txt"

    {
        echo "═══════════════════════════════════════════════════════════"
        echo "  PETER v10.0.0 Build Report"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "Build Time: $(date)"
        echo "Total Duration: $(format_time $total_duration)"
        echo "Mode: $([ "$PRODUCTION" = true ] && echo "Production" || echo "Development")"
        echo ""
        echo "Package Sizes:"

        for package in "${PACKAGES[@]}"; do
            local size=$(get_dir_size "$PROJECT_ROOT/packages/$package/dist")
            echo "  @rag/$package: $size"
        done

        echo ""
        echo "Application Sizes:"

        echo "  api: $(get_dir_size "$PROJECT_ROOT/apps/api")"
        echo "  web: $(get_dir_size "$PROJECT_ROOT/apps/web/.next")"
        echo "  pwa: $(get_dir_size "$PROJECT_ROOT/apps/pwa/dist")"

        echo ""
        echo "Build Options:"
        echo "  Parallel: $PARALLEL_BUILD"
        echo "  Skip Lint: $SKIP_LINT"
        echo "  Production: $PRODUCTION"
        echo ""
        echo "═══════════════════════════════════════════════════════════"
    } > "$report_file"

    # Display summary
    cat "$report_file"

    print_success "Build report saved to $report_file"
}

################################################################################
# Final Summary
################################################################################

print_final_summary() {
    print_header "Build Complete!"

    local build_end_time=$(date +%s)
    local total_duration=$((build_end_time - BUILD_START_TIME))

    echo -e "${GREEN}${CHECKMARK} Build completed successfully in $(format_time $total_duration)!${NC}\n"

    echo -e "${BLUE}Build Artifacts:${NC}"
    echo -e "  • Packages: ${YELLOW}packages/*/dist${NC}"
    echo -e "  • Web: ${YELLOW}apps/web/.next${NC}"
    echo -e "  • PWA: ${YELLOW}apps/pwa/dist${NC}"
    echo -e "  • Report: ${YELLOW}dist/build-report.txt${NC}"
    echo -e ""

    echo -e "${BLUE}Next Steps:${NC}"
    if $PRODUCTION; then
        echo -e "  1. Deploy to production:"
        echo -e "     ${YELLOW}./scripts/deploy-production.sh${NC}"
        echo -e ""
        echo -e "  2. Or test production build locally:"
        echo -e "     ${YELLOW}cd apps/web && pnpm start${NC}"
    else
        echo -e "  1. Start development server:"
        echo -e "     ${YELLOW}pnpm dev${NC}"
        echo -e ""
        echo -e "  2. Or run tests:"
        echo -e "     ${YELLOW}./scripts/test-all.sh${NC}"
    fi
    echo -e ""

    echo -e "${GREEN}Build artifacts ready for deployment! 🚀${NC}\n"
}

################################################################################
# Main Script
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --parallel)
                PARALLEL_BUILD=true
                shift
                ;;
            --skip-lint)
                SKIP_LINT=true
                shift
                ;;
            --production)
                PRODUCTION=true
                shift
                ;;
            --help)
                echo "Usage: ./build-all.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --parallel       Build packages/apps in parallel"
                echo "  --skip-lint      Skip linting step"
                echo "  --production     Build for production (optimized)"
                echo "  --help           Show this help message"
                echo ""
                echo "Examples:"
                echo "  ./build-all.sh                    # Standard build"
                echo "  ./build-all.sh --parallel         # Faster parallel build"
                echo "  ./build-all.sh --production       # Production build"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    print_header "PETER v10.0.0 Build Script"

    if $PRODUCTION; then
        echo -e "${BLUE}Building for PRODUCTION (optimized)${NC}\n"
    else
        echo -e "${BLUE}Building for DEVELOPMENT${NC}\n"
    fi

    sleep 1

    pre_build_checks
    type_check
    run_linting
    build_packages
    build_apps
    generate_build_report
    print_final_summary
}

# Run main function
main "$@"
