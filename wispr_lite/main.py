"""Main application entry point for Wispr-Lite.

This module provides backward compatibility. The actual implementation
has been split into app.py, pipeline.py, and cli.py.
"""

import sys
from wispr_lite.cli import main

if __name__ == "__main__":
    sys.exit(main())
