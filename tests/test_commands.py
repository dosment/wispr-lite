"""Tests for command registry."""

import pytest
from wispr_lite.commands.registry import CommandRegistry
from wispr_lite.commands.builtin import get_default_commands
from wispr_lite.config.schema import CommandConfig


def test_default_commands():
    """Test default command loading."""
    commands = get_default_commands()

    assert "open terminal" in commands
    assert "open browser" in commands
    assert commands["open terminal"]["action"] == "launch"


def test_command_registry_initialization():
    """Test command registry initialization."""
    config = CommandConfig()
    config.commands = get_default_commands()

    registry = CommandRegistry(config)

    assert len(registry.commands) > 0


def test_command_matching_exact():
    """Test exact command matching."""
    config = CommandConfig()
    config.commands = {"open terminal": {"action": "launch", "target": "gnome-terminal"}}

    registry = CommandRegistry(config)

    # Exact match
    command = registry.match_command("open terminal")
    assert command is not None
    assert command["action"] == "launch"


def test_command_matching_with_prefix():
    """Test command matching with prefix."""
    config = CommandConfig()
    config.prefix = "cmd:"
    config.commands = {"open terminal": {"action": "launch", "target": "gnome-terminal"}}

    registry = CommandRegistry(config)

    # Match with prefix
    command = registry.match_command("cmd:open terminal")
    assert command is not None
    assert command["action"] == "launch"


def test_command_matching_with_query():
    """Test command matching with query substitution."""
    config = CommandConfig()
    config.commands = {
        "search": {"action": "url", "target": "https://google.com/search?q={query}"}
    }

    registry = CommandRegistry(config)

    # Match with query
    command = registry.match_command("search python tutorial")
    assert command is not None
    assert command["action"] == "url"
    assert "query" in command


def test_command_no_match():
    """Test command not matching."""
    config = CommandConfig()
    config.commands = {"open terminal": {"action": "launch", "target": "gnome-terminal"}}

    registry = CommandRegistry(config)

    # No match
    command = registry.match_command("unknown command")
    assert command is None
