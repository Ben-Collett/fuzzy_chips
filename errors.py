from casing import Casing


def parse_assumed_casing_error_message(casing: str, default: Casing) -> str:
    return f"assumed casing: {casing} is not a valid casing type, defaulting to {default}"
