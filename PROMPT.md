# Prompt: Wispr Flow–Style Voice Dictation & Command Launcher for Linux Mint Cinnamon

Build a Wispr Flow–style, push-to-talk voice dictation and command launcher for Linux Mint Cinnamon. It must run locally, be lightweight, and integrate cleanly with the Cinnamon desktop. Treat “Wispr Flow” as the reference experience: a global hotkey summons a minimal overlay that records while held, transcribes speech in real time, and either types the text into the focused app (dictation) or executes mapped commands (command mode). Deliver production-ready code, packaging, and docs.

## Objectives
- Provide fast, accurate, low-latency dictation via local Whisper (no cloud required).
- Offer a clean overlay UI and tray icon with Cinnamon-friendly styling.
- Support a global push-to-talk shortcut and a toggle mode.
- Type transcribed text into the focused window reliably without breaking app focus.
- Provide an optional “command mode” with safe, user-configurable actions.
- Package for easy install on latest Linux Mint Cinnamon (21.3/22) with autostart support.

## Target Environment
- OS: Linux Mint 21.3/22 (x86_64), Cinnamon desktop, Xorg session (default). Wayland support is a stretch goal.
- Audio: PulseAudio or PipeWire (Mint 22 uses PipeWire by default). Use PortAudio-based libs that work for both.
- Python: 3.10+ present by default on Mint. Prefer Python solution for speed of development.
- System integrations: `.desktop` launcher, tray icon via AppIndicator, autostart in `~/.config/autostart`, global shortcut registration that works on Cinnamon/Xorg.

## Primary Features
- Push-to-talk and toggle
  - Default: hold a configurable hotkey (e.g., `Ctrl+Super`) to record; release to finalize.
  - Toggle mode: press once to start, again to stop.
  - Visual overlay shows recording state; optional start/stop beep.
- Real-time transcription
  - Use local Whisper via `faster-whisper` (CTranslate2) with CPU by default; auto-detect GPU (NVIDIA CUDA) if available.
  - Stream partial results with punctuation; finalize on release.
  - Language auto-detect with option to pin a language.
  - Configurable model size (`tiny`, `base`, `small`, `medium`, `large`) with clear CPU/RAM guidance. Default: `base`
- Dictation output
  - Type into the currently focused window without stealing focus.
  - Implement two strategies:
    1) Clipboard-and-paste (safe fallback, preserves non-ASCII).
    2) XTest synthetic typing (fast; use `python-xlib`), selectable in settings.
  - Optional smart spacing and capitalization.
  - Preserve and restore clipboard contents (both `CLIPBOARD` and `PRIMARY` selections, including MIME types) when using paste strategy; configurable to skip restore for power users.
  - Provide "Undo last dictation" that reverts the most recent inserted text (tracks inserted length across paste/typing modes) via hotkey and tray menu.
- Command mode
  - Trigger by prefix (e.g., `cmd:`), hotkey chord, or overlay toggle.
  - Map intents/keywords to actions in a user-editable YAML/JSON config.
  - Built-in actions: open application, run shell command, open URL, insert snippet, control media volume/mute, switch workspace, open settings.
  - Safety: confirmation dialogs for commands that could be destructive, allowlists, dry-run mode.
  - Verbal punctuation and special keys: configurable mappings for "period", "comma", "question mark", "newline", "tab", "escape", "select all", etc.; document in config with examples per locale.
- Microphone and VAD
  - Device selection in settings; input volume meter.
  - Use `webrtcvad` (with energy-based fallback) to gate audio and reduce latency.
  - Optional noise suppression (RNNoise or WebRTC NS if feasible).
- UI/UX
  - GTK (PyGObject) overlay window: minimal, centered, rounded, follows Mint theme (dark/light).
  - Preferences window for settings (hotkeys, model, mic, modes, behavior).
  - Tray icon via `ayatana-appindicator3` with quick toggles (PTT/toggle, dictation/command).
  - Accessibility and i18n: add AT-SPI roles/labels for screen readers, full keyboard navigation, high-contrast theme compatibility. Externalize UI strings, honor system locale for punctuation/segmentation. Ensure IME compatibility for CJK and RTL languages.
