from command_processor import CommandProcessor
from config import current_config
from my_logger import log_info


def cmd_reload(_):
    log_info("reloading")
    current_config.reload()


def make_processor():
    command_processor = CommandProcessor()
    command_processor.register("reload_config", cmd_reload)

    return command_processor
