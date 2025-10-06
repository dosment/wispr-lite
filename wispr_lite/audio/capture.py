"""Audio capture using sounddevice (PortAudio).

Captures audio in fixed-size frames and feeds them to a queue for VAD and ASR processing.
"""

import queue
import threading
from typing import Optional, Callable, List
import numpy as np
import sounddevice as sd

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import AudioConfig

logger = get_logger(__name__)


class AudioCapture:
    """Manages audio input from the microphone."""

    def __init__(self, config: AudioConfig):
        """Initialize audio capture.

        Args:
            config: Audio configuration
        """
        self.config = config
        self.sample_rate = config.sample_rate
        self.channels = config.channels
        self.frame_duration_ms = config.frame_duration_ms
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)

        self.audio_queue: queue.Queue = queue.Queue()
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self._lock = threading.Lock()

        logger.info(f"AudioCapture initialized: {self.sample_rate}Hz, {self.channels}ch, {self.frame_duration_ms}ms frames")

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Callback for sounddevice stream.

        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Time info from PortAudio
            status: Status flags
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        if self.is_recording:
            # Convert to int16 and queue
            audio_data = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            try:
                self.audio_queue.put_nowait(audio_data)
            except queue.Full:
                logger.warning("Audio queue full, dropping frame")

    def start(self) -> None:
        """Start audio capture."""
        with self._lock:
            if self.is_recording:
                logger.warning("Audio capture already running")
                return

            try:
                device = self.config.device or sd.default.device[0]
                logger.info(f"Starting audio capture on device: {device}")

                self.stream = sd.InputStream(
                    device=device,
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    blocksize=self.frame_size,
                    dtype=np.float32,
                    callback=self._audio_callback
                )
                self.stream.start()
                self.is_recording = True
                logger.info("Audio capture started")

            except Exception as e:
                logger.error(f"Failed to start audio capture: {e}")
                raise

    def stop(self) -> None:
        """Stop audio capture."""
        with self._lock:
            if not self.is_recording:
                return

            self.is_recording = False

            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
                    logger.info("Audio capture stopped")
                except Exception as e:
                    logger.error(f"Error stopping audio stream: {e}")

            # Clear the queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break

    def get_frame(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """Get an audio frame from the queue.

        Args:
            timeout: Timeout in seconds, None for blocking

        Returns:
            Audio frame as bytes, or None if timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self) -> None:
        """Clear all pending audio frames."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    @staticmethod
    def list_devices() -> List[dict]:
        """List available audio input devices.

        Returns:
            List of device info dictionaries
        """
        devices = sd.query_devices()
        input_devices = []

        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'index': idx,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })

        return input_devices

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
