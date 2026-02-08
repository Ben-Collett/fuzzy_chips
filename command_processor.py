from typing import Callable, List

CommandHandler = Callable[[List[str]], None]


class CommandProcessor:
    def __init__(self, fallback: Callable[[str], None] | None = None):
        self._commands: dict[str, CommandHandler] = {}
        self.ipc_commands: set[str] = set()
        self._fallback = fallback

    def has_command(self, cmd: str):
        return cmd in self._commands.keys()

    def register(self, name: str, handler: CommandHandler, ipc_enabled=False):
        self._commands[name] = handler
        if ipc_enabled:
            self.ipc_commands.add(name)

    def process(self, line: str):
        tokens = line.strip().split()
        if not tokens:
            return

        command = tokens[0]
        args = tokens[1:]

        handler = self._commands.get(command)
        if handler:
            handler(args)
        elif self._fallback:
            self._fallback(line)

    def process_ipc(self, line: str) -> str:
        command_l: list[str] = []
        arg_l: list[str] = []

        finished_command = False

        line = line.lstrip()
        for ch in line:
            if not finished_command and ch.isspace():
                finished_command = True
            elif not finished_command:
                command_l.append(ch)
            else:
                arg_l.append(ch)

        command = ''.join(command_l)
        args = ''.join(arg_l)
        if command not in self._commands:
            return "invalid"

        if command not in self.ipc_commands:
            return "not ipc enabled"

        try:
            handler = self._commands[command]
            handler(args)
            return "succeeded"
        except Exception:
            return "invalid"
