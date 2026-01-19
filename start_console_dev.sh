#!/bin/bash

# Alibi Console Development Startup Script
# Starts both backend API and frontend dev server

set -e

echo "🔒 Starting Alibi Console (Development Mode)"
echo "============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if backend is running
echo -e "${BLUE}[1/3]${NC} Checking backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend already running on http://localhost:8000"
else
    echo "⚠️  Backend not detected. Start it manually:"
    echo "   python -m alibi.alibi_api"
    echo ""
fi

# Install frontend dependencies if needed
echo -e "${BLUE}[2/3]${NC} Checking frontend dependencies..."
cd "alibi/console"

if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/vite" ]; then
    echo "📦 Installing npm packages..."
    unset NODE_ENV
    npm install
else
    echo "✅ Dependencies already installed"
fi

# Start dev server
echo -e "${BLUE}[3/3]${NC} Starting frontend dev server..."
echo ""
echo -e "${GREEN}Console will be available at: http://localhost:5173${NC}"
echo ""
echo "Demo credentials:"
echo "  operator1 / operator123"
echo "  supervisor1 / supervisor123"
echo "  admin / admin123"
echo ""
echo "Press Ctrl+C to stop"
echo ""

unset NODE_ENV
npm run dev
