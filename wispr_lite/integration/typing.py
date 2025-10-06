"""Text output integration for dictation (compatibility shim).

This module provides backward compatibility. The actual implementation
has been split into typing/clipboard.py, typing/xtest.py, and typing/core.py.
"""

from wispr_lite.integration.typing.core import TextOutput

__all__ = ['TextOutput']
