#!/bin/bash
# Start Cloudflare Tunnel for RAG Enterprise
# Usage: ./scripts/start-cloudflare-tunnel.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Cloudflare Tunnel ===${NC}"

# Check if cloudflared is installed
if ! command -v ~/bin/cloudflared &> /dev/null; then
    echo -e "${YELLOW}cloudflared not found. Installing...${NC}"
    mkdir -p ~/bin
    cd /tmp
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O ~/bin/cloudflared
    chmod +x ~/bin/cloudflared
    echo -e "${GREEN}✓ cloudflared installed${NC}"
fi

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Check if tunnel is already running
if pgrep -f "cloudflared tunnel" > /dev/null; then
    echo -e "${YELLOW}⚠ Cloudflare tunnel is already running${NC}"
    echo "PID: $(pgrep -f 'cloudflared tunnel')"
    echo ""
    echo "To stop the tunnel:"
    echo "  pkill -f 'cloudflared tunnel'"
    echo ""
    echo "Log file: $PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log"

    # Extract URL from log
    if [ -f "$PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log" ]; then
        URL=$(grep -oP 'https://[^\s]+\.trycloudflare\.com' "$PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log" | head -1)
        if [ ! -z "$URL" ]; then
            echo ""
            echo -e "${GREEN}Public URL: $URL${NC}"
            echo -e "${GREEN}Chat Interface: $URL/chat.html${NC}"
        fi
    fi
    exit 0
fi

# Start tunnel
echo -e "${BLUE}Starting tunnel for frontend (port 80)...${NC}"
nohup ~/bin/cloudflared tunnel --url http://localhost:80 > "$PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log" 2>&1 &
TUNNEL_PID=$!

echo -e "${GREEN}✓ Tunnel started (PID: $TUNNEL_PID)${NC}"
echo "Waiting for tunnel to initialize..."

# Wait for URL to appear in log
for i in {1..10}; do
    sleep 1
    if grep -q "trycloudflare.com" "$PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log" 2>/dev/null; then
        break
    fi
    echo -n "."
done
echo ""

# Extract and display URL
if [ -f "$PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log" ]; then
    URL=$(grep -oP 'https://[^\s]+\.trycloudflare\.com' "$PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log" | head -1)
    if [ ! -z "$URL" ]; then
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  Cloudflare Tunnel Active!                                    ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}Public URL:${NC}        $URL"
        echo -e "${BLUE}Chat Interface:${NC}    $URL/chat.html"
        echo -e "${BLUE}API Endpoint:${NC}      $URL/api/v1"
        echo -e "${BLUE}Health Check:${NC}      $URL/health/ready"
        echo ""
        echo -e "${YELLOW}Note: This is a temporary tunnel. URL will change on restart.${NC}"
        echo -e "${YELLOW}For permanent tunnels, set up a named tunnel with Cloudflare account.${NC}"
        echo ""
        echo -e "${BLUE}Tunnel PID:${NC}        $TUNNEL_PID"
        echo -e "${BLUE}Log file:${NC}          $PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log"
        echo ""
        echo "To stop the tunnel:"
        echo "  pkill -f 'cloudflared tunnel'"
        echo "  # or"
        echo "  kill $TUNNEL_PID"
        echo ""
    else
        echo -e "${YELLOW}⚠ Could not extract URL from log. Check: $PROJECT_ROOT/logs/cloudflare-frontend-tunnel.log${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Log file not found. Tunnel may have failed to start.${NC}"
    exit 1
fi
