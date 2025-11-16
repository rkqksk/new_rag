#!/usr/bin/env bash
# ================================================================
# Claude Code System Validation Script
# ================================================================
# Validates MCP servers, agents, skills, and feature bundles
# Version: 1.0.0
# ================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Claude Code System Validation${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# ================================================================
# Helper Functions
# ================================================================

check() {
    local name="$1"
    local command="$2"

    ((TOTAL_CHECKS++))

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASSED_CHECKS++))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        ((FAILED_CHECKS++))
        return 1
    fi
}

section() {
    echo ""
    echo -e "${BLUE}──────────────────────────────────────────────────────${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}──────────────────────────────────────────────────────${NC}"
}

# ================================================================
# 1. Configuration Files
# ================================================================

section "1. Configuration Files"

check "mcp.json exists" "test -f '$CLAUDE_DIR/mcp.json'"
check "mcp.json is valid JSON" "python3 -m json.tool '$CLAUDE_DIR/mcp.json' > /dev/null"
check "feature-bundles.json exists" "test -f '$CLAUDE_DIR/feature-bundles.json'"
check "feature-bundles.json is valid JSON" "python3 -m json.tool '$CLAUDE_DIR/feature-bundles.json' > /dev/null"
check "No TestSprite in mcp.json" "! grep -q 'testsprite' '$CLAUDE_DIR/mcp.json'"
check "No TestSprite in feature-bundles.json" "! grep -q 'testsprite' '$CLAUDE_DIR/feature-bundles.json'"

# ================================================================
# 2. MCP Servers
# ================================================================

section "2. MCP Servers"

# Check MCP server files exist
check "qdrant_server.py exists" "test -f '$PROJECT_ROOT/mcp_servers/qdrant_server.py'"
check "ollama_server.py exists" "test -f '$PROJECT_ROOT/mcp_servers/ollama_server.py'"
check "rag_orchestrator.py exists" "test -f '$PROJECT_ROOT/mcp_servers/rag_orchestrator.py'"
check "query_router.py exists" "test -f '$PROJECT_ROOT/mcp_servers/query_router.py'"
check "google_devtools server exists" "test -f '$PROJECT_ROOT/mcp_servers/google_devtools/server.py'"

# Check MCP servers are executable
check "qdrant_server.py is valid Python" "python3 -m py_compile '$PROJECT_ROOT/mcp_servers/qdrant_server.py'"
check "ollama_server.py is valid Python" "python3 -m py_compile '$PROJECT_ROOT/mcp_servers/ollama_server.py'"
check "rag_orchestrator.py is valid Python" "python3 -m py_compile '$PROJECT_ROOT/mcp_servers/rag_orchestrator.py'"
check "query_router.py is valid Python" "python3 -m py_compile '$PROJECT_ROOT/mcp_servers/query_router.py'"

# ================================================================
# 3. Agents
# ================================================================

section "3. Agents"

# Check agent files exist
check "code-review-agent.md exists" "test -f '$CLAUDE_DIR/agents/code-review-agent.md'"
check "testing-agent.md exists" "test -f '$CLAUDE_DIR/agents/testing-agent.md'"
check "rag-agent.md exists" "test -f '$CLAUDE_DIR/agents/rag-agent.md'"
check "crawling-agent.md exists" "test -f '$CLAUDE_DIR/agents/crawling-agent.md'"
check "data-agent.md exists" "test -f '$CLAUDE_DIR/agents/data-agent.md'"
check "frontend-agent.md exists" "test -f '$CLAUDE_DIR/agents/frontend-agent.md'"
check "deployment-agent.md exists" "test -f '$CLAUDE_DIR/agents/deployment-agent.md'"
check "monitoring-agent.md exists" "test -f '$CLAUDE_DIR/agents/monitoring-agent.md'"

# Check agents have valid YAML front matter
check "code-review-agent has YAML front matter" "grep -q '^---$' '$CLAUDE_DIR/agents/code-review-agent.md'"
check "testing-agent has YAML front matter" "grep -q '^---$' '$CLAUDE_DIR/agents/testing-agent.md'"

# Check agents don't reference TestSprite
check "code-review-agent no TestSprite refs" "! grep -i 'testsprite' '$CLAUDE_DIR/agents/code-review-agent.md'"
check "testing-agent no TestSprite refs" "! grep -i 'testsprite' '$CLAUDE_DIR/agents/testing-agent.md'"

# ================================================================
# 4. Skills
# ================================================================

section "4. Skills"

# Count skills
SKILL_COUNT=$(find "$CLAUDE_DIR/skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
echo -e "${BLUE}ℹ${NC}  Found $SKILL_COUNT skills"

# Check key skills exist
check "rag-pipeline skill exists" "test -d '$CLAUDE_DIR/skills/rag-pipeline'"
check "data-collector skill exists" "test -d '$CLAUDE_DIR/skills/data-collector'"
check "debugging-expert skill exists" "test -d '$CLAUDE_DIR/skills/debugging-expert'"
check "web-crawler-pipeline skill exists" "test -d '$CLAUDE_DIR/skills/web-crawler-pipeline'"

# ================================================================
# 5. Feature Bundles
# ================================================================

section "5. Feature Bundles"

# Parse feature bundles
ACTIVE_BUNDLES=$(python3 -c "
import json
with open('$CLAUDE_DIR/feature-bundles.json') as f:
    data = json.load(f)
    print(','.join(data.get('active', [])))
")

echo -e "${BLUE}ℹ${NC}  Active bundles: $ACTIVE_BUNDLES"

check "core bundle defined" "python3 -c \"import json; f=open('$CLAUDE_DIR/feature-bundles.json'); data=json.load(f); assert 'core' in data['bundles']\""
check "development bundle defined" "python3 -c \"import json; f=open('$CLAUDE_DIR/feature-bundles.json'); data=json.load(f); assert 'development' in data['bundles']\""
check "rag bundle defined" "python3 -c \"import json; f=open('$CLAUDE_DIR/feature-bundles.json'); data=json.load(f); assert 'rag' in data['bundles']\""

# ================================================================
# 6. Python Dependencies
# ================================================================

section "6. Python Dependencies"

check "qdrant-client installed" "python3 -c 'import qdrant_client'"
check "aiohttp installed" "python3 -c 'import aiohttp'"
check "pytest installed" "python3 -c 'import pytest'"
check "fastapi installed" "python3 -c 'import fastapi'"
check "dotenv installed" "python3 -c 'import dotenv'"

# ================================================================
# 7. Environment Variables
# ================================================================

section "7. Environment Variables"

check ".env file exists" "test -f '$PROJECT_ROOT/.env'"
check "GITHUB_PERSONAL_ACCESS_TOKEN in .env" "grep -q 'GITHUB_PERSONAL_ACCESS_TOKEN' '$PROJECT_ROOT/.env'"
check "No TESTSPRITE_API_KEY in .env" "! grep -q 'TESTSPRITE_API_KEY' '$PROJECT_ROOT/.env' || grep -q '^#.*TESTSPRITE_API_KEY' '$PROJECT_ROOT/.env'"

# ================================================================
# Summary
# ================================================================

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo -e "Total checks:  ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Passed:        ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed:        ${RED}$FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review and fix the issues above.${NC}"
    exit 1
fi
