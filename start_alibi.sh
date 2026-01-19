#!/bin/bash

# Alibi Startup Script
# Starts both API and Console in separate terminals

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║                    🚀 STARTING ALIBI SYSTEM 🚀                        ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📂 Working directory: $SCRIPT_DIR"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python not found. Please install Python 3.10+"
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Check if Node is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js not found. Please install Node.js 16+"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   Mobile camera will use basic CV mode (less accurate)"
    echo "   To use OpenAI Vision:"
    echo "   export OPENAI_API_KEY='sk-your-key'"
    echo ""
else
    echo "✅ OpenAI API Key configured"
    echo ""
fi

# Check if dependencies are installed
if [ ! -d "venv" ] && [ ! -f ".deps_installed" ]; then
    echo "📦 First time setup - Installing dependencies..."
    echo ""
    
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    touch .deps_installed
    
    echo ""
    echo "Installing Node dependencies..."
    cd alibi/console
    npm install
    cd ../..
    
    echo ""
    echo "✅ Dependencies installed!"
    echo ""
fi

# Check if users exist
if [ ! -f "alibi/data/users.json" ]; then
    echo "🔐 First startup - users will be created with random passwords"
    echo "   ⚠️  COPY THE PASSWORDS when they appear!"
    echo ""
fi

# Kill any existing processes
echo "🧹 Cleaning up any existing processes..."
pkill -f "uvicorn.*alibi_api" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                      STARTING SERVICES                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Start API in background
echo "🚀 Starting API Backend..."
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --reload > /tmp/alibi_api.log 2>&1 &
API_PID=$!
echo "   PID: $API_PID"
echo "   Logs: /tmp/alibi_api.log"
echo ""

# Wait for API to start
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""
echo ""

# Check for initial passwords
if [ -f "alibi/data/.initial_passwords.txt" ]; then
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                      🔑 INITIAL PASSWORDS                             ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo ""
    cat "alibi/data/.initial_passwords.txt"
    echo ""
    echo "⚠️  COPY THESE PASSWORDS NOW! They won't be shown again."
    echo "   After copying, press ENTER to continue..."
    read -r
    echo ""
fi

# Start Console
echo "🚀 Starting Frontend Console..."
cd alibi/console
npm run dev > /tmp/alibi_console.log 2>&1 &
CONSOLE_PID=$!
echo "   PID: $CONSOLE_PID"
echo "   Logs: /tmp/alibi_console.log"
cd ../..
echo ""

# Wait for Console to start
echo "⏳ Waiting for Console to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✅ Console is ready!"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""
echo ""

# Get local IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║                   ✅ ALIBI IS NOW RUNNING! ✅                          ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 SERVICES"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ API Backend:     http://localhost:8000"
echo "✅ API Docs:        http://localhost:8000/docs"
echo "✅ Frontend:        http://localhost:5173"
echo "✅ Mobile Camera:   http://localhost:8000/camera/mobile-stream"
echo ""
if [ -n "$LOCAL_IP" ]; then
    echo "📱 FROM YOUR PHONE"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    echo "   Open Safari/Chrome and go to:"
    echo "   http://$LOCAL_IP:8000/camera/mobile-stream"
    echo ""
fi
echo "🛑 TO STOP"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "   Press Ctrl+C or run: ./stop_alibi.sh"
echo ""
echo "📖 DOCUMENTATION"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "   START_ALIBI.md                - Complete startup guide"
echo "   MOBILE_CAMERA_GUIDE.md        - Mobile camera docs"
echo "   DEPLOYMENT_SECURITY_GUIDE.md  - Production deployment"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Save PIDs for stop script
echo "$API_PID" > /tmp/alibi_api.pid
echo "$CONSOLE_PID" > /tmp/alibi_console.pid

# Open browser
if command -v open &> /dev/null; then
    echo "🌐 Opening browser..."
    sleep 2
    open http://localhost:5173
fi

echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for interrupt
trap "echo ''; echo '🛑 Stopping Alibi...'; kill $API_PID $CONSOLE_PID 2>/dev/null; rm -f /tmp/alibi_*.pid; echo '✅ Stopped'; exit 0" INT TERM

# Keep script running
wait
