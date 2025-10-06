#!/bin/bash
# Smoke test for Wispr-Lite
# Verifies basic functionality without full integration

set -e

echo "Wispr-Lite Smoke Test"
echo "===================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "✗ Python 3 not found"
    exit 1
fi
echo "✓ Python 3 available"
echo ""

# Check if wispr-lite is installed
echo "Checking wispr-lite installation..."
if ! command -v wispr-lite &> /dev/null; then
    echo "✗ wispr-lite command not found"
    echo "  Run: make install"
    exit 1
fi
echo "✓ wispr-lite command available"
echo ""

# Check dependencies
echo "Checking Python dependencies..."
python3 -c "import sounddevice" 2>/dev/null || { echo "✗ sounddevice not installed"; exit 1; }
python3 -c "import webrtcvad" 2>/dev/null || { echo "✗ webrtcvad not installed"; exit 1; }
python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null || { echo "✗ PyGObject not installed"; exit 1; }
python3 -c "import yaml" 2>/dev/null || { echo "✗ PyYAML not installed"; exit 1; }
python3 -c "import numpy" 2>/dev/null || { echo "✗ numpy not installed"; exit 1; }
echo "✓ Core dependencies installed"
echo ""

# Check system dependencies
echo "Checking system dependencies..."
command -v xclip &> /dev/null || { echo "⚠ xclip not found (clipboard operations may fail)"; }
command -v xdotool &> /dev/null || echo "⚠ xdotool not found (optional)"
echo "✓ System dependencies checked"
echo ""

# Check audio devices
echo "Checking audio devices..."
python3 << 'EOF'
try:
    import sounddevice as sd
    devices = sd.query_devices()
    input_devices = [d for d in devices if d['max_input_channels'] > 0]
    if input_devices:
        print(f"✓ Found {len(input_devices)} input device(s)")
        for d in input_devices[:3]:  # Show first 3
            print(f"  - {d['name']}")
    else:
        print("✗ No input devices found")
        exit(1)
except Exception as e:
    print(f"✗ Error checking audio devices: {e}")
    exit(1)
EOF
echo ""

# Test configuration loading
echo "Testing configuration..."
python3 << 'EOF'
try:
    from wispr_lite.config.schema import Config
    config = Config.load()
    print(f"✓ Configuration loaded successfully")
    print(f"  - Mode: {config.mode}")
    print(f"  - Model: {config.asr.model_size}")
    print(f"  - Strategy: {config.typing.strategy}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
    exit(1)
EOF
echo ""

# Test imports
echo "Testing module imports..."
python3 << 'EOF'
try:
    from wispr_lite.audio.capture import AudioCapture
    from wispr_lite.audio.vad import VAD
    from wispr_lite.asr.engine import create_asr_engine
    from wispr_lite.integration.typing import TextOutput
    from wispr_lite.integration.hotkeys import HotkeyManager
    from wispr_lite.commands.registry import CommandRegistry
    print("✓ All core modules import successfully")
except Exception as e:
    print(f"✗ Import error: {e}")
    exit(1)
EOF
echo ""

# Check desktop environment
echo "Checking desktop environment..."
python3 << 'EOF'
from wispr_lite.integration.cinnamon import get_desktop_info
info = get_desktop_info()
print(f"  - Desktop: {info['current_desktop']}")
print(f"  - Session: {info['session_type']}")
print(f"  - Cinnamon: {info['is_cinnamon']}")
print(f"  - Wayland: {info['is_wayland']}")
if info['is_wayland']:
    print("  ⚠ Running on Wayland - some features may be limited")
EOF
echo ""

# Test D-Bus (optional)
echo "Testing D-Bus availability..."
python3 << 'EOF'
try:
    import dbus
    bus = dbus.SessionBus()
    print("✓ D-Bus session bus available")
except Exception as e:
    print(f"⚠ D-Bus not available: {e}")
EOF
echo ""

# Test CLI flags (exit code checks)
echo "Testing CLI flags..."
echo "  Testing --help..."
wispr-lite --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ --help returns exit code 0"
else
    echo "  ✗ --help failed with exit code $?"
    exit 1
fi

# The following tests require daemon interaction
# We'll test them non-destructively
echo "  Testing D-Bus integration (requires daemon)..."
DAEMON_RUNNING=false
if pgrep -f "wispr-lite" > /dev/null 2>&1; then
    DAEMON_RUNNING=true
    echo "  ⚠ Daemon already running, testing live CLI flags..."

    # Test --toggle (toggle listening state)
    wispr-lite --toggle > /dev/null 2>&1
    TOGGLE_EXIT=$?
    if [ $TOGGLE_EXIT -eq 0 ]; then
        echo "  ✓ --toggle returns exit code 0"
        # Toggle back to restore state
        wispr-lite --toggle > /dev/null 2>&1
    else
        echo "  ⚠ --toggle returned exit code $TOGGLE_EXIT"
    fi

    # Test --mode (switch modes)
    wispr-lite --mode dictation > /dev/null 2>&1
    MODE_EXIT=$?
    if [ $MODE_EXIT -eq 0 ]; then
        echo "  ✓ --mode dictation returns exit code 0"
    else
        echo "  ⚠ --mode dictation returned exit code $MODE_EXIT"
    fi

else
    echo "  ⚠ Daemon not running, skipping live D-Bus tests"
    echo "  To test CLI flags, start wispr-lite in background and re-run"
fi
echo ""

echo "===================="
echo "Smoke test complete!"
echo ""
echo "To start Wispr-Lite:"
echo "  wispr-lite"
echo ""
echo "To test CLI control (with daemon running):"
echo "  wispr-lite --toggle     # Toggle listening"
echo "  wispr-lite --start      # Start listening"
echo "  wispr-lite --stop       # Stop listening"
echo "  wispr-lite --mode dictation"
echo "  wispr-lite --mode command"
echo "  wispr-lite --undo       # Undo last insertion"
echo ""
