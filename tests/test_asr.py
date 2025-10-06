"""Tests for ASR backend consent and download callbacks."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from wispr_lite.asr.faster_whisper_backend import FasterWhisperBackend
from wispr_lite.config.schema import ASRConfig


def test_consent_callback_granted():
    """Test model consent callback when user grants consent."""
    config = ASRConfig()
    config.model_size = "tiny"

    backend = FasterWhisperBackend(config)

    # Mock _model_exists to return False (model not available)
    with patch.object(backend, '_model_exists', return_value=False):
        # Set up consent callback that grants consent (new API: (model, event, result_list))
        calls = []

        def consent_callback(model_size, event, result_list):
            calls.append(model_size)
            result_list[0] = True
            event.set()

        backend.on_consent_needed = consent_callback

        # Mock WhisperModel to avoid actual model loading
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], Mock(language='en'))

        with patch('wispr_lite.asr.faster_whisper_backend.WhisperModel', return_value=mock_model):
            # Trigger model load by calling transcribe
            audio = np.zeros(16000, dtype=np.float32)
            backend.transcribe(audio, 16000)

            # Verify consent callback was called with correct model size
            assert calls == ["tiny"]


def test_consent_callback_denied():
    """Test model consent callback when user denies consent."""
    config = ASRConfig()
    config.model_size = "base"

    backend = FasterWhisperBackend(config)

    # Mock _model_exists to return False (model not available)
    with patch.object(backend, '_model_exists', return_value=False):
        # Set up consent callback that denies consent (new API)
        def consent_callback(model_size, event, result_list):
            result_list[0] = False
            event.set()

        backend.on_consent_needed = consent_callback

        # Trigger model load by calling transcribe
        audio = np.zeros(16000, dtype=np.float32)

        # Should raise RuntimeError when consent is denied
        with pytest.raises(RuntimeError) as exc_info:
            backend.transcribe(audio, 16000)

        # Verify error message mentions offline preload
        assert "preload_models.sh" in str(exc_info.value)
        assert "base" in str(exc_info.value)

        # Confirm denied path triggered by checking exception message above


def test_consent_callback_not_called_when_model_exists():
    """Test consent callback is not called when model already exists."""
    config = ASRConfig()
    config.model_size = "tiny"

    backend = FasterWhisperBackend(config)

    # Mock _model_exists to return True (model already available)
    with patch.object(backend, '_model_exists', return_value=True):
        # Set up consent callback (should not be called)
        calls = []

        def consent_callback(model_size, event, result_list):
            calls.append(model_size)
            result_list[0] = True
            event.set()

        backend.on_consent_needed = consent_callback

        # Mock WhisperModel to avoid actual model loading
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], Mock(language='en'))

        with patch('wispr_lite.asr.faster_whisper_backend.WhisperModel', return_value=mock_model):
            # Trigger model load
            audio = np.zeros(16000, dtype=np.float32)
            backend.transcribe(audio, 16000)

            # Consent callback should NOT be called when model exists
            assert calls == []


def test_download_progress_callbacks():
    """Test download progress callbacks are called appropriately."""
    config = ASRConfig()
    config.model_size = "tiny"

    backend = FasterWhisperBackend(config)

    # Mock _model_exists to return False (model needs download)
    with patch.object(backend, '_model_exists', return_value=False):
        # Set up callbacks
        progress_callback = Mock()

        def consent_callback(model_size, event, result_list):
            result_list[0] = True
            event.set()

        backend.on_consent_needed = consent_callback
        backend.on_download_progress = progress_callback

        # Mock WhisperModel
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], Mock(language='en'))

        with patch('wispr_lite.asr.faster_whisper_backend.WhisperModel', return_value=mock_model):
            # Trigger model load
            audio = np.zeros(16000, dtype=np.float32)
            backend.transcribe(audio, 16000)

            # Progress callback should be called at start (0.0) and end (1.0)
            assert progress_callback.call_count == 2

            # First call should be with 0.0 (start)
            first_call = progress_callback.call_args_list[0]
            assert first_call[0] == ("tiny", 0.0)

            # Second call should be with 1.0 (complete)
            second_call = progress_callback.call_args_list[1]
            assert second_call[0] == ("tiny", 1.0)


def test_download_progress_on_error():
    """Test download progress callback with -1.0 on error."""
    config = ASRConfig()
    config.model_size = "tiny"

    backend = FasterWhisperBackend(config)

    # Mock _model_exists to return False
    with patch.object(backend, '_model_exists', return_value=False):
        # Set up callbacks
        progress_callback = Mock()

        def consent_callback(model_size, event, result_list):
            result_list[0] = True
            event.set()

        backend.on_consent_needed = consent_callback
        backend.on_download_progress = progress_callback

        # Mock WhisperModel to raise an error
        with patch('wispr_lite.asr.faster_whisper_backend.WhisperModel', side_effect=RuntimeError("Download failed")):
            # Trigger model load
            audio = np.zeros(16000, dtype=np.float32)

            with pytest.raises(RuntimeError):
                backend.transcribe(audio, 16000)

            # Progress callback should be called with -1.0 on error
            error_call_found = any(
                call[0] == ("tiny", -1.0)
                for call in progress_callback.call_args_list
            )
            assert error_call_found, "Progress callback should be called with -1.0 on error"
