import os
import sys

from command_processor import CommandProcessor
from main_context import AppContext
from casing import Casing
from my_logger import log_info
from typing import Callable
from config_utils import reload_config


def activate_casing(casing: Casing):
    from main_context import AppContext

    ctx = AppContext.get_current()
    ctx.current_casing = casing


def terminate(_: list[str]):
    log_info("terminating...")
    from main_context import AppContext

    ctx = AppContext.get_current()
    ctx.stop_event.set()


def clear_buffer(_: list[str]):
    from main_context import AppContext

    ctx = AppContext.get_current()
    ctx._buffer.clear()
    ctx._right_arrow_buffer.clear()


def set_buffer(args, buffer):
    from main_context import AppContext

    ctx = AppContext.get_current()
    ctx.just_set.set()

    if not buffer.is_equal(args):
        buffer.set_buffer(args, recent=False)


def set_main_buffer(args: list[str]):
    from main_context import AppContext

    set_buffer(args, AppContext.get_current()._buffer)


def set_buffer_right(args: list[str]):
    from main_context import AppContext

    set_buffer(args[::-1], AppContext.get_current()._right_arrow_buffer)


def restart(_: list[str]):
    log_info("restarting")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def activate_kabab_mode(_: list[str]):
    activate_casing(Casing.KEBAB)


def activate_snake_mode(_: list[str]):
    activate_casing(Casing.SNAKE)


def activate_normal_casing_mode(_: list[str]):
    activate_casing(Casing.NORMAL)


def activate_upper_snake_mode(_: list[str]):
    activate_casing(Casing.UPPER_SNAKE)


def activate_proper_mode(_: list[str]):
    activate_casing(Casing.PROPER)


def activate_camel_mode(_: list[str]):
    activate_casing(Casing.CAMEL)


def cmd_reload(ctx: AppContext,  _):
    log_info("reloading")
    reload_config(ctx.config)
    ctx.resize_buffers(ctx.config.general.buffer_size)


def make_processor(ctx: AppContext):
    command_processor = CommandProcessor()
    command_processor.register(
        "reload_config", lambda _: cmd_reload(ctx,  _))

    command_processor.register("restart", restart)
    command_processor.register("quit", terminate)

    commands: dict[str, Callable[[list[str]], None]] = {
        "clear_buffer": clear_buffer,
        "normalc": activate_normal_casing_mode,
        "kebab-case-mode": activate_kabab_mode,
        "snake_case_mode": activate_snake_mode,
        "ProperCaseMode": activate_proper_mode,
        "camelCaseMode": activate_camel_mode,
        "UPPER_SNAKE_CASE_MODE": activate_upper_snake_mode,
        "cb": clear_buffer,
        "mc": activate_normal_casing_mode,
        "sc": activate_snake_mode,
        "pm": activate_proper_mode,
        "cm": activate_camel_mode,
        "us": activate_upper_snake_mode,
        "kb": activate_kabab_mode,
        "sm": set_main_buffer,
        "sr": set_buffer_right,
    }

    for command, func in commands.items():
        command_processor.register(command, func)

    return command_processor
