import pytest
from command_processor import CommandProcessor


class TestCommandProcessor:
    def test_initialization(self):
        processor = CommandProcessor()
        assert processor._commands == {}
        assert processor.ipc_commands == set()
        assert processor._fallback is None

    def test_initialization_with_fallback(self):
        def fallback(x): return None
        processor = CommandProcessor(fallback=fallback)
        assert processor._fallback == fallback


class TestHasCommand:
    def test_has_command_returns_true_for_registered(self):
        processor = CommandProcessor()
        processor.register("test", lambda args: None)
        assert processor.has_command("test") is True

    def test_has_command_returns_false_for_unregistered(self):
        processor = CommandProcessor()
        assert processor.has_command("unknown") is False


class TestRegister:
    def test_register_command(self):
        processor = CommandProcessor()
        def handler(args): return None
        processor.register("test", handler)
        assert "test" in processor._commands
        assert processor._commands["test"] == handler

    def test_register_command_ipc_enabled(self):
        processor = CommandProcessor()
        def handler(args): return None
        processor.register("test", handler, ipc_enabled=True)
        assert "test" in processor._commands
        assert "test" in processor.ipc_commands


class TestProcess:
    def test_process_empty_line(self):
        processor = CommandProcessor()
        processor.process("")

    def test_process_command_no_args(self):
        processor = CommandProcessor()
        called = False

        def handler(args):
            nonlocal called
            called = True

        processor.register("test", handler)
        processor.process("test")
        assert called is True

    def test_process_command_with_args(self):
        processor = CommandProcessor()
        result = []

        def handler(args):
            result.append(args)

        processor.register("test", handler)
        processor.process("test arg1 arg2")
        assert result == [["arg1", "arg2"]]

    def test_process_unknown_command_no_fallback(self):
        processor = CommandProcessor()
        processor.process("unknown")

    def test_process_unknown_command_with_fallback(self):
        processor = CommandProcessor()
        fallback_called = False

        def fallback(line):
            nonlocal fallback_called
            fallback_called = True

        processor = CommandProcessor(fallback=fallback)
        processor.process("unknown_command")
        assert fallback_called is True


class TestProcessIpc:
    def test_process_ipc_empty(self):
        processor = CommandProcessor()
        result = processor.process_ipc("")
        assert result == "invalid"

    def test_process_ipc_invalid_command(self):
        processor = CommandProcessor()
        result = processor.process_ipc("unknown")
        assert result == "invalid"

    def test_process_ipc_not_ipc_enabled(self):
        processor = CommandProcessor()
        def handler(args): return None
        processor.register("test", handler)
        result = processor.process_ipc("test")
        assert result == "not ipc enabled"

    def test_process_ipc_success(self):
        processor = CommandProcessor()
        called = False

        def handler(args):
            nonlocal called
            called = True

        processor.register("test", handler, ipc_enabled=True)
        result = processor.process_ipc("test arg")
        assert result == "succeeded"
        assert called is True

    def test_process_ipc_with_args(self):
        processor = CommandProcessor()
        result_args = []

        def handler(args):
            result_args.append(args)

        processor.register("cmd", handler, ipc_enabled=True)
        result = processor.process_ipc("cmd hello world")
        assert result == "succeeded"
        assert result_args[0] == ["hello world"]

    def test_process_ipc_leading_whitespace(self):
        processor = CommandProcessor()
        called = False

        def handler(args):
            nonlocal called
            called = True

        processor.register("test", handler, ipc_enabled=True)
        result = processor.process_ipc("   test")
        assert result == "succeeded"
        assert called is True

    def test_process_ipc_exception(self):
        processor = CommandProcessor()

        def handler(args):
            raise ValueError("test error")

        processor.register("test", handler, ipc_enabled=True)
        result = processor.process_ipc("test")
        assert result == "invalid"
