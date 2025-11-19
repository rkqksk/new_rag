#!/usr/bin/env bash
# Start all development servers

echo "🚀 Starting Development Servers"
echo "==============================="
echo ""

# Function to kill all background processes on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting API (port 8001)..."
cd apps/api && source ../../.venv/bin/activate && uvicorn main:app --reload --port 8001 &
cd ../..

# Start frontend
echo "Starting Web (port 3000)..."
pnpm --filter @rag/web dev &

# Wait for all background processes
echo ""
echo "✅ All services started!"
echo ""
echo "URLs:"
echo "  - API: http://localhost:8001/docs"
echo "  - Web: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
