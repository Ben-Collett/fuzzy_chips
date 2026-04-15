from my_logger import log_info
from typing import Optional
def safe_enum_from_str(enum_type, key, default, err_msg:Optional[str]=None):
    try:
        out = enum_type(key)
    except ValueError:
        if err_msg:
            log_info(err_msg)
        out = default

        return out


