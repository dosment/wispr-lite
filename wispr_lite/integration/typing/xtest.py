"""XTest keyboard operations for text output.

Handles XLib/XTest typing, delta typing for partials, and undo operations.
"""

import subprocess
import time

try:
    from Xlib import X, XK, display
    from Xlib.ext import xtest
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


def check_xdotool() -> bool:
    """Check if xdotool is available."""
    try:
        subprocess.run(["xdotool", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("xdotool not found, undo fallback unavailable")
        return False


def type_character(disp, char: str) -> None:
    """Type a single character using XTest.

    Args:
        disp: X display
        char: Character to type
    """
    # Special handling for characters that need specific keysym names
    char_map = {
        ' ': 'space',
        '.': 'period',
        ',': 'comma',
        '!': 'exclam',
        '?': 'question',
        ':': 'colon',
        ';': 'semicolon',
        "'": 'apostrophe',
        '"': 'quotedbl',
        '-': 'minus',
        '_': 'underscore',
        '(': 'parenleft',
        ')': 'parenright',
        '[': 'bracketleft',
        ']': 'bracketright',
        '{': 'braceleft',
        '}': 'braceright',
        '/': 'slash',
        '\\': 'backslash',
        '@': 'at',
        '#': 'numbersign',
        '$': 'dollar',
        '%': 'percent',
        '^': 'asciicircum',
        '&': 'ampersand',
        '*': 'asterisk',
        '+': 'plus',
        '=': 'equal',
        '<': 'less',
        '>': 'greater',
        '|': 'bar',
        '~': 'asciitilde',
        '`': 'grave',
    }

    if char in char_map:
        keysym = XK.string_to_keysym(char_map[char])
    else:
        # Get keysym for character
        keysym = XK.string_to_keysym(char)
        if keysym == 0:
            # Try unicode keysym
            keysym = ord(char) | 0x01000000

    # Get keycode
    keycode = disp.keysym_to_keycode(keysym)
    if keycode == 0:
        logger.warning(f"No keycode for character: {char}")
        return

    # Check if shift is needed for this character
    # We check all modifier combinations to find if this keysym requires shift
    shift_needed = False
    if keycode != 0:
        # Check keysym at index 0 (unshifted) and 1 (shifted)
        unshifted = disp.keycode_to_keysym(keycode, 0)
        shifted = disp.keycode_to_keysym(keycode, 1)

        # If our target keysym matches the shifted version but not unshifted, we need shift
        if keysym == shifted and keysym != unshifted:
            shift_needed = True

    # Get shift keycode
    if shift_needed:
        shift_keycode = disp.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
        xtest.fake_input(disp, X.KeyPress, shift_keycode)

    # Simulate key press and release
    xtest.fake_input(disp, X.KeyPress, keycode)
    xtest.fake_input(disp, X.KeyRelease, keycode)

    # Release shift if we pressed it
    if shift_needed:
        xtest.fake_input(disp, X.KeyRelease, shift_keycode)


def insert_via_xtest(text: str, typing_delay_ms: int) -> bool:
    """Insert text via XTest keyboard simulation.

    Args:
        text: Text to insert
        typing_delay_ms: Delay between keystrokes in milliseconds

    Returns:
        True if successful
    """
    if not XLIB_AVAILABLE:
        logger.error("python-xlib not available for XTest strategy")
        return False

    try:
        disp = display.Display()
        root = disp.screen().root

        # Type each character
        for char in text:
            type_character(disp, char)
            if typing_delay_ms > 0:
                time.sleep(typing_delay_ms / 1000.0)

        disp.sync()
        logger.debug(f"Inserted text via XTest: {len(text)} chars")
        return True

    except Exception as e:
        logger.error(f"XTest typing failed: {e}")
        return False


def insert_partial(
    new_text: str,
    current_partial_text: str,
    typing_delay_ms: int
) -> tuple[bool, str, int]:
    """Insert partial text incrementally (delta from previous partial).

    Args:
        new_text: New partial transcription
        current_partial_text: Current partial text
        typing_delay_ms: Delay between keystrokes in milliseconds

    Returns:
        Tuple of (success, updated_partial_text, updated_length)
    """
    if not XLIB_AVAILABLE:
        # Can't do incremental typing without XLib
        logger.debug("Incremental typing requires XLib, skipping partial")
        return False, current_partial_text, len(current_partial_text)

    try:
        # Calculate delta
        common_prefix_len = 0
        for i, (old_char, new_char) in enumerate(zip(current_partial_text, new_text)):
            if old_char == new_char:
                common_prefix_len = i + 1
            else:
                break

        # How many characters to delete
        chars_to_delete = len(current_partial_text) - common_prefix_len

        # New characters to type
        chars_to_add = new_text[common_prefix_len:]

        disp = display.Display()

        # Delete old suffix
        if chars_to_delete > 0:
            backspace_code = disp.keysym_to_keycode(XK.string_to_keysym("BackSpace"))
            for _ in range(chars_to_delete):
                xtest.fake_input(disp, X.KeyPress, backspace_code)
                xtest.fake_input(disp, X.KeyRelease, backspace_code)

        # Type new suffix
        for char in chars_to_add:
            type_character(disp, char)

        disp.sync()

        logger.debug(f"Partial delta: -{chars_to_delete}, +{len(chars_to_add)}")
        return True, new_text, len(new_text)

    except Exception as e:
        logger.error(f"Partial typing failed: {e}")
        return False, current_partial_text, len(current_partial_text)


def undo_via_xlib(num_chars: int, typing_delay_ms: int) -> bool:
    """Undo using XLib/XTest.

    Args:
        num_chars: Number of characters to undo
        typing_delay_ms: Delay between keystrokes in milliseconds

    Returns:
        True if successful
    """
    if not XLIB_AVAILABLE:
        return False

    try:
        disp = display.Display()
        backspace_code = disp.keysym_to_keycode(XK.string_to_keysym("BackSpace"))

        # Press backspace for each character
        for _ in range(num_chars):
            xtest.fake_input(disp, X.KeyPress, backspace_code)
            xtest.fake_input(disp, X.KeyRelease, backspace_code)
            if typing_delay_ms > 0:
                time.sleep(typing_delay_ms / 1000.0)

        disp.sync()

        logger.info(f"Undid {num_chars} characters via XLib")
        return True

    except Exception as e:
        logger.error(f"XLib undo failed: {e}")
        return False


def undo_via_xdotool(num_chars: int, typing_delay_ms: int) -> bool:
    """Undo using xdotool as fallback.

    Args:
        num_chars: Number of characters to undo
        typing_delay_ms: Delay between keystrokes in milliseconds

    Returns:
        True if successful
    """
    try:
        # Use xdotool to type backspaces
        for _ in range(num_chars):
            subprocess.run(
                ["xdotool", "key", "BackSpace"],
                capture_output=True,
                check=True,
                timeout=0.5
            )
            if typing_delay_ms > 0:
                time.sleep(typing_delay_ms / 1000.0)

        logger.info(f"Undid {num_chars} characters via xdotool")
        return True

    except Exception as e:
        logger.error(f"xdotool undo failed: {e}")
        return False
