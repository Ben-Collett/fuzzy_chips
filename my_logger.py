YELLOW = "\033[33m"
RESET = "\033[0m"


def log_info(*objects, sep=" ", end="\n", file=None, flush=False):
    print(*objects, sep=sep, end=end, file=file, flush=flush)


def log_warning(*objects, sep=" ", end="\n", file=None, flush=False):
    print(f"{YELLOW}", *objects, f"{RESET}", sep=sep, end=end, file=file, flush=flush)
