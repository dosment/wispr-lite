"""Built-in commands for command mode."""

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


# Default built-in commands
DEFAULT_COMMANDS = {
    "open terminal": {
        "action": "launch",
        "target": "gnome-terminal"
    },
    "open browser": {
        "action": "launch",
        "target": "firefox"
    },
    "open editor": {
        "action": "launch",
        "target": "xed"
    },
    "search": {
        "action": "url",
        "target": "https://www.google.com/search?q={query}"
    },
    "open files": {
        "action": "launch",
        "target": "nemo"
    },
}


def get_default_commands() -> dict:
    """Get the default built-in commands.

    Returns:
        Dictionary of default commands
    """
    return DEFAULT_COMMANDS.copy()
