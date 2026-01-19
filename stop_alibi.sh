#!/bin/bash

# Alibi Stop Script
# Stops all Alibi services

echo "🛑 Stopping Alibi System..."
echo ""

# Kill processes by PID if available
if [ -f "/tmp/alibi_api.pid" ]; then
    API_PID=$(cat /tmp/alibi_api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "   Stopping API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null
    fi
    rm -f /tmp/alibi_api.pid
fi

if [ -f "/tmp/alibi_console.pid" ]; then
    CONSOLE_PID=$(cat /tmp/alibi_console.pid)
    if kill -0 $CONSOLE_PID 2>/dev/null; then
        echo "   Stopping Console (PID: $CONSOLE_PID)..."
        kill $CONSOLE_PID 2>/dev/null
    fi
    rm -f /tmp/alibi_console.pid
fi

# Fallback: kill by process name
echo "   Cleaning up any remaining processes..."
pkill -f "uvicorn.*alibi_api" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Clean up log files
rm -f /tmp/alibi_api.log /tmp/alibi_console.log

echo ""
echo "✅ Alibi stopped"
echo ""
