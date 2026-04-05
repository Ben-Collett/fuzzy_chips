from enum import Enum


class SpacingType(Enum):
    NORMAL = "normal"
    CODE = "code"
    NEW = "new"

    @staticmethod
    def safe_from_str(spacing_type: str, default=NORMAL, print_on_err=True):
        out = None
        try:
            out = SpacingType(spacing_type)
        except ValueError:
            if print_on_err:
                print(spacing_type,
                      f"is not a valid spacing type, defaulting to {default}")
            out = default

        return out
