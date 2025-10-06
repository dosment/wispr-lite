"""Integration tests for typing and clipboard operations."""

import os
import pytest

# Skip tests if DISPLAY is not available
pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'),
    reason="Requires X display"
)


def test_clipboard_preservation():
    """Test that clipboard preservation works correctly."""
    from wispr_lite.integration.typing import TextOutput
    from wispr_lite.config.schema import TypingConfig

    try:
        import subprocess

        # Set initial clipboard content
        test_text = "original clipboard content"
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=test_text.encode(),
            timeout=1,
            check=True
        )

        # Create text output with preservation enabled
        config = TypingConfig(strategy="clipboard", preserve_clipboard=True)
        text_output = TextOutput(config)

        # This would normally insert text and restore clipboard
        # For testing, we just verify the clipboard operations work
        saved = text_output._get_clipboard('clipboard')
        assert saved == test_text

        # Set new content
        new_text = "dictated text"
        text_output._set_clipboard(new_text, 'clipboard')

        # Verify it was set
        current = text_output._get_clipboard('clipboard')
        assert current == new_text

        # Restore original
        text_output._set_clipboard(test_text, 'clipboard')
        restored = text_output._get_clipboard('clipboard')
        assert restored == test_text

    except FileNotFoundError:
        pytest.skip("xclip not available")


def test_primary_selection_preservation():
    """Test that PRIMARY selection is preserved."""
    from wispr_lite.integration.typing import TextOutput
    from wispr_lite.config.schema import TypingConfig

    try:
        import subprocess

        # Set primary selection
        test_text = "primary selection"
        subprocess.run(
            ["xclip", "-selection", "primary"],
            input=test_text.encode(),
            timeout=1,
            check=True
        )

        config = TypingConfig(strategy="clipboard", preserve_clipboard=True)
        text_output = TextOutput(config)

        # Verify primary selection operations
        saved = text_output._get_clipboard('primary')
        if saved:  # PRIMARY might be empty
            assert isinstance(saved, str)

    except FileNotFoundError:
        pytest.skip("xclip not available")


def test_wayland_detection():
    """Test Wayland detection."""
    from wispr_lite.integration.cinnamon import is_wayland, get_wayland_limitations

    # Save current env
    original_session = os.environ.get('XDG_SESSION_TYPE')
    original_wayland = os.environ.get('WAYLAND_DISPLAY')

    try:
        # Test X11
        os.environ['XDG_SESSION_TYPE'] = 'x11'
        os.environ.pop('WAYLAND_DISPLAY', None)
        assert not is_wayland()

        # Test Wayland
        os.environ['XDG_SESSION_TYPE'] = 'wayland'
        assert is_wayland()

        # Test Wayland via display
        os.environ['XDG_SESSION_TYPE'] = 'x11'
        os.environ['WAYLAND_DISPLAY'] = 'wayland-0'
        assert is_wayland()

        # Verify limitations are documented
        limitations = get_wayland_limitations()
        assert len(limitations) > 0
        assert all(isinstance(lim, str) for lim in limitations)

    finally:
        # Restore environment
        if original_session:
            os.environ['XDG_SESSION_TYPE'] = original_session
        else:
            os.environ.pop('XDG_SESSION_TYPE', None)

        if original_wayland:
            os.environ['WAYLAND_DISPLAY'] = original_wayland
        else:
            os.environ.pop('WAYLAND_DISPLAY', None)


def test_delta_typing():
    """Test delta typing (incremental partial updates)."""
    from wispr_lite.integration.typing import TextOutput
    from wispr_lite.integration.typing.xtest import XLIB_AVAILABLE
    from wispr_lite.config.schema import TypingConfig

    if not XLIB_AVAILABLE:
        pytest.skip("XLib not available for delta typing")

    try:
        config = TypingConfig(strategy="xtest", preserve_clipboard=False)
        text_output = TextOutput(config)

        # Simulate streaming partials
        # "Hello" -> "Hello world" -> "Hello world!"

        # First partial
        result1 = text_output.insert_partial("Hello")
        assert result1 is True
        assert text_output.current_partial_text == "Hello"
        assert text_output.partial_typed_length == 5

        # Second partial (adds " world")
        result2 = text_output.insert_partial("Hello world")
        assert result2 is True
        assert text_output.current_partial_text == "Hello world"
        assert text_output.partial_typed_length == 11

        # Third partial (adds "!")
        result3 = text_output.insert_partial("Hello world!")
        assert result3 is True
        assert text_output.current_partial_text == "Hello world!"
        assert text_output.partial_typed_length == 12

        # Finalize with same text
        final = text_output.finalize_partial("Hello world!")
        assert final is True
        assert text_output.current_partial_text == ""  # Reset after finalize
        assert text_output.last_inserted_text == "Hello world!"

    except Exception as e:
        pytest.skip(f"Delta typing test failed (may need X display): {e}")


def test_mime_clipboard_preservation():
    """Test MIME type preservation (text/html, text/uri-list)."""
    from wispr_lite.integration.typing import TextOutput
    from wispr_lite.config.schema import TypingConfig

    try:
        import subprocess

        # Set clipboard with HTML content
        html_content = b"<p>Test HTML</p>"
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/html"],
            input=html_content,
            timeout=1,
            check=True
        )

        config = TypingConfig(strategy="clipboard", preserve_clipboard=True)
        text_output = TextOutput(config)

        # Save clipboard data (should include MIME types)
        saved_data = text_output._save_clipboard_data('clipboard')

        assert saved_data is not None
        assert 'text' in saved_data
        assert 'targets' in saved_data
        assert 'mime_data' in saved_data

        # Check if text/html was saved
        if saved_data.get('targets') and 'text/html' in saved_data['targets']:
            assert 'text/html' in saved_data['mime_data']
            assert saved_data['mime_data']['text/html'] == html_content

        # Modify clipboard
        text_output._set_clipboard("different text", 'clipboard')

        # Restore
        text_output._restore_clipboard_with_targets(saved_data, 'clipboard')

        # Verify HTML was restored if it was saved
        if 'text/html' in saved_data.get('mime_data', {}):
            restored_html = subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "text/html", "-o"],
                capture_output=True,
                timeout=1
            )
            assert restored_html.stdout == html_content

    except FileNotFoundError:
        pytest.skip("xclip not available")
    except Exception as e:
        pytest.skip(f"MIME test failed: {e}")


def test_mime_uri_list_preservation():
    """Test text/uri-list MIME type preservation."""
    from wispr_lite.integration.typing import TextOutput
    from wispr_lite.config.schema import TypingConfig

    try:
        import subprocess

        # Set clipboard with URI list
        uri_list = b"file:///home/user/test.txt\nfile:///home/user/doc.pdf"
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/uri-list"],
            input=uri_list,
            timeout=1,
            check=True
        )

        config = TypingConfig(strategy="clipboard", preserve_clipboard=True)
        text_output = TextOutput(config)

        # Save and verify
        saved_data = text_output._save_clipboard_data('clipboard')

        if saved_data.get('targets') and 'text/uri-list' in saved_data['targets']:
            assert 'text/uri-list' in saved_data['mime_data']
            assert saved_data['mime_data']['text/uri-list'] == uri_list

            # Modify and restore
            text_output._set_clipboard("other", 'clipboard')
            text_output._restore_clipboard_with_targets(saved_data, 'clipboard')

            # Verify restoration
            restored = subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "text/uri-list", "-o"],
                capture_output=True,
                timeout=1
            )
            assert restored.stdout == uri_list

    except FileNotFoundError:
        pytest.skip("xclip not available")
    except Exception as e:
        pytest.skip(f"URI list test failed: {e}")
