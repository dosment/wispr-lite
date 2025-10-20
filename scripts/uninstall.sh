#!/bin/bash
# Uninstaller for Wispr-Lite
# Removes all files created by install.sh

set -e

INSTALL_DIR="$HOME/.local/share/wispr-lite"
VENV_DIR="$INSTALL_DIR/venv"
DESKTOP_FILE="$HOME/.local/share/applications/wispr-lite.desktop"
AUTOSTART_FILE="$HOME/.config/autostart/wispr-lite.desktop"
USER_ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
SYSTEM_ICON_DIR="/usr/share/icons/hicolor/scalable/apps"

echo "Uninstalling Wispr-Lite..."

# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Wispr-Lite is not installed at $INSTALL_DIR"
    echo "Nothing to uninstall."
    exit 0
fi

# Stop any running instance
echo "Stopping any running Wispr-Lite instances..."
if pgrep -f "wispr-lite" > /dev/null; then
    pkill -f "wispr-lite" || true
    sleep 1
fi

# Remove installation directory (includes venv)
echo "Removing installation directory: $INSTALL_DIR"
rm -rf "$INSTALL_DIR"

# Remove desktop file
if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing desktop launcher: $DESKTOP_FILE"
    rm -f "$DESKTOP_FILE"
fi

# Remove autostart file if it exists
if [ -f "$AUTOSTART_FILE" ]; then
    echo "Removing autostart file: $AUTOSTART_FILE"
    rm -f "$AUTOSTART_FILE"
fi

# Remove user icons
echo "Removing user icons..."
if [ -d "$USER_ICON_DIR" ]; then
    rm -f "$USER_ICON_DIR/wispr-lite"*.svg 2>/dev/null || true
fi

# Update user icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# Remove system icons (requires sudo)
echo ""
echo "Removing system-wide icons (requires sudo)..."
echo "(This requires sudo access - you may be prompted for your password)"
if sudo test -d "$SYSTEM_ICON_DIR" 2>/dev/null; then
    if sudo rm -f "$SYSTEM_ICON_DIR/wispr-lite"*.svg 2>/dev/null; then
        sudo gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
        echo "System icons removed successfully"
    else
        echo "Warning: Could not remove system icons (may need to remove manually)"
    fi
else
    echo "No system icons found"
fi

# Optional: Remove config and cache
echo ""
read -p "Do you want to remove user configuration and cache? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CONFIG_DIR="$HOME/.config/wispr-lite"
    CACHE_DIR="$HOME/.cache/wispr-lite"
    LOG_DIR="$HOME/.local/state/wispr-lite"

    if [ -d "$CONFIG_DIR" ]; then
        echo "Removing configuration: $CONFIG_DIR"
        rm -rf "$CONFIG_DIR"
    fi

    if [ -d "$CACHE_DIR" ]; then
        echo "Removing cache (including models): $CACHE_DIR"
        rm -rf "$CACHE_DIR"
    fi

    if [ -d "$LOG_DIR" ]; then
        echo "Removing logs: $LOG_DIR"
        rm -rf "$LOG_DIR"
    fi

    echo "User data removed"
else
    echo "Keeping user configuration and cache at:"
    echo "  Config: $HOME/.config/wispr-lite"
    echo "  Cache:  $HOME/.cache/wispr-lite"
    echo "  Logs:   $HOME/.local/state/wispr-lite"
fi

echo ""
echo "Uninstallation complete!"
echo ""
