#!/bin/bash
# Migration Script 1: Copy src/ features to backend/
# Safe, incremental copy with conflict detection

set -e

echo "🚀 Phase 3B: Copying src/ features to backend/"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track statistics
COPIED=0
SKIPPED=0
CONFLICTS=0

# Function to safely copy file
safe_copy() {
    local src="$1"
    local dest="$2"
    local filename=$(basename "$src")

    if [ -f "$dest" ]; then
        # File exists, check if different
        if diff -q "$src" "$dest" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $dest (identical, skipped)"
            ((SKIPPED++))
        else
            # Files differ, create versioned copy
            local dest_v2="${dest%.py}_v2.py"
            cp "$src" "$dest_v2"
            echo -e "  ${YELLOW}⚠${NC} $dest_v2 (conflict, created v2)"
            ((CONFLICTS++))
        fi
    else
        cp "$src" "$dest"
        echo -e "  ${GREEN}✓${NC} $dest (copied)"
        ((COPIED++))
    fi
}

# Step 1: Create backend/api/v2/ structure
echo ""
echo "Step 1: Creating backend/api/v2/ structure..."
mkdir -p backend/api/v2/

cat > backend/api/v2/__init__.py << 'EOF'
"""
API v2 - Experimental Features
Version: v8-v9
Status: Preview

Experimental APIs from v8-v9:
- JWT Authentication
- Advanced Manufacturing (LORA + UR10e)
- Metrics & Analytics
- Recommendations
- Search Ranking
- WebSocket Notifications
- SaaS Platform
- Ultimate Services
"""

__version__ = "2.0.0"
__all__ = [
    "auth",
    "manufacturing",
    "metrics",
    "recommendations",
    "search_ranking",
    "websocket",
    "saas",
]
EOF

echo -e "  ${GREEN}✓${NC} Created backend/api/v2/__init__.py"

# Step 2: Copy src/api/routes/ to backend/api/v2/
echo ""
echo "Step 2: Copying src/api/routes/ to backend/api/v2/..."

# Critical v2 routes
routes=(
    "auth.py"
    "manufacturing.py"
    "metrics.py"
    "recommendations.py"
    "search_ranking.py"
    "websocket.py"
)

for route in "${routes[@]}"; do
    if [ -f "src/api/routes/$route" ]; then
        safe_copy "src/api/routes/$route" "backend/api/v2/$route"
    else
        echo -e "  ${RED}✗${NC} src/api/routes/$route not found"
    fi
done

# Ultimate services routes
echo ""
echo "Step 2b: Copying ultimate_* routes..."
for file in src/api/routes/ultimate_*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        safe_copy "$file" "backend/api/v2/$filename"
    fi
done

# Copy SaaS from v1
if [ -f "src/api/v1/saas.py" ]; then
    safe_copy "src/api/v1/saas.py" "backend/api/v2/saas.py"
fi

# Step 3: Copy src/middleware/ to backend/middleware/advanced/
echo ""
echo "Step 3: Copying src/middleware/ to backend/middleware/advanced/..."
mkdir -p backend/middleware/advanced/

safe_copy "src/middleware/rate_limiting.py" "backend/middleware/advanced/rate_limiting.py"
safe_copy "src/middleware/error_tracking.py" "backend/middleware/advanced/error_tracking.py"

cat > backend/middleware/advanced/__init__.py << 'EOF'
"""
Advanced Middleware (v8.5+)
- Rate limiting with multiple algorithms
- Error tracking and analytics
"""

from .rate_limiting import RateLimitMiddleware, RateLimitTier, RateLimitAlgorithm
from .error_tracking import (
    ErrorTrackingMiddleware,
    RequestContextMiddleware,
    AnalyticsMiddleware
)

__all__ = [
    "RateLimitMiddleware",
    "RateLimitTier",
    "RateLimitAlgorithm",
    "ErrorTrackingMiddleware",
    "RequestContextMiddleware",
    "AnalyticsMiddleware",
]
EOF

