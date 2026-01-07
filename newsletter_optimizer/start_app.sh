#!/bin/bash
# Start the Newsletter Optimizer app
# Run this script to start the app in the background

# Change to the script's directory
cd "$(dirname "$0")"

# Check if already running
if lsof -i :8501 | grep -q python; then
    echo "App is already running on port 8501"
    echo "Visit: http://localhost:8501"
    exit 0
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Streamlit
echo "Starting Newsletter Optimizer..."
nohup streamlit run app.py --server.headless true --server.port 8501 > app.log 2>&1 &

sleep 3

if lsof -i :8501 | grep -q python; then
    echo "✅ App started successfully!"
    echo "Visit: http://localhost:8501"
    echo ""
    echo "To stop: ./stop_app.sh"
else
    echo "❌ Failed to start. Check app.log for errors."
fi









