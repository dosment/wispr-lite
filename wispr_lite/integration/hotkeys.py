"""Global hotkey registration using pynput.

Provides cross-platform hotkey support for push-to-talk and toggle modes.
"""

import threading
from typing import Optional, Callable, Set
from pynput import keyboard

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import HotkeyConfig

logger = get_logger(__name__)


class HotkeyManager:
    """Manages global hotkey registration and callbacks."""

    def __init__(self, config: HotkeyConfig):
        """Initialize hotkey manager.

        Args:
            config: Hotkey configuration
        """
        self.config = config
        self.listener: Optional[keyboard.Listener] = None
        self.currently_pressed: Set[keyboard.Key] = set()

        # Conflict detection
        self.on_conflict_detected: Optional[Callable[[str], None]] = None
        self.hotkey_test_passed = False
        self.conflict_warning_shown = False

        # Callbacks
        self.on_push_to_talk_press: Optional[Callable] = None
        self.on_push_to_talk_release: Optional[Callable] = None
        self.on_toggle: Optional[Callable] = None
        self.on_undo: Optional[Callable] = None

        # Parse hotkey strings to key combinations
        self.ptt_keys = self._parse_hotkey(config.push_to_talk)
        self.toggle_keys = self._parse_hotkey(config.toggle)
        self.undo_keys = self._parse_hotkey(config.undo_last) if config.undo_last else set()

        logger.info(f"HotkeyManager initialized: PTT={config.push_to_talk}, Toggle={config.toggle}")

    def _parse_hotkey(self, hotkey_str: str) -> Set[keyboard.Key]:
        """Parse a hotkey string into a set of keys.

        Args:
            hotkey_str: Hotkey string (e.g., "ctrl+space")

        Returns:
            Set of keyboard.Key objects
        """
        if not hotkey_str:
            return set()

        keys = set()
        parts = hotkey_str.lower().split('+')

        for part in parts:
            part = part.strip()

            # Map common modifiers
            if part in ('ctrl', 'control'):
                keys.add(keyboard.Key.ctrl_l)
            elif part in ('shift',):
                keys.add(keyboard.Key.shift_l)
            elif part in ('alt',):
                keys.add(keyboard.Key.alt_l)
            elif part in ('super', 'win', 'cmd'):
                keys.add(keyboard.Key.cmd)
            elif part == 'space':
                keys.add(keyboard.Key.space)
            elif len(part) == 1:
                # Single character
                try:
                    keys.add(keyboard.KeyCode.from_char(part))
                except Exception as e:
                    logger.warning(f"Failed to parse key '{part}': {e}")

        return keys

    def _keys_match(self, target_keys: Set[keyboard.Key]) -> bool:
        """Check if currently pressed keys match target.

        Args:
            target_keys: Target key combination

        Returns:
            True if keys match
        """
        if not target_keys:
            return False

        # Normalize the currently pressed keys
        normalized_pressed = set()
        for key in self.currently_pressed:
            if isinstance(key, keyboard.Key):
                # Handle left/right variants of modifiers
                if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    normalized_pressed.add(keyboard.Key.ctrl_l)
                elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
                    normalized_pressed.add(keyboard.Key.shift_l)
                elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
                    normalized_pressed.add(keyboard.Key.alt_l)
                elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                    # Normalize Super/Windows/Command key variants (all three: cmd, cmd_l, cmd_r)
                    normalized_pressed.add(keyboard.Key.cmd)
                else:
                    normalized_pressed.add(key)
            else:
                normalized_pressed.add(key)

        return normalized_pressed == target_keys

    def _on_press(self, key) -> None:
        """Handle key press event.

        Args:
            key: Key that was pressed
        """
        self.currently_pressed.add(key)

        # Check for hotkey matches
        if self._keys_match(self.ptt_keys):
            self.mark_hotkey_working()  # Mark as working on first use
            if self.on_push_to_talk_press:
                self.on_push_to_talk_press()

        elif self._keys_match(self.toggle_keys):
            self.mark_hotkey_working()  # Mark as working on first use
            if self.on_toggle:
                self.on_toggle()
            # Clear pressed keys to avoid repeated triggers
            self.currently_pressed.clear()

        elif self.undo_keys and self._keys_match(self.undo_keys):
            self.mark_hotkey_working()  # Mark as working on first use
            if self.on_undo:
                self.on_undo()
            self.currently_pressed.clear()

    def _on_release(self, key) -> None:
        """Handle key release event.

        Args:
            key: Key that was released
        """
        if key in self.currently_pressed:
            self.currently_pressed.remove(key)

        # Check if PTT hotkey was released
        if self.ptt_keys and not self._keys_match(self.ptt_keys):
            # At least one PTT key was released
            if self.on_push_to_talk_release:
                # Only trigger if we had all PTT keys pressed before
                self.on_push_to_talk_release()

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self.listener is not None:
            logger.warning("Hotkey listener already running")
            return

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            logger.info("Hotkey listener started")

            # Check for common conflicts after a short delay
            if not self.conflict_warning_shown:
                threading.Timer(2.0, self._check_for_conflicts).start()

        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
            # Notify about failure
            if self.on_conflict_detected and not self.conflict_warning_shown:
                self.conflict_warning_shown = True
                self.on_conflict_detected(
                    "Failed to start hotkey listener. This may be due to permission issues "
                    "or conflicts with other applications."
                )
            raise

    def _check_for_conflicts(self) -> None:
        """Check for common hotkey conflicts and warn if detected."""
        if self.conflict_warning_shown or self.hotkey_test_passed:
            return

        # Check if listener is still running
        if not self.listener or not self.listener.running:
            logger.warning("Hotkey listener stopped unexpectedly - possible conflict")
            if self.on_conflict_detected:
                self.conflict_warning_shown = True
                self.on_conflict_detected(
                    "Hotkey listener stopped unexpectedly. Your hotkeys may not work. "
                    "Check for conflicts with other applications."
                )
            return

        # Check for known problematic hotkey combinations
        problematic_combos = [
            ("ctrl+space", "Input method switchers (ibus, fcitx) often use Ctrl+Space"),
            ("ctrl+shift+space", "Some desktop environments reserve this combination"),
            ("super+space", "Desktop environment app launchers often use Super+Space"),
        ]

        for combo_str, reason in problematic_combos:
            if (self.config.push_to_talk == combo_str or
                self.config.toggle == combo_str):
                logger.warning(f"Potential hotkey conflict: {combo_str} - {reason}")
                if self.on_conflict_detected:
                    self.conflict_warning_shown = True
                    self.on_conflict_detected(
                        f"Your hotkey '{combo_str}' may conflict with system shortcuts.\n\n"
                        f"{reason}\n\n"
                        "If hotkeys don't work, try changing them in Preferences."
                    )
                    return

    def mark_hotkey_working(self) -> None:
        """Mark hotkeys as working (called when first successful activation)."""
        self.hotkey_test_passed = True

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self.listener is not None:
            self.listener.stop()
            self.listener = None
            self.currently_pressed.clear()
            logger.info("Hotkey listener stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