- Privacy
  - No network usage by default; transcription entirely local.
  - Transparent logs; user can disable logs. Respect `$XDG_*` base dirs.
  - Clearly label any optional cloud integrations (disabled unless configured).
- Performance
  - Keep end-to-end latency under ~300–500 ms on typical CPUs using `tiny/base` models.
  - Stream partial results to the UI and optionally “type as you speak” in dictation mode (configurable).

## Non-Functional Requirements
- Robust error handling with clear user feedback and log files under `~/.local/state/wispr-lite/logs`.
- Minimal dependencies; avoid heavy frameworks. Vendor small helpers if they reduce friction.
- No root required to install or run.
- Clear separation of concerns with a maintainable module layout.
 - Accessibility: conform to basic a11y expectations (AT-SPI exposure, keyboard navigable UI). Internationalization-ready strings and locale-aware punctuation.
 - Resume/Hot-swap resilience: auto-reinitialize audio after system suspend/resume and when default input device changes.

## Tech Choices
- Language: Python 3.10+.
- UI: GTK 3/4 via PyGObject; AppIndicator for the tray icon.
- Audio I/O: `sounddevice` (PortAudio) or `pyaudio`. Prefer `sounddevice`.
- VAD: `webrtcvad`.
- ASR: `faster-whisper` (CTranslate2 backend). Optional `whisper.cpp` integration as a pluggable backend.
- Hotkeys: `pynput` on Xorg or `python-xlib` + XRecord. Provide a fallback using a user-configurable Cinnamon keyboard shortcut that sends D-Bus to the app.
- Typing/Paste: `python-xlib` for XTest; fallback clipboard+paste via `xclip`/`xsel` and simulated `Ctrl+V`.
- Packaging: `.deb` via `python -m build` + `debhelper` or `fpm`. Also provide a “no-root” installer that sets up a venv in `~/.local/share/wispr-lite` and installs a `.desktop` file. Flatpak is a stretch goal.
 - Optional: use `rtkit`/`realtimekit` via `dbus` to request elevated audio thread priority when available; fail soft if unavailable.

## Deliverables
- Source code with this structure:
  - `wispr_lite/main.py` (entrypoint)
  - `wispr_lite/ui/overlay.py`, `wispr_lite/ui/preferences.py`, `wispr_lite/ui/tray.py`, `wispr_lite/ui/notifications.py`
  - `wispr_lite/audio/capture.py`, `wispr_lite/audio/vad.py`
  - `wispr_lite/asr/engine.py` (backend interface), `wispr_lite/asr/faster_whisper_backend.py`, `wispr_lite/asr/whisper_cpp_backend.py` (optional)
  - `wispr_lite/integration/typing.py`, `wispr_lite/integration/cinnamon.py`, `wispr_lite/integration/hotkeys.py`, `wispr_lite/integration/dbus.py`
  - `wispr_lite/commands/registry.py`, `wispr_lite/commands/builtin.py`
  - `wispr_lite/config/schema.py`, `wispr_lite/config/defaults.yaml`
  - `wispr_lite/logging.py`
- Installer and packaging:
  - `pyproject.toml` with pinned deps; lockfile if using Poetry.
  - `scripts/install.sh` to create venv in `~/.local/share/wispr-lite`, install deps, register `.desktop`, and optional autostart.
  - `.desktop` launcher in `~/.local/share/applications/wispr-lite.desktop`.
  - Autostart entry in `~/.config/autostart/wispr-lite.desktop` (toggle in settings).
  - Makefile targets: `make dev`, `make run`, `make test`, `make deb`, `make clean`.
