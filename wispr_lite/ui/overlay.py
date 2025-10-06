from gi.repository import Gtk, Gdk, GLib

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import UIConfig
from wispr_lite import strings

logger = get_logger(__name__)


class OverlayWindow(Gtk.Window):
    """Transparent overlay window for dictation feedback."""

    def __init__(self, config: UIConfig):
        """Initialize overlay window.

        Args:
            config: UI configuration
        """
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.config = config

        # Window setup
        self.set_title("Wispr-Lite Overlay")
        self.set_default_size(400, 150)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.set_accept_focus(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Enable transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Apply CSS for styling
        self._apply_css()

        # Create UI
        self._create_ui()

        # Start hidden
        self.hide()

        logger.info("OverlayWindow initialized")

    def _apply_css(self) -> None:
        """Apply CSS styling to the window."""
        css_provider = Gtk.CssProvider()
        css = f"""
        .overlay-window {{
            background-color: rgba(0, 0, 0, {self.config.overlay_transparency});
            border-radius: 12px;
        }}
        .overlay-label {{
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 20px;
        }}
        .overlay-transcript {{
            color: #e0e0e0;
            font-size: 14px;
            padding: 10px 20px;
        }}
        .state-idle {{
            color: #888888;
        }}
        .state-listening {{
            color: #4CAF50;
        }}
        .state-processing {{
            color: #FFC107;
        }}
        .state-error {{
            color: #F44336;
        }}
        """

        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _create_ui(self) -> None:
        """Create the overlay UI components."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.get_style_context().add_class("overlay-window")

        # State label
        self.state_label = Gtk.Label()
        self.state_label.set_markup(f"<span size='large' weight='bold'>{strings.OVERLAY_IDLE}</span>")
        self.state_label.get_style_context().add_class("overlay-label")
        self.state_label.get_style_context().add_class("state-idle")
        # Accessibility
        self.state_label.get_accessible().set_name("Recording State")
        self.state_label.get_accessible().set_description("Current voice recording state")
        main_box.pack_start(self.state_label, False, False, 0)

        # Transcript label
        self.transcript_label = Gtk.Label()
        self.transcript_label.set_line_wrap(True)
        self.transcript_label.set_max_width_chars(50)
        self.transcript_label.set_text("")
        self.transcript_label.get_style_context().add_class("overlay-transcript")
        # Accessibility
        self.transcript_label.get_accessible().set_name("Transcription")
        self.transcript_label.get_accessible().set_description("Real-time voice transcription text")
        main_box.pack_start(self.transcript_label, True, True, 0)

        # Window accessibility
        self.get_accessible().set_name("Wispr-Lite Voice Recording Overlay")
        self.get_accessible().set_description("Shows current recording state and transcribed text")

        self.add(main_box)

    def set_state(self, state: str) -> None:
        """Set the overlay state.

        Args:
            state: State name (idle, listening, processing, error)
        """
        # Update label text
        state_text = {
            "idle": strings.OVERLAY_IDLE,
            "listening": strings.OVERLAY_LISTENING,
            "processing": strings.OVERLAY_PROCESSING,
            "error": strings.OVERLAY_ERROR
        }.get(state, state.capitalize())

        self.state_label.set_markup(f"<span size='large' weight='bold'>{state_text}</span>")

        # Update CSS class
        context = self.state_label.get_style_context()
        for cls in ["state-idle", "state-listening", "state-processing", "state-error"]:
            context.remove_class(cls)
        context.add_class(f"state-{state}")

        logger.debug(f"Overlay state: {state}")

    def set_transcript(self, text: str) -> None:
        """Set the transcript text.

        Args:
            text: Transcript text to display
        """
        self.transcript_label.set_text(text)

    def show_overlay(self) -> None:
        """Show the overlay window."""
        if self.config.show_overlay:
            self.show_all()
            logger.debug("Overlay shown")

    def hide_overlay(self) -> None:
        """Hide the overlay window."""
        self.hide()
        logger.debug("Overlay hidden")

    def flash_message(self, message: str, duration_ms: int = 2000) -> None:
        """Flash a temporary message on the overlay.

        Args:
            message: Message to display
            duration_ms: Duration in milliseconds
        """
        if not self.config.show_overlay:
            return

        # Save current state
        current_state = self.state_label.get_text()
        current_transcript = self.transcript_label.get_text()

        # Show message
        self.set_state("idle")
        self.set_transcript(message)
        self.show_overlay()

        # Restore after duration
        def restore():
            self.set_transcript(current_transcript)
            if not current_state or current_state == "Idle":
                self.hide_overlay()
            return False

        GLib.timeout_add(duration_ms, restore)
