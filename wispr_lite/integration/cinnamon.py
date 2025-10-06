"""Cinnamon desktop environment integration.

Provides Cinnamon-specific functionality.
"""

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


def is_cinnamon() -> bool:
    """Check if running on Cinnamon desktop.

    Returns:
        True if Cinnamon is detected
    """
    import os
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    return 'cinnamon' in desktop or desktop == 'x-cinnamon'


def is_wayland() -> bool:
    """Check if running on Wayland session.

    Returns:
        True if Wayland is detected
    """
    import os
    session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
    wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
    return session_type == 'wayland' or bool(wayland_display)


def get_desktop_info() -> dict:
    """Get desktop environment information.

    Returns:
        Dictionary with desktop info
    """
    import os

    return {
        'current_desktop': os.environ.get('XDG_CURRENT_DESKTOP', 'unknown'),
        'session_type': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
        'is_cinnamon': is_cinnamon(),
        'is_wayland': is_wayland(),
    }


def get_wayland_limitations() -> list:
    """Get list of limitations when running on Wayland.

    Returns:
        List of limitation strings
    """
    return [
        "Global hotkeys may not work (use Cinnamon custom shortcuts instead)",
        "XTest keyboard simulation unavailable (clipboard paste will be used)",
        "Some window focus operations may be restricted",
    ]
