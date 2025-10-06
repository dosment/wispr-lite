"""Tests for configuration module."""

import tempfile
import os
from pathlib import Path

import pytest
from wispr_lite.config.schema import Config, HotkeyConfig, AudioConfig, ASRConfig


def test_config_defaults():
    """Test default configuration values."""
    config = Config()

    assert config.mode == "dictation"
    assert config.autostart is False
    assert config.log_level == "INFO"


def test_hotkey_config_defaults():
    """Test default hotkey configuration."""
    hotkeys = HotkeyConfig()

    assert hotkeys.push_to_talk == "ctrl+space"
    assert hotkeys.toggle == "ctrl+shift+space"
    assert hotkeys.undo_last == "ctrl+shift+z"


def test_audio_config_defaults():
    """Test default audio configuration."""
    audio = AudioConfig()

    assert audio.sample_rate == 16000
    assert audio.channels == 1
    assert audio.vad_mode == 3


def test_asr_config_defaults():
    """Test default ASR configuration."""
    asr = ASRConfig()

    assert asr.backend == "faster-whisper"
    assert asr.model_size == "base"
    assert asr.device == "auto"


def test_config_to_dict():
    """Test configuration conversion to dictionary."""
    config = Config()
    config_dict = config.to_dict()

    assert isinstance(config_dict, dict)
    assert "hotkeys" in config_dict
    assert "audio" in config_dict
    assert "asr" in config_dict


def test_config_save_load(tmp_path, monkeypatch):
    """Test configuration save and load."""
    # Patch the config path
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    def mock_get_config_path():
        return config_dir / "config.yaml"

    monkeypatch.setattr(Config, 'get_config_path', staticmethod(mock_get_config_path))

    # Create and save config
    config1 = Config()
    config1.mode = "command"
    config1.autostart = True
    config1.save()

    # Load config
    config2 = Config.load()

    assert config2.mode == "command"
    assert config2.autostart is True
