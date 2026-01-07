#!/bin/bash
# Install Newsletter Optimizer as a macOS service that runs automatically

PLIST_NAME="com.developai.newsletter-optimizer.plist"
PLIST_SOURCE="$(dirname "$0")/$PLIST_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "Installing Newsletter Optimizer as a macOS service..."

# Copy plist to LaunchAgents
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Load the service
launchctl unload "$PLIST_DEST" 2>/dev/null
launchctl load "$PLIST_DEST"

sleep 3

if lsof -i :8501 | grep -q python; then
    echo ""
    echo "✅ Service installed and running!"
    echo ""
    echo "The app will now:"
    echo "  - Start automatically when you log in"
    echo "  - Restart automatically if it crashes"
    echo "  - Run at: http://localhost:8501"
    echo ""
    echo "To stop: launchctl unload $PLIST_DEST"
    echo "To start: launchctl load $PLIST_DEST"
    echo "To uninstall: ./uninstall_service.sh"
else
    echo ""
    echo "⚠️ Service installed but may not be running yet."
    echo "Check logs at:"
    echo "  $(dirname "$0")/app.log"
    echo "  $(dirname "$0")/app_error.log"
fi









