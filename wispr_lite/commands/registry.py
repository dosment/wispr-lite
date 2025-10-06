"""Command registry for command mode.

Matches transcribed text to configured actions.
"""

from typing import Dict, Any, Optional
import subprocess

from wispr_lite.logging import get_logger
from wispr_lite.config.schema import CommandConfig

logger = get_logger(__name__)


class CommandRegistry:
    """Registry for command mode actions."""

    def __init__(self, config: CommandConfig):
        """Initialize command registry.

        Args:
            config: Command configuration
        """
        self.config = config
        self.commands = config.commands or {}

        logger.info(f"CommandRegistry initialized with {len(self.commands)} commands")

    def match_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Match transcribed text to a command.

        Args:
            text: Transcribed text

        Returns:
            Command dict or None
        """
        text_lower = text.lower().strip()

        # Remove prefix if present
        if self.config.prefix and text_lower.startswith(self.config.prefix.lower()):
            text_lower = text_lower[len(self.config.prefix):].strip()

        # Exact match
        if text_lower in self.commands:
            return self.commands[text_lower]

        # Fuzzy match (starts with)
        for cmd_name, cmd_config in self.commands.items():
            if text_lower.startswith(cmd_name.lower()):
                # Extract query if URL action
                if cmd_config.get('action') == 'url' and '{query}' in cmd_config.get('target', ''):
                    query = text_lower[len(cmd_name):].strip()
                    cmd_config = cmd_config.copy()
                    cmd_config['query'] = query
                return cmd_config

        return None

    def execute_command(self, command: Dict[str, Any]) -> bool:
        """Execute a command.

        Args:
            command: Command configuration

        Returns:
            True if successful
        """
        action = command.get('action')
        target = command.get('target')

        if not action or not target:
            logger.error("Invalid command: missing action or target")
            return False

        try:
            if action == 'launch':
                return self._launch_app(target)
            elif action == 'url':
                query = command.get('query', '')
                return self._open_url(target, query)
            elif action == 'shell':
                return self._run_shell(target)
            else:
                logger.error(f"Unknown command action: {action}")
                return False

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False

    def _launch_app(self, app: str) -> bool:
        """Launch an application.

        Args:
            app: Application name or command

        Returns:
            True if successful
        """
        logger.info(f"Launching app: {app}")
        subprocess.Popen([app], start_new_session=True)
        return True

    def _open_url(self, url_template: str, query: str = "") -> bool:
        """Open a URL.

        Args:
            url_template: URL template with optional {query} placeholder
            query: Query string to substitute

        Returns:
            True if successful
        """
        url = url_template.replace('{query}', query)
        logger.info(f"Opening URL: {url}")
        subprocess.Popen(['xdg-open', url], start_new_session=True)
        return True

    def _run_shell(self, command: str) -> bool:
        """Run a shell command.

        Args:
            command: Shell command to run

        Returns:
            True if successful
        """
        if self.config.require_confirmation:
            from wispr_lite.ui.confirm_dialog import show_confirmation_dialog

            confirmed = show_confirmation_dialog(
                "Execute Shell Command?",
                "This will execute a shell command. Are you sure?",
                f"Command: {command}"
            )

            if not confirmed:
                logger.info("Shell command cancelled by user")
                return False

        logger.info(f"Running shell command: {command}")

        # Parse command into args to avoid shell=True
        import shlex
        try:
            args = shlex.split(command)
        except ValueError as e:
            logger.error(f"Failed to parse command: {e}")
            return False

        # Use minimal environment
        import os
        env = {
            'PATH': '/usr/bin:/bin:/usr/local/bin',
            'HOME': os.environ.get('HOME', '/'),
            'USER': os.environ.get('USER', ''),
        }

        try:
            subprocess.Popen(
                args,
                start_new_session=True,
                env=env,
                shell=False  # Explicitly avoid shell
            )
            return True
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False