- Documentation:
  - `README.md` with system requirements, quick install, usage, troubleshooting (PulseAudio/PipeWire tips).
  - `docs/CONFIG.md` describing all settings and the command mapping format.
  - `docs/PACKAGING.md` with `.deb` build steps and Flatpak notes (if done).
- Tests:
  - Unit tests for VAD segmentation and ASR chunking.
  - Integration tests for typing/paste path (Xorg required; skip on CI if unavailable).
  - Smoke test script: verifies mic capture, hotkey, overlay, typing loop.
- CI:
  - GitHub Actions workflow to lint, type-check, and run unit tests (Linux).

## Key User Flows
- Dictation flow
  1) User holds hotkey → overlay shows “Listening”.
  2) Audio captured, VAD-gated, partial ASR shown in overlay.
  3) On release, final transcript is typed or pasted into active window.
- Command flow
  1) User toggles Command mode or says “cmd: open terminal”.
  2) Intent recognized via prefix/keyword → mapped action runs (with confirmation if needed).
  3) Overlay shows action result or error.

## Detailed Implementation Notes
- Overlay window
  - Always-on-top, transparent background, centered; no taskbar entry; suppress focus stealing.
  - Keyboard capture limited to the app; do not disrupt the active application.
- Global hotkeys on Cinnamon/Xorg
  - Primary: `pynput` or `python-xlib` global key event hook.
  - Fallback: instruct users to bind a Cinnamon custom shortcut to call `wispr-lite --toggle` via D-Bus/CLI arguments.
  - Detect hotkey conflicts on startup; surface a one-time warning toast and deep link to Preferences for rebinding.
- Typing/paste strategies
  - Default: clipboard+paste for reliability across apps and IMEs.
  - Advanced: XTest injection with proper UTF-8 support; implement rate limiting and retry.
  - Clipboard preservation: capture current clipboard/primary selections, perform paste, then restore prior content; guard against large binary payloads and provide a size limit.
- Audio pipeline
  - Use a small, fixed frame size (e.g., 20 ms) and queue to ASR worker.
  - VAD gates frames; if silence persists (configurable timeout), auto-stop in toggle mode.
  - Handle system suspend/resume: detect via DBus/UPower or GLib signals; re-open streams on resume. Detect device hot-swap and reselect default device or the configured device when it reappears.
  - Watchdog: monitor capture/ASR worker health; restart crashed workers once with exponential backoff; emit a single error toast and log details.
- ASR
  - `faster-whisper` with `compute_type` auto-detect (e.g., `int8_float16` on GPU, `int8` on CPU).
  - Model caching in `~/.cache/wispr-lite/models`; explicit model selection in settings.
  - Model integrity: verify SHA256 checksums and sizes; support resuming interrupted downloads; display license notice before first download; provide an offline pre-download script.
- Settings persistence
  - YAML or TOML at `~/.config/wispr-lite/config.yaml`.
  - Editable via Preferences UI with live validation and restartless apply where possible.
- Logging
  - Rotate logs, configurable verbosity, redact sensitive data.
- Security
  - Commands run in a restricted subprocess; warn on interpolated user input.
  - Whitelist-based mapping; confirmation for shell actions unless explicitly marked safe.

