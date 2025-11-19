#!/usr/bin/env bash
# Build all apps and packages

set -e

echo "🔨 Building All Components"
echo "=========================="
echo ""

# Build packages first (dependencies)
echo "📦 Building packages..."
pnpm --filter "./packages/*" build

echo ""
echo "📦 Building apps..."
pnpm --filter "./apps/web" build
pnpm --filter "./apps/pwa" build

echo ""
echo "✅ Build complete!"
echo ""
echo "Build artifacts:"
echo "  - packages/*/dist/"
echo "  - apps/web/.next/"
echo "  - apps/pwa/dist/"
