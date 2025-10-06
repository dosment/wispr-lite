"""System tray icon using AppIndicator.

Provides quick access to controls and status display.
Dynamic icons for different states.
"""

import gi
from typing import Optional, Callable

try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
    APPINDICATOR_TYPE = "Ayatana"
except (ValueError, ImportError):
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator
        APPINDICATOR_TYPE = "AppIndicator3"
    except (ValueError, ImportError):
        AppIndicator = None
        APPINDICATOR_TYPE = None

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from wispr_lite.logging import get_logger
from wispr_lite import strings

logger = get_logger(__name__)


class TrayIcon:
    """System tray icon with menu."""

    def __init__(self):
        """Initialize tray icon."""
        if not AppIndicator:
            logger.error("AppIndicator not available, tray icon disabled")
            self.indicator = None
            return

        logger.info(f"Using {APPINDICATOR_TYPE} for tray icon")

        # Create indicator
        # Icon theme path - try user icons first, then bundled icons
        import os
        from pathlib import Path

        user_icon_path = Path.home() / ".local/share/icons/hicolor/scalable/apps"
        bundled_icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "icons"
        )

        # Use user icons if they exist, otherwise use bundled
        icon_path = str(user_icon_path) if user_icon_path.exists() else bundled_icon_path

        self.indicator = AppIndicator.Indicator.new(
            "wispr-lite",
            "wispr-lite-idle",
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_icon_theme_path(icon_path)
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        logger.info(f"Tray icon path set to: {icon_path}")

        # Create menu
        self.menu = Gtk.Menu()
        self._create_menu()
        self.indicator.set_menu(self.menu)

        # Callbacks (will be set by main app)
        self.on_toggle_listening: Optional[Callable] = None
        self.on_toggle_mode: Optional[Callable] = None
        self.on_mute: Optional[Callable] = None
        self.on_preferences: Optional[Callable] = None
        self.on_view_logs: Optional[Callable] = None
        self.on_undo: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None

        logger.info("TrayIcon initialized")

    def _create_menu(self) -> None:
        """Create the tray menu."""
        # Toggle listening
        self.toggle_item = Gtk.MenuItem(label=strings.TRAY_START_LISTENING)
        self.toggle_item.connect("activate", self._on_toggle_listening)
        self.toggle_item.get_accessible().set_name("Toggle Listening")
        self.toggle_item.get_accessible().set_description("Starts or stops voice dictation")
        self.menu.append(self.toggle_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Mode toggle
        self.mode_item = Gtk.MenuItem(label=strings.TRAY_MODE_DICTATION)
        self.mode_item.connect("activate", self._on_toggle_mode)
        self.mode_item.get_accessible().set_name("Toggle Mode")
        self.mode_item.get_accessible().set_description("Switches between dictation and command mode")
        self.menu.append(self.mode_item)

        # Mute
        self.mute_item = Gtk.MenuItem(label=strings.TRAY_MUTE_MICROPHONE)
        self.mute_item.connect("activate", self._on_mute)
        self.mute_item.get_accessible().set_name("Mute Microphone")
        self.mute_item.get_accessible().set_description("Toggles the microphone on or off")
        self.menu.append(self.mute_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Undo last dictation
        undo_item = Gtk.MenuItem(label=strings.TRAY_UNDO_LAST_DICTATION)
        undo_item.connect("activate", self._on_undo)
        undo_item.get_accessible().set_name("Undo Last Dictation")
        undo_item.get_accessible().set_description("Removes the last dictated text")
        self.menu.append(undo_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Preferences
        prefs_item = Gtk.MenuItem(label=strings.TRAY_PREFERENCES)
        prefs_item.connect("activate", self._on_preferences)
        prefs_item.get_accessible().set_name("Preferences")
        prefs_item.get_accessible().set_description("Opens the application settings window")
        self.menu.append(prefs_item)

        # View logs
        logs_item = Gtk.MenuItem(label=strings.TRAY_VIEW_LOGS)
        logs_item.connect("activate", self._on_view_logs)
        logs_item.get_accessible().set_name("View Logs")
        logs_item.get_accessible().set_description("Opens the application log file")
        self.menu.append(logs_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label=strings.TRAY_QUIT)
        quit_item.connect("activate", self._on_quit)
        quit_item.get_accessible().set_name("Quit")
        quit_item.get_accessible().set_description("Closes the application")
        self.menu.append(quit_item)

        self.menu.show_all()

    def _on_toggle_listening(self, _widget) -> None:
        """Handle toggle listening menu item."""
        if self.on_toggle_listening:
            self.on_toggle_listening()

    def _on_toggle_mode(self, _widget) -> None:
        """Handle toggle mode menu item."""
        if self.on_toggle_mode:
            self.on_toggle_mode()

    def _on_mute(self, _widget) -> None:
        """Handle mute menu item."""
        if self.on_mute:
            self.on_mute()

    def _on_preferences(self, _widget) -> None:
        """Handle preferences menu item."""
        if self.on_preferences:
            self.on_preferences()

    def _on_view_logs(self, _widget) -> None:
        """Handle view logs menu item."""
        if self.on_view_logs:
            self.on_view_logs()

    def _on_undo(self, _widget) -> None:
        """Handle undo menu item."""
        if self.on_undo:
            self.on_undo()

    def _on_quit(self, _widget) -> None:
        """Handle quit menu item."""
        if self.on_quit:
            self.on_quit()

    def set_state(self, state: str) -> None:
        """Update tray icon based on state.

        Args:
            state: State name (idle, listening, processing, muted, error)
        """
        if not self.indicator:
            return

        # Map state to icon name
        icon_name = f"wispr-lite-{state}"
        self.indicator.set_icon(icon_name)

        # Update menu items
        if state == "listening":
            self.toggle_item.set_label(strings.TRAY_STOP_LISTENING)
        else:
            self.toggle_item.set_label(strings.TRAY_START_LISTENING)

        logger.debug(f"Tray state: {state}")

    def set_mode(self, mode: str) -> None:
        """Update mode display.

        Args:
            mode: Mode name (dictation, command)
        """
        if mode == "dictation":
            self.mode_item.set_label(strings.TRAY_MODE_DICTATION)
        else:
            self.mode_item.set_label(strings.TRAY_MODE_COMMAND)

    def set_mute_label(self, is_unmuted: bool) -> None:
        """Update mute menu item label.

        Args:
            is_unmuted: True if microphone is unmuted (show "Mute"), False if muted (show "Unmute")
        """
        if is_unmuted:
            self.mute_item.set_label(strings.TRAY_MUTE_MICROPHONE)
        else:
            self.mute_item.set_label(strings.TRAY_UNMUTE_MICROPHONE)

    def set_tooltip(self, text: str) -> None:
        """Set the tray icon tooltip.

        Args:
            text: Tooltip text
        """
        if self.indicator:
            self.indicator.set_title(text)

    def show(self) -> None:
        """Show the tray icon."""
        if self.indicator:
            self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

    def hide(self) -> None:
        """Hide the tray icon."""
        if self.indicator:
            self.indicator.set_status(AppIndicator.IndicatorStatus.PASSIVE)
