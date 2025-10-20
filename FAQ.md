# Frequently Asked Questions (FAQ)

## General

### What is Wispr-Lite?

Wispr-Lite is a local, privacy-focused voice dictation and command launcher for Linux Mint Cinnamon. It uses OpenAI's Whisper model to transcribe speech entirely on your computer—no cloud services required.

### Is my speech data sent to the cloud?

No. All transcription happens locally on your computer using the Whisper model. No audio or transcripts are sent to any server unless you explicitly configure optional cloud features (which are disabled by default).

### What are the system requirements?

- Linux Mint 21.3+ or 22 with Cinnamon desktop
- Xorg session (Wayland has limitations)
- Python 3.10 or later
- 4GB RAM minimum (8GB recommended for larger models)
- Microphone

### Does it work on other Linux distributions?

Wispr-Lite is designed for Linux Mint Cinnamon but may work on other Debian-based distributions with Cinnamon desktop and Xorg. Ubuntu with Cinnamon should work. Other desktops (GNOME, KDE, etc.) are not currently supported.

### Does it work on Wayland?

Partial support. On Wayland sessions:
- Global hotkeys may not work
- XTest typing strategy is unavailable
- Clipboard paste strategy still works

For full functionality, use Xorg (default on Linux Mint).

## Installation & Setup

### How do I install Wispr-Lite?

```bash
git clone https://github.com/dosment/wispr-lite.git
cd wispr-lite
bash scripts/install.sh
```

