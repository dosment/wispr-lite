"""Preferences window for configuration.

Provides UI for editing settings without manual YAML editing.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Optional, Callable

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import Config
from wispr_lite import strings

logger = get_logger(__name__)


class PreferencesWindow(Gtk.Window):
    """Preferences dialog for Wispr-Lite settings."""

    def __init__(self, config: Config):
        """Initialize preferences window.

        Args:
            config: Current configuration
        """
        super().__init__(title=strings.PREFS_TITLE)

        self.config = config
        self.on_save: Optional[Callable] = None

        self.set_default_size(600, 500)
        self.set_border_width(10)

        # Create notebook with tabs
        notebook = Gtk.Notebook()

        # Add tabs
        notebook.append_page(self._create_general_tab(), Gtk.Label(label=strings.PREFS_GENERAL))
        notebook.append_page(self._create_audio_tab(), Gtk.Label(label=strings.PREFS_AUDIO))
        notebook.append_page(self._create_asr_tab(), Gtk.Label(label=strings.PREFS_ASR))
        notebook.append_page(self._create_typing_tab(), Gtk.Label(label=strings.PREFS_TYPING))
        notebook.append_page(self._create_hotkeys_tab(), Gtk.Label(label=strings.PREFS_HOTKEYS))
        notebook.append_page(self._create_notifications_tab(), Gtk.Label(label=strings.PREFS_NOTIFICATIONS))

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label=strings.PREFS_CANCEL)
        cancel_btn.connect("clicked", lambda _: self.hide())
        cancel_btn.get_accessible().set_name("Cancel")
        cancel_btn.get_accessible().set_description("Close the preferences window without saving changes")
        button_box.pack_start(cancel_btn, False, False, 0)

        save_btn = Gtk.Button(label=strings.PREFS_SAVE)
        save_btn.connect("clicked", self._on_save_clicked)
        save_btn.get_accessible().set_name("Save")
        save_btn.get_accessible().set_description("Save the current settings and close the window")
        button_box.pack_start(save_btn, False, False, 0)

        # Main layout (vertical box with notebook and buttons)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.pack_start(notebook, True, True, 0)
        main_box.pack_start(button_box, False, False, 0)

        self.add(main_box)

        logger.info("PreferencesWindow initialized")

    def _create_general_tab(self) -> Gtk.Widget:
        """Create the General settings tab."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Mode
        grid.attach(Gtk.Label(label=strings.PREFS_GENERAL_MODE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("dictation")
        self.mode_combo.append_text("command")
        self.mode_combo.set_active(0 if self.config.mode == "dictation" else 1)
        self.mode_combo.set_tooltip_text("Dictation: Types transcribed speech into focused window\nCommand: Executes voice commands (open apps, URLs, etc.)")
        self.mode_combo.get_accessible().set_name("Application Mode")
        self.mode_combo.get_accessible().set_description("Switch between dictation and command mode")
        grid.attach(self.mode_combo, 1, row, 1, 1)
        row += 1

        # Autostart
        self.autostart_check = Gtk.CheckButton(label=strings.PREFS_GENERAL_AUTOSTART)
        self.autostart_check.set_active(self.config.autostart)
        self.autostart_check.set_tooltip_text("Launch Wispr-Lite automatically when you log in to your desktop session")
        self.autostart_check.get_accessible().set_name("Autostart")
        self.autostart_check.get_accessible().set_description("Start Wispr-Lite automatically when you log in")
        grid.attach(self.autostart_check, 0, row, 2, 1)
        row += 1

        # Log level
        grid.attach(Gtk.Label(label=strings.PREFS_GENERAL_LOG_LEVEL, halign=Gtk.Align.START), 0, row, 1, 1)
        self.log_level_combo = Gtk.ComboBoxText()
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            self.log_level_combo.append_text(level)
        self.log_level_combo.set_active(["DEBUG", "INFO", "WARNING", "ERROR"].index(self.config.log_level))
        self.log_level_combo.set_tooltip_text("DEBUG: Detailed logs for troubleshooting\nINFO: Normal operation logs\nWARNING: Important warnings only\nERROR: Errors only")
        self.log_level_combo.get_accessible().set_name("Log Level")
        self.log_level_combo.get_accessible().set_description("Set the logging verbosity for troubleshooting")
        grid.attach(self.log_level_combo, 1, row, 1, 1)

        return grid

    def _create_audio_tab(self) -> Gtk.Widget:
        """Create the Audio settings tab."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Audio device selection
        grid.attach(Gtk.Label(label=strings.PREFS_AUDIO_INPUT_DEVICE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.device_combo = Gtk.ComboBoxText()
        self._populate_audio_devices()
        self.device_combo.set_tooltip_text("Select which microphone to use for recording.\n'System Default' uses your OS default input device.")
        # Accessibility
        self.device_combo.get_accessible().set_name("Input Device")
        self.device_combo.get_accessible().set_description("Select audio input device for voice recording")
        grid.attach(self.device_combo, 1, row, 1, 1)
        row += 1

        # Input level meter
        grid.attach(Gtk.Label(label=strings.PREFS_AUDIO_INPUT_LEVEL, halign=Gtk.Align.START), 0, row, 1, 1)
        self.level_meter = Gtk.LevelBar()
        self.level_meter.set_mode(Gtk.LevelBarMode.CONTINUOUS)
        self.level_meter.set_min_value(0.0)
        self.level_meter.set_max_value(1.0)
        self.level_meter.set_value(0.0)
        self.level_meter.set_hexpand(True)
        self.level_meter.set_tooltip_text("Real-time display of microphone input volume.\nSpeak to see the meter move.\n\nRecommended: Set system microphone level to 30-35% for best quality.\nToo high = distortion/noise, too low = poor recognition.")
        # Accessibility
        self.level_meter.get_accessible().set_name("Input Level Meter")
        self.level_meter.get_accessible().set_description("Real-time microphone input level indicator")
        grid.attach(self.level_meter, 1, row, 1, 1)
        row += 1

        # Sample rate
        grid.attach(Gtk.Label(label=strings.PREFS_AUDIO_SAMPLE_RATE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.sample_rate_spin = Gtk.SpinButton()
        self.sample_rate_spin.set_range(8000, 48000)
        self.sample_rate_spin.set_increments(1000, 8000)
        self.sample_rate_spin.set_value(self.config.audio.sample_rate)
        self.sample_rate_spin.set_tooltip_text("Audio sampling rate in Hz. 16000 Hz is recommended for Whisper.\nHigher rates use more memory but may improve quality slightly.")
        self.sample_rate_spin.get_accessible().set_name("Sample Rate")
        self.sample_rate_spin.get_accessible().set_description("Audio sample rate in Hz")
        grid.attach(self.sample_rate_spin, 1, row, 1, 1)
        row += 1

        # VAD mode
        grid.attach(Gtk.Label(label=strings.PREFS_AUDIO_VAD_AGGRESSIVENESS, halign=Gtk.Align.START), 0, row, 1, 1)
        self.vad_mode_spin = Gtk.SpinButton()
        self.vad_mode_spin.set_range(0, 3)
        self.vad_mode_spin.set_increments(1, 1)
        self.vad_mode_spin.set_value(self.config.audio.vad_mode)
        self.vad_mode_spin.set_tooltip_text("Voice Activity Detection sensitivity (0-3):\n0: Least aggressive (more false positives)\n3: Most aggressive (filters background noise)\nDefault: 3")
        self.vad_mode_spin.get_accessible().set_name("VAD Aggressiveness")
        self.vad_mode_spin.get_accessible().set_description("Voice Activity Detection aggressiveness (0-3)")
        grid.attach(self.vad_mode_spin, 1, row, 1, 1)
        row += 1

        # Silence timeout
        grid.attach(Gtk.Label(label=strings.PREFS_AUDIO_SILENCE_TIMEOUT, halign=Gtk.Align.START), 0, row, 1, 1)
        self.silence_timeout_spin = Gtk.SpinButton()
        self.silence_timeout_spin.set_range(500, 5000)
        self.silence_timeout_spin.set_increments(100, 500)
        self.silence_timeout_spin.set_value(self.config.audio.vad_silence_timeout_ms)
        self.silence_timeout_spin.set_tooltip_text("How long to wait (in milliseconds) after you stop speaking\nbefore automatically ending recording and transcribing.\nRecommended: 2000-3000ms (2-3 seconds)")
        self.silence_timeout_spin.get_accessible().set_name("Silence Timeout")
        self.silence_timeout_spin.get_accessible().set_description("Silence duration in milliseconds to end recording")
        grid.attach(self.silence_timeout_spin, 1, row, 1, 1)

        # Start input level monitoring
        self._start_level_monitoring()

        return grid

    def _populate_audio_devices(self) -> None:
        """Populate the audio device dropdown."""
        from wispr_lite.audio.capture import AudioCapture

        self.device_combo.append("auto", "System Default")
        devices = AudioCapture.list_devices()

        for device in devices:
            device_id = str(device['index'])
            device_name = f"{device['name']} ({device['channels']}ch)"
            self.device_combo.append(device_id, device_name)

        # Set current selection
        if self.config.audio.device is None:
            self.device_combo.set_active_id("auto")
        else:
            self.device_combo.set_active_id(str(self.config.audio.device))

    def _start_level_monitoring(self) -> None:
        """Start monitoring audio input level."""
        import sounddevice as sd
        import numpy as np
        from gi.repository import GLib

        def update_level():
            try:
                # Record a short sample
                device = self.config.audio.device
                duration = 0.05  # 50ms
                data = sd.rec(
                    int(duration * self.config.audio.sample_rate),
                    samplerate=self.config.audio.sample_rate,
                    channels=1,
                    device=device,
                    blocking=True
                )
                # Calculate RMS level
                rms = np.sqrt(np.mean(data**2))
                # Update level meter on main thread
                GLib.idle_add(self.level_meter.set_value, min(rms * 10, 1.0))
                return True  # Continue monitoring
            except Exception as e:
                logger.debug(f"Level monitoring error: {e}")
                return False

        # Update every 100ms
        GLib.timeout_add(100, update_level)

    def _create_asr_tab(self) -> Gtk.Widget:
        """Create the ASR settings tab."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Model size
        grid.attach(Gtk.Label(label=strings.PREFS_ASR_MODEL_SIZE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.model_size_combo = Gtk.ComboBoxText()
        for size in ["tiny", "base", "small", "medium", "large"]:
            self.model_size_combo.append_text(size)
        self.model_size_combo.set_active(["tiny", "base", "small", "medium", "large"].index(self.config.asr.model_size))
        self.model_size_combo.set_tooltip_text("Whisper model accuracy vs speed tradeoff:\ntiny (~75MB): Fastest, least accurate - not recommended\nbase (~145MB): Fast but may miss punctuation\nsmall (~466MB): Better accuracy and punctuation\nmedium (~1.5GB): Recommended - very accurate with good punctuation\nlarge (~2.9GB): Best accuracy, but very slow\n\nNote: Larger models provide better punctuation and capitalization.")
        self.model_size_combo.get_accessible().set_name("Whisper Model Size")
        self.model_size_combo.get_accessible().set_description("Select the Whisper model size. Larger models are more accurate but slower.")
        grid.attach(self.model_size_combo, 1, row, 1, 1)
        row += 1

        # Device
        grid.attach(Gtk.Label(label=strings.PREFS_ASR_DEVICE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.asr_device_combo = Gtk.ComboBoxText()
        for device in ["auto", "cpu", "cuda"]:
            self.asr_device_combo.append_text(device)
        self.asr_device_combo.set_active(["auto", "cpu", "cuda"].index(self.config.asr.device))
        self.asr_device_combo.get_accessible().set_name("ASR Device")
        self.asr_device_combo.get_accessible().set_description("Select the device for ASR processing. 'auto' will use GPU if available.")
        grid.attach(self.asr_device_combo, 1, row, 1, 1)
        row += 1

        # Language
        grid.attach(Gtk.Label(label=strings.PREFS_ASR_LANGUAGE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.language_combo = Gtk.ComboBoxText()

        # Add common languages with codes
        languages = [
            ("auto", "Auto-detect"),
            ("en", "English"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("ru", "Russian"),
            ("zh", "Chinese"),
            ("ja", "Japanese"),
            ("ko", "Korean"),
            ("ar", "Arabic"),
            ("hi", "Hindi"),
            ("nl", "Dutch"),
            ("pl", "Polish"),
            ("tr", "Turkish"),
        ]

        for code, name in languages:
            self.language_combo.append(code, name)

        # Set current selection
        current_lang = self.config.asr.language or "auto"
        self.language_combo.set_active_id(current_lang)

        self.language_combo.set_tooltip_text("Language for transcription. Auto-detect will identify the language automatically.\nFor best accuracy, select your specific language.")
        self.language_combo.get_accessible().set_name("Language")
        self.language_combo.get_accessible().set_description("Select the language for transcription. Auto-detect identifies language automatically.")
        grid.attach(self.language_combo, 1, row, 1, 1)

        return grid

    def _create_typing_tab(self) -> Gtk.Widget:
        """Create the Typing settings tab."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Strategy
        grid.attach(Gtk.Label(label=strings.PREFS_TYPING_STRATEGY, halign=Gtk.Align.START), 0, row, 1, 1)
        self.strategy_combo = Gtk.ComboBoxText()
        self.strategy_combo.append_text("clipboard")
        self.strategy_combo.append_text("xtest")
        self.strategy_combo.set_active(0 if self.config.typing.strategy == "clipboard" else 1)
        # Accessibility
        self.strategy_combo.get_accessible().set_name("Typing Strategy")
        self.strategy_combo.get_accessible().set_description("Method for inserting transcribed text")
        grid.attach(self.strategy_combo, 1, row, 1, 1)
        row += 1

        # Preserve clipboard
        self.preserve_clipboard_check = Gtk.CheckButton(label=strings.PREFS_TYPING_PRESERVE_CLIPBOARD)
        self.preserve_clipboard_check.set_active(self.config.typing.preserve_clipboard)
        # Accessibility
        self.preserve_clipboard_check.get_accessible().set_name("Preserve Clipboard")
        self.preserve_clipboard_check.get_accessible().set_description("Restore clipboard contents after dictation")
        grid.attach(self.preserve_clipboard_check, 0, row, 2, 1)
        row += 1

        # Smart spacing
        self.smart_spacing_check = Gtk.CheckButton(label=strings.PREFS_TYPING_SMART_SPACING)
        self.smart_spacing_check.set_active(self.config.typing.smart_spacing)
        self.smart_spacing_check.get_accessible().set_name("Smart Spacing")
        self.smart_spacing_check.get_accessible().set_description("Automatically add a space before dictated text if needed")
        grid.attach(self.smart_spacing_check, 0, row, 2, 1)
        row += 1

        # Type while speaking (experimental)
        self.type_while_speaking_check = Gtk.CheckButton(
            label=strings.PREFS_TYPING_TYPE_WHILE_SPEAKING
        )
        self.type_while_speaking_check.set_active(self.config.typing.type_while_speaking)
        self.type_while_speaking_check.get_accessible().set_name("Type While Speaking")
        self.type_while_speaking_check.get_accessible().set_description("Show partial transcription results in real-time. Experimental.")
        grid.attach(self.type_while_speaking_check, 0, row, 2, 1)

        return grid

    def _create_hotkeys_tab(self) -> Gtk.Widget:
        """Create the Hotkeys settings tab."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Push to talk
        grid.attach(Gtk.Label(label=strings.PREFS_HOTKEYS_PUSH_TO_TALK, halign=Gtk.Align.START), 0, row, 1, 1)
        self.ptt_entry = Gtk.Entry()
        self.ptt_entry.set_text(self.config.hotkeys.push_to_talk)
        self.ptt_entry.get_accessible().set_name("Push to Talk Hotkey")
        self.ptt_entry.get_accessible().set_description("Press and hold this key to record audio")
        grid.attach(self.ptt_entry, 1, row, 1, 1)
        row += 1

        # Toggle
        grid.attach(Gtk.Label(label=strings.PREFS_HOTKEYS_TOGGLE, halign=Gtk.Align.START), 0, row, 1, 1)
        self.toggle_entry = Gtk.Entry()
        self.toggle_entry.set_text(self.config.hotkeys.toggle)
        self.toggle_entry.get_accessible().set_name("Toggle Recording Hotkey")
        self.toggle_entry.get_accessible().set_description("Press this key to start or stop recording")
        grid.attach(self.toggle_entry, 1, row, 1, 1)
        row += 1

        # Undo
        grid.attach(Gtk.Label(label=strings.PREFS_HOTKEYS_UNDO_LAST, halign=Gtk.Align.START), 0, row, 1, 1)
        self.undo_entry = Gtk.Entry()
        self.undo_entry.set_text(self.config.hotkeys.undo_last)
        self.undo_entry.get_accessible().set_name("Undo Last Hotkey")
        self.undo_entry.get_accessible().set_description("Press this key to undo the last dictation")
        grid.attach(self.undo_entry, 1, row, 1, 1)

        return grid

    def _create_notifications_tab(self) -> Gtk.Widget:
        """Create the Notifications settings tab."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_border_width(10)

        row = 0

        # Enable notifications
        self.notifications_enabled_check = Gtk.CheckButton(label=strings.PREFS_NOTIFICATIONS_ENABLE)
        self.notifications_enabled_check.set_active(self.config.notifications.enabled)
        self.notifications_enabled_check.get_accessible().set_name("Enable Notifications")
        self.notifications_enabled_check.get_accessible().set_description("Enable or disable all application notifications")
        grid.attach(self.notifications_enabled_check, 0, row, 2, 1)
        row += 1

        # Respect DND
        self.respect_dnd_check = Gtk.CheckButton(label=strings.PREFS_NOTIFICATIONS_RESPECT_DND)
        self.respect_dnd_check.set_active(self.config.notifications.respect_dnd)
        self.respect_dnd_check.get_accessible().set_name("Respect Do Not Disturb")
        self.respect_dnd_check.get_accessible().set_description("Prevent notifications from appearing when Do Not Disturb is active")
        grid.attach(self.respect_dnd_check, 0, row, 2, 1)
        row += 1

        # Show warnings
        self.show_warnings_check = Gtk.CheckButton(label=strings.PREFS_NOTIFICATIONS_SHOW_WARNINGS)
        self.show_warnings_check.set_active(self.config.notifications.show_warnings)
        self.show_warnings_check.get_accessible().set_name("Show Warnings")
        self.show_warnings_check.get_accessible().set_description("Show notifications for non-critical warnings")
        grid.attach(self.show_warnings_check, 0, row, 2, 1)
        row += 1

        # Show errors
        self.show_errors_check = Gtk.CheckButton(label=strings.PREFS_NOTIFICATIONS_SHOW_ERRORS)
        self.show_errors_check.set_active(self.config.notifications.show_errors)
        self.show_errors_check.get_accessible().set_name("Show Errors")
        self.show_errors_check.get_accessible().set_description("Show notifications for critical errors")
        grid.attach(self.show_errors_check, 0, row, 2, 1)

        return grid

    def _on_save_clicked(self, _widget) -> None:
        """Handle save button click."""
        # Update config from UI
        self.config.mode = self.mode_combo.get_active_text()
        self.config.autostart = self.autostart_check.get_active()
        self.config.log_level = self.log_level_combo.get_active_text()

        # Audio device
        device_id = self.device_combo.get_active_id()
        self.config.audio.device = None if device_id == "auto" else int(device_id)

        self.config.audio.sample_rate = int(self.sample_rate_spin.get_value())
        self.config.audio.vad_mode = int(self.vad_mode_spin.get_value())
        self.config.audio.vad_silence_timeout_ms = int(self.silence_timeout_spin.get_value())

        self.config.asr.model_size = self.model_size_combo.get_active_text()
        self.config.asr.device = self.asr_device_combo.get_active_text()
        lang_code = self.language_combo.get_active_id()
        self.config.asr.language = None if lang_code == "auto" else lang_code

        self.config.typing.strategy = self.strategy_combo.get_active_text()
        self.config.typing.preserve_clipboard = self.preserve_clipboard_check.get_active()
        self.config.typing.smart_spacing = self.smart_spacing_check.get_active()
        self.config.typing.type_while_speaking = self.type_while_speaking_check.get_active()

        self.config.hotkeys.push_to_talk = self.ptt_entry.get_text()
        self.config.hotkeys.toggle = self.toggle_entry.get_text()
        self.config.hotkeys.undo_last = self.undo_entry.get_text()

        self.config.notifications.enabled = self.notifications_enabled_check.get_active()
        self.config.notifications.respect_dnd = self.respect_dnd_check.get_active()
        self.config.notifications.show_warnings = self.show_warnings_check.get_active()
        self.config.notifications.show_errors = self.show_errors_check.get_active()

        # Save to file
        self.config.save()

        # Notify callback
        if self.on_save:
            self.on_save()

        self.hide()
        logger.info("Configuration saved")