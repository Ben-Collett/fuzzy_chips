import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from config import (
    _load_toml,
    _chip_map,
    _get_section,
    _get_from_toml,
    Config,
)


class TestChipMap:
    def test_chip_map_single_entry(self):
        chips = {"hello": "world"}
        result = _chip_map(chips)
        assert result is not None

    def test_chip_map_multiple_entries(self):
        chips = {"hi": "there", "hello": "world"}
        result = _chip_map(chips)
        assert len(result) == 2


class TestGetSection:
    @pytest.mark.parametrize(
        "section,config_map,expected",
        [
            ("chips", {"chips": {"a": "b"}}, {"a": "b"}),
            ("chips", {}, {}),
        ],
    )
    def test_get_section(self, section, config_map, expected):
        result = _get_section(section, config_map)
        assert result == expected


class TestGetFromToml:
    @pytest.mark.parametrize(
        "section,name,config_map,default,expected",
        [
            ("chips", "hello", {"chips": {"hello": "world"}}, None, "world"),
            ("chips", "missing", {"chips": {}}, None, None),
            ("chips", "missing", {}, "default", "default"),
        ],
    )
    def test_get_from_toml(self, section, name, config_map, default, expected):
        result = _get_from_toml(section, name, config_map, default)
        assert result == expected


class TestConfigClass:
    def test_config_default_values(self):
        config = Config({})
        assert config.append_chars == [".", ",", "!", "?", ";"]
        assert config.capitalize_after == [".", "!", "?"]
        assert config.capitalize_passthrough == ["'", '"', "`"]
        assert config.auto_apped is True
        assert config.toggle_case_on == ["shift"]
        assert config.clear_buffer_on_keys == ["windows_down", "alt_down", "ctrl_down"]
        assert config.just_set_safe_clear == ["up", "down"]

    def test_config_custom_values(self):
        config_map = {
            "general": {
                "append_chars": [","],
                "capitalize_after": ["!"],
                "auto_append": False,
                "toggle_case_on": ["ctrl"],
            },
        }
        config = Config(config_map)
        assert config.append_chars == [","]
        assert config.capitalize_after == ["!"]
        assert config.auto_apped is False
        assert config.toggle_case_on == ["ctrl"]

    def test_config_default_values_empty_map(self):
        config = Config({})
        from spacing_type import SpacingType
        from casing import Casing

        assert config.spacing_type == SpacingType.NORMAL
        assert config.assumed_casing == Casing.NORMAL
        assert config.space_on_new is True


class TestConfigGeneral:
    @pytest.mark.parametrize(
        "config_map,attr,expected",
        [
            ({"general": {"ignored_leading": ["("]}}, "ignored_leading", ["("]),
            ({"general": {"ignored_trailing": [")"]}}, "ignored_trailing", [")"]),
            (
                {"general": {"buffer_state_timeout_ms": 500}},
                "buffer_state_timeout_ms",
                500,
            ),
        ],
    )
    def test_config_general_attributes(self, config_map, attr, expected):
        config = Config(config_map)
        assert getattr(config, attr) == expected
