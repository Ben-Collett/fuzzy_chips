import tomllib
import warnings
from frozen_dict import FrozenDict


def _load_toml() -> dict:
    with open("config.toml", "rb") as file:
        data = tomllib.load(file)
    print("")
    return data


def _chip_map(chips) -> dict[FrozenDict[str], str]:
    out = {}
    for k, v in chips.items():
        key = FrozenDict.from_string(k)
        if key in out.keys():
            old_val = out[key]
            warnings.warn(f"colliding key overridng: {
                          k}={old_val} with {k} = {v}")

        out[key] = v
    return out


class Config:
    def __init__(self, config_map):
        self.chip_map = _chip_map(config_map["chips"])


current_config = Config(_load_toml())
