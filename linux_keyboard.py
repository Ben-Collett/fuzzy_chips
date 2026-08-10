from enum import Enum

from enum_utils import safe_enum_from_str


class LinuxKeyboardType(Enum):
    NONE = "none"
    PATIENT = "patient"
    GRAB = "grab"

    @staticmethod
    def safe_from_str(keyboard_type: str, default) -> "LinuxKeyboardType":
        err_msg = f"linux keyboard type: {
            keyboard_type} is not a valid keyboard_type type, defaulting to {default}"
        return safe_enum_from_str(LinuxKeyboardType, keyboard_type, default, err_msg)
