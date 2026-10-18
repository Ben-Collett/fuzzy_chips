"""Regression tests for the Windows hook hand-off barrier.

The low-level hook callback runs before Windows hands the physical key event
to the focused application, and the processing thread can start injecting an
expansion while that hand-off is still pending. Without the barrier the
injected backspace overtakes the trigger key ("th" + space -> "t at ").
"""
import sys
import threading

import pytest

if sys.platform != "win32":
    pytest.skip("the winkeyboard backend is Windows-only", allow_module_level=True)

from keyboard import _winkeyboard as winkeyboard  # noqa: E402


@pytest.fixture(autouse=True)
def reset_hook_state():
    """Never let a failing test leave the hook marked as in flight."""
    yield
    with winkeyboard._hook_release:
        winkeyboard._hook_events_in_flight = 0
        winkeyboard._hook_release.notify_all()


def _start(target):
    done = threading.Event()
    thread = threading.Thread(target=lambda: (target(), done.set()))
    thread.start()
    return thread, done


class TestHookReleaseBarrier:
    def test_wait_returns_immediately_when_hook_is_idle(self):
        winkeyboard._wait_for_hook_release()

    def test_hook_thread_never_waits_for_itself(self):
        # Suppressed/remapped keys are re-injected from inside the hook
        # callback; waiting there would deadlock.
        winkeyboard._enter_hook()
        try:
            winkeyboard._wait_for_hook_release()
        finally:
            winkeyboard._leave_hook()

    def test_wait_blocks_until_hook_returns(self):
        winkeyboard._enter_hook()
        thread, released = _start(winkeyboard._wait_for_hook_release)
        try:
            assert not released.wait(0.1)
        finally:
            winkeyboard._leave_hook()
        assert released.wait(5)
        thread.join()

    def test_send_event_waits_for_hook_handoff(self, monkeypatch):
        sent = []
        monkeypatch.setattr(
            winkeyboard.user32, "keybd_event", lambda *args: sent.append(args))

        winkeyboard._enter_hook()
        thread, done = _start(lambda: winkeyboard.press(14))
        try:
            assert not done.wait(0.1)
            assert sent == []
        finally:
            winkeyboard._leave_hook()

        assert done.wait(5)
        assert len(sent) == 1
        thread.join()

    def test_type_unicode_waits_for_hook_handoff(self, monkeypatch):
        sent = []
        monkeypatch.setattr(
            winkeyboard, "SendInput", lambda *args: sent.append(args))

        winkeyboard._enter_hook()
        thread, done = _start(lambda: winkeyboard.type_unicode("a"))
        try:
            assert not done.wait(0.1)
            assert sent == []
        finally:
            winkeyboard._leave_hook()

        assert done.wait(5)
        assert len(sent) == 1
        thread.join()
