"""Accessibility settings management.

Manages system accessibility features that may interfere with wispr-lite.
"""

import subprocess
from typing import Optional

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


class AccessibilityManager:
    """Manages accessibility settings for wispr-lite compatibility."""

    def __init__(self):
        """Initialize accessibility manager."""
        self.bounce_keys_original_state: Optional[bool] = None
        self.bounce_keys_managed = False

    def _get_bounce_keys_state(self) -> Optional[bool]:
        """Get current Bounce Keys state.

        Returns:
            True if enabled, False if disabled, None if unable to determine
        """
        try:
            result = subprocess.run(
                ['gsettings', 'get', 'org.cinnamon.desktop.a11y.keyboard', 'bouncekeys-enable'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                value = result.stdout.strip().lower()
                return value == 'true'
        except Exception as e:
            logger.debug(f"Could not get Bounce Keys state: {e}")
        return None

    def _set_bounce_keys_state(self, enabled: bool) -> bool:
        """Set Bounce Keys state.

        Args:
            enabled: True to enable, False to disable

        Returns:
            True if successful
        """
        try:
            value = 'true' if enabled else 'false'
            result = subprocess.run(
                ['gsettings', 'set', 'org.cinnamon.desktop.a11y.keyboard', 'bouncekeys-enable', value],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to set Bounce Keys state: {e}")
            return False

    def setup(self) -> None:
        """Setup accessibility settings for wispr-lite.

        Saves current state and temporarily disables Bounce Keys if enabled.
        """
        # Check if Bounce Keys is enabled
        current_state = self._get_bounce_keys_state()

        if current_state is None:
            logger.debug("Could not detect Bounce Keys state (may not be on Cinnamon)")
            return

        if current_state:
            logger.info("Bounce Keys is enabled - temporarily disabling for wispr-lite")
            self.bounce_keys_original_state = True

            if self._set_bounce_keys_state(False):
                self.bounce_keys_managed = True
                logger.info("Bounce Keys disabled successfully - will restore on exit")
            else:
                logger.warning("Failed to disable Bounce Keys - typing may have issues with double letters")
        else:
            logger.debug("Bounce Keys is already disabled")
            self.bounce_keys_original_state = False

    def restore(self) -> None:
        """Restore accessibility settings to original state."""
        if not self.bounce_keys_managed:
            return

        if self.bounce_keys_original_state:
            logger.info("Restoring Bounce Keys to original enabled state")
            if self._set_bounce_keys_state(True):
                logger.info("Bounce Keys restored successfully")
            else:
                logger.warning("Failed to restore Bounce Keys state")

        self.bounce_keys_managed = False
