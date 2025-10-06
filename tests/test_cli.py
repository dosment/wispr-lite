"""Minimal CLI flag parsing tests (D-Bus stubbed).

These tests validate that wispr_lite.main routes CLI flags to
send_dbus_command and returns the stubbed exit codes, without
requiring a running daemon or GTK environment.
"""

from types import SimpleNamespace
import builtins

import pytest


def run_main_with_args(monkeypatch, args_list, return_code=0):
    """Helper to run main() with patched argv and send_dbus_command."""
    # Import inside to ensure fresh monkeypatching per call
    import sys
    from wispr_lite import cli

    # Patch argv
    monkeypatch.setattr(sys, 'argv', ['wispr-lite'] + args_list)

    # Patch send_dbus_command to controlled return code
    monkeypatch.setattr(cli, 'send_dbus_command', lambda *a, **k: return_code)

    # Run
    return cli.main()


def test_cli_toggle_returns_zero(monkeypatch):
    rc = run_main_with_args(monkeypatch, ['--toggle'], return_code=0)
    assert rc == 0


def test_cli_mode_command_returns_zero(monkeypatch):
    rc = run_main_with_args(monkeypatch, ['--mode', 'command'], return_code=0)
    assert rc == 0

