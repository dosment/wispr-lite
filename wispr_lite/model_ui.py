"""Model download UI interactions.

Handles consent dialogs and progress notifications for model downloads.
"""

import threading
from gi.repository import GLib

from wispr_lite.logging import get_logger
from wispr_lite.ui.confirm_dialog import show_confirmation_dialog
from wispr_lite.ui.notifications import NotificationManager, Severity

logger = get_logger(__name__)


def get_model_size_mb(model_size: str) -> str:
    """Get approximate model download size in MB."""
    sizes = {
        "tiny": "75",
        "base": "145",
        "small": "466",
        "medium": "1.5GB",
        "large": "2.9GB"
    }
    return sizes.get(model_size, "unknown")


def show_model_consent_dialog(
    model_size: str,
    consent_event: threading.Event,
    consent_result: list
) -> None:
    """Show model download consent dialog on GTK main thread.

    Args:
        model_size: Model size being requested
        consent_event: Event to set when the user responds
        consent_result: A list to store the boolean result
    """
    logger.info(f"Requesting consent to download model: {model_size}")

    def show_dialog():
        try:
            result = show_confirmation_dialog(
                "Model Download Required",
                f"The Whisper '{model_size}' model needs to be downloaded (~{get_model_size_mb(model_size)}MB).\n\n"
                "Download now? (You can also pre-download models offline using 'scripts/preload_models.sh')",
                f"Model will be cached in ~/.cache/wispr-lite/models/\n"
                f"This is a one-time download per model size."
            )
            consent_result[0] = result
            logger.info(f"Model download consent: {'granted' if result else 'denied'}")
        finally:
            consent_event.set()  # Signal the waiting thread

    GLib.idle_add(show_dialog)


def notify_model_download_progress(
    notification_manager: NotificationManager,
    model_size: str,
    progress: float
) -> None:
    """Show model download progress notification.

    Args:
        notification_manager: Notification manager instance
        model_size: Model size being downloaded
        progress: Progress value (0.0-1.0, or -1.0 for error)
    """
    if progress < 0:
        # Download failed
        GLib.idle_add(
            notification_manager.notify,
            "Model Download Failed",
            Severity.ERROR,
            "model_download",
            f"Failed to download model '{model_size}'"
        )
    elif progress == 0.0:
        # Download started
        GLib.idle_add(
            notification_manager.notify,
            "Downloading Model",
            Severity.PROGRESS,
            "model_download",
            f"Downloading Whisper '{model_size}' model...",
            0.0
        )
    elif progress == 1.0:
        # Download complete
        GLib.idle_add(
            notification_manager.notify,
            "Model Ready",
            Severity.PROGRESS,
            "model_download",
            f"Model '{model_size}' downloaded successfully",
            1.0
        )
    else:
        # Progress update
        GLib.idle_add(
            notification_manager.notify,
            "Downloading Model",
            Severity.PROGRESS,
            "model_download",
            f"Downloading Whisper '{model_size}' model...",
            progress
        )