## Notifications & Tray UX (Anti‑Spam, Best Practices)
- Philosophy: overlays/tray for routine feedback; toasts only for important, user-actionable events or background completions. Never steal focus.
- DND: respect the desktop’s Do‑Not‑Disturb; when active, suppress toasts and route messages to overlay/tray/log only. Disable sounds while DND.
- Severity policy: info → tray/overlay only; warning → toast once with dedupe; error → toast + tray badge; progress → single persistent, updated in place.
- Rate limits: global max 3 toasts/min; per‑category min interval 10s; burst coalescing with “(xN)” counter. Cooldown resets after 60s idle.
- Deduplication: same event key within 5 min updates existing toast or increments counter; no new toast.
- Progress: use one resident notification with progress (model download, backend restart). Update via replace ID; auto-close on success; show a single error toast on failure.
- Actions: only where useful (Open Logs, Retry, Open Preferences, Cancel). No destructive one‑click actions; require confirm in app.
- Sounds: off by default; optional short start/stop chime. Never play when DND or muted.
- Copy: concise, single sentence; no marketing; no repeated “success” toasts for routine dictation.
- Privacy: no content previews for dictated text in toasts; show generic “Dictation delivered”.
- Tray behaviors
  - Use Ayatana AppIndicator on Cinnamon; fallback to AppIndicator3 if needed.
  - Dynamic icons for states: idle, listening, processing, muted/error; provide 16/24/32/48 assets under `wispr_lite/ui/icons/`, install to `share/icons/hicolor/.../apps/wispr-lite.(png|svg)`.
  - Left-click toggles overlay; middle-click mutes mic; tooltip shows mode and active mic.
  - Menu items: Start/Stop Listening, Toggle PTT/Toggle Mode, Dictation/Command Mode, Microphone submenu (enumerate inputs), Paste Strategy (Clipboard/XTest), Autostart On/Off, Open Preferences, View Logs, Restart Backend, Quit.
  - Graceful degrade if AppIndicator missing (basic `Gtk.StatusIcon` fallback or notify user).
  - Add "Undo Last Dictation" and "Disable Hotkey Temporarily" menu items.

### Implementation
- Library: `gi.repository.Notify` (libnotify). Reuse the same `Notify.Notification` instance to update via server replace ID rather than creating new toasts.
- Manager: add `wispr_lite/ui/notifications.py` with:
  - `notify(event: str, severity: 'info'|'warn'|'error'|'progress', key: str=None, text: str='', progress: Optional[float]=None, actions: list=[])`
  - DND check (desktop notifications server or Cinnamon setting; if undetectable, assume DND off but still obey rate limits).
  - Per-key dedup store with timestamps/counters; global token bucket for rate limiting.
  - Category policy: info → tray/overlay, warn/error → toast (subject to limits), progress → single updated toast.
- Tray: `wispr_lite/ui/tray.py`
  - Dynamic icons: idle/listening/processing/muted/error; install 16/24/32/48px assets.
  - Left-click toggles listening; middle-click mute; tooltip shows mode/mic.
  - Full menu as listed above; avoid stealing focus.
- Overlay: show ephemeral, non-modal banners for benign events (hotkey bound, mic switched) instead of toasts.
- Logging: all events to `~/.local/state/wispr-lite/logs`; “View Logs” opens latest file.
- Settings (Preferences → Notifications)
  - Master toggle; per‑level toggles (info/warn/error/progress).
  - DND respect on/off; quiet hours; sound on/off and volume.
  - Rate limit sliders (advanced): max toasts/min, per‑category cooldown.
  - “Test notification” and “Clear cooldowns” buttons.

## D‑Bus/CLI Control
- Session bus name `org.wispr_lite.Daemon` with methods: `Toggle()`, `Start()`, `Stop()`, `SetMode(dictation|command)`, `OpenPreferences()`.
- Signals: `StateChanged(idle|listening|processing|error)`, `Error(message)`.
- CLI wrapper `wispr-lite --toggle|--start|--stop|--mode|--prefs` to integrate with Cinnamon custom shortcuts and headless control.
 - Add `--undo` flag to revert the last dictation insertion, if possible.

## Compatibility and Packaging
- Runtime dependencies for `.deb`:
  - `python3 (>= 3.10)`, `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-ayatanaappindicator3-0.1` (or `gir1.2-appindicator3-0.1` fallback), `gir1.2-notify-0.7`, `libnotify4`, `xclip` or `xsel`, `xdotool` (optional), `libportaudio2`.
- User-level installer `scripts/install.sh`:
  - Creates venv under `~/.local/share/wispr-lite/venv`.
  - Installs wheels for `faster-whisper`, `sounddevice`, `webrtcvad`, `PyGObject`.
  - Registers `.desktop` files and autostart if chosen.
