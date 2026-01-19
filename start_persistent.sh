#!/bin/bash

# Start Alibi as persistent background services
# These will keep running even if you close the terminal

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║         Starting Alibi as Persistent Background Services             ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Get Python and npm paths
PYTHON=$(which python3 || which python)
NODE=$(which node)
NPM=$(which npm)

echo "Starting API service..."
nohup $PYTHON -m uvicorn alibi.alibi_api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --ssl-keyfile ssl/key_local.pem \
  --ssl-certfile ssl/cert_local.pem \
  > logs/alibi_api.log 2>&1 &

API_PID=$!
echo "$API_PID" > logs/alibi_api.pid
echo "✅ API started (PID: $API_PID)"

sleep 3

cd alibi/console
echo "Starting Console service..."
nohup $NPM run dev -- --host \
  > ../../logs/alibi_console.log 2>&1 &

CONSOLE_PID=$!
echo "$CONSOLE_PID" > ../../logs/alibi_console.pid
cd ../..
echo "✅ Console started (PID: $CONSOLE_PID)"

sleep 3

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                     ✅ Alibi is Now Running!                          ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access Alibi at:"
echo "   https://McNallyMac.local:8000/"
echo ""
echo "📊 View logs:"
echo "   API:     tail -f logs/alibi_api.log"
echo "   Console: tail -f logs/alibi_console.log"
echo ""
echo "🛠️  Manage services:"
echo "   Stop:    ./stop_persistent.sh"
echo "   Status:  ./status_persistent.sh"
echo ""
echo "💡 These services will keep running in the background!"
echo "   Close this terminal - Alibi stays running."
echo ""
