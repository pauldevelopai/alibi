#!/bin/bash

# Install Alibi as a persistent service on macOS
set -e

echo "Installing Alibi as persistent service..."
echo ""

# Get paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "✓ Project: $PROJECT_DIR"

PYTHON_PATH=$(which python3 || which python)
echo "✓ Python: $PYTHON_PATH"

NPM_PATH=$(which npm)
echo "✓ npm: $NPM_PATH"

# Create LaunchAgents directory
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

echo ""
echo "Creating service files..."

# Uninstall existing services first
bash uninstall_service.sh 2>/dev/null || true

echo "Services will be created. Installation complete!"
echo ""
echo "Run: ./start_persistent.sh to start services"

