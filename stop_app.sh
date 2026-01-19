#!/bin/bash
# Stop the Newsletter Optimizer app

echo "Stopping Newsletter Optimizer..."
pkill -f "streamlit run app.py"

sleep 1

if lsof -i :8501 | grep -q python; then
    echo "⚠️ App still running, force killing..."
    pkill -9 -f "streamlit run app.py"
fi

echo "✅ App stopped."









