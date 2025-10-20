#!/bin/bash
# User-level installer for Wispr-Lite
# Creates a venv in ~/.local/share/wispr-lite and installs the application

set -e

# Get the absolute path to the script's directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INSTALL_DIR="$HOME/.local/share/wispr-lite"
VENV_DIR="$INSTALL_DIR/venv"
DESKTOP_FILE="$HOME/.local/share/applications/wispr-lite.desktop"
AUTOSTART_FILE="$HOME/.config/autostart/wispr-lite.desktop"

echo "Installing Wispr-Lite..."

# Check for system dependencies
echo "Checking system dependencies..."
MISSING_DEPS=()

for dep in python3 python3-venv python3-dev python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7 xclip portaudio19-dev; do
    if ! dpkg -l | grep -q "^ii  $dep"; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo "Missing system dependencies: ${MISSING_DEPS[*]}"
    echo "Please install them with:"
    echo "  sudo apt install ${MISSING_DEPS[*]}"
    exit 1
fi

# Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Create virtual environment with system site packages access
# This is required for PyGObject (python3-gi) which can't be installed via pip
echo "Creating virtual environment..."
python3 -m venv --system-site-packages "$VENV_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package
echo "Installing Wispr-Lite and dependencies..."
pip install -e "$PROJECT_ROOT"

# Install icons to user icon directory
echo "Installing icons..."
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
cp "$PROJECT_ROOT/wispr_lite/ui/icons/"*.svg "$ICON_DIR/"
# Create base app icon alias for .desktop file
cp "$ICON_DIR/wispr-lite-idle.svg" "$ICON_DIR/wispr-lite.svg"

# Update icon cache if possible
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# Install icons system-wide for proper tray icon support (requires sudo)
echo ""
echo "Installing icons system-wide for tray icon support..."
echo "(This requires sudo access - you may be prompted for your password)"
if sudo mkdir -p /usr/share/icons/hicolor/scalable/apps 2>/dev/null; then
    sudo cp "$PROJECT_ROOT/wispr_lite/ui/icons/"*.svg /usr/share/icons/hicolor/scalable/apps/
    sudo gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
    echo "System icons installed successfully"
else
    echo "Warning: Could not install system icons (tray icon may show generic symbol)"
    echo "You can manually install them later with:"
    echo "  sudo cp $PROJECT_ROOT/wispr_lite/ui/icons/*.svg /usr/share/icons/hicolor/scalable/apps/"
    echo "  sudo gtk-update-icon-cache /usr/share/icons/hicolor/"
fi

# Create .desktop file
echo "Creating desktop launcher..."
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Wispr-Lite
Comment=Voice dictation and command launcher
Exec=$VENV_DIR/bin/wispr-lite
Icon=wispr-lite
Terminal=false
Categories=Utility;Accessibility;
Keywords=voice;dictation;speech;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"

echo ""
echo "Installation complete!"
echo ""
echo "To start Wispr-Lite:"
echo "  $VENV_DIR/bin/wispr-lite"
echo ""
echo "Or search for 'Wispr-Lite' in your application menu."
echo ""
echo "To enable autostart on login, run:"
echo "  cp $DESKTOP_FILE $AUTOSTART_FILE"
echo ""
