# Configuration Guide

Wispr-Lite configuration is stored in `~/.config/wispr-lite/config.yaml`.

## Configuration File Structure

```yaml
# General settings
mode: "dictation"  # dictation or command
autostart: false
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR

# Hotkeys
hotkeys:
  push_to_talk: "ctrl+space"
  toggle: "ctrl+shift+space"
  command_mode: ""
  undo_last: "ctrl+shift+z"

# Audio settings
audio:
  device: null  # null = system default, or device index
  sample_rate: 16000
  channels: 1
  frame_duration_ms: 20
  vad_mode: 3  # 0-3, higher = more aggressive
  vad_silence_timeout_ms: 1000

# ASR settings
asr:
  backend: "faster-whisper"
  model_size: "base"  # tiny, base, small, medium, large
  language: null  # null = auto-detect, or language code (e.g., "en")
  compute_type: "auto"  # auto, int8, float16
  device: "auto"  # auto, cpu, cuda
  beam_size: 5
  best_of: 5

# Typing/output settings
typing:
  strategy: "clipboard"  # clipboard or xtest
  preserve_clipboard: true
  typing_delay_ms: 10
  smart_spacing: true
  smart_capitalization: true
  type_while_speaking: false  # Type partial results in real-time (experimental)

# Notification settings
notifications:
  enabled: true
  respect_dnd: true
  show_info: false
  show_warnings: true
  show_errors: true
  show_progress: true
  max_toasts_per_minute: 3
  per_category_cooldown_sec: 10
  enable_sounds: false
  sound_volume: 0.5

# UI settings
ui:
  show_overlay: true
  overlay_transparency: 0.9
  theme: "auto"  # auto, light, dark

# Command mode
commands:
  enabled: true
  prefix: "cmd:"
  require_confirmation: true
  commands:
    "open terminal":
      action: "launch"
      target: "gnome-terminal"
    "open browser":
      action: "launch"
      target: "firefox"
    "search":
      action: "url"
      target: "https://www.google.com/search?q={query}"
```

## Settings Reference

### Hotkeys

Hotkey format: `modifier+modifier+key`

Supported modifiers: `ctrl`, `shift`, `alt`, `super`

Examples:
- `ctrl+super` (default push-to-talk)
- `ctrl+shift+super` (default toggle)
- `ctrl+shift+z` (default undo)
- `alt+v`

Note: `super` is the Windows/Command key

### Audio

- `device`: Microphone device index or `null` for default
  - Use the Preferences UI to select from available devices
  - Live input level meter shows microphone activity
- `vad_mode`: Voice activity detection aggressiveness (0-3)
  - 0: Least aggressive (accepts more as speech)
  - 3: Most aggressive (strict speech detection)
- `vad_silence_timeout_ms`: Auto-stop after silence in toggle mode

### ASR

- `model_size`: Whisper model
  - `tiny`: ~75M params, fastest
  - `base`: ~125M params, good balance (recommended)
  - `small`: ~244M params
  - `medium`: ~769M params
  - `large`: ~1550M params
- `language`: ISO 639-1 code (`en`, `es`, `fr`, etc.) or `null` for auto-detect
  - In Preferences UI: Select from dropdown of 16 common languages or "Auto-detect"
  - Supported languages include: English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Polish, Turkish
- `compute_type`: Quantization type
  - `auto`: Selects based on device
  - `int8`: CPU-friendly, smaller memory
  - `float16`: GPU-friendly, better quality
- `device`: Compute device
  - `auto`: CUDA if available, else CPU
  - `cpu`: Force CPU
  - `cuda`: Force CUDA GPU

### Typing

- `strategy`:
  - `clipboard`: Safe, works everywhere, preserves formatting (includes MIME type preservation)
  - `xtest`: Faster, requires X11, types character-by-character (works in terminals)
- `preserve_clipboard`: Restore clipboard (both CLIPBOARD and PRIMARY selections) after paste
- `smart_spacing`: Automatically add space before new dictation after sentence-ending punctuation (`.`, `!`, `?`)
  - Example: "First sentence." → [dictate "second sentence"] → "First sentence. Second sentence."
  - Enabled by default
- `smart_capitalization`: Automatically capitalize first letter of new dictation
  - Capitalizes at start of first dictation and after sentences ending with `.`, `!`, or `?`
  - Example: "hello world." → [dictate "this is next"] → "hello world. This is next."
  - Enabled by default; helps with smaller models that may not capitalize correctly
- `type_while_speaking`: **Experimental** - Type partial transcription results as they arrive
  - Requires `xtest` strategy
  - Uses delta typing (only types new characters, backspaces corrections)
  - Can be distracting but provides immediate feedback
  - Final result is corrected if it differs from partials
  - **Note**: Partials are streamed from the ASR engine after recording completes, not in true real-time during capture. The effect is "typing as transcribing" rather than "typing while speaking".

### Notifications

- `respect_dnd`: Suppress toasts when Do Not Disturb is active
- Rate limiting prevents notification spam
- `max_toasts_per_minute`: Global limit
- `per_category_cooldown_sec`: Minimum time between same-category toasts

### Commands

Command actions:

- `launch`: Run an application
  ```yaml
  "open terminal":
    action: "launch"
    target: "gnome-terminal"
  ```

- `url`: Open a URL (with optional query substitution)
  ```yaml
  "search":
    action: "url"
    target: "https://www.google.com/search?q={query}"
  ```

- `shell`: Run a shell command (requires confirmation)
  ```yaml
  "update system":
    action: "shell"
    target: "sudo apt update && sudo apt upgrade -y"
  ```

## Advanced Configuration

### Custom Commands

Add to the `commands.commands` section:

