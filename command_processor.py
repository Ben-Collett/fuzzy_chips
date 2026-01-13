from typing import Callable, List

CommandHandler = Callable[[List[str]], None]


class CommandProcessor:
    def __init__(self, fallback: Callable[[str], None] | None = None):
        self._commands: dict[str, CommandHandler] = {}
        self._fallback = fallback

    def has_command(self, cmd: str):
        return cmd in self._commands.keys()

    def register(self, name: str, handler: CommandHandler):
        self._commands[name] = handler

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
