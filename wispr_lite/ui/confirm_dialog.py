"""Confirmation dialog for risky operations."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


def show_confirmation_dialog(title: str, message: str, details: str = "") -> bool:
    """Show a confirmation dialog.

    Args:
        title: Dialog title
        message: Main message
        details: Optional detailed text

    Returns:
        True if user confirmed, False otherwise
    """
    dialog = Gtk.MessageDialog(
        transient_for=None,
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.YES_NO,
        text=title
    )

    dialog.format_secondary_text(message)

    if details:
        expander = Gtk.Expander(label="Show details")
        details_label = Gtk.Label(label=details)
        details_label.set_selectable(True)
        details_label.set_line_wrap(True)
        details_label.set_max_width_chars(60)
        expander.add(details_label)
        dialog.get_content_area().pack_end(expander, True, True, 0)
        dialog.show_all()

    response = dialog.run()
    dialog.destroy()

    return response == Gtk.ResponseType.YES
