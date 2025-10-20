# Changelog

All notable changes to Wispr-Lite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Hotkey detection on system boot now works correctly - all Super key variants (cmd, cmd_l, cmd_r) are properly normalized

## [0.1.0] - 2025-10-06

### Added
- **Core Features**
  - Push-to-talk voice dictation with Ctrl+Super hotkey (hold to record, release to transcribe)
  - Toggle listening mode with Ctrl+Shift+Super
  - Local transcription using Whisper via faster-whisper (no cloud required)
  - Real-time feedback with minimal overlay showing recording state
  - System tray integration with dynamic status icons
  - Undo last dictation with Ctrl+Shift+Z

- **Transcription**
  - Support for multiple Whisper model sizes (tiny, base, small, medium)
  - Auto-detect language or select from 16 common languages
  - Smart spacing after sentence-ending punctuation
  - Smart capitalization of first letter after sentences
  - Model download consent dialog with progress notifications

- **Audio**
  - Microphone device selection
  - Voice Activity Detection (VAD) for automatic speech detection
  - Support for both PulseAudio and PipeWire
  - Live input level meter in preferences

- **Typing/Output**
  - Two typing strategies: clipboard paste (default) and XTest
  - Clipboard preservation (restores clipboard after paste)
  - Support for typing in any application without stealing focus
  - Undo functionality for last dictation

- **UI/UX**
  - GTK-based preferences window
  - Minimal, transparent overlay during recording
  - System tray icon with right-click menu
  - Notification system with DND (Do Not Disturb) support
  - Rate-limited notifications to prevent spam
  - Icon states for idle, listening, processing, muted, and error

- **Configuration**
  - YAML-based configuration at ~/.config/wispr-lite/config.yaml
  - Customizable hotkeys
  - Audio device selection
  - Model size selection
  - Typing strategy selection
  - Smart spacing and capitalization toggles

- **Integration**
  - D-Bus service for CLI control
  - Desktop launcher (.desktop file)
  - Icon installation to system icon directories
  - Xorg/X11 session support

- **Installation**
  - User-level installation script (scripts/install.sh)
  - Automatic dependency checking
  - Virtual environment setup with system site packages
  - Desktop integration (launcher and icons)
  - Uninstallation script (scripts/uninstall.sh)

- **Documentation**
  - Comprehensive README with installation and usage instructions
  - Configuration guide (docs/CONFIG.md)
  - Packaging guide (docs/PACKAGING.md)

### Technical Details
- Python 3.10+ support
- GTK 3 via PyGObject
- AppIndicator for system tray (Ayatana)
- XDG Base Directory compliance
- Logging to ~/.local/state/wispr-lite/logs
- Model caching to ~/.cache/wispr-lite/models

### Known Limitations
- Xorg session required for full functionality (Wayland has limitations)
- Global hotkeys may conflict with input method switchers
- AppIndicator on Cinnamon typically doesn't support left-click or middle-click actions

[Unreleased]: https://github.com/dosment/wispr-lite/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dosment/wispr-lite/releases/tag/v0.1.0
