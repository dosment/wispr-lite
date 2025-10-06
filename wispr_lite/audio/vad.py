"""Voice Activity Detection using webrtcvad with energy-based fallback."""

import struct
import math
from typing import Optional
import webrtcvad

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import AudioConfig

logger = get_logger(__name__)


class VAD:
    """Voice Activity Detector with webrtcvad and energy fallback."""

    def __init__(self, config: AudioConfig):
        """Initialize VAD.

        Args:
            config: Audio configuration
        """
        self.config = config
        self.sample_rate = config.sample_rate
        self.vad_mode = config.vad_mode
        self.frame_duration_ms = config.frame_duration_ms

        # Initialize webrtcvad
        self.vad = webrtcvad.Vad(self.vad_mode)

        # Energy-based fallback parameters
        self.energy_threshold = 500  # Adjustable threshold
        self.use_energy_fallback = True

        logger.info(f"VAD initialized: mode={self.vad_mode}, energy_fallback={self.use_energy_fallback}")

    def is_speech(self, frame: bytes) -> bool:
        """Determine if the audio frame contains speech.

        Args:
            frame: Raw audio frame (16-bit PCM)

        Returns:
            True if speech is detected, False otherwise
        """
        # Validate frame size
        expected_size = int(self.sample_rate * self.frame_duration_ms / 1000) * 2  # 2 bytes per sample
        if len(frame) != expected_size:
            logger.warning(f"Invalid frame size: {len(frame)} (expected {expected_size})")
            return False

        try:
            # Try webrtcvad first
            is_speech_webrtc = self.vad.is_speech(frame, self.sample_rate)

            # If using energy fallback, combine with energy detection
            if self.use_energy_fallback:
                energy = self._calculate_energy(frame)
                is_speech_energy = energy > self.energy_threshold

                # Return True if either detector says speech
                return is_speech_webrtc or is_speech_energy

            return is_speech_webrtc

        except Exception as e:
            logger.error(f"VAD error: {e}")
            # Fallback to energy-based detection
            if self.use_energy_fallback:
                energy = self._calculate_energy(frame)
                return energy > self.energy_threshold
            return False

    def _calculate_energy(self, frame: bytes) -> float:
        """Calculate the energy (RMS) of an audio frame.

        Args:
            frame: Raw audio frame (16-bit PCM)

        Returns:
            Energy level
        """
        # Convert bytes to list of 16-bit integers
        samples = struct.unpack(f"{len(frame) // 2}h", frame)

        # Calculate RMS
        sum_squares = sum(sample ** 2 for sample in samples)
        rms = math.sqrt(sum_squares / len(samples))

        return rms

    def set_energy_threshold(self, threshold: float) -> None:
        """Set the energy threshold for fallback detection.

        Args:
            threshold: Energy threshold
        """
        self.energy_threshold = threshold
        logger.info(f"Energy threshold set to {threshold}")

    def calibrate(self, silence_frames: list) -> None:
        """Calibrate the energy threshold based on silence samples.

        Args:
            silence_frames: List of audio frames representing silence
        """
        if not silence_frames:
            logger.warning("No silence frames provided for calibration")
            return

        energies = [self._calculate_energy(frame) for frame in silence_frames]
        avg_energy = sum(energies) / len(energies)
        max_energy = max(energies)

        # Set threshold above the max silence energy
        self.energy_threshold = max_energy * 2.0
        logger.info(f"Calibrated energy threshold to {self.energy_threshold} (avg silence: {avg_energy}, max: {max_energy})")


class SilenceDetector:
    """Detects periods of silence for auto-stopping in toggle mode."""

    def __init__(self, silence_timeout_ms: int, frame_duration_ms: int):
        """Initialize silence detector.

        Args:
            silence_timeout_ms: Silence duration before triggering
            frame_duration_ms: Duration of each audio frame
        """
        self.silence_timeout_ms = silence_timeout_ms
        self.frame_duration_ms = frame_duration_ms
        self.max_silence_frames = silence_timeout_ms // frame_duration_ms
        self.silence_frame_count = 0

    def update(self, is_speech: bool) -> bool:
        """Update silence detection state.

        Args:
            is_speech: Whether current frame contains speech

        Returns:
            True if silence timeout reached, False otherwise
        """
        if is_speech:
            self.silence_frame_count = 0
            return False
        else:
            self.silence_frame_count += 1
            return self.silence_frame_count >= self.max_silence_frames

    def reset(self) -> None:
        """Reset the silence counter."""
        self.silence_frame_count = 0
