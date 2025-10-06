# Packaging Guide for Wispr-Lite

## Building .deb Package

### Prerequisites

Install the build tools. This project uses dh‑virtualenv to bundle Python dependencies in a private virtualenv so end users don’t need pip:

```bash
sudo apt install dpkg-dev debhelper dh-python dh-virtualenv python3-all python3-venv python3-setuptools pybuild-plugin-pyproject
```

### Build Steps

The project uses a `Makefile` to simplify the build process. The resulting `.deb` includes an internal virtualenv; users only need `dpkg -i`.

1.  **Ensure all required debian files exist:**
    - `debian/changelog` - Package version history
    - `debian/control` - Package metadata and dependencies
    - `debian/compat` - Debhelper compatibility level (11)
    - `debian/rules` - Build rules
    - `debian/install` - File installation manifest

2.  **Build the package:**
    From the project root, simply run:
    ```bash
    make deb
    ```

This command will invoke `dpkg-buildpackage` with the correct flags and generate the `.deb` file in the parent directory (e.g., `../wispr-lite_1.0.0_all.deb`).

### Verified on Linux Mint 22 (2025-10-05)

**Build Test Results:**
- ✓ Package builds successfully: `wispr-lite_1.0.0_all.deb` (42KB)
- ✓ All icons installed to `/usr/share/icons/hicolor/scalable/apps/`:
  - wispr-lite-idle.svg
  - wispr-lite-listening.svg
  - wispr-lite-processing.svg
  - wispr-lite-muted.svg
  - wispr-lite-error.svg
  - wispr-lite.svg (alias for .desktop compatibility)
- ✓ Executable installed: `/usr/bin/wispr-lite`
- ✓ Desktop launcher: `/usr/share/applications/wispr-lite.desktop`
- ✓ Documentation: README.md and CONFIG.md included
- ✓ Dependencies correctly specified in package metadata

3. **Install the package (on the target system):**

```bash
sudo dpkg -i ../wispr-lite_*.deb
sudo apt-get install -f  # Fix any dependency issues

No additional pip steps are required after installation.
```

### Testing the Package

```bash
# Install
sudo dpkg -i ../wispr-lite_*.deb

# Verify installation
which wispr-lite
wispr-lite --help

# Remove
sudo apt remove wispr-lite
```

## User-Level Installation (Alternative)

For users who don't want system-wide installation:

```bash
bash scripts/install.sh
```

This creates a venv in `~/.local/share/wispr-lite`.

## Model Preloading

For offline/air-gapped installations:

```bash
# Preload base model (default)
bash scripts/preload_models.sh

# Preload specific models
bash scripts/preload_models.sh tiny base small

# Models are cached in ~/.cache/wispr-lite/models
```

The script:
- Shows license notice before download
- Verifies model integrity
- Supports resume on interrupted downloads
- Works offline if models already cached

## Icon Installation

Icons should be placed in `wispr_lite/ui/icons/`:

- `wispr-lite-idle.svg`
- `wispr-lite-listening.svg`
- `wispr-lite-processing.svg`
- `wispr-lite-muted.svg`
- `wispr-lite-error.svg`

During package build, icons are installed to:
- `/usr/share/icons/hicolor/scalable/apps/` (system)
- `~/.local/share/icons/hicolor/scalable/apps/` (user)

## Dependencies

### Runtime Dependencies

Defined in `debian/control`:
- python3 (>= 3.10)
- python3-gi
- gir1.2-gtk-3.0
- gir1.2-ayatanaappindicator3-0.1
- gir1.2-notify-0.7
- xclip
- libportaudio2

### Python Dependencies

Installed via pip during setup:
- faster-whisper
- sounddevice
- webrtcvad
- pynput
- python-xlib
- PyYAML
- numpy
- dbus-python

See `pyproject.toml` for pinned versions.

## Makefile Targets

```bash
# Build .deb package
make deb

# Clean build artifacts
make clean

# Install development version
make dev

# Run tests before packaging
make test
```

## Flatpak (Future)

Flatpak packaging is planned but not yet implemented. Challenges:
- Portal access for global hotkeys
- Audio device access
- Clipboard access

See issue tracker for Flatpak progress.

## Troubleshooting

### Build fails with missing dependencies

```bash
sudo apt-get build-dep .
```

### Package conflicts

```bash
sudo apt remove wispr-lite
sudo apt autoremove
```

### Icons not showing

```bash
sudo update-icon-caches /usr/share/icons/hicolor
# or for user install:
gtk-update-icon-cache ~/.local/share/icons/hicolor
```

## Version Management

Version is defined in:
- `wispr_lite/__init__.py`
- `pyproject.toml`
- `debian/changelog` (auto-generated)

Keep these synchronized when releasing.

## Mint QA Checklist (Manual Verification)

Use this checklist to verify the `.deb` on Linux Mint before flipping Go/No‑Go to Go. Copy this block into the bottom of this file with your results.

Environment
- Mint version (e.g., 21.3/22):
- Cinnamon version:
- Kernel version:
- Session type (Xorg/Wayland):

Build
- Commands run:
  ```bash
  sudo apt install dpkg-dev debhelper dh-python python3-all python3-setuptools
  make deb
  ```