```yaml
commands:
  commands:
    "open music":
      action: "launch"
      target: "rhythmbox"
    "github":
      action: "url"
      target: "https://github.com"
    "volume up":
      action: "shell"
      target: "pactl set-sink-volume @DEFAULT_SINK@ +5%"
```

### Multiple Microphones

List available devices:

```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Set device index in `audio.device`.

### GPU Acceleration

For NVIDIA GPUs with CUDA:

```yaml
asr:
  device: "cuda"
  compute_type: "float16"
```

Ensure CUDA and cuDNN are installed.

## Configuration Recipes

### High Accuracy Setup (Best Quality)

For maximum transcription accuracy (requires more RAM and CPU):

```yaml
asr:
  model_size: "medium"
  language: "en"  # Set explicitly for better accuracy
  beam_size: 5
  best_of: 5

audio:
  vad_mode: 2  # Less aggressive (accepts more audio)
  vad_silence_timeout_ms: 1500  # Wait longer before stopping

typing:
  smart_spacing: true
  smart_capitalization: true
```

### Fast Performance Setup (Speed Priority)

For minimal latency on older hardware:

```yaml
asr:
  model_size: "tiny"
  compute_type: "int8"
  device: "cpu"

audio:
  vad_mode: 3  # Most aggressive (quick detection)
  vad_silence_timeout_ms: 800  # Stop quickly

typing:
  strategy: "xtest"  # Faster than clipboard
  typing_delay_ms: 5  # Minimum delay
```

### Privacy-Focused Setup

Maximum privacy with minimal logging:

```yaml
mode: "dictation"
log_level: "ERROR"  # Only log errors

typing:
  preserve_clipboard: false  # Don't access clipboard
  smart_spacing: true
  smart_capitalization: true

notifications:
  enabled: true
  show_info: false  # Don't show info notifications
  show_progress: false  # Don't show progress
```

### Multi-Language Setup

For users who switch between languages:

```yaml
asr:
  model_size: "small"  # Better for multi-language
  language: null  # Auto-detect
  beam_size: 5

typing:
  strategy: "clipboard"  # Better for non-ASCII
  preserve_clipboard: true
  smart_spacing: true
  smart_capitalization: true
```

### Command-Heavy Workflow

For users who primarily use voice commands:

```yaml
mode: "command"

commands:
  enabled: true
  require_confirmation: false  # Skip confirmations for trusted commands
  commands:
    "open terminal":
      action: "launch"
      target: "gnome-terminal"
    "open browser":
      action: "launch"
      target: "firefox"
    "open files":
      action: "launch"
      target: "nemo"
    "search":
      action: "url"
      target: "https://www.google.com/search?q={query}"
    "youtube":
      action: "url"
      target: "https://youtube.com"
    "volume up":
      action: "shell"
      target: "pactl set-sink-volume @DEFAULT_SINK@ +5%"
    "volume down":
      action: "shell"
      target: "pactl set-sink-volume @DEFAULT_SINK@ -5%"
    "mute":
      action: "shell"
      target: "pactl set-sink-mute @DEFAULT_SINK@ toggle"
```

### Laptop/Mobile Setup

For use on laptops with limited resources:

```yaml
asr:
  model_size: "base"
  device: "cpu"
  compute_type: "int8"

audio:
  vad_mode: 3
  vad_silence_timeout_ms: 1000

typing:
  strategy: "clipboard"
  smart_spacing: true
  smart_capitalization: true

notifications:
  enabled: true
  respect_dnd: true  # Important for battery life
  max_toasts_per_minute: 2
```

## Troubleshooting Common Configurations

### Hotkey Conflicts

If your hotkeys conflict with system shortcuts:

```yaml
hotkeys:
  push_to_talk: "ctrl+alt+space"  # Alternative
  toggle: "ctrl+alt+shift+space"
  undo_last: "ctrl+alt+z"
```

Or use Cinnamon custom shortcuts instead.

### Audio Dropouts

If you experience audio dropouts or missed speech:

```yaml
audio:
  vad_mode: 1  # Less aggressive
  vad_silence_timeout_ms: 2000  # Wait longer
  frame_duration_ms: 30  # Larger frames (less CPU)
```

### Clipboard Issues

If clipboard paste doesn't work reliably:

```yaml
typing:
  strategy: "xtest"  # Try XTest instead
  preserve_clipboard: false  # Disable if causing issues
```

### Performance Issues

If transcription is slow or uses too much CPU:

```yaml
asr:
  model_size: "tiny"  # Smallest, fastest model
  compute_type: "int8"
  device: "cpu"

audio:
  sample_rate: 16000  # Default, don't increase
  channels: 1  # Mono only
```

## Environment Variables

- `XDG_CONFIG_HOME`: Config directory (default: `~/.config`)
- `XDG_CACHE_HOME`: Model cache directory (default: `~/.cache`)
- `XDG_STATE_HOME`: Log directory (default: `~/.local/state`)
- `WISPR_LOG_LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR)

Example:

```bash
WISPR_LOG_LEVEL=DEBUG wispr-lite
```

## Tips and Best Practices

1. **Start with defaults**: The default configuration is optimized for most users
2. **Model selection**: Use `base` for daily use, `small` for better accuracy, `tiny` for speed
3. **Hotkey choice**: Avoid common shortcuts like Ctrl+Space (input methods) or Super+Space (launchers)
4. **VAD sensitivity**: Mode 3 (default) works well; lower if it cuts off speech
5. **Clipboard vs XTest**: Clipboard is safer and works everywhere; XTest is faster but may have compatibility issues
6. **Smart features**: Keep smart_spacing and smart_capitalization enabled for better output
7. **Notifications**: Respect DND to avoid interruptions during presentations/screen sharing
8. **Backup config**: Keep a backup of your customized config.yaml
