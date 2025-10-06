"""Faster-Whisper ASR backend using CTranslate2."""

import os
import threading
from pathlib import Path
from typing import Optional, Iterator, Tuple, Callable
import numpy as np
from faster_whisper import WhisperModel

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import ASRConfig
from wispr_lite.asr.engine import ASREngine

logger = get_logger(__name__)


class FasterWhisperBackend(ASREngine):
    """ASR backend using faster-whisper (CTranslate2)."""

    def __init__(self, config: ASRConfig):
        """Initialize faster-whisper backend.

        Args:
            config: ASR configuration
        """
        self.config = config
        self.model: Optional[WhisperModel] = None
        self.model_loaded = False

        # Callbacks for consent and progress
        self.on_consent_needed: Optional[Callable[[str, threading.Event, list], None]] = None
        self.on_download_progress: Optional[Callable[[str, float], None]] = None

        # Determine cache directory
        self.cache_dir = Path(
            os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')
        ) / 'wispr-lite' / 'models'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"FasterWhisperBackend initialized: model={config.model_size}, device={config.device}")

    def _model_exists(self) -> bool:
        """Check if the model is already downloaded."""
        model_path = self.cache_dir / f"models--Systran--faster-whisper-{self.config.model_size}"
        # Also check alternate naming
        alt_path = self.cache_dir / self.config.model_size
        return model_path.exists() or alt_path.exists()

    def _load_model(self) -> None:
        """Load the Whisper model lazily."""
        if self.model_loaded:
            return

        try:
            # Check if model needs to be downloaded
            needs_download = not self._model_exists()

            if needs_download:
                logger.info(f"Model {self.config.model_size} not found locally, download required")

                # Request consent using threading.Event
                if self.on_consent_needed:
                    consent_event = threading.Event()
                    consent_result = [False]  # Use a list to pass by reference
                    self.on_consent_needed(self.config.model_size, consent_event, consent_result)
                    consent_event.wait()  # Block until the user responds

                    if not consent_result[0]:
                        logger.warning("Model download consent denied by user")
                        raise RuntimeError(
                            f"Model '{self.config.model_size}' not available locally. "
                            "Please run 'scripts/preload_models.sh' to download models offline, "
                            "or grant download permission when prompted."
                        )

                # Notify download start
                if self.on_download_progress:
                    self.on_download_progress(self.config.model_size, 0.0)

            logger.info(f"Loading faster-whisper model: {self.config.model_size}")

            # Determine device and compute type
            device = self.config.device
            if device == "auto":
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"

            compute_type = self.config.compute_type
            if compute_type == "auto":
                compute_type = "int8_float16" if device == "cuda" else "int8"

            logger.info(f"Using device={device}, compute_type={compute_type}")

            self.model = WhisperModel(
                self.config.model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(self.cache_dir),
            )

            # Notify download complete (if it was downloading)
            if needs_download and self.on_download_progress:
                self.on_download_progress(self.config.model_size, 1.0)

            self.model_loaded = True
            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Notify download failed
            if self.on_download_progress:
                self.on_download_progress(self.config.model_size, -1.0)
            raise

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32)
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text
        """
        self._load_model()

        try:
            # Ensure audio is float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / 32768.0

            segments, info = self.model.transcribe(
                audio,
                language=self.config.language,
                beam_size=self.config.beam_size,
                best_of=self.config.best_of,
                vad_filter=False,  # We handle VAD separately
            )

            # Combine all segments
            text = " ".join(segment.text.strip() for segment in segments)

            logger.debug(f"Transcribed: '{text}' (language: {info.language})")
            return text.strip()

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def transcribe_streaming(
        self, audio: np.ndarray, sample_rate: int
    ) -> Iterator[Tuple[str, bool]]:
        """Transcribe audio with streaming partial results.

        Args:
            audio: Audio data as numpy array (float32)
            sample_rate: Sample rate in Hz

        Yields:
            Tuples of (text, is_final)
        """
        self._load_model()

        try:
            # Ensure audio is float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / 32768.0

            segments, info = self.model.transcribe(
                audio,
                language=self.config.language,
                beam_size=self.config.beam_size,
                best_of=self.config.best_of,
                vad_filter=False,
            )

            # Yield each segment as it's processed
            texts = []
            for segment in segments:
                texts.append(segment.text.strip())
                current_text = " ".join(texts)
                yield (current_text, False)  # Partial result

            # Final result
            final_text = " ".join(texts).strip()
            yield (final_text, True)

        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            yield ("", True)

    def unload(self) -> None:
        """Unload the model to free resources."""
        if self.model is not None:
            logger.info("Unloading model")
            del self.model
            self.model = None
            self.model_loaded = False

            # Force garbage collection
            import gc
            gc.collect()

    def get_model_path(self) -> Path:
        """Get the path where the model is cached.

        Returns:
            Path to model cache directory
        """
        return self.cache_dir / self.config.model_size
