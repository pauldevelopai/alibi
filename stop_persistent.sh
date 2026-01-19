#!/bin/bash

# Stop persistent Alibi services

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping Alibi services..."
echo ""

# Stop API
if [ -f logs/alibi_api.pid ]; then
    API_PID=$(cat logs/alibi_api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        kill $API_PID
        echo "✓ Stopped API (PID: $API_PID)"
    fi
    rm logs/alibi_api.pid
fi

# Stop Console
if [ -f logs/alibi_console.pid ]; then
    CONSOLE_PID=$(cat logs/alibi_console.pid)
    if kill -0 $CONSOLE_PID 2>/dev/null; then
        kill $CONSOLE_PID
        echo "✓ Stopped Console (PID: $CONSOLE_PID)"
    fi
    rm logs/alibi_console.pid
fi

# Also kill any remaining processes
pkill -f "uvicorn.*alibi_api" 2>/dev/null && echo "✓ Cleaned up API processes"
pkill -f "vite.*alibi" 2>/dev/null && echo "✓ Cleaned up Console processes"

echo ""
echo "✅ All Alibi services stopped"
