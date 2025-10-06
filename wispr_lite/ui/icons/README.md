# Wispr-Lite Icons

This directory contains icon assets for the system tray.

## Required Icons

The tray uses different icons for different states:

- `wispr-lite-idle.svg` - Idle/ready state
- `wispr-lite-listening.svg` - Listening/recording state
- `wispr-lite-processing.svg` - Processing/transcribing state
- `wispr-lite-muted.svg` - Microphone muted state
- `wispr-lite-error.svg` - Error state

## Installation

Icons should be installed to:
- System: `/usr/share/icons/hicolor/{size}/apps/wispr-lite-*.{svg,png}`
- User: `~/.local/share/icons/hicolor/{size}/apps/wispr-lite-*.{svg,png}`

Supported sizes: 16x16, 24x24, 32x32, 48x48, scalable

## Placeholder Icons

For development, symbolic placeholders are used. Replace with proper icons before release.

## Design Guidelines

- Monochrome-friendly for panel integration
- Clear visual distinction between states
- Follow system icon theme conventions
