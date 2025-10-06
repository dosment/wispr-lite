"""Core text output coordination.

Provides high-level TextOutput class that dispatches to clipboard or XTest strategies.
"""

from typing import Optional

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import TypingConfig
from wispr_lite.integration.typing import clipboard, xtest

logger = get_logger(__name__)


class TextOutput:
    """Handles typing/pasting transcribed text."""

    def __init__(self, config: TypingConfig):
        """Initialize text output.

        Args:
            config: Typing configuration
        """
        self.config = config
        self.last_inserted_text = ""
        self.last_inserted_length = 0

        # For incremental typing
        self.current_partial_text = ""
        self.partial_typed_length = 0

        # Check xclip availability for clipboard strategy
        self.xclip_available = clipboard.check_xclip()

        # Check xdotool availability for undo fallback
        self.xdotool_available = xtest.check_xdotool()

        # Track if we've shown undo warning
        self.undo_warning_shown = False

        # Callback for undo unavailable warning
        self.on_undo_unavailable = None

        # Check XLib availability for XTest strategy
        if config.strategy == "xtest" and not xtest.XLIB_AVAILABLE:
            logger.warning("python-xlib not available, falling back to clipboard")
            self.config.strategy = "clipboard"

        logger.info(f"TextOutput initialized: strategy={self.config.strategy}")

    def insert_text(self, text: str) -> bool:
        """Insert text into the active window.

        Args:
            text: Text to insert

        Returns:
            True if successful
        """
        if not text:
            return False

        # Smart spacing: auto-add space after sentence-ending punctuation
        if self.config.smart_spacing and self.last_inserted_text:
            logger.debug(f"Smart spacing check: last_text='{self.last_inserted_text[-20:]}', new_text='{text[:20]}'")
            # Check if last text ended with sentence-ending punctuation
            if self.last_inserted_text.rstrip().endswith(('.', '!', '?')):
                # Check if new text doesn't start with whitespace or punctuation
                if text and not text[0].isspace() and text[0] not in '.,!?;:':
                    text = ' ' + text
                    logger.info(f"Smart spacing: added space before '{text[:20]}'")
                else:
                    logger.debug(f"Smart spacing: text already starts with whitespace/punctuation")
            else:
                logger.debug(f"Smart spacing: previous text doesn't end with sentence punctuation")
        elif not self.config.smart_spacing:
            logger.debug("Smart spacing disabled in config")
        elif not self.last_inserted_text:
            logger.debug("Smart spacing: no previous text")

        # Smart capitalization: capitalize first letter after sentence-ending punctuation or at start
        if self.config.smart_capitalization:
            should_capitalize = False

            # Capitalize if this is the first text
            if not self.last_inserted_text:
                should_capitalize = True
                logger.debug("Smart capitalization: first text, capitalizing")
            # Capitalize if previous text ended with sentence-ending punctuation
            elif self.last_inserted_text.rstrip().endswith(('.', '!', '?')):
                should_capitalize = True
                logger.debug("Smart capitalization: previous sentence ended, capitalizing")

            if should_capitalize and text:
                # Find the first letter to capitalize (skip leading whitespace/punctuation)
                for i, char in enumerate(text):
                    if char.isalpha():
                        text = text[:i] + char.upper() + text[i+1:]
                        logger.info(f"Smart capitalization: capitalized first letter to '{text[:20]}'")
                        break

        # Track for undo
        self.last_inserted_text = text
        self.last_inserted_length = len(text)

        # Choose strategy
        if self.config.strategy == "clipboard":
            return clipboard.insert_via_clipboard(
                text,
                self.config.preserve_clipboard,
                self.xclip_available
            )
        elif self.config.strategy == "xtest":
            return xtest.insert_via_xtest(text, self.config.typing_delay_ms)
        else:
            logger.error(f"Unknown typing strategy: {self.config.strategy}")
            return False

    def insert_partial(self, new_text: str) -> bool:
        """Insert partial text incrementally (delta from previous partial).

        Args:
            new_text: New partial transcription

        Returns:
            True if successful
        """
        success, updated_text, updated_length = xtest.insert_partial(
            new_text,
            self.current_partial_text,
            self.config.typing_delay_ms
        )

        if success:
            self.current_partial_text = updated_text
            self.partial_typed_length = updated_length

        return success

    def finalize_partial(self, final_text: str) -> bool:
        """Finalize partial typing with the final transcription.

        Args:
            final_text: Final transcription

        Returns:
            True if successful
        """
        if not self.current_partial_text:
            # No partial was typed, just insert normally
            return self.insert_text(final_text)

        # If final matches current partial, we're done
        if final_text == self.current_partial_text:
            logger.debug("Final matches partial, no correction needed")
            self.last_inserted_text = final_text
            self.last_inserted_length = len(final_text)
            self._reset_partial_state()
            return True

        # Otherwise, correct the partial
        success = self.insert_partial(final_text)
        if success:
            self.last_inserted_text = final_text
            self.last_inserted_length = len(final_text)

        self._reset_partial_state()
        return success

    def _reset_partial_state(self) -> None:
        """Reset incremental typing state."""
        self.current_partial_text = ""
        self.partial_typed_length = 0

    def undo_last(self) -> bool:
        """Undo the last inserted text by simulating backspaces.

        Returns:
            True if successful
        """
        if not self.last_inserted_length:
            logger.info("No text to undo")
            return False

        # Try XLib first (preferred)
        if xtest.XLIB_AVAILABLE:
            success = xtest.undo_via_xlib(
                self.last_inserted_length,
                self.config.typing_delay_ms
            )
            if success:
                self.last_inserted_length = 0
                self.last_inserted_text = ""
                return True

        # Fall back to xdotool if available
        if self.xdotool_available:
            logger.info("Using xdotool for undo (XLib not available)")
            success = xtest.undo_via_xdotool(
                self.last_inserted_length,
                self.config.typing_delay_ms
            )
            if success:
                self.last_inserted_length = 0
                self.last_inserted_text = ""
                return True

        # Neither available - show one-time warning
        if not self.undo_warning_shown:
            self.undo_warning_shown = True
            logger.warning(
                "Undo not available: neither python-xlib nor xdotool found. "
                "Install python-xlib (pip install python-xlib) or xdotool (apt install xdotool) "
                "to enable undo functionality."
            )
            # Emit warning notification if callback is set
            if self.on_undo_unavailable:
                self.on_undo_unavailable()

        return False
