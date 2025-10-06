"""Notification manager with anti-spam and DND support.

Implements rate limiting, deduplication, and desktop DND awareness.
"""

import time
from typing import Dict, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify, GLib
    NOTIFY_AVAILABLE = True
except (ImportError, ValueError) as e:
    NOTIFY_AVAILABLE = False

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import NotificationConfig

logger = get_logger(__name__)


class Severity(Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warn"
    ERROR = "error"
    PROGRESS = "progress"


@dataclass
class NotificationState:
    """State for a notification key."""
    last_shown: float = 0.0
    count: int = 0
    notification: Optional[object] = None  # Notify.Notification instance


class NotificationManager:
    """Manages desktop notifications with anti-spam features."""

    def __init__(
        self,
        config: NotificationConfig,
        action_callback: Optional[Callable[[str], None]] = None
    ):
        """Initialize notification manager.

        Args:
            config: Notification configuration
            action_callback: Optional callback for notification actions, receives action_id
        """
        self.config = config
        self.enabled = NOTIFY_AVAILABLE and config.enabled
        self.action_callback = action_callback

        if not NOTIFY_AVAILABLE:
            logger.warning("libnotify not available, notifications disabled")
            return

        # Initialize libnotify
        if not Notify.is_initted():
            Notify.init("Wispr-Lite")

        # State tracking
        self.states: Dict[str, NotificationState] = {}
        self.global_toast_times: List[float] = []

        logger.info(f"NotificationManager initialized (enabled={self.enabled})")

    def notify(
        self,
        event: str,
        severity: Severity = Severity.INFO,
        key: Optional[str] = None,
        text: str = "",
        progress: Optional[float] = None,
        actions: Optional[List[Tuple[str, str]]] = None
    ) -> None:
        """Send a notification with anti-spam controls.

        Args:
            event: Event name/title
            severity: Notification severity
            key: Deduplication key (defaults to event)
            text: Notification body
            progress: Progress value 0.0-1.0 for progress notifications
            actions: List of (action_id, label) tuples
        """
        if not self.enabled:
            return

        key = key or event

        # Check DND
        if self.config.respect_dnd and self._is_dnd_active():
            logger.debug(f"DND active, suppressing notification: {event}")
            return

        # Apply severity policy
        if not self._should_show_severity(severity):
            logger.debug(f"Severity {severity.value} disabled, skipping: {event}")
            return

        # Rate limiting (except for progress updates)
        if severity != Severity.PROGRESS:
            if not self._check_rate_limit(key):
                logger.debug(f"Rate limited: {key}")
                return

        # Show or update notification
        self._show_notification(event, text, severity, key, progress, actions)

    def _should_show_severity(self, severity: Severity) -> bool:
        """Check if notifications for this severity are enabled."""
        if severity == Severity.INFO:
            return self.config.show_info
        elif severity == Severity.WARNING:
            return self.config.show_warnings
        elif severity == Severity.ERROR:
            return self.config.show_errors
        elif severity == Severity.PROGRESS:
            return self.config.show_progress
        return True

    def _check_rate_limit(self, key: str) -> bool:
        """Check if notification passes rate limits."""
        now = time.time()

        # Global rate limit
        self.global_toast_times = [t for t in self.global_toast_times if now - t < 60]
        if len(self.global_toast_times) >= self.config.max_toasts_per_minute:
            return False

        # Per-key cooldown
        if key in self.states:
            last_shown = self.states[key].last_shown
            if now - last_shown < self.config.per_category_cooldown_sec:
                # Increment counter for coalescing
                self.states[key].count += 1
                return False

        return True

    def _show_notification(
        self,
        event: str,
        text: str,
        severity: Severity,
        key: str,
        progress: Optional[float],
        actions: Optional[List[Tuple[str, str]]]
    ) -> None:
        """Show or update a notification."""
        now = time.time()

        # Get or create state
        if key not in self.states:
            self.states[key] = NotificationState()

        state = self.states[key]

        # Add count suffix if coalesced
        title = event
        if state.count > 1:
            title = f"{event} (x{state.count})"

        # Determine urgency
        urgency = Notify.Urgency.NORMAL
        if severity == Severity.ERROR:
            urgency = Notify.Urgency.CRITICAL
        elif severity == Severity.INFO:
            urgency = Notify.Urgency.LOW

        try:
            # Create or update notification
            if state.notification is None:
                notification = Notify.Notification.new(title, text, "wispr-lite")
                state.notification = notification
            else:
                notification = state.notification
                notification.update(title, text, "wispr-lite")

            notification.set_urgency(urgency)

            # Add progress hint if provided
            if progress is not None:
                notification.set_hint("value", GLib.Variant.new_int32(int(progress * 100)))

            # Add actions if provided
            if actions:
                notification.clear_actions()
                for action_id, label in actions:
                    notification.add_action(action_id, label, self._on_action_clicked, None)

            notification.show()

            # Update state
            state.last_shown = now
            self.global_toast_times.append(now)

            # Reset count after showing
            if state.count > 1:
                logger.debug(f"Showed coalesced notification: {title}")
            state.count = 0

        except Exception as e:
            logger.error(f"Failed to show notification: {e}")

    def _on_action_clicked(self, notification, action_id, user_data):
        """Handle notification action clicks.

        Args:
            notification: The notification instance
            action_id: ID of the clicked action
            user_data: User data (unused)
        """
        logger.info(f"Notification action clicked: {action_id}")

        # Call the action callback if provided
        if self.action_callback:
            try:
                self.action_callback(action_id)
            except Exception as e:
                logger.error(f"Error handling notification action '{action_id}': {e}")

    def _is_dnd_active(self) -> bool:
        """Check if Do Not Disturb is active.

        Returns:
            True if DND is active (best effort detection)
        """
        try:
            import dbus
            bus = dbus.SessionBus()

            # Try Cinnamon notification settings
            try:
                proxy = bus.get_object(
                    'org.Cinnamon',
                    '/org/Cinnamon/Notification'
                )
                interface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
                dnd = interface.Get('org.Cinnamon.Notification', 'DoNotDisturb')
                return bool(dnd)
            except dbus.exceptions.DBusException:
                pass

            # Fallback: check FreeDesktop notifications inhibited property
            try:
                proxy = bus.get_object(
                    'org.freedesktop.Notifications',
                    '/org/freedesktop/Notifications'
                )
                interface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
                inhibited = interface.Get('org.freedesktop.Notifications', 'Inhibited')
                return bool(inhibited)
            except dbus.exceptions.DBusException:
                pass

        except Exception as e:
            logger.debug(f"DND detection failed: {e}")

        return False

    def clear_cooldowns(self) -> None:
        """Clear all rate limit cooldowns."""
        self.states.clear()
        self.global_toast_times.clear()
        logger.info("Cleared all notification cooldowns")

    def close_all(self) -> None:
        """Close all active notifications."""
        for state in self.states.values():
            if state.notification:
                try:
                    state.notification.close()
                except Exception as e:
                    logger.debug(f"Error closing notification: {e}")

        self.states.clear()

    def __del__(self):
        """Cleanup on destruction."""
        if NOTIFY_AVAILABLE and Notify.is_initted():
            self.close_all()
            Notify.uninit()
