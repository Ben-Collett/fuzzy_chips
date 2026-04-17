from enum import Enum
from enum_utils import safe_enum_from_str
class ChunkingType(Enum):
    LAST = "last"
    NONE = "none"
    ALL = "all"
    NEW = "new"
    @staticmethod
    def safe_from_str(key,default):
        err_msg= f"{key} is not a valid chunking type, defaulting to {default}"
        return safe_enum_from_str(ChunkingType,key,default,err_msg)

   

