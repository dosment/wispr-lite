# Wispr-Lite

Local voice dictation and command launcher for Linux Mint Cinnamon, inspired by Wispr Flow.

## Features

- **Push-to-talk & Toggle modes**: Hold a hotkey to record or toggle on/off
- **Local transcription**: Uses Whisper via faster-whisper (no cloud required)
- **Real-time feedback**: Minimal overlay shows recording state and partial transcripts
- **Dictation mode**: Types transcribed text into any focused application
- **Command mode**: Execute voice commands (open apps, URLs, etc.)
- **Privacy-first**: All processing happens locally, no network calls by default
- **Lightweight**: Minimal CPU/RAM usage when idle
- **System tray integration**: Quick access to controls and status

## System Requirements

- Linux Mint 21.3+ or 22 with Cinnamon desktop
- Xorg session (Wayland has limitations)
- Python 3.10 or later
- 4GB RAM minimum (8GB recommended for larger models)
- Microphone

## Installation

### Quick Install

```bash
git clone https://github.com/wispr-lite/wispr-lite.git
cd wispr-lite
bash scripts/install.sh
```

This creates a virtual environment in `~/.local/share/wispr-lite` and installs all dependencies.

### System Dependencies

The installer checks for these automatically:

```bash
sudo apt install python3 python3-venv python3-dev python3-gi \
    gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
    gir1.2-notify-0.7 xclip portaudio19-dev
```

### Manual Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

## Usage

### Starting Wispr-Lite

From the application menu, search for "Wispr-Lite", or run:

```bash
~/.local/share/wispr-lite/venv/bin/wispr-lite
```

Or if installed in a virtual environment:

```bash
wispr-lite
```

### Default Hotkeys

- **Push-to-talk**: `Ctrl+Super` (hold to record, release to transcribe)
- **Toggle listening**: `Ctrl+Shift+Super` (press once to start, again to stop)
- **Undo last dictation**: `Ctrl+Shift+Z`

Configure hotkeys in Preferences. (Note: `Super` is the Windows/Command key)

### CLI Control

Control a running Wispr-Lite instance via command-line:

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

- **Dictation mode**: Transcribes speech and types it into the focused window
- **Command mode**: Matches speech to configured commands

Toggle between modes via the tray icon menu.

### System Tray

The tray icon provides quick access to controls:

- **Right-click**: Opens the menu with all options (Start/Stop Listening, Mode, Mute, Undo, Preferences, Logs, Quit)
- **Icon states**: Visual feedback shows current state (idle, listening, processing, muted, error)

**Note**: AppIndicator (used on Cinnamon) typically doesn't support left-click or middle-click actions. All interaction is through the right-click menu. This is a limitation of the AppIndicator specification, not Wispr-Lite.

### Voice Commands

Default commands (in command mode):

- "open terminal" - Opens gnome-terminal
- "open browser" - Opens Firefox
- "open editor" - Opens text editor
- "search [query]" - Opens Google search
- "open files" - Opens file manager

Configure additional commands in `~/.config/wispr-lite/config.yaml`.

## Configuration

Settings are stored in `~/.config/wispr-lite/config.yaml`.

Edit via the Preferences UI (tray menu → Preferences) or manually.

See `docs/CONFIG.md` for detailed configuration options.

### Model Selection

Wispr-Lite supports multiple Whisper model sizes:

- `tiny`: Fastest, lower accuracy (~1GB RAM)
- `base`: Good balance (default, ~1GB RAM)
- `small`: Better accuracy (~2GB RAM)
- `medium`: High accuracy (~5GB RAM)

Models are automatically downloaded on first use and cached in `~/.cache/wispr-lite/models`.

### Model Downloads

The first time you select a new model size, Wispr-Lite will need to download it. A confirmation dialog will appear asking for your consent before starting the download. This is a one-time process for each model size.

A notification will show the download progress. If you prefer to download the models manually or for offline installation, you can use the provided script:

```bash
# Preload the default 'base' model
bash scripts/preload_models.sh

# Preload specific models
bash scripts/preload_models.sh tiny small
```

## Troubleshooting

### Audio Issues

**No microphone detected:**

```bash
# List audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Set the device index in Preferences → Audio.

**PulseAudio vs PipeWire:**

Linux Mint 22 uses PipeWire by default. Both are supported via PortAudio.

### Hotkey Not Working

If global hotkeys don't work:

1. Check for conflicts: System Settings → Keyboard → Shortcuts
2. Use Cinnamon custom shortcuts as fallback:
   - Command: `wispr-lite --toggle` (via D-Bus)

### Clipboard/Typing Issues

**Clipboard paste fails:**

Ensure `xclip` is installed:

```bash
sudo apt install xclip
```

**XTest typing not working:**

Install python-xlib or switch to clipboard strategy in Preferences.

### Performance

**High CPU usage:**

- Use a smaller model (`tiny` or `base`)
- Ensure GPU support if you have NVIDIA (CUDA)

**Model downloads slowly:**

Models are ~150MB-1.5GB depending on size. First download may take time.

## Logs

Logs are stored in `~/.local/state/wispr-lite/logs/wispr-lite.log`.

View via tray menu → View Logs.

## Development

```bash
# Install dev dependencies
make dev

# Run from source
make run

# Run tests
make test

# Lint
make lint
```

Collaboration: PM/Claude tracker is maintained in `docs/COLLAB.md`.

## Architecture

- `wispr_lite/main.py` - Application entry point and orchestration
- `wispr_lite/audio/` - Audio capture and VAD
- `wispr_lite/asr/` - ASR engine interface and backends
- `wispr_lite/ui/` - GTK overlay, tray, preferences, notifications
- `wispr_lite/integration/` - Typing, hotkeys, D-Bus, Cinnamon integration
- `wispr_lite/commands/` - Command mode registry
- `wispr_lite/config/` - Configuration schema

## Contributing

Contributions welcome! Please:

1. Keep files under 500 lines
2. Follow PEP 8 and add type hints
3. Update tests and docs
4. Run `make lint` before submitting

## License

MIT License - see LICENSE file

## Credits

Inspired by [Wispr Flow](https://wispr.co/).

Built with:
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [pynput](https://github.com/moses-palmer/pynput)
- GTK / PyGObject
