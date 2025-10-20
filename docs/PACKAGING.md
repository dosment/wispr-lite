# Packaging Guide for Wispr-Lite

This guide covers building and distributing Wispr-Lite packages.

## Table of Contents

- [.deb Package](#deb-package)
- [User-Level Installation](#user-level-installation)
- [Model Preloading](#model-preloading)
- [Icon Installation](#icon-installation)
- [Dependencies](#dependencies)
- [Version Management](#version-management)
- [Flatpak (Future)](#flatpak-future)
- [Troubleshooting](#troubleshooting)

## .deb Package

### Prerequisites

Install the build tools:

```bash
sudo apt install dpkg-dev debhelper dh-python dh-virtualenv \
    python3-all python3-venv python3-setuptools pybuild-plugin-pyproject
```

**Note**: `dh-virtualenv` is required for building .deb packages with bundled Python dependencies.

### Build Steps

The project uses a `Makefile` to simplify the build process:

```bash
# Build the .deb package
make deb
```

This will:
1. Verify all required `debian/` files exist
2. Run `dpkg-buildpackage` with correct flags
3. Generate `.deb` file in parent directory (e.g., `../wispr-lite_0.1.0_all.deb`)

### Required Debian Files

Ensure these files exist in `debian/` directory:

- `debian/changelog` - Package version history
- `debian/control` - Package metadata and dependencies
- `debian/compat` - Debhelper compatibility level
- `debian/rules` - Build rules
- `debian/install` - File installation manifest

### Installing the Package

On the target system:

```bash
# Install package
sudo dpkg -i ../wispr-lite_*.deb

# Fix any dependency issues
sudo apt-get install -f
```

No additional pip steps are required after installation—the .deb includes a bundled virtualenv.

### Testing the Package

```bash
# Install
sudo dpkg -i ../wispr-lite_*.deb

# Verify installation
which wispr-lite
wispr-lite --help

# Test basic functionality
wispr-lite --version

# Remove
sudo apt remove wispr-lite
```

### Package Contents

The .deb package includes:

- **Executable**: `/usr/bin/wispr-lite`
- **Desktop launcher**: `/usr/share/applications/wispr-lite.desktop`
- **Icons**: `/usr/share/icons/hicolor/scalable/apps/wispr-lite*.svg`
- **Documentation**: README.md and CONFIG.md
- **Bundled virtualenv**: All Python dependencies included

## User-Level Installation

For users who don't want system-wide installation or don't have sudo access:

```bash
bash scripts/install.sh
```

This will:
- Create a venv in `~/.local/share/wispr-lite`
- Install all dependencies
- Create symlink in `~/.local/bin/wispr-lite`
- Install icons to `~/.local/share/icons/`
- Install desktop launcher to `~/.local/share/applications/`

### Uninstall

```bash
bash scripts/uninstall.sh
```

Options:
- Remove application and virtual environment
- Optionally remove user configuration (`~/.config/wispr-lite/`)
- Optionally remove cache (`~/.cache/wispr-lite/`)

## Model Preloading

For offline or air-gapped installations:

```bash
# Preload default (base) model
bash scripts/preload_models.sh

# Preload specific models
bash scripts/preload_models.sh tiny base small

# Models are cached in ~/.cache/wispr-lite/models
```

The preload script:
- Shows license notice before download
- Verifies model integrity (SHA256 checksums)
- Supports resume on interrupted downloads
- Works offline if models already cached

## Icon Installation

### Icon Files

Icons should be placed in `wispr_lite/ui/icons/`:

- `wispr-lite-idle.svg` - Gray microphone (idle state)
- `wispr-lite-listening.svg` - Blue microphone (recording)
- `wispr-lite-processing.svg` - Orange microphone (transcribing)
- `wispr-lite-muted.svg` - Microphone with slash (muted)
- `wispr-lite-error.svg` - Red microphone (error state)

### Installation Paths

**System-wide (.deb package)**:
```bash
/usr/share/icons/hicolor/scalable/apps/
```

**User-level**:
```bash
~/.local/share/icons/hicolor/scalable/apps/
```

### Icon Cache Update

After installing icons:

```bash
# System-wide
sudo gtk-update-icon-cache /usr/share/icons/hicolor

# User-level
gtk-update-icon-cache ~/.local/share/icons/hicolor
```

### Base Icon Alias

Create an alias for desktop file compatibility:

```bash
cp wispr-lite-idle.svg wispr-lite.svg
```

## Dependencies

### Runtime Dependencies (System)

Defined in `debian/control` and checked by `scripts/install.sh`:

- `python3` (>= 3.10)
- `python3-gi` - PyGObject bindings
- `gir1.2-gtk-3.0` - GTK 3
- `gir1.2-ayatanaappindicator3-0.1` - System tray (AppIndicator)
- `gir1.2-notify-0.7` - Desktop notifications
- `xclip` - Clipboard access
- `libportaudio2` - Audio I/O

### Python Dependencies

Installed via pip during setup (see `pyproject.toml`):

- `faster-whisper` - Whisper ASR backend
- `sounddevice` - Audio capture
- `webrtcvad` - Voice activity detection
- `pynput` - Global hotkeys
- `python-xlib` - X11 integration (optional)
- `PyYAML` - Configuration
- `numpy` - Array processing
- `dbus-python` - D-Bus service

### Build Dependencies

Required for building .deb packages:

- `dpkg-dev`
- `debhelper`
- `dh-python`
- `dh-virtualenv`
- `python3-all`
- `python3-setuptools`
- `pybuild-plugin-pyproject`

## Version Management

Version is defined in multiple files—keep them synchronized:

1. **wispr_lite/__init__.py**
   ```python
   __version__ = "0.1.0"
   ```

2. **pyproject.toml**
   ```toml
   [project]
   version = "0.1.0"
   ```

3. **debian/changelog**
   ```
   wispr-lite (0.1.0) unstable; urgency=low
   ```

### Updating Version

When releasing a new version:

1. Update all three files above
2. Update `CHANGELOG.md` with new version
3. Tag the commit:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

## Makefile Targets

```bash
# Build .deb package
make deb

# Clean build artifacts
make clean

# Install development version
make dev

# Run tests
make test

# Run linting
make lint

# Run application from source
make run
```

## Flatpak (Future)

Flatpak packaging is planned but not yet implemented.

### Challenges

- Portal access for global hotkeys
- Audio device access via PipeWire
- Clipboard access restrictions
- D-Bus service registration

### Progress

Track Flatpak progress in [GitHub Issues](https://github.com/dosment/wispr-lite/issues).

## Troubleshooting

### Build Fails with Missing Dependencies

Install build dependencies:

```bash
sudo apt-get build-dep .
```

Or install manually:

```bash
sudo apt install dpkg-dev debhelper dh-python dh-virtualenv \
    python3-all python3-setuptools pybuild-plugin-pyproject
```

### Package Conflicts

Remove existing installation:

```bash
sudo apt remove wispr-lite
sudo apt autoremove
```

### Icons Not Showing

Update icon cache:

```bash
# System-wide
sudo gtk-update-icon-cache /usr/share/icons/hicolor

# User-level
gtk-update-icon-cache ~/.local/share/icons/hicolor

# Verify icons exist
ls /usr/share/icons/hicolor/scalable/apps/wispr-lite*.svg
```

### Virtualenv Issues in .deb

If building .deb with `dh-virtualenv` fails:

1. Ensure `dh-virtualenv` is installed:
   ```bash
   sudo apt install dh-virtualenv
   ```

2. Check `pyproject.toml` doesn't conflict with system packages

3. Review build logs in `debian/` directory

### Python Dependency Conflicts

If pip dependencies conflict with system packages:

1. Use `--system-site-packages` for venv
2. Exclude conflicting packages from `pyproject.toml`
3. Install system packages via apt:
   ```bash
   sudo apt install python3-gi python3-dbus
   ```

## Quality Assurance

### Testing Checklist

Before releasing a package, verify:

- [ ] Package builds successfully
- [ ] Installation completes without errors
- [ ] Binary is on PATH (`which wispr-lite`)
- [ ] Desktop launcher appears in application menu
- [ ] Icons display correctly in tray
- [ ] Hotkeys work (PTT and toggle)
- [ ] Dictation works in test applications
- [ ] Preferences window opens and saves settings
- [ ] Model download consent works
- [ ] CLI commands work (`--toggle`, `--start`, `--stop`)
- [ ] Logs are created and accessible
- [ ] Uninstallation removes all files cleanly

### Test Environment

Test on clean Linux Mint installation:

- Linux Mint 21.3 (Virginia) or 22 (Wilma)
- Cinnamon desktop
- Xorg session
- Fresh user account (no existing config)

### Reporting Issues

Document test results with:

- OS and Cinnamon versions
- Session type (Xorg/Wayland)
- Installation method (.deb or user-level)
- Any errors or warnings
- Relevant logs from `~/.local/state/wispr-lite/logs/`

## Distribution

### GitHub Releases

1. Create release on GitHub
2. Attach .deb package as release asset
3. Include CHANGELOG in release notes
4. Tag with version number (e.g., `v0.1.0`)

### Package Repositories

Future options:

- Submit to Ubuntu/Mint PPAs
- Debian package repositories
- Flatpak repository (Flathub)
- Snap Store

## References

- [Debian Packaging Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [dh-virtualenv Documentation](https://dh-virtualenv.readthedocs.io/)
- [Flatpak Documentation](https://docs.flatpak.org/)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
