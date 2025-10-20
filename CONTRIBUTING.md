# Contributing to Wispr-Lite

Thank you for your interest in contributing to Wispr-Lite! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project follows a simple code of conduct:
- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment** (see below)
4. **Create a branch** for your changes
5. **Make your changes** following our coding standards
6. **Test your changes** thoroughly
7. **Submit a pull request**

## Development Setup

### Prerequisites

- Linux Mint 21.3+ or 22 with Cinnamon desktop
- Xorg session (Wayland has limitations)
- Python 3.10 or later
- Git

### Install Development Dependencies

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/wispr-lite.git
cd wispr-lite

# Install system dependencies
sudo apt install python3 python3-venv python3-dev python3-gi \
    gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
    gir1.2-notify-0.7 xclip portaudio19-dev

# Create virtual environment with system site packages
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development tools (optional)
pip install pytest mypy black flake8
```

### Run from Source

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python -m wispr_lite.main
```

For more detailed development information, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add type hints to all functions and class attributes
- Keep files under 500 lines
- Keep functions under 50 lines
- Keep classes under 200 lines

### Code Organization

```
wispr_lite/
├── main.py              # Entry point
├── app.py               # Main application orchestration
├── pipeline.py          # Audio pipeline
├── cli.py               # CLI interface
├── audio/               # Audio capture and VAD
├── asr/                 # ASR engine interface and backends
├── ui/                  # GTK UI components
├── integration/         # System integrations (hotkeys, typing, D-Bus)
├── commands/            # Command mode registry
└── config/              # Configuration schema
```

### Documentation

- Add docstrings to all public functions and classes
- Update README.md if adding user-facing features
- Update docs/CONFIG.md if adding configuration options
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format

### Testing

- Add unit tests for new functionality
- Ensure existing tests pass before submitting PR
- Test on Linux Mint if possible (Cinnamon desktop preferred)

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=wispr_lite tests/
```

## Pull Request Process

1. **Update documentation** as needed
2. **Add tests** for new functionality
3. **Ensure all tests pass** locally
4. **Update CHANGELOG.md** with your changes under `[Unreleased]`
5. **Create a pull request** with a clear title and description
6. **Reference any related issues** in your PR description

### PR Title Format

Use conventional commit format:

```
type: brief description

Examples:
feat: Add support for customizable voice commands
fix: Resolve hotkey conflict on system boot
docs: Update installation instructions
refactor: Simplify audio pipeline code
test: Add tests for VAD functionality
```

### PR Description

Include:
- **What**: Brief description of changes
- **Why**: Motivation or issue being solved
- **How**: Approach taken (if non-obvious)
- **Testing**: How you tested the changes
- **Screenshots**: If UI changes are involved

## Reporting Bugs

### Before Submitting

- Check if the bug has already been reported in [Issues](https://github.com/dosment/wispr-lite/issues)
- Verify you're using the latest version
- Collect relevant logs from `~/.local/state/wispr-lite/logs/wispr-lite.log`

### Bug Report Template

```markdown
**Environment:**
- OS: Linux Mint 22
- Cinnamon version: 6.4.8
- Wispr-Lite version: 0.1.0
- Session type: Xorg

**Description:**
Clear description of the bug

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Logs:**
Relevant logs from ~/.local/state/wispr-lite/logs/wispr-lite.log

**Additional Context:**
Any other relevant information
```

## Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

1. **Clear use case**: Why is this enhancement needed?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've thought about
4. **Impact**: Who would benefit from this enhancement?

## Questions?

If you have questions about contributing:
- Open a [discussion](https://github.com/dosment/wispr-lite/discussions)
- Check existing documentation in `docs/`
- Review the [development guide](docs/DEVELOPMENT.md)

Thank you for contributing to Wispr-Lite!
