"""Main application orchestration for Wispr-Lite.

Coordinates all components and manages application lifecycle.
"""

import sys
import signal
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from wispr_lite.logging import get_logger, set_log_level
from wispr_lite.config.schema import Config
from wispr_lite.audio.capture import AudioCapture
from wispr_lite.audio.vad import VAD, SilenceDetector
from wispr_lite.asr.engine import create_asr_engine
from wispr_lite.ui.overlay import OverlayWindow
from wispr_lite.ui.tray import TrayIcon
from wispr_lite.ui.preferences import PreferencesWindow
from wispr_lite.ui.notifications import NotificationManager, Severity
from wispr_lite.integration.typing import TextOutput
from wispr_lite.integration.hotkeys import HotkeyManager
from wispr_lite.integration.dbus import create_dbus_service
from wispr_lite.commands.registry import CommandRegistry
from wispr_lite.pipeline import AudioPipeline
from wispr_lite.model_ui import show_model_consent_dialog, notify_model_download_progress

logger = get_logger(__name__)


class WisprLiteApp:
    """Main application class."""

    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing Wispr-Lite...")

        # Check for Wayland and warn
        from wispr_lite.integration.cinnamon import is_wayland, get_wayland_limitations
        if is_wayland():
            logger.warning("Running on Wayland session - some features may be limited")
            limitations = get_wayland_limitations()
            for limit in limitations:
                logger.warning(f"  - {limit}")

        # Load configuration
        self.config = Config.load()
        set_log_level(getattr(__import__('logging'), self.config.log_level))

        # Application state
        self.is_listening = False
        self.is_muted = False
        self.current_state = "idle"

        # Initialize components
        audio_capture = AudioCapture(self.config.audio)
        vad = VAD(self.config.audio)
        silence_detector = SilenceDetector(
            self.config.audio.vad_silence_timeout_ms,
            self.config.audio.frame_duration_ms
        )
        self.notification_manager = NotificationManager(
            self.config.notifications,
            action_callback=self._on_notification_action
        )
        self.asr_engine = create_asr_engine(self.config.asr)

        # Wire up model download consent and progress callbacks
        self.asr_engine.on_consent_needed = self._on_model_consent_needed
        self.asr_engine.on_download_progress = self._on_model_download_progress

        self.text_output = TextOutput(self.config.typing)
        # Wire up undo unavailable warning callback
        self.text_output.on_undo_unavailable = self._on_undo_unavailable

        self.command_registry = CommandRegistry(self.config.commands)

        # Audio pipeline
        self.pipeline = AudioPipeline(audio_capture, vad, silence_detector, self.asr_engine)
        self.pipeline.on_state_change = self._update_state
        self.pipeline.on_transcript = self._handle_transcript
        self.pipeline.on_stop_listening = self.stop_listening
        self.pipeline.on_worker_crash = self._handle_worker_crash

        # Worker watchdog
        self.worker_crash_count = 0
        self.max_worker_restarts = 1

        # UI components
        self.overlay = OverlayWindow(self.config.ui)
        self.tray = TrayIcon()
        self.preferences = PreferencesWindow(self.config)

        # Hotkey manager
        self.hotkey_manager = HotkeyManager(self.config.hotkeys)

        # D-Bus service
        self.dbus_service = create_dbus_service()

        # Setup callbacks
        self._setup_callbacks()

        logger.info("Wispr-Lite initialized successfully")

    def _setup_callbacks(self) -> None:
        """Setup callbacks between components."""
        # Tray callbacks
        self.tray.on_toggle_listening = self.toggle_listening
        self.tray.on_toggle_mode = self.toggle_mode
        self.tray.on_mute = self.toggle_mute
        self.tray.on_preferences = self.open_preferences
        self.tray.on_view_logs = self.view_logs
        self.tray.on_undo = self.undo_last
        self.tray.on_quit = self.quit

        # Hotkey callbacks
        self.hotkey_manager.on_push_to_talk_press = self.start_listening
        self.hotkey_manager.on_push_to_talk_release = self.stop_listening
        self.hotkey_manager.on_toggle = self.toggle_listening
        self.hotkey_manager.on_undo = self.undo_last_dictation
        self.hotkey_manager.on_conflict_detected = self._on_hotkey_conflict

        # D-Bus callbacks
        if self.dbus_service:
            self.dbus_service.on_toggle = self.toggle_listening
            self.dbus_service.on_start = self.start_listening
            self.dbus_service.on_stop = self.stop_listening
            self.dbus_service.on_set_mode = self.set_mode
            self.dbus_service.on_open_preferences = self.open_preferences
            self.dbus_service.on_undo = self.undo_last

        # Preferences callback
        self.preferences.on_save = self.on_preferences_saved

    def start_listening(self) -> None:
        """Start listening for audio."""
        if self.is_listening:
            return

        if self.is_muted:
            logger.info("Cannot start listening: microphone is muted")
            return

        logger.info("Starting listening")
        self.is_listening = True

        # Reset crash counter on new session
        self.worker_crash_count = 0

        # Update UI
        GLib.idle_add(self._update_state, "listening")

        # Start pipeline
        self.pipeline.start()

    def stop_listening(self) -> None:
        """Stop listening and process final audio."""
        if not self.is_listening:
            return

        logger.info("Stopping listening")
        self.is_listening = False

        # Stop pipeline
        self.pipeline.stop()

        # Update UI
        GLib.idle_add(self._update_state, "idle")

    def toggle_listening(self) -> None:
        """Toggle listening state."""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def _handle_transcript(self, audio_array) -> None:
        """Handle transcription of audio array.

        Args:
            audio_array: Audio samples as numpy array
        """
        # Use streaming transcription if type-while-speaking is enabled
        if self.config.typing.type_while_speaking and self.config.mode == "dictation":
            final_text = ""
            for partial_text, is_final in self.asr_engine.transcribe_streaming(
                audio_array, self.config.audio.sample_rate
            ):
                # Update overlay with partial
                GLib.idle_add(self.overlay.set_transcript, partial_text)

                if is_final:
                    final_text = partial_text
                elif partial_text:
                    # Type partial incrementally (delta from previous)
                    self.text_output.insert_partial(partial_text)

            if final_text:
                logger.info(f"Transcribed: '{final_text}'")
                # Finalize with corrections if needed
                # (TextOutput tracks last_inserted_* internally)
                self.text_output.finalize_partial(final_text)

        else:
            # Standard non-streaming transcription
            text = self.asr_engine.transcribe(audio_array, self.config.audio.sample_rate)

            if text:
                logger.info(f"Transcribed: '{text}'")

                # Update overlay
                GLib.idle_add(self.overlay.set_transcript, text)

                # Output based on mode
                if self.config.mode == "dictation":
                    GLib.idle_add(self._output_dictation, text)
                elif self.config.mode == "command":
                    GLib.idle_add(self._execute_command, text)

    def _output_dictation(self, text: str) -> None:
        """Output dictated text.

        Args:
            text: Text to output
        """
        success = self.text_output.insert_text(text)
        if success:
            logger.info("Dictation delivered")
        else:
            logger.error("Dictation failed")
            self.notification_manager.notify(
                "Dictation Failed",
                Severity.ERROR,
                text="Failed to insert text"
            )

    def _execute_command(self, text: str) -> None:
        """Execute a voice command.

        Args:
            text: Command text
        """
        command = self.command_registry.match_command(text)

        if command:
            logger.info(f"Executing command: {command}")
            success = self.command_registry.execute_command(command)
            if not success:
                self.notification_manager.notify(
                    "Command Failed",
                    Severity.ERROR,
                    text="Command could not be executed"
                )
        else:
            logger.warning(f"No command matched: {text}")
            self.notification_manager.notify(
                "Unknown Command",
                Severity.WARNING,
                text="No matching command found"
            )

    def _handle_worker_crash(self) -> None:
        """Handle worker thread crash with restart logic."""
        self.worker_crash_count += 1

        if self.worker_crash_count <= self.max_worker_restarts:
            logger.warning(f"Restarting worker (attempt {self.worker_crash_count}/{self.max_worker_restarts})")

            # Show error notification
            GLib.idle_add(
                self.notification_manager.notify,
                "Worker Restarted",
                Severity.ERROR,
                "worker_crash",
                "Audio processing worker crashed and was restarted"
            )

            # Wait a bit before restarting
            import time
            time.sleep(1.0)

            # Restart if still listening
            if self.is_listening:
                self.pipeline.start()
        else:
            logger.error("Worker crash limit reached, stopping")
            GLib.idle_add(
                self.notification_manager.notify,
                "Worker Failed",
                Severity.ERROR,
                "worker_failed",
                "Audio processing has stopped after multiple crashes"
            )
            GLib.idle_add(self.stop_listening)

    def _on_model_consent_needed(self, model_size: str, consent_event: threading.Event, consent_result: list) -> None:
        """Handle model download consent request."""
        show_model_consent_dialog(model_size, consent_event, consent_result)

    def _on_model_download_progress(self, model_size: str, progress: float) -> None:
        """Handle model download progress updates."""
        notify_model_download_progress(self.notification_manager, model_size, progress)

    def _on_undo_unavailable(self) -> None:
        """Handle undo unavailable warning (one-time notification)."""
        GLib.idle_add(
            self.notification_manager.notify,
            "Undo Not Available",
            Severity.WARNING,
            "undo_unavailable",
            "Undo requires python-xlib or xdotool. Install one to enable undo:\n"
            "• pip install python-xlib\n"
            "• sudo apt install xdotool"
        )

    def _on_hotkey_conflict(self, message: str) -> None:
        """Handle hotkey conflict detection (one-time warning).

        Args:
            message: Conflict warning message
        """
        def show_notification():
            self.notification_manager.notify(
                "Hotkey Conflict Detected",
                Severity.WARNING,
                "hotkey_conflict",
                message,
                actions=[("open_prefs", "Open Preferences")]
            )

        # Show notification on main thread
        GLib.idle_add(show_notification)

    def _on_notification_action(self, action_id: str) -> None:
        """Handle notification action clicks.

        Args:
            action_id: ID of the clicked action
        """
        if action_id == "open_prefs":
            logger.info("Opening preferences from notification action")
            GLib.idle_add(self.open_preferences)
        else:
            logger.warning(f"Unknown notification action: {action_id}")

    def _update_state(self, state: str) -> None:
        """Update application state.

        Args:
            state: New state
        """
        self.current_state = state
        self.overlay.set_state(state)
        self.tray.set_state(state)

        if state == "listening":
            self.overlay.show_overlay()
        elif state == "idle":
            self.overlay.hide_overlay()

        # Emit D-Bus signal
        if self.dbus_service:
            self.dbus_service.StateChanged(state)

    def toggle_mode(self) -> None:
        """Toggle between dictation and command mode."""
        if self.config.mode == "dictation":
            self.config.mode = "command"
        else:
            self.config.mode = "dictation"

        self.tray.set_mode(self.config.mode)
        self.config.save()
        logger.info(f"Mode changed to: {self.config.mode}")

    def set_mode(self, mode: str) -> None:
        """Set the application mode.

        Args:
            mode: Mode to set
        """
        if mode in ("dictation", "command"):
            self.config.mode = mode
            self.tray.set_mode(mode)
            self.config.save()
            logger.info(f"Mode set to: {mode}")

    def toggle_mute(self) -> None:
        """Toggle microphone mute."""
        self.is_muted = not self.is_muted

        if self.is_muted:
            logger.info("Microphone muted")
            # Stop listening if currently active
            if self.is_listening:
                self.stop_listening()
            # Update tray to show muted state
            GLib.idle_add(self._update_state, "muted")
            # Update mute menu item label
            GLib.idle_add(self.tray.set_mute_label, False)  # False = show "Unmute"
        else:
            logger.info("Microphone unmuted")
            # Restore to idle state
            GLib.idle_add(self._update_state, "idle")
            # Update mute menu item label
            GLib.idle_add(self.tray.set_mute_label, True)  # True = show "Mute"

    def undo_last(self) -> None:
        """Undo last dictation."""
        success = self.text_output.undo_last()
        if success:
            logger.info("Undid last dictation")
        else:
            logger.warning("No dictation to undo")

    def undo_last_dictation(self) -> None:
        """Undo last dictation (alias for hotkey)."""
        self.undo_last()

    def open_preferences(self) -> None:
        """Open preferences window."""
        logger.info("Opening preferences window")
        self.preferences.show_all()
        self.preferences.present()  # Bring window to front and give focus
        logger.info(f"Preferences window shown, visible: {self.preferences.get_visible()}, realized: {self.preferences.get_realized()}")

    def on_preferences_saved(self) -> None:
        """Handle preferences saved event."""
        logger.info("Preferences saved, reloading configuration")

        # Store old model size to detect changes
        old_model_size = self.asr_engine.config.model_size

        # Reload config from file
        self.config = Config.load()

        # Update text_output config so smart_spacing and other settings take effect
        self.text_output.config = self.config.typing

        # Update ASR engine config to reflect new settings
        self.asr_engine.config = self.config.asr

        # If model size changed, unload the old model so new one can be loaded
        if self.config.asr.model_size != old_model_size:
            logger.info(f"Model size changed from {old_model_size} to {self.config.asr.model_size}, unloading old model")
            self.asr_engine.unload()

        logger.info("Configuration reloaded - changes will take effect on next dictation")

    def view_logs(self) -> None:
        """Open log file in default text editor."""
        import subprocess
        from wispr_lite.logging import get_log_dir

        log_file = get_log_dir() / 'wispr-lite.log'
        try:
            subprocess.Popen(['xdg-open', str(log_file)])
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")

    def run(self) -> None:
        """Run the application."""
        logger.info("Starting Wispr-Lite")

        # Check Wayland and show notice to user
        from wispr_lite.integration.cinnamon import is_wayland, get_wayland_limitations
        if is_wayland():
            limitations_text = "\n".join(f"• {limit}" for limit in get_wayland_limitations())
            self.notification_manager.notify(
                "Wayland Session Detected",
                Severity.WARNING,
                key="wayland_notice",
                text=f"Some features may be limited:\n{limitations_text}"
            )
            # Force clipboard strategy on Wayland
            if self.config.typing.strategy == "xtest":
                logger.warning("Forcing clipboard strategy on Wayland")
                self.config.typing.strategy = "clipboard"

        # Start hotkey listener (may not work on Wayland)
        try:
            self.hotkey_manager.start()
        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
            logger.info("Use --toggle via CLI or configure Cinnamon custom shortcuts")

        # Show tray icon
        self.tray.show()

        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda *args: self.quit())
        signal.signal(signal.SIGTERM, lambda *args: self.quit())

        # Run GTK main loop
        Gtk.main()

    def quit(self) -> None:
        """Quit the application."""
        logger.info("Shutting down Wispr-Lite")

        # Stop listening
        if self.is_listening:
            self.stop_listening()

        # Stop hotkey listener
        self.hotkey_manager.stop()

        # Unload ASR model
        self.asr_engine.unload()

        # Close notifications
        self.notification_manager.close_all()

        # Quit GTK
        Gtk.main_quit()
