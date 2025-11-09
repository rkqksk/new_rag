#!/bin/bash
#
# Install Git hooks from .githooks/ to .git/hooks/
#

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🪝 Installing Git hooks..."
echo ""

# Check if .git exists
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Copy hooks
if [ -d ".githooks" ]; then
    for hook in .githooks/*; do
        hook_name=$(basename "$hook")
        target=".git/hooks/$hook_name"

        cp "$hook" "$target"
        chmod +x "$target"

        echo "✅ Installed: $hook_name"
    done
else
    echo "⚠️  No .githooks directory found"
    exit 1
fi

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
ls -1 .git/hooks/ | grep -v ".sample"
echo ""