See [README.md](README.md#installation) for detailed instructions.

### How do I uninstall Wispr-Lite?

```bash
cd wispr-lite
bash scripts/uninstall.sh
```

This will remove the application and optionally remove user configuration and cache.

### Where are configuration files stored?

- **Configuration**: `~/.config/wispr-lite/config.yaml`
- **Logs**: `~/.local/state/wispr-lite/logs/wispr-lite.log`
- **Models**: `~/.cache/wispr-lite/models/`

These follow the XDG Base Directory specification.

### How much disk space do the models require?

Model sizes (approximate):
- `tiny`: ~75MB
- `base`: ~150MB (default)
- `small`: ~500MB
- `medium`: ~1.5GB

Models are downloaded on first use and cached locally.

## Usage

### What are the default hotkeys?

- **Push-to-talk**: `Ctrl+Super` (hold to record, release to transcribe)
- **Toggle listening**: `Ctrl+Shift+Super` (press once to start, again to stop)
- **Undo last dictation**: `Ctrl+Shift+Z`

Note: `Super` is the Windows/Command key.

### My hotkeys don't work. What should I check?

1. **Check for conflicts**: Go to System Settings → Keyboard → Shortcuts and ensure Ctrl+Super isn't used by another application
2. **Input method conflict**: If you use ibus or fcitx, they often use Ctrl+Space. Wispr-Lite now uses Ctrl+Super to avoid this conflict
3. **Wayland**: Global hotkeys don't work on Wayland sessions. Switch to Xorg or use CLI commands
4. **Fallback**: Use Cinnamon custom shortcuts to bind commands like `wispr-lite --toggle`

### Hotkeys don't work after system boot but work after restarting wispr-lite

This issue has been fixed in recent versions. Make sure you're running the latest version and all Super key variants are properly normalized.

### How do I change the hotkeys?

Open Preferences (right-click tray icon → Preferences) and go to the Hotkeys section. You can customize:
- Push-to-talk hotkey
- Toggle hotkey
- Undo hotkey

### Can I use Wispr-Lite without hotkeys?

Yes! You can control Wispr-Lite via:
- **Tray menu**: Right-click the tray icon
- **CLI commands**: `wispr-lite --toggle`, `wispr-lite --start`, `wispr-lite --stop`
- **Cinnamon keyboard shortcuts**: Bind custom shortcuts to CLI commands

### Why doesn't the tray icon respond to left-click or middle-click?

This is a limitation of AppIndicator on Cinnamon desktop. AppIndicator typically only supports right-click menu interaction. This is not a bug in Wispr-Lite but a design choice of the AppIndicator specification.

Use the right-click menu to access all features.

## Transcription & Audio

### Which Whisper model should I use?

- **tiny**: Fastest, lower accuracy (~1GB RAM)
- **base**: Good balance (default, ~1GB RAM)
- **small**: Better accuracy (~2GB RAM)
- **medium**: High accuracy (~5GB RAM)

Start with `base`. If transcription quality is poor, try `small` or `medium`. If performance is slow, try `tiny`.

### How do I change the model?

Open Preferences → ASR → Model Size and select your preferred model. The new model will download on first use.

### Transcription quality is poor. What can I improve?

1. **Upgrade model**: Use `small` or `medium` instead of `base`
2. **Check microphone**: Ensure your mic is working and has good audio quality
3. **Reduce background noise**: Use a quiet environment
4. **Check VAD settings**: Adjust voice activity detection aggressiveness in config
5. **Language selection**: Set your language explicitly instead of auto-detect

### How do I select a different microphone?

Open Preferences → Audio → Microphone Device. You'll see a list of available input devices. Select your preferred microphone.

### The microphone level meter doesn't show in preferences

The input level meter is a live visual indicator. Make sure Wispr-Lite has permission to access your microphone and that the selected device is working.

### Can I use Wispr-Lite for languages other than English?

Yes! Whisper supports multiple languages. In Preferences → ASR → Language, select from:
- Auto-detect (default)
- 16 common languages (English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Polish, Turkish, and more)

Or edit `config.yaml` to set a specific language code (e.g., `en`, `es`, `fr`).

## Dictation Output

### Dictated text doesn't appear in my application

1. **Focus**: Ensure the target application is focused when you release the hotkey
2. **Strategy**: Try switching between clipboard and XTest strategies (Preferences → Typing → Strategy)
3. **Permissions**: Some applications may block paste/typing. Try a text editor first to verify it works
4. **Wayland**: XTest doesn't work on Wayland. Use clipboard strategy

### Text is pasted instead of typed character-by-character

This is expected behavior for the **clipboard strategy** (default). It's safer and works in more applications.

If you want character-by-character typing, switch to **XTest strategy** in Preferences → Typing → Strategy.

### Smart spacing isn't working

Ensure **Smart Spacing** is enabled in Preferences → Typing → Smart Spacing. This automatically adds a space before new dictation after sentence-ending punctuation (`.`, `!`, `?`).

### Smart capitalization isn't working

Ensure **Smart Capitalization** is enabled in Preferences → Typing → Smart Capitalization. This automatically capitalizes the first letter of new dictation and after sentences.

### How do I undo the last dictation?

Press `Ctrl+Shift+Z` or right-click the tray icon → Undo Last Dictation.

Note: Undo requires `python-xlib` or `xdotool` to be installed.

### My clipboard is replaced after dictation

By default, Wispr-Lite **preserves and restores your clipboard** after paste (Preferences → Typing → Preserve Clipboard).

If your clipboard is not being restored, ensure this setting is enabled.

## Performance

### Wispr-Lite is slow or uses too much CPU

1. **Use a smaller model**: Switch to `tiny` or `base`
2. **Check system resources**: Ensure you have enough RAM
3. **Close other applications**: Free up CPU/RAM
4. **GPU acceleration**: If you have an NVIDIA GPU with CUDA, enable GPU mode in Preferences

### Can I use GPU acceleration?

Yes, if you have an NVIDIA GPU with CUDA installed:

1. Install CUDA and cuDNN
2. Edit `~/.config/wispr-lite/config.yaml`:
   ```yaml
   asr:
     device: "cuda"
     compute_type: "float16"
   ```
3. Restart Wispr-Lite

### Model download is slow

Whisper models are 150MB-1.5GB depending on size. The first download may take time depending on your internet connection.

You can pre-download models offline:
```bash
bash scripts/preload_models.sh base
```

## Troubleshooting

### Wispr-Lite won't start

1. **Check logs**: `~/.local/state/wispr-lite/logs/wispr-lite.log`
2. **Check dependencies**: Ensure all system dependencies are installed
   ```bash
   sudo apt install python3 python3-venv python3-gi gir1.2-gtk-3.0 \
       gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7 xclip portaudio19-dev
   ```
3. **Reinstall**: Try uninstalling and reinstalling

### How do I view logs?

- **Via tray**: Right-click tray icon → View Logs
- **Manually**: `cat ~/.local/state/wispr-lite/logs/wispr-lite.log`

### The overlay window doesn't appear

1. **Check if listening**: Ensure you're holding the hotkey or toggle is active
2. **Overlay setting**: Ensure "Show Overlay" is enabled in Preferences
3. **Transparency**: Check if overlay transparency is set too high

### Notifications are spammy

Wispr-Lite has built-in notification rate limiting:
- Maximum 3 toasts per minute
- Per-category cooldown of 10 seconds
- Respects Do Not Disturb mode

If you're still getting too many notifications, check Preferences → Notifications and adjust settings.

### Do Not Disturb (DND) isn't being respected

Wispr-Lite attempts to detect desktop DND settings. If it's not working:
1. Check Preferences → Notifications → Respect DND is enabled
2. Check your system's DND settings
3. Manually disable notifications in Preferences

## Advanced

### Can I run Wispr-Lite from the command line?

Yes! Wispr-Lite supports CLI control:

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

### How do I edit the configuration file directly?

Configuration is stored at `~/.config/wispr-lite/config.yaml`.

You can edit it with any text editor:
```bash
nano ~/.config/wispr-lite/config.yaml
```

Restart Wispr-Lite for changes to take effect.

See [docs/CONFIG.md](docs/CONFIG.md) for all configuration options.

### Can I add custom voice commands?

Yes! Edit `~/.config/wispr-lite/config.yaml` and add commands under the `commands.commands` section:

```yaml
commands:
  commands:
    "open music":
      action: "launch"
      target: "rhythmbox"
    "github":
      action: "url"
      target: "https://github.com"
```

See [docs/CONFIG.md](docs/CONFIG.md#commands) for more examples.

### How do I make Wispr-Lite start on login?

Enable autostart in Preferences or manually create an autostart entry:

```bash
cp ~/.local/share/applications/wispr-lite.desktop ~/.config/autostart/
```

### Can I contribute to Wispr-Lite?

Yes! Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Still Have Questions?

- **Issues**: [GitHub Issues](https://github.com/dosment/wispr-lite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dosment/wispr-lite/discussions)
- **Documentation**: Check [README.md](README.md) and [docs/](docs/)
