# Wispr-Lite

> Local voice dictation and command launcher for Linux Mint Cinnamon

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux Mint](https://img.shields.io/badge/platform-Linux%20Mint-brightgreen.svg)](https://linuxmint.com/)

Wispr-Lite is a privacy-focused, local voice dictation and command launcher for Linux Mint Cinnamon, inspired by Wispr Flow. All transcription happens on your computer using OpenAI's Whisper model—no cloud services required.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Functionality

- **🎤 Push-to-Talk & Toggle Modes**: Hold a hotkey to record or toggle listening on/off
- **🔒 Privacy-First**: All processing happens locally—no network calls, no cloud dependencies
- **⚡ Real-Time Transcription**: Uses Whisper via faster-whisper for accurate, low-latency transcription
- **💬 Smart Dictation**:
  - Automatic spacing after sentences
  - Smart capitalization after punctuation
  - Types into any focused application without stealing focus
  - Undo last dictation with Ctrl+Shift+Z
- **🌍 Multi-Language Support**: 16 common languages plus auto-detect
- **🎯 Command Mode**: Execute voice commands (open apps, URLs, shell commands)
- **🪶 Lightweight**: Minimal CPU/RAM when idle; models load on first use

### User Interface

- **Minimal Overlay**: Shows recording state and partial transcripts
- **System Tray Integration**: Quick access to controls and status with dynamic icons
- **Preferences Window**: Configure all settings via clean GTK interface
- **Smart Notifications**: Rate-limited, respects Do Not Disturb mode

### Technical Features

- **Multiple Model Sizes**: tiny, base, small, medium—choose your balance of speed vs. accuracy
- **Two Typing Strategies**: Clipboard paste (safe, universal) or XTest (fast, character-by-character)
- **Clipboard Preservation**: Automatically restores clipboard after paste
- **GPU Support**: Auto-detects NVIDIA CUDA for faster transcription
- **Voice Activity Detection**: Automatically detects speech vs. silence
- **D-Bus API**: Control via command line or integrate with other apps

## Quick Start

Get running in under 2 minutes:

```bash
# Install
git clone https://github.com/dosment/wispr-lite.git
cd wispr-lite
bash scripts/install.sh

# Launch
~/.local/share/wispr-lite/venv/bin/wispr-lite
```

**First Use**:
1. Look for the microphone icon in your system tray
2. Hold `Ctrl+Super` and speak
3. Release to see your text appear!

> **Note**: `Super` is the Windows/Command key. On first model use, you'll be asked to consent to downloading the model.

## Installation

### System Requirements

- Linux Mint 21.3+ or 22 with Cinnamon desktop
- Xorg session (Wayland has limitations—see [FAQ](FAQ.md#does-it-work-on-wayland))
- Python 3.10 or later
- 4GB RAM minimum (8GB recommended for larger models)
- Microphone

### Quick Install (Recommended)

The install script handles everything automatically:

```bash
git clone https://github.com/dosment/wispr-lite.git
cd wispr-lite
bash scripts/install.sh
```

This creates a virtual environment in `~/.local/share/wispr-lite` and installs all dependencies.

### System Dependencies

The installer checks for these automatically, but you can install them manually if needed:

```bash
sudo apt install python3 python3-venv python3-dev python3-gi \
    gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
    gir1.2-notify-0.7 xclip portaudio19-dev
```

### Manual Installation

For advanced users or custom setups:

```bash
# Create virtual environment with system site packages (required for PyGObject)
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Wispr-Lite
pip install -e .
```

### Uninstallation

To remove Wispr-Lite completely:

```bash
bash scripts/uninstall.sh
```

This will:
- Stop any running instances
- Remove the installed application and virtual environment
- Remove desktop launchers and icons
- Optionally remove user configuration and cache (you'll be prompted)

## Usage

### Starting Wispr-Lite

**From Application Menu**:
Search for "Wispr-Lite" in your application menu.

**From Terminal**:
```bash
~/.local/share/wispr-lite/venv/bin/wispr-lite
```

Or if installed in a virtual environment:
```bash
wispr-lite
```

The application runs in the background with a system tray icon.

### Default Hotkeys

- **Push-to-talk**: `Ctrl+Super` (hold to record, release to transcribe)
- **Toggle listening**: `Ctrl+Shift+Super` (press once to start, again to stop)
- **Undo last dictation**: `Ctrl+Shift+Z`

> **Note**: `Super` is the Windows/Command key

Configure hotkeys in Preferences (right-click tray icon → Preferences → Hotkeys).

### Dictation Basics

1. **Focus** the application where you want text to appear (text editor, web browser, etc.)
2. **Hold** `Ctrl+Super` and speak clearly
3. **Release** the hotkey when done
4. Your text appears automatically!

**Tips**:
- Speak naturally; Whisper handles punctuation
- Use toggle mode (`Ctrl+Shift+Super`) for longer dictations
- Smart spacing and capitalization are enabled by default
- Press `Ctrl+Shift+Z` to undo if needed

### Command Line Control

Control a running Wispr-Lite instance via command line:

```bash
wispr-lite --toggle          # Toggle listening on/off
wispr-lite --start           # Start listening
wispr-lite --stop            # Stop listening
wispr-lite --mode dictation  # Switch to dictation mode
wispr-lite --mode command    # Switch to command mode
wispr-lite --prefs           # Open preferences window
wispr-lite --undo            # Undo last dictation
```

These commands communicate with the running daemon via D-Bus.

### Modes

**Dictation Mode** (default):
Transcribes speech and types it into the focused window.

**Command Mode**:
Matches speech to configured commands. Default commands:
- "open terminal" - Opens gnome-terminal
- "open browser" - Opens Firefox
- "open editor" - Opens text editor
- "search [query]" - Opens Google search
- "open files" - Opens file manager

Toggle between modes via tray menu or add custom commands in settings.

### System Tray

The tray icon provides quick access to controls:

- **Right-click**: Opens menu with all options
  - Start/Stop Listening
  - Toggle Mode (Dictation/Command)
  - Mute Microphone
  - Undo Last Dictation
  - Preferences
  - View Logs
  - Quit
- **Icon States**: Visual feedback shows current state
  - Idle (gray microphone)
  - Listening (blue microphone)
  - Processing (orange microphone)
  - Muted (microphone with slash)
  - Error (red microphone)

> **Note**: AppIndicator (used on Cinnamon) typically doesn't support left-click or middle-click actions. All interaction is through the right-click menu. This is a limitation of the AppIndicator specification, not Wispr-Lite.

## Configuration

### Preferences Window

Access via tray menu → Preferences or `wispr-lite --prefs`.

**Settings**:
- **General**: Mode (dictation/command), log level
- **Hotkeys**: Customize push-to-talk, toggle, and undo hotkeys
- **Audio**: Select microphone, adjust VAD sensitivity
- **ASR**: Choose model size (tiny/base/small/medium), language
- **Typing**: Strategy (clipboard/XTest), smart spacing, smart capitalization
- **Notifications**: Enable/disable, DND respect, rate limiting

### Configuration File

Settings are stored in `~/.config/wispr-lite/config.yaml`.

You can edit this file directly with any text editor. See [docs/CONFIG.md](docs/CONFIG.md) for detailed configuration options.

### Model Selection

Wispr-Lite supports multiple Whisper model sizes:

| Model  | Size  | RAM Usage | Speed    | Accuracy |
|--------|-------|-----------|----------|----------|
| tiny   | 75MB  | ~1GB      | Fastest  | Lower    |
| base   | 150MB | ~1GB      | Fast     | Good     |
| small  | 500MB | ~2GB      | Moderate | Better   |
| medium | 1.5GB | ~5GB      | Slower   | Best     |

**Default**: `base` (good balance of speed and accuracy)

Models are automatically downloaded on first use and cached in `~/.cache/wispr-lite/models`.

### Model Download

The first time you select a model, Wispr-Lite will:
1. Show a consent dialog
2. Download the model with progress notification
3. Cache it for future use

**Offline Installation**:
Pre-download models without starting the application:
```bash
bash scripts/preload_models.sh base
```

## Troubleshooting

### Hotkeys Not Working

**On System Boot**:
If hotkeys don't work after system boot but work after restarting Wispr-Lite, ensure you're running the latest version (this bug was fixed in recent commits).

**Conflicts**:
1. Check for conflicts: System Settings → Keyboard → Shortcuts
2. Change hotkeys in Preferences if needed
3. Use Cinnamon custom shortcuts as fallback:
   - Command: `wispr-lite --toggle`
   - Hotkey: Your preferred key combination

**Common Conflicts**:
- `Ctrl+Space`: Often used by ibus/fcitx input method switchers
- `Super+Space`: Desktop environment app launchers
- Wispr-Lite now uses `Ctrl+Super` by default to avoid these conflicts

### Audio Issues

**No Microphone Detected**:
```bash
# List available audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```
Set the device index in Preferences → Audio → Microphone Device.

**PulseAudio vs PipeWire**:
Both are supported via PortAudio. Linux Mint 22 uses PipeWire by default.

### Clipboard/Typing Issues

**Clipboard Paste Fails**:
Ensure `xclip` is installed:
```bash
sudo apt install xclip
```

**XTest Typing Not Working**:
1. XTest requires Xorg (doesn't work on Wayland)
2. Install `python-xlib` if not already installed
3. Try switching to clipboard strategy in Preferences

### Transcription Quality

**Poor Accuracy**:
1. Use a larger model (small or medium) in Preferences → ASR
2. Ensure good microphone quality
3. Reduce background noise
4. Set language explicitly instead of auto-detect

**Slow Performance**:
1. Use a smaller model (tiny or base)
2. Close other resource-intensive applications
3. Enable GPU acceleration if you have NVIDIA CUDA

### Logs

View logs for detailed error information:

**Via Tray Menu**: Right-click tray icon → View Logs

**Manual**:
```bash
cat ~/.local/state/wispr-lite/logs/wispr-lite.log
```

### Still Having Issues?

- Check the [FAQ](FAQ.md) for common questions
- Search [existing issues](https://github.com/dosment/wispr-lite/issues)
- Open a [new issue](https://github.com/dosment/wispr-lite/issues/new) with:
  - Your Linux Mint version
  - Cinnamon version
  - Session type (Xorg/Wayland)
  - Relevant log excerpt

## FAQ

See [FAQ.md](FAQ.md) for frequently asked questions including:
- Does it work on Wayland?
- How do I change models?
- Can I use it with languages other than English?
- How do I add custom voice commands?
- And many more...

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Pull request process
- Bug reporting guidelines

### Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Architecture overview
- Project structure
- Component details
- Testing guidelines

## Roadmap

Planned features:
- [ ] Wayland native support
- [ ] Additional ASR backends (whisper.cpp)
- [ ] Flatpak packaging
- [ ] More built-in voice commands
- [ ] Voice command configuration UI
- [ ] TTS feedback
- [ ] Multi-profile support

## Architecture

Key components:
- **wispr_lite/app.py** - Application orchestration
- **wispr_lite/audio/** - Audio capture and VAD
- **wispr_lite/asr/** - Speech recognition engine
- **wispr_lite/ui/** - GTK interface (overlay, tray, preferences)
- **wispr_lite/integration/** - System integrations (hotkeys, typing, D-Bus)
- **wispr_lite/commands/** - Voice command system
- **wispr_lite/config/** - Configuration management

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed architecture documentation.

## Credits

Inspired by [Wispr Flow](https://wispr.co/).

Built with:
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkey support
- [GTK / PyGObject](https://pygobject.readthedocs.io/) - User interface
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio capture

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/dosment/wispr-lite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dosment/wispr-lite/discussions)
- **Documentation**: [docs/](docs/)

---

Made with ❤️ for the Linux Mint community
