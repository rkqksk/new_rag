#!/bin/bash
# MCP Profile Switcher
# Usage: ./scripts/switch_mcp_profile.sh [max|api|full]

PROJECT_ROOT="/Users/oypnus/Project/rag-enterprise"
PROFILE="${1:-max}"

echo "🔧 MCP Profile Switcher"
echo "======================"

# Backup current configuration
if [ -f "$PROJECT_ROOT/.mcp.json" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$PROJECT_ROOT/.backups"
    cp "$PROJECT_ROOT/.mcp.json" "$PROJECT_ROOT/.backups/.mcp.json.$TIMESTAMP"
    echo "✅ Backed up current config to .backups/.mcp.json.$TIMESTAMP"
fi

# Switch to requested profile
case "$PROFILE" in
    max)
        echo "🚀 Switching to MAX profile (7 servers, ~2100 tokens)"
        echo "   Purpose: Full functionality with all capabilities"
        echo "   Active: ALL 7 servers (filesystem, claude_api, chrome_devtools,"
        echo "           qdrant, ollama, rag_orchestrator, note_keeper)"
        echo "   ✅ API calls, browser automation, vector search, orchestration"
        echo ""
        echo "   Use this for: General development, full RAG system, production-like environment"
        cp "$PROJECT_ROOT/.mcp.max.json" "$PROJECT_ROOT/.mcp.json"
        ;;
    api)
        echo "🔌 Switching to API profile (4 servers, ~1200 tokens)"
        echo "   Purpose: Lightweight configuration for focused work"
        echo "   Active: claude_api, qdrant, rag_orchestrator, note_keeper"
        echo "   ⚠️  API CHARGES: claude_api enabled"
        echo ""
        echo "   Use this for: API testing, token optimization, focused RAG development"
        cp "$PROJECT_ROOT/.mcp.api.json" "$PROJECT_ROOT/.mcp.json"
        ;;
    full)
        echo "⚠️  DEPRECATED: 'full' profile is now 'max'"
        echo "   Switching to MAX profile instead..."
        cp "$PROJECT_ROOT/.mcp.max.json" "$PROJECT_ROOT/.mcp.json"
        ;;
    *)
        echo "❌ Invalid profile: $PROFILE"
        echo "   Usage: $0 [max|api]"
        echo ""
        echo "Profiles:"
        echo "  • max  - Full functionality (7 servers, ~2100 tokens) [DEFAULT]"
        echo "  • api  - Lightweight mode (4 servers, ~1200 tokens)"
        echo ""
        echo "Configuration:"
        echo "  • max:  All capabilities including API, browser, vector search"
        echo "  • api:  Core RAG features only, optimized for token usage"
        exit 1
        ;;
esac

echo ""
echo "✅ Profile switched to: $PROFILE"
echo "⚠️  Restart Claude Code for changes to take effect"
echo ""
echo "Token & Cost Estimate:"
if [ "$PROFILE" = "max" ] || [ "$PROFILE" = "full" ]; then
    echo "  • MCP servers: ~2,100 tokens"
    echo "  • Configuration: All 7 servers enabled"
    echo "  • API Cost: Pay-per-use when claude_api tools are used"
    echo ""
    echo "  ✅ Full functionality available"
    echo "  ✅ Browser automation, vector search, orchestration"
    echo "  ⚠️  API charges apply when using mcp__claude_api__* tools"
elif [ "$PROFILE" = "api" ]; then
    echo "  • MCP servers: ~1,200 tokens"
    echo "  • Configuration: 4 core servers only"
    echo "  • API Cost: Pay-per-use (Haiku/Sonnet pricing)"
    echo ""
    echo "  ✅ Token optimized for focused work"
    echo "  ✅ Core RAG functionality maintained"
    echo "  ⚠️  Use mcp__claude_api__* tools explicitly"
fi
