"""Audio processing pipeline for Wispr-Lite.

Handles audio capture, VAD, silence detection, and transcription dispatch.
"""

import threading
import numpy as np

from gi.repository import GLib

from wispr_lite.logging import get_logger
from wispr_lite.audio.capture import AudioCapture
from wispr_lite.audio.vad import VAD, SilenceDetector
from wispr_lite.asr.engine import ASREngine

logger = get_logger(__name__)


class AudioPipeline:
    """Manages audio capture and transcription pipeline."""

    def __init__(
        self,
        audio_capture: AudioCapture,
        vad: VAD,
        silence_detector: SilenceDetector,
        asr_engine: ASREngine
    ):
        """Initialize audio pipeline.

        Args:
            audio_capture: Audio capture component
            vad: Voice activity detector
            silence_detector: Silence timeout detector
            asr_engine: ASR engine for transcription
        """
        self.audio_capture = audio_capture
        self.vad = vad
        self.silence_detector = silence_detector
        self.asr_engine = asr_engine

        # Processing state
        self.processing_thread = None
        self.stop_processing = threading.Event()
        self.audio_buffer = []

        # Callbacks
        self.on_state_change = None
        self.on_transcript = None
        self.on_partial_transcript = None
        self.on_insert_partial = None
        self.on_finalize_partial = None
        self.on_stop_listening = None
        self.on_worker_crash = None

    def start(self) -> None:
        """Start audio processing pipeline."""
        logger.info("Starting audio pipeline")
        self.audio_buffer.clear()
        self.silence_detector.reset()

        # Start audio capture
        self.audio_capture.start()

        # Start processing thread
        self.stop_processing.clear()
        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.processing_thread.start()

    def stop(self) -> None:
        """Stop audio processing pipeline."""
        logger.info("Stopping audio pipeline")

        # Stop audio capture
        self.audio_capture.stop()

        # Signal processing thread to stop
        self.stop_processing.set()

        # Wait for processing to complete
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)

    def _set_thread_priority(self) -> None:
        """Attempt to set higher priority for audio processing thread (best-effort)."""
        try:
            import os
            import sys

            # Try to increase thread priority (niceness)
            # Lower nice value = higher priority (range: -20 to 19)
            # We'll try -10 (moderately high priority) with fallback to 0
            current_nice = os.nice(0)  # Get current without changing
            target_nice = -10

            try:
                # Attempt to set nice value
                new_nice = os.nice(target_nice - current_nice)
                logger.info(f"Set process nice value to {new_nice} (audio processing priority increased)")
            except PermissionError:
                # Don't have permission for negative nice - that's OK
                logger.debug(f"Cannot set negative nice value (requires privileges), using default priority")
            except Exception as e:
                logger.debug(f"Failed to adjust process priority: {e}")

            # On Linux, also try setting real-time priority if we have the capability
            if sys.platform.startswith('linux'):
                try:
                    import resource
                    # Try to set RT priority policy for this thread
                    # This usually requires CAP_SYS_NICE capability
                    # We don't use os.sched_setscheduler because it's process-wide, not thread-specific
                    # and requires root. Just rely on nice for now.
                    pass
                except Exception as e:
                    logger.debug(f"RT scheduling not available: {e}")

        except Exception as e:
            logger.debug(f"Priority adjustment failed (continuing with default): {e}")

    def _process_audio(self) -> None:
        """Process audio frames in background thread with crash recovery."""
        # Attempt to increase thread priority for better audio latency
        self._set_thread_priority()

        try:
            while not self.stop_processing.is_set():
                # Get audio frame
                frame = self.audio_capture.get_frame(timeout=0.1)
                if not frame:
                    continue

                # VAD check
                is_speech = self.vad.is_speech(frame)

                if is_speech:
                    self.audio_buffer.append(frame)
                    self.silence_detector.reset()
                else:
                    # Check silence timeout (for toggle mode)
                    if self.silence_detector.update(False):
                        logger.info("Silence timeout reached")
                        if self.on_stop_listening:
                            GLib.idle_add(self.on_stop_listening)
                        break

            # Process accumulated audio
            if self.audio_buffer:
                if self.on_state_change:
                    GLib.idle_add(self.on_state_change, "processing")
                self._transcribe_and_output()

        except Exception as e:
            logger.error(f"Worker thread crashed: {e}", exc_info=True)
            if self.on_worker_crash:
                self.on_worker_crash()

    def _transcribe_and_output(self) -> None:
        """Transcribe accumulated audio and output text."""
        if not self.audio_buffer:
            return

        try:
            # Convert audio buffer to numpy array
            audio_bytes = b''.join(self.audio_buffer)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            logger.info(f"Transcribing {len(audio_array)} samples")

            # Delegate transcription to callback
            if self.on_transcript:
                self.on_transcript(audio_array)

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            if self.on_state_change:
                GLib.idle_add(self.on_state_change, "error")

        finally:
            self.audio_buffer.clear()
