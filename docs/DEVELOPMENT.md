# Development Guide

This guide provides information for developers working on Wispr-Lite.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Code Style](#code-style)

## Architecture Overview

Wispr-Lite is built with a modular architecture separating concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│  ┌──────────┐  ┌────────────┐  ┌──────┐  ┌────────────┐ │
│  │ Overlay  │  │ Preferences│  │ Tray │  │Notifications│ │
│  └──────────┘  └────────────┘  └──────┘  └────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│                Application Orchestration                 │
│                    (app.py, cli.py)                      │
└───┬─────────┬──────────┬──────────┬──────────┬─────────┘
    │         │          │          │          │
┌───▼───┐ ┌──▼────┐ ┌───▼───┐ ┌────▼─────┐ ┌─▼────────┐
│ Audio │ │  ASR  │ │ Typing│ │ Hotkeys  │ │  Config  │
│Pipeline│ │Engine │ │       │ │          │ │          │
└───────┘ └───────┘ └───────┘ └──────────┘ └──────────┘
```

### Key Design Principles

1. **Local-First**: All processing happens locally; no cloud dependencies
2. **Privacy by Design**: No data sent externally; minimal logging
3. **Modular**: Clear separation of concerns with well-defined interfaces
4. **Fail Softly**: Graceful degradation when features unavailable
5. **User-Invisible**: Minimal resource usage when idle

## Development Setup

### Prerequisites

- Linux Mint 21.3+ or 22 (Cinnamon desktop)
- Python 3.10+
- Git

### Quick Setup

```bash
# Clone repository
git clone https://github.com/dosment/wispr-lite.git
cd wispr-lite

# Install system dependencies
sudo apt install python3 python3-venv python3-dev python3-gi \
    gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
    gir1.2-notify-0.7 xclip portaudio19-dev

# Create development environment
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development tools
pip install pytest pytest-cov mypy black flake8
```

### Running from Source

```bash
# Activate environment
source venv/bin/activate

# Run application
python -m wispr_lite.main

# Or use the entry point
wispr-lite
```

## Project Structure

```
wispr-lite/
├── wispr_lite/              # Main package
│   ├── main.py              # Entry point (compatibility)
│   ├── app.py               # Application orchestration
│   ├── cli.py               # CLI interface and D-Bus client
│   ├── pipeline.py          # Audio processing pipeline
│   ├── model_ui.py          # Model download consent UI
│   ├── logging.py           # Logging configuration
│   │
│   ├── audio/               # Audio capture and processing
│   │   ├── capture.py       # Microphone capture
│   │   └── vad.py           # Voice Activity Detection
│   │
│   ├── asr/                 # Speech recognition
│   │   ├── engine.py        # ASR engine interface
│   │   └── faster_whisper_backend.py  # Whisper implementation
│   │
│   ├── ui/                  # User interface components
│   │   ├── overlay.py       # Recording overlay window
│   │   ├── tray.py          # System tray icon
│   │   ├── preferences.py   # Preferences window
│   │   ├── notifications.py # Notification manager
│   │   └── icons/           # Icon assets
│   │
│   ├── integration/         # System integrations
│   │   ├── hotkeys.py       # Global hotkey management
│   │   ├── typing/          # Text output strategies
│   │   │   ├── core.py      # Output coordinator
│   │   │   ├── clipboard.py # Clipboard-based paste
│   │   │   └── xtest.py     # XTest keyboard simulation
│   │   ├── dbus.py          # D-Bus service
│   │   └── cinnamon.py      # Cinnamon desktop integration
│   │
│   ├── commands/            # Voice command system
│   │   └── registry.py      # Command registry
│   │
│   └── config/              # Configuration
│       └── schema.py        # Configuration schema and validation
│
├── scripts/                 # Utility scripts
│   ├── install.sh           # User installation script
│   ├── uninstall.sh         # Uninstallation script
│   └── preload_models.sh    # Offline model downloader
│
├── tests/                   # Test suite
│   ├── test_vad.py
│   ├── test_config.py
│   └── test_hotkeys.py
│
├── docs/                    # Documentation
│   ├── CONFIG.md            # Configuration guide
│   ├── PACKAGING.md         # Packaging guide
│   └── DEVELOPMENT.md       # This file
│
├── .dev/                    # Internal development docs
│   ├── PROMPT.md            # Original project prompt
│   ├── claude.md            # Claude coding guide
│   ├── gemini.md            # Gemini coding guide (archived)
│   └── COLLAB.md            # Collaboration tracker
│
├── README.md                # Main documentation
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guidelines
├── FAQ.md                   # Frequently asked questions
├── LICENSE                  # MIT License
└── pyproject.toml           # Package metadata
```

## Core Components

### Application Orchestration (`app.py`)

The `WisprLiteApp` class coordinates all components:

- Initializes audio, ASR, UI, and integration components
- Manages application lifecycle
- Coordinates callbacks between components
- Handles state transitions

Key methods:
- `start_listening()` / `stop_listening()` - Control recording
- `_handle_transcript()` - Process transcription results
- `toggle_mode()` - Switch between dictation and command modes

### Audio Pipeline (`pipeline.py`)

The `AudioPipeline` manages audio capture and processing:

1. **Capture** (`audio/capture.py`): Records audio from microphone
2. **VAD** (`audio/vad.py`): Detects speech vs. silence
3. **Silence Detection**: Auto-stops recording after timeout

Runs in background threads; communicates via queues.

### ASR Engine (`asr/`)

Interface for speech recognition backends:

- `engine.py`: Abstract interface
- `faster_whisper_backend.py`: Whisper implementation via faster-whisper

Features:
- Lazy model loading (on first use)
- Model caching in `~/.cache/wispr-lite/models`
- Streaming transcription support
- GPU auto-detection

### UI Components (`ui/`)

GTK-based user interface:

- **Overlay** (`overlay.py`): Minimal recording indicator
- **Tray** (`tray.py`): System tray icon with menu
- **Preferences** (`preferences.py`): Settings window
- **Notifications** (`notifications.py`): Toast notifications with rate limiting

All UI updates must run on GTK main thread via `GLib.idle_add()`.

### Integration (`integration/`)

System-level integrations:

- **Hotkeys** (`hotkeys.py`): Global keyboard shortcuts via pynput
- **Typing** (`typing/`): Two strategies for text output:
  - Clipboard: Safe, works everywhere
  - XTest: Fast, character-by-character
- **D-Bus** (`dbus.py`): Session bus service for CLI control
- **Cinnamon** (`cinnamon.py`): Desktop environment detection

### Configuration (`config/schema.py`)

Type-safe configuration using dataclasses:

- YAML persistence at `~/.config/wispr-lite/config.yaml`
- XDG Base Directory compliance
- Validation on load
- Hot-reload support for some settings

## Development Workflow

### Making Changes

1. **Create a branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** following code style guidelines

3. **Test changes**:
   ```bash
   python -m pytest tests/
   ```

4. **Update documentation** as needed

5. **Commit with conventional format**:
   ```bash
   git commit -m "feat: add new feature"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   ```

### Code Style Guidelines

- **PEP 8**: Follow Python style guide
- **Type Hints**: Annotate all functions
- **File Size**: Keep files under 500 lines
- **Function Size**: Keep functions under 50 lines
- **Class Size**: Keep classes under 200 lines
- **Docstrings**: Use Google or NumPy style

Example:

```python
def transcribe_audio(audio_array: np.ndarray, sample_rate: int) -> str:
    """Transcribe audio to text.

    Args:
        audio_array: Audio samples as numpy array
        sample_rate: Sample rate in Hz

    Returns:
        Transcribed text

    Raises:
        ASRError: If transcription fails
    """
    # Implementation
    pass
```

### Threading Rules

- **UI Thread**: All GTK operations on main thread
- **Worker Threads**: Audio capture, ASR processing
- **Cross-Thread**: Use `GLib.idle_add()` for UI updates
- **Queues**: Use `queue.Queue` for thread-safe communication
- **Locks**: Minimize lock usage; prefer queues

Example:

```python
import threading
from gi.repository import GLib

def background_work():
    result = expensive_operation()
    # Update UI on main thread
    GLib.idle_add(update_ui, result)

threading.Thread(target=background_work, daemon=True).start()
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=wispr_lite

# Specific test file
pytest tests/test_vad.py

# Verbose output
pytest -v
```

### Writing Tests

Place tests in `tests/` directory:

```python
import pytest
from wispr_lite.audio.vad import VAD

def test_vad_detection():
    """Test VAD detects speech correctly."""
    vad = VAD(mode=3)
    # Test implementation
    assert vad.is_speech(audio_frame)
```

### Test Categories

- **Unit Tests**: Individual functions/classes
- **Integration Tests**: Component interactions
- **Smoke Tests**: End-to-end workflows

Some tests require DISPLAY (Xorg) and may be skipped on CI.

## Debugging

### Logging

Wispr-Lite uses Python's `logging` module:

```python
from wispr_lite.logging import get_logger

logger = get_logger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

Logs are written to `~/.local/state/wispr-lite/logs/wispr-lite.log`.

### Log Levels

Set in config.yaml:

```yaml
log_level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

Or via environment:

```bash
WISPR_LOG_LEVEL=DEBUG wispr-lite
```

### Common Issues

**Import errors**:
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall in development mode
pip install -e .
```

**GTK errors**:
```bash
# Verify PyGObject is available
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"
```

**Audio errors**:
```bash
# List audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

## Makefile Targets

```bash
# Install development dependencies
make dev

# Run from source
make run

# Run tests
make test

# Lint code
make lint

# Build .deb package
make deb

# Clean build artifacts
make clean
```

## Build System

### pyproject.toml

Package metadata and dependencies:

```toml
[project]
name = "wispr-lite"
version = "0.1.0"
dependencies = [
    "faster-whisper>=1.0.0",
    "sounddevice>=0.4.6",
    # ... more
]
```

### Entry Points

```toml
[project.scripts]
wispr-lite = "wispr_lite.main:main"
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code of conduct
- Pull request process
- Bug reporting
- Feature requests

## Resources

- **Whisper**: https://github.com/openai/whisper
- **faster-whisper**: https://github.com/guillaumekln/faster-whisper
- **PyGObject**: https://pygobject.readthedocs.io/
- **pynput**: https://pynput.readthedocs.io/

## Questions?

- Open an issue: https://github.com/dosment/wispr-lite/issues
- Start a discussion: https://github.com/dosment/wispr-lite/discussions
- Review internal docs: `.dev/` directory
