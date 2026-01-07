#!/bin/bash
# Uninstall the Newsletter Optimizer macOS service

PLIST_NAME="com.developai.newsletter-optimizer.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "Uninstalling Newsletter Optimizer service..."

# Unload the service
launchctl unload "$PLIST_DEST" 2>/dev/null

# Remove the plist
rm -f "$PLIST_DEST"

# Kill any remaining processes
pkill -f "streamlit run app.py" 2>/dev/null

echo "✅ Service uninstalled."
echo "The app will no longer start automatically."
echo ""
echo "To run manually: ./start_app.sh"









