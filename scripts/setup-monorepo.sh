#!/bin/bash

# RAG Enterprise - Monorepo Setup Script
# This script initializes the monorepo structure with Turborepo and PNPM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi

    # Check PNPM
    if ! command -v pnpm &> /dev/null; then
        log_warning "PNPM not found. Installing PNPM..."
        npm install -g pnpm
    fi

    log_success "Prerequisites check passed"
}

# Create monorepo structure
create_structure() {
    log_info "Creating monorepo structure..."

    cd "$PROJECT_ROOT"

    # Create main directories
    mkdir -p apps/web
    mkdir -p apps/mobile
    mkdir -p apps/pwa
    mkdir -p apps/api

    mkdir -p packages/ui/src/components
    mkdir -p packages/ui/src/layouts
    mkdir -p packages/ui/src/themes

    mkdir -p packages/core/src/auth
    mkdir -p packages/core/src/api
    mkdir -p packages/core/src/utils

    mkdir -p packages/mobile-ui/src

    mkdir -p packages/config/eslint
    mkdir -p packages/config/tsconfig
    mkdir -p packages/config/tailwind

    log_success "Directory structure created"
}

# Initialize root package.json
init_root_package() {
    log_info "Initializing root package.json..."

    cat > "$PROJECT_ROOT/package.json" << 'EOF'
{
  "name": "rag-enterprise",
  "version": "1.0.0",
  "private": true,
  "description": "RAG Enterprise - Multi-platform AI-powered search system",
  "scripts": {
    "dev": "turbo run dev",
    "dev:web": "turbo run dev --filter=@rag/web",
    "dev:mobile": "turbo run dev --filter=@rag/mobile",
    "dev:pwa": "turbo run dev --filter=@rag/pwa",
    "dev:api": "turbo run dev --filter=@rag/api",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "type-check": "turbo run type-check",
    "clean": "turbo run clean",
    "format": "prettier --write \"**/*.{ts,tsx,md,json}\"",
    "changeset": "changeset",
    "version": "changeset version",
    "publish": "turbo run build --filter=./packages/* && changeset publish"
  },
  "devDependencies": {
    "@changesets/cli": "^2.27.1",
    "@turbo/gen": "^2.0.0",
    "eslint": "^8.57.0",
    "prettier": "^3.2.5",
    "turbo": "^2.0.0",
    "typescript": "^5.3.3"
  },
  "packageManager": "pnpm@9.1.0",
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=9.0.0"
  }
}
EOF

    log_success "Root package.json created"
}

# Create PNPM workspace
create_pnpm_workspace() {
    log_info "Creating PNPM workspace configuration..."

    cat > "$PROJECT_ROOT/pnpm-workspace.yaml" << 'EOF'
packages:
  - 'apps/*'
  - 'packages/*'
  - 'infrastructure/*'
EOF

    log_success "PNPM workspace configured"
}

