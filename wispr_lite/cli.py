"""Command-line interface for Wispr-Lite.

Provides CLI flags and D-Bus communication with running daemon.
"""

import sys
import argparse

from wispr_lite.logging import get_logger

logger = get_logger(__name__)


def send_dbus_command(method: str, *args) -> int:
    """Send a command to running daemon via D-Bus.

    Args:
        method: D-Bus method name
        *args: Method arguments

    Returns:
        Exit code (0 on success)
    """
    try:
        import dbus
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.wispr_lite.Daemon', '/org/wispr_lite/Daemon')
        interface = dbus.Interface(proxy, 'org.wispr_lite.Daemon')

        method_func = getattr(interface, method)
        method_func(*args)
        return 0

    except dbus.exceptions.DBusException as e:
        if "org.freedesktop.DBus.Error.ServiceUnknown" in str(e):
            logger.error("Wispr-Lite daemon not running. Start the application first.")
            return 1
        else:
            logger.error(f"D-Bus error: {e}")
            return 1
    except Exception as e:
        logger.error(f"Failed to send command: {e}")
        return 1


def main():
    """Application entry point with CLI support."""
    parser = argparse.ArgumentParser(
        description='Wispr-Lite: Local voice dictation and command launcher'
    )
    parser.add_argument('--toggle', action='store_true',
                        help='Toggle listening state')
    parser.add_argument('--start', action='store_true',
                        help='Start listening')
    parser.add_argument('--stop', action='store_true',
                        help='Stop listening')
    parser.add_argument('--mode', type=str, choices=['dictation', 'command'],
                        help='Set mode')
    parser.add_argument('--prefs', action='store_true',
                        help='Open preferences')
    parser.add_argument('--undo', action='store_true',
                        help='Undo last dictation')

    args = parser.parse_args()

    # Check if any CLI command was specified
    if args.toggle:
        return send_dbus_command('Toggle')
    elif args.start:
        return send_dbus_command('Start')
    elif args.stop:
        return send_dbus_command('Stop')
    elif args.mode:
        return send_dbus_command('SetMode', args.mode)
    elif args.prefs:
        return send_dbus_command('OpenPreferences')
    elif args.undo:
        return send_dbus_command('Undo')

    # No CLI command, run the application
    from wispr_lite.app import WisprLiteApp
    app = WisprLiteApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
