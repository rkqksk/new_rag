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
