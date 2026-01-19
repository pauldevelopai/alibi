#!/bin/bash

# Check status of persistent Alibi services

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                     Alibi Service Status                             ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check API
if [ -f logs/alibi_api.pid ]; then
    API_PID=$(cat logs/alibi_api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "✅ API Service: RUNNING (PID: $API_PID)"
        echo "   URL: https://McNallyMac.local:8000/"
    else
        echo "❌ API Service: NOT RUNNING (stale PID file)"
    fi
else
    if pgrep -f "uvicorn.*alibi_api" > /dev/null; then
        echo "⚠️  API Service: RUNNING (no PID file)"
    else
        echo "❌ API Service: NOT RUNNING"
    fi
fi

echo ""

# Check Console
if [ -f logs/alibi_console.pid ]; then
    CONSOLE_PID=$(cat logs/alibi_console.pid)
    if kill -0 $CONSOLE_PID 2>/dev/null; then
        echo "✅ Console Service: RUNNING (PID: $CONSOLE_PID)"
        echo "   URL: http://localhost:5173/"
    else
        echo "❌ Console Service: NOT RUNNING (stale PID file)"
    fi
else
    if pgrep -f "vite.*console" > /dev/null; then
        echo "⚠️  Console Service: RUNNING (no PID file)"
    else
        echo "❌ Console Service: NOT RUNNING"
    fi
fi

echo ""
echo "📊 Recent Logs:"
echo "───────────────────────────────────────────────────────────────────────"
echo "API (last 5 lines):"
tail -5 logs/alibi_api.log 2>/dev/null || echo "  No logs found"
echo ""
echo "Console (last 5 lines):"
tail -5 logs/alibi_console.log 2>/dev/null || echo "  No logs found"
echo ""
