from frozen_dict import FrozenDict
from my_logger import log_info


def load_chips(config_map: dict) -> dict[FrozenDict, str]:
    out = {}
    # print(config_map)
    chips = config_map.get("chips")
    if isinstance(chips, dict):
        out = _chip_map(chips)
    return out


def _chip_map(chips) -> dict[FrozenDict, str]:
    out = {}
    for k, v in chips.items():
        key = FrozenDict.from_string(k)
        if key in out.keys():
            old_val = out[key]
            log_info(f"colliding key overridng: {k}={old_val} with {k} = {v}")
        out[key] = v
    return out
