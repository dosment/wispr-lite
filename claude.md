# Claude Coding Guide for Wispr‑Lite (Linux Mint Cinnamon)

Purpose
- This guide instructs Claude on how to implement and maintain the Wispr Flow–style voice dictation and command launcher described in PROMPT.md.
- Scope applies to the entire repo. Follow these rules unless explicitly overridden in an issue/task.

Core Principles
- Local-first: no network calls by default; privacy by design.
- User-invisible when idle: minimal CPU/RAM, no focus stealing, no toast spam.
- Modular and maintainable: small files, clear interfaces, cohesive packages.
- Fail softly with clear feedback and visible logs.
- Prefer simple, robust solutions over clever ones.

Architecture Expectations
- Language: Python 3.10+ with type hints everywhere.
- UI: GTK (PyGObject). Keep UI updates on the GTK main thread. Use GLib.idle_add for cross-thread updates.
- Audio + ASR: background worker(s) feeding an ASR backend (`faster-whisper`) via queues.
- Integrations: isolate Xorg/Cinnamon specifics under `wispr_lite/integration/*`.
- Config + State: YAML config under `~/.config/wispr-lite/config.yaml`; logs under `~/.local/state/wispr-lite/logs`; cache models under `~/.cache/wispr-lite/models`.

File And Function Size Limits
- Hard rule: keep each source file under 500 lines. If a file approaches 400 lines, split it.
- Prefer functions ≤ 50 lines and classes ≤ 200 lines. Extract helpers early.
- Separate concerns: do not mix UI, audio, ASR, hotkeys, and OS integration in one file.

Project Structure (conform to PROMPT.md)
- wispr_lite/main.py (entry)
- wispr_lite/ui/overlay.py, preferences.py, tray.py, notifications.py
- wispr_lite/audio/capture.py, vad.py
- wispr_lite/asr/engine.py, faster_whisper_backend.py, whisper_cpp_backend.py (optional)
- wispr_lite/integration/typing.py, cinnamon.py, hotkeys.py, dbus.py
- wispr_lite/commands/registry.py, builtin.py
- wispr_lite/config/schema.py, defaults.yaml
- wispr_lite/logging.py

Coding Standards
- Style: PEP 8 + meaningful names. No one-letter vars except indices.
- Types: annotate all public functions and class attributes. Enable mypy (strict if practical) and fix type errors.
- Docstrings: short, actionable. Use Google style or NumPy style consistently.
- Imports: standard → third-party → local, each section alphabetized. Use explicit exports in __init__.py where relevant.
- Errors: never swallow exceptions silently. Catch at boundaries, log with context, and show user-safe messages via overlay/notifications.
- Logging: use a shared logger (wispr_lite.logging.get_logger). No print(). Redact sensitive data.
- Concurrency: keep ASR and audio off the UI thread. Use queues, short-lived locks, and clean shutdown signals. Join threads on exit.
- Resource management: use context managers (with) for mics, files, streams. Close everything on stop/quit.
- Configuration: validate on load; write back only on explicit save. Provide safe defaults.
- Dependencies: keep minimal; pin in pyproject. Avoid heavy frameworks.

UI & UX Rules
- Overlay: always-on-top, transparent, centered; never steals focus. Avoid modal dialogs during dictation.
- Tray: AppIndicator with dynamic icons (idle/listening/processing/muted/error). Left-click toggles listening; middle-click mutes. Menu exposes primary actions.
- Notifications (anti-spam):
  - Respect desktop DND; suppress toasts during DND and route to tray/log.
  - Severity policy: info → overlay/tray only; warning → one deduped toast; error → toast + tray badge; progress → single updated toast.
  - Rate limit: ≤ 3 toasts/min globally; per-key cooldown ≥ 10s; coalesce bursts with “(xN)”.
  - No dictated text in notifications. Keep copy concise.