- Icons: install to `~/.local/share/icons/hicolor/*/apps/` and system hicolor paths when packaging; provide monochrome-friendly variants.
 - Wayland detection: on Wayland sessions, fall back to clipboard/portals for paste, document limitations (global hotkeys/XTest typing), and guide users to Cinnamon’s Xorg session for full functionality.
 - Provide `scripts/preload_models.sh` to pre-download and verify models offline (with checksums) for air-gapped installs.

## Acceptance Criteria
- Fresh install on Linux Mint Cinnamon 21.3 or 22:
  - Launches from menu; tray icon appears.
  - Hotkey works globally (PTT and toggle).
  - Overlay displays while recording; no app focus is lost.
  - Dictation types correct text with punctuation into active apps (e.g., Text Editor, Firefox).
  - Command mode successfully opens Terminal, browser URLs, and runs a safe sample script with confirmation.
  - Settings persist across restarts; mic device selection works; model selection loads.
  - No network calls unless optional cloud features are explicitly enabled.
  - CPU-only works smoothly with `tiny`/`base`; GPU used if available.
- Notifications & Tray (anti‑spam):
  - With defaults, routine dictation never produces toasts; only overlay feedback. Errors do.
  - During DND, no toasts or sounds; events still appear in tray/overlay and logs.
  - Repeated identical warnings within a minute produce at most one toast with “(xN)” coalescing.
  - Model download shows a single progress toast that updates in place and auto‑closes on success.
  - Tray icon reflects states and exposes all listed menu actions without stealing focus.
  - Toggling notification settings immediately changes behavior (no app restart).
 - Clipboard preservation: after dictation via paste, the user’s clipboard and primary selections are restored exactly (text and common MIME types) unless the setting is disabled.
 - Accessibility/i18n: UI is keyboard navigable, labeled for screen readers, respects high contrast; strings are externalized; locale-aware punctuation works.
 - Suspend/resume & device hot-swap: dictation still works after resuming from suspend and after switching microphone devices without requiring app restart.
 - Undo: "Undo last dictation" reliably removes the most recently inserted text in both paste and XTest typing modes.
 - Verbal punctuation & keys: speaking configured punctuation or special key words results in the intended characters/actions.
 - Hotkey conflicts: if the default hotkey is already taken, the app surfaces a one-time warning and offers to open Preferences.
 - Wayland: on Wayland sessions, the app degrades gracefully, informs the user of limitations, and dictation via clipboard still works.
 - Model integrity: model downloads are verified (checksum/size), can resume if interrupted, and display a license notice at first download.
 - Watchdog & priority: if audio/ASR workers crash, they are restarted automatically once, with a single error toast and an entry in logs; attempting RT priority does not crash or lock up the system.

## Nice-to-Haves (Stretch)
- Wayland compatibility on Cinnamon: document limitations and provide a `wl-clipboard`/portal-based paste path.
- On-device TTS feedback (e.g., `piper` or `espeak-ng`) with a brief chime readout.
- Rofi/Ulauncher integration for command palette style fallback.
- Flatpak packaging.
 - Export/import settings profiles (YAML) and a first-run setup wizard for hotkeys, mic, and model pre-download.

## Project Guidance
- Default to the simplest robust path; avoid premature optimization.
- Fail softly: if XTest is unavailable, fall back to paste; if GPU missing, run CPU models.
- Include troubleshooting tips in README for PulseAudio/PipeWire, keyboard hooks, and permissions.
- Keep code modular and documented; prioritize maintainability.

## Deliver Now (MVP Scope)
- Implement the full MVP with dictation, overlay, hotkey, typing/paste, preferences UI, local Whisper.
- Add command mode with at least 5 useful built-in actions and YAML mapping.
- Ship `.deb`, user-level installer, docs, and tests.