# Create Turbo configuration
create_turbo_config() {
    log_info "Creating Turborepo configuration..."

    cat > "$PROJECT_ROOT/turbo.json" << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**", "build/**"],
      "env": ["NODE_ENV", "API_URL", "NEXT_PUBLIC_*"]
    },
    "dev": {
      "cache": false,
      "persistent": true,
      "env": ["NODE_ENV", "API_URL", "NEXT_PUBLIC_*"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"],
      "env": ["NODE_ENV"]
    },
    "lint": {
      "outputs": []
    },
    "type-check": {
      "outputs": []
    },
    "clean": {
      "cache": false
    }
  }
}
EOF

    log_success "Turborepo configured"
}

# Create shared UI package
create_ui_package() {
    log_info "Creating @rag/ui package..."

    cat > "$PROJECT_ROOT/packages/ui/package.json" << 'EOF'
{
  "name": "@rag/ui",
  "version": "1.0.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./components": "./src/components/index.ts",
    "./themes": "./src/themes/index.ts",
    "./layouts": "./src/layouts/index.ts"
  },
  "scripts": {
    "dev": "tsc --watch",
    "build": "tsc",
    "lint": "eslint src/",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@radix-ui/react-alert-dialog": "^1.0.5",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-toast": "^1.1.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.400.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "tailwind-merge": "^2.3.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.3"
  }
}
EOF

    # Create index files
    cat > "$PROJECT_ROOT/packages/ui/src/index.ts" << 'EOF'
// UI Components
export * from './components'
export * from './themes'
export * from './layouts'
EOF

    cat > "$PROJECT_ROOT/packages/ui/src/components/index.ts" << 'EOF'
// Export all components
export { Button } from './Button'
export { Input } from './Input'
export { Card } from './Card'
export { LoginForm } from './auth/LoginForm'
export { RegisterForm } from './auth/RegisterForm'
EOF

    log_success "@rag/ui package created"
}

# Create shared Core package
create_core_package() {
    log_info "Creating @rag/core package..."

    cat > "$PROJECT_ROOT/packages/core/package.json" << 'EOF'
{
  "name": "@rag/core",
  "version": "1.0.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./auth": "./src/auth/index.ts",
    "./api": "./src/api/index.ts",
    "./utils": "./src/utils/index.ts"
  },
  "scripts": {
    "dev": "tsc --watch",
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src/",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "axios": "^1.6.8",
    "zustand": "^4.5.2",
    "@tanstack/react-query": "^5.32.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "jest": "^29.7.0",
    "typescript": "^5.3.3"
  }
}
EOF

    # Create auth service
    cat > "$PROJECT_ROOT/packages/core/src/auth/authService.ts" << 'EOF'
import axios from 'axios'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  name: string
  company: string
}

export class AuthService {
  private baseURL: string

  constructor(baseURL: string = process.env.API_URL || 'http://localhost:8001') {
    this.baseURL = baseURL
  }

  async login(credentials: LoginCredentials) {
    const response = await axios.post(`${this.baseURL}/api/v1/auth/login`, credentials)
    return response.data
  }

  async register(data: RegisterData) {
    const response = await axios.post(`${this.baseURL}/api/v1/auth/register`, data)
    return response.data
  }

  async logout() {
    // Clear tokens and user data
    return true
  }

  async refreshToken(token: string) {
    const response = await axios.post(`${this.baseURL}/api/v1/auth/refresh`, { token })
    return response.data
  }
}

export const authService = new AuthService()
EOF

    log_success "@rag/core package created"
}

# Migrate existing frontend-v2 to apps/web
migrate_web_app() {
    log_info "Migrating frontend-v2 to apps/web..."

    if [ -d "$PROJECT_ROOT/frontend-v2" ]; then
        # Copy frontend-v2 to apps/web
        cp -r "$PROJECT_ROOT/frontend-v2/"* "$PROJECT_ROOT/apps/web/" 2>/dev/null || true

        # Update package.json
        cat > "$PROJECT_ROOT/apps/web/package.json" << 'EOF'
{
  "name": "@rag/web",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@rag/ui": "workspace:*",
    "@rag/core": "workspace:*",
    "next": "14.2.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5"
  }
}
EOF

        log_success "Web app migrated"
    else
        log_warning "frontend-v2 not found, creating new web app structure"
        # Create basic Next.js structure
        mkdir -p "$PROJECT_ROOT/apps/web/app"
    fi
}

# Create PWA app
create_pwa_app() {
    log_info "Creating PWA app..."

    cat > "$PROJECT_ROOT/apps/pwa/package.json" << 'EOF'
{
  "name": "@rag/pwa",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src/",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@rag/ui": "workspace:*",
    "@rag/core": "workspace:*",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "workbox-window": "^7.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.2.0",
    "vite-plugin-pwa": "^0.19.0",
    "typescript": "^5.3.3"
  }
}
EOF

    # Create manifest.json
    cat > "$PROJECT_ROOT/apps/pwa/manifest.json" << 'EOF'
{
  "name": "RAG Enterprise",
  "short_name": "RAG",
  "description": "AI-powered enterprise search",
  "theme_color": "#3B82F6",
  "background_color": "#ffffff",
  "display": "standalone",
  "orientation": "portrait",
  "scope": "/",
  "start_url": "/",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    }
  ]
}
EOF

    log_success "PWA app created"
}

# Create mobile app structure
create_mobile_app() {
    log_info "Creating mobile app structure..."

    cat > "$PROJECT_ROOT/apps/mobile/package.json" << 'EOF'
{
  "name": "@rag/mobile",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "build:android": "eas build --platform android",
    "build:ios": "eas build --platform ios",
    "test": "jest",
    "lint": "eslint src/"
  },
  "dependencies": {
    "@rag/core": "workspace:*",
    "expo": "~50.0.0",
    "expo-status-bar": "~1.11.1",
    "react": "18.2.0",
    "react-native": "0.73.6",
    "@react-navigation/native": "^6.1.17",
    "@react-navigation/stack": "^6.3.29"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0",
    "@types/react": "~18.2.0",
    "jest": "^29.7.0",
    "typescript": "^5.3.3"
  }
}
EOF

    # Create App.tsx
    cat > "$PROJECT_ROOT/apps/mobile/App.tsx" << 'EOF'
import React from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { AuthProvider } from '@rag/core/auth'
import { AppNavigator } from './src/navigation/AppNavigator'

export default function App() {
  return (
    <NavigationContainer>
      <AuthProvider>
        <AppNavigator />
      </AuthProvider>
    </NavigationContainer>
  )
}
EOF

    log_success "Mobile app created"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."

    cd "$PROJECT_ROOT"

    # Install root dependencies
    pnpm install

    log_success "Dependencies installed"
}

# Create development scripts
create_dev_scripts() {
    log_info "Creating development scripts..."

    # Create start-all script
    cat > "$PROJECT_ROOT/scripts/start-all.sh" << 'EOF'
#!/bin/bash
# Start all services in development mode

echo "Starting all services..."

# Start backend
docker-compose up -d

# Wait for backend to be ready
echo "Waiting for backend..."
sleep 10

# Start all frontend apps
pnpm dev

echo "All services started!"
echo "Web: http://localhost:3000"
echo "PWA: http://localhost:5173"
echo "Mobile: Use Expo Go app"
echo "API: http://localhost:8001"
EOF

    chmod +x "$PROJECT_ROOT/scripts/start-all.sh"

    log_success "Development scripts created"
}

# Main execution
main() {
    log_info "Starting monorepo setup..."
    echo "================================"

    check_prerequisites
    create_structure
    init_root_package
    create_pnpm_workspace
    create_turbo_config
    create_ui_package
    create_core_package
    migrate_web_app
    create_pwa_app
    create_mobile_app
    install_dependencies
    create_dev_scripts

    echo "================================"
    log_success "Monorepo setup complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review the structure in apps/ and packages/"
    echo "  2. Run 'pnpm dev' to start all apps"
    echo "  3. Run 'pnpm dev:web' for web only"
    echo "  4. Run 'pnpm dev:mobile' for mobile only"
    echo ""
    log_info "Documentation:"
    echo "  See docs/MULTI_PLATFORM_ARCHITECTURE.md for details"
}

# Run if not sourced
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi