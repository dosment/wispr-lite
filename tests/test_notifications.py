"""Tests for notification anti-spam and rate limiting."""

import pytest
import time
from unittest.mock import Mock, patch

from wispr_lite.ui.notifications import NotificationManager, Severity
from wispr_lite.config.schema import NotificationConfig


@pytest.fixture
def config():
    """Create a test notification configuration."""
    return NotificationConfig(
        enabled=True,
        max_toasts_per_minute=3,
        per_category_cooldown_sec=10,
        show_info=True,
        show_warnings=True,
        show_errors=True,
        show_progress=True,
        respect_dnd=False
    )


@pytest.fixture
def notification_manager(config):
    """Create a notification manager for testing."""
    with patch('wispr_lite.ui.notifications.NOTIFY_AVAILABLE', True):
        with patch('wispr_lite.ui.notifications.Notify'):
            manager = NotificationManager(config)
            return manager


def test_global_rate_limit(notification_manager):
    """Test that global rate limit enforces max toasts per minute."""
    config = notification_manager.config

    # Mock time to control rate limiting
    with patch('time.time') as mock_time:
        mock_time.return_value = 0.0

        # First 3 notifications should pass (max_toasts_per_minute=3)
        assert notification_manager._check_rate_limit("key1") is True
        notification_manager.global_toast_times.append(0.0)

        assert notification_manager._check_rate_limit("key2") is True
        notification_manager.global_toast_times.append(0.0)

        assert notification_manager._check_rate_limit("key3") is True
        notification_manager.global_toast_times.append(0.0)

        # 4th notification should be rate limited
        assert notification_manager._check_rate_limit("key4") is False

        # After 60 seconds, rate limit should reset
        mock_time.return_value = 61.0
        assert notification_manager._check_rate_limit("key5") is True


def test_per_key_cooldown(notification_manager):
    """Test that per-key cooldown prevents repeated notifications."""
    config = notification_manager.config

    with patch('time.time') as mock_time:
        mock_time.return_value = 0.0

        # First notification for key should pass
        assert notification_manager._check_rate_limit("test_key") is True

        # Record that we showed it
        from wispr_lite.ui.notifications import NotificationState
        notification_manager.states["test_key"] = NotificationState(last_shown=0.0)

        # Immediate retry should be blocked (within cooldown period)
        mock_time.return_value = 5.0  # 5 seconds later (< 10 second cooldown)
        assert notification_manager._check_rate_limit("test_key") is False

        # After cooldown period, should pass again
        mock_time.return_value = 11.0  # 11 seconds later (> 10 second cooldown)
        assert notification_manager._check_rate_limit("test_key") is True


def test_coalescing_counter(notification_manager):
    """Test that repeated notifications increment the count for coalescing."""
    with patch('time.time') as mock_time:
        mock_time.return_value = 0.0

        # First notification
        notification_manager._check_rate_limit("test_key")
        from wispr_lite.ui.notifications import NotificationState
        notification_manager.states["test_key"] = NotificationState(last_shown=0.0, count=1)

        # Blocked notifications should increment count
        mock_time.return_value = 1.0
        notification_manager._check_rate_limit("test_key")
        assert notification_manager.states["test_key"].count == 2

        mock_time.return_value = 2.0
        notification_manager._check_rate_limit("test_key")
        assert notification_manager.states["test_key"].count == 3


def test_severity_filtering(notification_manager):
    """Test that severity filtering works correctly."""
    # Initially all severities enabled
    assert notification_manager._should_show_severity(Severity.INFO) is True
    assert notification_manager._should_show_severity(Severity.WARNING) is True
    assert notification_manager._should_show_severity(Severity.ERROR) is True
    assert notification_manager._should_show_severity(Severity.PROGRESS) is True

    # Disable info
    notification_manager.config.show_info = False
    assert notification_manager._should_show_severity(Severity.INFO) is False
    assert notification_manager._should_show_severity(Severity.WARNING) is True

    # Disable warnings
    notification_manager.config.show_warnings = False
    assert notification_manager._should_show_severity(Severity.WARNING) is False
    assert notification_manager._should_show_severity(Severity.ERROR) is True


def test_progress_notifications_bypass_rate_limit(notification_manager):
    """Test that progress notifications are not subject to per-key rate limiting."""
    with patch('time.time') as mock_time:
        mock_time.return_value = 0.0

        # Mock the _show_notification method since we're testing notify() flow
        notification_manager._show_notification = Mock()

        # First progress notification
        notification_manager.notify("Download", Severity.PROGRESS, progress=0.0)
        assert notification_manager._show_notification.call_count == 1

        # Immediate second progress notification should not be rate limited
        mock_time.return_value = 0.1
        notification_manager.notify("Download", Severity.PROGRESS, progress=0.5)
        assert notification_manager._show_notification.call_count == 2

        # Third progress notification
        mock_time.return_value = 0.2
        notification_manager.notify("Download", Severity.PROGRESS, progress=1.0)
        assert notification_manager._show_notification.call_count == 3


def test_dnd_suppression(notification_manager):
    """Test that notifications are suppressed when DND is active."""
    notification_manager.config.respect_dnd = True
    notification_manager._show_notification = Mock()

    # Mock DND as active
    with patch.object(notification_manager, '_is_dnd_active', return_value=True):
        notification_manager.notify("Test Event", Severity.INFO, text="Test")
        # Notification should not be shown
        assert notification_manager._show_notification.call_count == 0

    # Mock DND as inactive
    with patch.object(notification_manager, '_is_dnd_active', return_value=False):
        notification_manager.notify("Test Event", Severity.INFO, text="Test")
        # Notification should be shown
        assert notification_manager._show_notification.call_count == 1
