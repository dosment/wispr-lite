"""Clipboard operations for text output.

Handles clipboard save/restore with MIME type support and paste simulation.
"""

import subprocess
import time
from typing import Optional

try:
    from Xlib import X, XK, display
    from Xlib.ext import xtest
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


def check_xclip() -> bool:
    """Check if xclip is available."""
    try:
        subprocess.run(["xclip", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("xclip not found, clipboard operations may fail")
        return False


def get_clipboard(selection: str = 'clipboard') -> Optional[str]:
    """Get current clipboard content.

    Args:
        selection: X selection ('clipboard' or 'primary')

    Returns:
        Clipboard content or None
    """
    try:
        result = subprocess.run(
            ["xclip", "-selection", selection, "-o"],
            capture_output=True,
            text=True,
            timeout=1
        )
        return result.stdout if result.returncode == 0 else None
    except Exception as e:
        logger.debug(f"Failed to get {selection}: {e}")
        return None


def set_clipboard(text: str, selection: str = 'clipboard') -> None:
    """Set clipboard content.

    Args:
        text: Text to set
        selection: X selection ('clipboard' or 'primary')
    """
    try:
        subprocess.run(
            ["xclip", "-selection", selection],
            input=text.encode(),
            timeout=1,
            check=True
        )
    except Exception as e:
        logger.error(f"Failed to set {selection}: {e}")
        raise


def get_clipboard_targets(selection: str = 'clipboard') -> Optional[list]:
    """Get available MIME types/targets for clipboard content.

    Args:
        selection: X selection ('clipboard' or 'primary')

    Returns:
        List of available targets or None
    """
    try:
        result = subprocess.run(
            ["xclip", "-selection", selection, "-t", "TARGETS", "-o"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0 and result.stdout:
            targets = [t.strip() for t in result.stdout.strip().split('\n')]
            return targets
        return None
    except Exception as e:
        logger.debug(f"Failed to get {selection} targets: {e}")
        return None


def get_clipboard_content_by_target(
    target: str, selection: str = 'clipboard'
) -> Optional[bytes]:
    """Get clipboard content for a specific MIME type.

    Args:
        target: MIME type (e.g., 'text/html', 'text/uri-list')
        selection: X selection ('clipboard' or 'primary')

    Returns:
        Binary content or None
    """
    try:
        result = subprocess.run(
            ["xclip", "-selection", selection, "-t", target, "-o"],
            capture_output=True,
            timeout=1
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception as e:
        logger.debug(f"Failed to get {selection} content for {target}: {e}")
        return None


def set_clipboard_content_by_target(
    content: bytes, target: str, selection: str = 'clipboard'
) -> bool:
    """Set clipboard content for a specific MIME type.

    Args:
        content: Binary content
        target: MIME type (e.g., 'text/html', 'text/uri-list')
        selection: X selection ('clipboard' or 'primary')

    Returns:
        True if successful
    """
    try:
        subprocess.run(
            ["xclip", "-selection", selection, "-t", target],
            input=content,
            timeout=1,
            check=True
        )
        return True
    except Exception as e:
        logger.debug(f"Failed to set {selection} content for {target}: {e}")
        return False


def save_clipboard_data(selection: str = 'clipboard') -> dict:
    """Save clipboard data including MIME types.

    Args:
        selection: X selection ('clipboard' or 'primary')

    Returns:
        Dictionary with 'text' and 'mime_data' keys
    """
    data = {
        'text': get_clipboard(selection),
        'targets': get_clipboard_targets(selection),
        'mime_data': {}
    }

    # Save content for important MIME types
    if data['targets']:
        for mime_type in ['text/html', 'text/uri-list']:
            if mime_type in data['targets']:
                content = get_clipboard_content_by_target(mime_type, selection)
                if content:
                    data['mime_data'][mime_type] = content

    return data


def restore_clipboard_with_targets(
    saved_data: dict, selection: str = 'clipboard'
) -> None:
    """Restore clipboard with awareness of MIME types.

    Args:
        saved_data: Dictionary with 'text', 'targets', and 'mime_data'
        selection: X selection ('clipboard' or 'primary')
    """
    try:
        # Restore MIME types if we have them
        if saved_data.get('mime_data'):
            for mime_type, content in saved_data['mime_data'].items():
                set_clipboard_content_by_target(content, mime_type, selection)
                logger.debug(f"Restored {selection} MIME type: {mime_type}")

        # Always restore plain text as fallback
        if saved_data.get('text'):
            set_clipboard(saved_data['text'], selection)

        logger.debug(
            f"Restored {selection} (targets: {len(saved_data.get('targets', []))})"
        )
    except Exception as e:
        logger.debug(f"Failed to restore {selection}: {e}")


def simulate_paste() -> None:
    """Simulate Ctrl+V key press."""
    if not XLIB_AVAILABLE:
        logger.error("python-xlib not available for paste simulation")
        return

    try:
        disp = display.Display()

        # Get keycodes
        ctrl_code = disp.keysym_to_keycode(XK.string_to_keysym("Control_L"))
        v_code = disp.keysym_to_keycode(XK.string_to_keysym("v"))

        # Press Ctrl
        xtest.fake_input(disp, X.KeyPress, ctrl_code)
        disp.sync()

        # Press V
        xtest.fake_input(disp, X.KeyPress, v_code)
        disp.sync()

        # Release V
        xtest.fake_input(disp, X.KeyRelease, v_code)
        disp.sync()

        # Release Ctrl
        xtest.fake_input(disp, X.KeyRelease, ctrl_code)
        disp.sync()

    except Exception as e:
        logger.error(f"Failed to simulate paste: {e}")
        raise


def insert_via_clipboard(
    text: str, preserve_clipboard: bool, xclip_available: bool
) -> bool:
    """Insert text via clipboard and paste.

    Args:
        text: Text to insert
        preserve_clipboard: Whether to preserve and restore clipboard
        xclip_available: Whether xclip is available

    Returns:
        True if successful
    """
    if not xclip_available:
        logger.error("xclip not available for clipboard strategy")
        return False

    try:
        # Save current clipboard and primary if configured (with MIME types)
        saved_clipboard = None
        saved_primary = None

        if preserve_clipboard:
            saved_clipboard = save_clipboard_data('clipboard')
            saved_primary = save_clipboard_data('primary')

        # Set clipboard to text
        set_clipboard(text, 'clipboard')

        # Small delay to ensure clipboard is set
        time.sleep(0.05)

        # Simulate Ctrl+V
        simulate_paste()

        # Restore clipboard and primary if configured
        if preserve_clipboard:
            time.sleep(0.1)  # Wait for paste to complete
            if saved_clipboard and saved_clipboard.get('text') is not None:
                restore_clipboard_with_targets(saved_clipboard, 'clipboard')
            if saved_primary and saved_primary.get('text') is not None:
                restore_clipboard_with_targets(saved_primary, 'primary')

        logger.debug(f"Inserted text via clipboard: {len(text)} chars")
        return True

    except Exception as e:
        logger.error(f"Clipboard paste failed: {e}")
        return False
