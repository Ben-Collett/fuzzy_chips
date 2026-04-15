from enum import Enum
from enum_utils import safe_enum_from_str


class SpacingType(Enum):
    NORMAL = "normal"
    CODE = "code"
    NEW = "new"

    @staticmethod
    def safe_from_str(spacing_type, default, print_on_err=True):
        err_msg = None
        if print_on_err:
            err_msg = f"is not a valid spacing type, defaulting to {default}"
        return safe_enum_from_str(SpacingType,spacing_type,default,err_msg)
