"""Configuration schema for Wispr-Lite using dataclasses."""

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    push_to_talk: str = "ctrl+super"
    toggle: str = "ctrl+shift+super"
    command_mode: str = ""
    undo_last: str = "ctrl+shift+z"


@dataclass
class AudioConfig:
    """Audio capture configuration."""
    device: Optional[str] = None  # None = default device
    sample_rate: int = 16000
    channels: int = 1
    frame_duration_ms: int = 20
    vad_mode: int = 3  # webrtcvad aggressiveness (0-3)
    vad_silence_timeout_ms: int = 3000


@dataclass
class ASRConfig:
    """ASR engine configuration."""
    backend: str = "faster-whisper"
    model_size: str = "base"  # tiny, base, small, medium, large
    language: Optional[str] = None  # None = auto-detect
    compute_type: str = "auto"  # auto, int8, float16, etc.
    device: str = "auto"  # auto, cpu, cuda
    beam_size: int = 5
    best_of: int = 5


@dataclass
class TypingConfig:
    """Text output configuration."""
    strategy: str = "clipboard"  # clipboard or xtest
    preserve_clipboard: bool = True
    typing_delay_ms: int = 10  # for XTest
    smart_spacing: bool = True
    smart_capitalization: bool = True
    type_while_speaking: bool = False  # Type partial results in real-time


@dataclass
class NotificationConfig:
    """Notification behavior configuration."""
    enabled: bool = True
    respect_dnd: bool = True
    show_info: bool = False
    show_warnings: bool = True
    show_errors: bool = True
    show_progress: bool = True
    max_toasts_per_minute: int = 3
    per_category_cooldown_sec: int = 10
    enable_sounds: bool = False
    sound_volume: float = 0.5


@dataclass
class UIConfig:
    """UI preferences."""
    show_overlay: bool = True
    overlay_transparency: float = 0.9
    theme: str = "auto"  # auto, light, dark


@dataclass
class CommandConfig:
    """Command mode configuration."""
    enabled: bool = True
    prefix: str = "cmd:"
    require_confirmation: bool = True
    commands: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    """Main configuration."""
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    typing: TypingConfig = field(default_factory=TypingConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    commands: CommandConfig = field(default_factory=CommandConfig)

    mode: str = "dictation"  # dictation or command
    autostart: bool = False
    log_level: str = "INFO"

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the config file path."""
        config_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'wispr-lite'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.yaml'

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file, or create default if not found."""
        config_path = cls.get_config_path()

        if not config_path.exists():
            logger.info(f"Config not found at {config_path}, creating default")
            config = cls()
            config.save()
            return config

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # Nested dataclass deserialization
            hotkeys = HotkeyConfig(**data.get('hotkeys', {}))
            audio = AudioConfig(**data.get('audio', {}))
            asr = ASRConfig(**data.get('asr', {}))
            typing = TypingConfig(**data.get('typing', {}))
            notifications = NotificationConfig(**data.get('notifications', {}))
            ui = UIConfig(**data.get('ui', {}))
            commands = CommandConfig(**data.get('commands', {}))

            config = cls(
                hotkeys=hotkeys,
                audio=audio,
                asr=asr,
                typing=typing,
                notifications=notifications,
                ui=ui,
                commands=commands,
                mode=data.get('mode', 'dictation'),
                autostart=data.get('autostart', False),
                log_level=data.get('log_level', 'INFO')
            )

            logger.info(f"Loaded config from {config_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return cls()

    def save(self) -> None:
        """Save configuration to file."""
        config_path = self.get_config_path()

        try:
            data = asdict(self)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved config to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