echo -e "  ${GREEN}✓${NC} Created backend/middleware/advanced/__init__.py"

# Step 4: Copy src/services/ to backend/services/
echo ""
echo "Step 4: Copying src/services/ to backend/services/..."

for file in src/services/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        safe_copy "$file" "backend/services/$filename"
    fi
done

# Step 5: Copy src/core/ subdirectories
echo ""
echo "Step 5: Copying src/core/ subdirectories..."

core_dirs=(
    "advanced_rag"
    "multimodal"
    "ocr"
    "recommendation"
    "auth"
    "caching"
    "enhancements"
    "image_matching"
    "shape_processors"
    "structured_processors"
)

for dir in "${core_dirs[@]}"; do
    if [ -d "src/core/$dir" ]; then
        if [ -d "backend/core/$dir" ]; then
            echo -e "  ${YELLOW}⚠${NC} backend/core/$dir already exists (skipped)"
            ((SKIPPED++))
        else
            cp -r "src/core/$dir" "backend/core/"
            echo -e "  ${GREEN}✓${NC} Copied backend/core/$dir"
            ((COPIED++))
        fi
    fi
done

# Copy individual core files
echo ""
echo "Step 5b: Copying individual core files..."
for file in src/core/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        safe_copy "$file" "backend/core/$filename"
    fi
done

# Step 6: Copy top-level modules
echo ""
echo "Step 6: Copying top-level modules..."

# Auth module
if [ -d "src/auth" ] && [ ! -d "backend/auth" ]; then
    cp -r src/auth backend/
    echo -e "  ${GREEN}✓${NC} Copied backend/auth"
    ((COPIED++))
elif [ -d "backend/auth" ]; then
    echo -e "  ${YELLOW}⚠${NC} backend/auth already exists (skipped)"
    ((SKIPPED++))
fi

# DB module
if [ -d "src/db" ] && [ ! -d "backend/db" ]; then
    cp -r src/db backend/
    echo -e "  ${GREEN}✓${NC} Copied backend/db"
    ((COPIED++))
elif [ -d "backend/db" ]; then
    echo -e "  ${YELLOW}⚠${NC} backend/db already exists (skipped)"
    ((SKIPPED++))
fi

# Models
if [ -f "src/models/saas_models.py" ]; then
    safe_copy "src/models/saas_models.py" "backend/models/saas_models.py"
fi

# Integrations
if [ -d "src/integrations" ] && [ ! -d "backend/integrations" ]; then
    cp -r src/integrations backend/
    echo -e "  ${GREEN}✓${NC} Copied backend/integrations"
    ((COPIED++))
fi

# Streaming
if [ -d "src/streaming" ] && [ ! -d "backend/streaming" ]; then
    cp -r src/streaming backend/
    echo -e "  ${GREEN}✓${NC} Copied backend/streaming"
    ((COPIED++))
fi

# Analytics
if [ -d "src/analytics" ] && [ ! -d "backend/analytics" ]; then
    cp -r src/analytics backend/
    echo -e "  ${GREEN}✓${NC} Copied backend/analytics"
    ((COPIED++))
fi

# Utils
if [ -d "src/utils" ] && [ ! -d "backend/utils" ]; then
    cp -r src/utils backend/
    echo -e "  ${GREEN}✓${NC} Copied backend/utils"
    ((COPIED++))
fi

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}✅ Migration Phase 3B Complete${NC}"
echo "=============================================="
echo ""
echo "Statistics:"
echo -e "  Files copied:    ${GREEN}$COPIED${NC}"
echo -e "  Files skipped:   ${YELLOW}$SKIPPED${NC}"
echo -e "  Conflicts:       ${YELLOW}$CONFLICTS${NC}"
echo ""

if [ $CONFLICTS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Warning: $CONFLICTS conflicts detected${NC}"
    echo "  Review files ending with _v2.py"
    echo ""
fi

echo "Next step: Run 02_update_imports.sh"