Audio & ASR Pipeline
- Capture with sounddevice (PortAudio). Fixed 16 kHz mono frames (e.g., 20 ms) to a thread-safe queue.
- VAD: webrtcvad gate; energy fallback for edge cases.
- ASR: faster-whisper with streaming partials. Auto-detect GPU; default to CPU `base` model. Cache models under XDG cache.
- Latency budget: 300–500 ms end-to-end on modern CPUs using tiny/base.

Integrations
- Hotkeys: prefer python-xlib/pynput on Xorg; fallback to Cinnamon custom shortcut invoking D-Bus/CLI.
- Typing: default clipboard+paste; optional XTest typing with UTF‑8 support and rate limiting. Never steal focus.
- D‑Bus: provide session bus API for Toggle/Start/Stop/Mode/Prefs; do not require D-Bus for basic usage.

Security
- Command mode: whitelist actions; explicit confirmations for risky ops. Shell commands run with minimal environment and proper escaping. No evaluation of dictated text as code.
- Privacy: no network by default; opt-in for any cloud features. Never log dictated content unless “diagnostics” explicitly enabled.

Testing
- Use pytest. Add unit tests for VAD segmentation and ASR chunking; mock audio/ASR.
- Integration tests for typing/paste on Xorg; skip if DISPLAY/permissions unavailable.
- Smoke script to verify hotkey → overlay → capture → ASR → output loop.

Packaging & Install
- Provide pyproject.toml with pinned versions. Make `scripts/install.sh` for user-level venv in ~/.local/share/wispr-lite.
- Add `.desktop` launcher and optional autostart entry. Install icons to hicolor theme paths.

Performance & Quality Budgets
- Startup < 1s to tray on typical laptop (without first-time model download).
- Idle CPU ~0%, RSS < 150 MB (CPU, base model not loaded). Load models lazily on first record.
- Dictation CPU: 1–3 cores active; avoid busy loops; use blocking queues.

When To Ask vs. Decide
- Ask only if blocking or user-impacting (e.g., inability to bind global hotkey). Otherwise choose sensible defaults and proceed.
- Document any assumptions in README and in PR summaries.

PR/Commit Hygiene (for maintainers or forks)
- Small, focused commits; descriptive messages (“area: short imperative summary”).
- Include rationale for non-obvious changes. Link to acceptance criteria.
- Update docs/tests alongside code.

Definition of Done (per feature)
- Meets acceptance criteria in PROMPT.md.
- Adheres to file/function size limits and coding standards above.
- Includes tests or a smoke script, and updates to README/docs if user-facing.
- No regressions to tray, hotkeys, overlay, or notifications behavior.

Authoring Tips For Claude
- Start by outlining modules and interfaces. Scaffold minimal files first.
- Implement vertical slices: overlay + hotkey + capture end-to-end, then iterate.
- Keep patches small and reviewable. If a file grows beyond 400 lines, split before adding features.
- Prefer explicit, typed data structures over ad-hoc dicts. Use dataclasses for config.
- For UI updates from workers, post via GLib.idle_add; never block the main loop.

References
- See PROMPT.md for detailed requirements, acceptance criteria, and packaging targets.

\n## Collaboration With Gemini (Archived)
- Gemini is no longer assisting. Claude owns remaining UI/UX packaging/docs follow‑ups required for final acceptance. See docs/COLLAB.md for the latest checklists and owners.

Ownership
- Claude (you):
  - Internals/integrations: hotkeys, typing/undo fallbacks, worker/watchdog/RT priority, D‑Bus/CLI, command security.
  - Final acceptance follow‑ups: packaging QA on Mint (document in docs/PACKAGING.md), consent threading polish (Event/GLib; single progress toast), remaining string externalization and README accessibility note.
  - Consent callback path unit tests; CLI/D‑Bus smoke (exit code) checks.

Working Agreement
- Coordinate via docs/COLLAB.md: add a short entry for each change and check off your checklist.
- Keep UI calls on GTK main thread; coalesce notifications; never include dictated text in toasts.
- Tests accompany changes; skip gracefully on missing DISPLAY/permissions.

Conflict Resolution
- Prefer smallest possible diffs; update docs/tests alongside.
