"""D-Bus interface for external control.

Provides session bus API for CLI and external integrations.
"""

from typing import Optional, Callable

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    dbus = None

from wispr_lite.logging import get_logger

logger = get_logger(__name__)

BUS_NAME = "org.wispr_lite.Daemon"
OBJECT_PATH = "/org/wispr_lite/Daemon"


if DBUS_AVAILABLE:
    class WisprLiteDBusService(dbus.service.Object):
        """D-Bus service for Wispr-Lite."""

        def __init__(self):
            """Initialize D-Bus service."""
            DBusGMainLoop(set_as_default=True)

            try:
                bus = dbus.SessionBus()
                bus_name = dbus.service.BusName(BUS_NAME, bus)
                super().__init__(bus_name, OBJECT_PATH)

                # Callbacks (set by main app)
                self.on_toggle: Optional[Callable] = None
                self.on_start: Optional[Callable] = None
                self.on_stop: Optional[Callable] = None
                self.on_set_mode: Optional[Callable] = None
                self.on_open_preferences: Optional[Callable] = None
                self.on_undo: Optional[Callable] = None

                logger.info("D-Bus service initialized")

            except Exception as e:
                logger.error(f"Failed to initialize D-Bus service: {e}")
                raise

        @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
        def Toggle(self):
            """Toggle listening state."""
            if self.on_toggle:
                self.on_toggle()

        @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
        def Start(self):
            """Start listening."""
            if self.on_start:
                self.on_start()

        @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
        def Stop(self):
            """Stop listening."""
            if self.on_stop:
                self.on_stop()

        @dbus.service.method(BUS_NAME, in_signature='s', out_signature='')
        def SetMode(self, mode: str):
            """Set the dictation mode.

            Args:
                mode: Mode to set (dictation or command)
            """
            if self.on_set_mode:
                self.on_set_mode(mode)

        @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
        def OpenPreferences(self):
            """Open preferences window."""
            if self.on_open_preferences:
                self.on_open_preferences()

        @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
        def Undo(self):
            """Undo last dictation."""
            if self.on_undo:
                self.on_undo()

        @dbus.service.signal(BUS_NAME, signature='s')
        def StateChanged(self, state: str):
            """Signal emitted when state changes.

            Args:
                state: New state (idle, listening, processing, error)
            """
            pass

        @dbus.service.signal(BUS_NAME, signature='s')
        def Error(self, message: str):
            """Signal emitted on error.

            Args:
                message: Error message
            """
            pass


def create_dbus_service() -> Optional[object]:
    """Create D-Bus service if available.

    Returns:
        D-Bus service instance or None
    """
    if not DBUS_AVAILABLE:
        logger.warning("D-Bus not available, service disabled")
        return None

    try:
        return WisprLiteDBusService()
    except Exception as e:
        logger.error(f"Failed to create D-Bus service: {e}")
        return None
