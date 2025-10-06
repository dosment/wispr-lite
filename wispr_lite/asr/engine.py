"""ASR engine interface and factory."""

from abc import ABC, abstractmethod
from typing import Optional, Iterator, Tuple
import numpy as np

from wispr_lite.config.schema import ASRConfig


class ASREngine(ABC):
    """Abstract base class for ASR backends."""

    @abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    def transcribe_streaming(
        self, audio: np.ndarray, sample_rate: int
    ) -> Iterator[Tuple[str, bool]]:
        """Transcribe audio with streaming partial results.

        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Yields:
            Tuples of (text, is_final)
        """
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model to free resources."""
        pass


def create_asr_engine(config: ASRConfig) -> ASREngine:
    """Factory function to create an ASR engine based on config.

    Args:
        config: ASR configuration

    Returns:
        ASR engine instance

    Raises:
        ValueError: If backend is not supported
    """
    if config.backend == "faster-whisper":
        from wispr_lite.asr.faster_whisper_backend import FasterWhisperBackend
        return FasterWhisperBackend(config)
    else:
        raise ValueError(f"Unsupported ASR backend: {config.backend}")
