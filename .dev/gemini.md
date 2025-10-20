# Gemini Coding Guide for Wispr‑Lite (Linux Mint Cinnamon) — Archived

Purpose
- Gemini is no longer assisting on this project. Historical scope and guidance are preserved for reference. All remaining tasks are reassigned to Claude (see docs/COLLAB.md and claude.md).

Core Principles
- Inherit principles from `claude.md`: local‑first, user‑invisible when idle, modular/maintainable, fail softly with clear feedback.
- Keep UI updates on the GTK main thread; use `GLib.idle_add` for cross‑thread updates.
- Respect XDG dirs; no network by default (explicit consent for model downloads).

Responsibilities (Gemini‑owned)
- Packaging & assets: `.deb` QA on Mint 21.3/22, install icons to hicolor, ensure base app icon alias `wispr-lite.svg`; update `docs/PACKAGING.md`.
- Accessibility & i18n: add AT‑SPI roles/names to overlay/tray/prefs; externalize user‑facing strings; update docs.
- Model consent UX: replace polling with `threading.Event` or GLib signal; keep a single coalesced PROGRESS toast; ensure decline path messaging and README notes.
- Docs: README and CONFIG updates (CLI examples, tray click behavior caveats, Wayland limitations, `type_while_speaking`, device meter notes).

Coding Standards
- Follow repo standards in `claude.md`: PEP 8, type hints, docstrings, imports order, logger usage (no print), privacy in logs.
- File/function size limits: files < 500 lines; functions ≤ 50 lines; classes ≤ 200 lines.
- UI strings: centralize for i18n; avoid hard‑coded user‑facing text in code where possible.

Collaboration
- Update `docs/COLLAB.md` with an “Implementation Updates” entry for each change; check items under “Final Acceptance Follow‑ups (Gemini)”.
- Do not modify Claude‑owned internals (hotkeys, typing/undo, worker/watchdog/RT priority, D‑Bus/CLI, command security) without a handoff note.
- Prefer smallest diffs; keep tests/docs in the same change.

Current Open Items (Gemini)
- Packaging QA on Mint 21.3/22: run `.deb` install; verify icon/menu; record notes in `docs/PACKAGING.md`.
- Accessibility/i18n: continue externalizing remaining user‑facing strings and confirm AT‑SPI labels/roles coverage; add a short accessibility note to README.
- Model consent UX threading: replace polling with `threading.Event` or GLib signal; ensure a single coalesced progress toast and clear decline messaging (link to `scripts/preload_models.sh`).
- README/CONFIG: confirm CLI examples, AppIndicator click behavior note, Wayland limitations, and `type_while_speaking`/device meter are documented.

Testing
- Add/extend tests where feasible; skip gracefully if DISPLAY/permissions missing.
- For packaging QA, include brief notes in `docs/PACKAGING.md` (what was tested, Mint version, outcomes).

Definition of Done (Gemini scope)
- Tasks in “Final Acceptance Follow‑ups (Gemini)” checked, with tests/docs updated.
- No regressions to tray, hotkeys, overlay, or notifications.
- Changes reviewed against privacy and anti‑spam policies.

References
- PROMPT.md and claude.md for full requirements and standards.
- docs/COLLAB.md for current ownership and checklists.
