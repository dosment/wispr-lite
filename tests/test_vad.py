"""Tests for VAD module."""

import struct
import pytest
from wispr_lite.audio.vad import VAD, SilenceDetector
from wispr_lite.config.schema import AudioConfig


def test_vad_initialization():
    """Test VAD initialization."""
    config = AudioConfig()
    vad = VAD(config)

    assert vad.vad_mode == 3
    assert vad.sample_rate == 16000


def test_vad_energy_calculation():
    """Test energy calculation."""
    config = AudioConfig()
    vad = VAD(config)

    # Create a silent frame (all zeros)
    silent_frame = struct.pack(f"{320}h", *([0] * 320))
    energy_silent = vad._calculate_energy(silent_frame)

    # Create a loud frame
    loud_frame = struct.pack(f"{320}h", *([1000] * 320))
    energy_loud = vad._calculate_energy(loud_frame)

    assert energy_silent < energy_loud


def test_silence_detector():
    """Test silence detector."""
    detector = SilenceDetector(silence_timeout_ms=1000, frame_duration_ms=20)

    # Should not timeout immediately
    assert not detector.update(is_speech=False)

    # Simulate speech
    detector.update(is_speech=True)
    assert detector.silence_frame_count == 0

    # Simulate silence until timeout
    for _ in range(49):  # 49 frames of silence
        result = detector.update(is_speech=False)
        if result:
            break

    # Should eventually timeout
    assert detector.update(is_speech=False) is True


def test_silence_detector_reset():
    """Test silence detector reset."""
    detector = SilenceDetector(silence_timeout_ms=1000, frame_duration_ms=20)

    # Build up some silence
    for _ in range(10):
        detector.update(is_speech=False)

    assert detector.silence_frame_count > 0

    # Reset
    detector.reset()
    assert detector.silence_frame_count == 0