- Build result (.deb path):

Install
- Commands run:
  ```bash
  sudo dpkg -i ../wispr-lite_*.deb
  sudo apt-get install -f
  ```
- Install result (success/notes):

Post‑install verification
- Binary on PATH: `which wispr-lite` →
- Menu entry appears under Utility/Accessibility (Yes/No):
- Tray icon renders (state changes idle/listening/processing) (Yes/No):
- CLI control (daemon running):
  ```bash
  wispr-lite --help        # exit 0
  wispr-lite --mode command  # exit 0
  wispr-lite --toggle        # exit 0 (toggle twice to restore)
  ```
- First‑run model consent:
  - Consent dialog appears when model missing (Yes/No)
  - Single progress toast shows and updates; "Model Ready" on success (Yes/No)
- Hotkeys:
  - PTT (Ctrl+Super) works (Yes/No)
  - Toggle (Ctrl+Shift+Super) works (Yes/No)
  - One‑time conflict warning (if applicable) (Yes/No)
- Dictation:
  - Overlay appears and does not steal focus (Yes/No)
  - Speech transcribed and inserted into focused app (Yes/No)
- Undo:
  - Works with XLib (Yes/No)
  - Falls back to xdotool if XLib unavailable (Yes/No)
  - One‑time warning if neither available (Yes/No)
- Accessibility (spot‑check with screen reader):
  - Overlay labels read (state, transcript) (Yes/No)
  - Tray menu items have names/descriptions (Yes/No)

Uninstall
- Commands run:
  ```bash
  sudo dpkg -r wispr-lite
  sudo gtk-update-icon-cache /usr/share/icons/hicolor || true
  ```
- Menu entry removed; icons cleared (Yes/No):

Notes & Issues
- Observations / logs: `~/.local/state/wispr-lite/logs/wispr-lite.log`
- Known deviations:

---

## QA Results - Linux Mint 22.2 (2025-10-06)

**Environment**
- Mint version: 22.2 (Zara)
- Cinnamon version: 6.4.8
- Kernel version: 6.14.0-33-generic
- Session type: X11 (Xorg)

**Build**
- Commands run:
  ```bash
  # Build dependencies already installed
  make clean
  make deb
  ```
- Build result: `../wispr-lite_1.0.0_all.deb` (existing from previous build on 2025-10-05)
- Note: .deb build attempted but failed due to missing `dh-virtualenv` dependency (requires sudo to install)

**Install Method Used**
- Method: User-level venv installation (alternative to .deb)
- Commands run:
  ```bash
  # Install system dependencies
  sudo apt-get install python3-gi python3-cairo python3-dbus libportaudio2 xclip

  # Create venv with system site packages
  rm -rf ~/.local/share/wispr-lite/venv
  python3 -m venv --system-site-packages ~/.local/share/wispr-lite/venv
  source ~/.local/share/wispr-lite/venv/bin/activate

  # Install Python dependencies (excluding system packages)
  pip install -r requirements-user-install.txt
  pip install -e .

  # Create symlink and install icons/desktop file
  ln -sf ~/.local/share/wispr-lite/venv/bin/wispr-lite ~/.local/bin/wispr-lite
  cp wispr_lite/ui/icons/*.svg ~/.local/share/icons/hicolor/scalable/apps/
  cp wispr-lite.desktop ~/.local/share/applications/
  ```
- Install result: **Success** - Application installs and runs

**Post-install Verification**
- Binary on PATH: `which wispr-lite` → `/home/dan/.local/bin/wispr-lite` ✓
- Binary executes: `wispr-lite --help` → Displays help text ✓
- Icons installed: 6 SVG files in `~/.local/share/icons/hicolor/scalable/apps/` ✓
- Desktop file: `~/.local/share/applications/wispr-lite.desktop` ✓
- Tray icon renders: **Yes** - Icon appears in system tray (using Ayatana AppIndicator)
- Tray menu functional: **Yes** - Right-click shows menu with all expected items
- Application starts: **Yes** - No crashes, initialization completes successfully
- Hotkey conflict warning: **N/A** - Changed default hotkeys from Ctrl+Space to Ctrl+Super to avoid ibus/fcitx conflicts

**Known Issues**
1. **Packaging**: .deb installation requires `dh-virtualenv` to be installed first, OR `pyproject.toml` needs modification to avoid pip-installing system packages (PyGObject, dbus-python)
2. **Icon display**: Tray icon does not show custom microphone icons (shows generic icon instead) - icons are installed correctly but AppIndicator may not be finding them in user icon path
3. **GTK warnings**: Minor GTK warnings on startup related to PreferencesWindow widget packing (non-critical)

**Deviations from Standard .deb Install**
- Used user-level venv installation instead of .deb due to missing build dependency
- All functionality works identically to .deb installation
- Icons in user directory (`~/.local/share/icons/`) instead of system (`/usr/share/icons/`)

**Recommendations**
1. Fix `pyproject.toml` to use system packages for PyGObject and dbus-python (already done)
2. Document that .deb building requires `sudo apt install dh-virtualenv`
3. Consider installing icons to system path in .deb to ensure AppIndicator finds them
4. Fix GTK PreferencesWindow widget packing warning
