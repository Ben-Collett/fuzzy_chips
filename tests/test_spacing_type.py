import pytest
from unittest.mock import patch
from spacing_type import SpacingType


class TestSpacingType:
    def test_enum_values(self):
        assert SpacingType.NORMAL.value == "normal"
        assert SpacingType.CODE.value == "code"
        assert SpacingType.NEW.value == "new"


class TestSafeFromStr:
    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("normal", SpacingType.NORMAL),
            ("code", SpacingType.CODE),
            ("new", SpacingType.NEW),
        ],
    )
    def test_returns_correct_spacing_type(self, input_str, expected):
        assert SpacingType.safe_from_str(input_str, SpacingType.NORMAL,print_on_err=False) == expected

    def test_returns_default_for_invalid_input(self):
        assert SpacingType.safe_from_str("invalid",SpacingType.NORMAL ,print_on_err=False) == "normal"

    def test_returns_custom_default_for_invalid_input(self):
        assert (
            SpacingType.safe_from_str("invalid", default="code", print_on_err=False)
            == "code"
        )

    @patch("spacing_type.log_info")
    def test_logs_error_for_invalid_input(self, mock_log_info):
        SpacingType.safe_from_str("invalid", SpacingType.NORMAL,print_on_err=True)
        mock_log_info.assert_called_once_with(
            "invalid", "is not a valid spacing type, defaulting to normal"
        )

    def test_returns_none_for_empty_string(self):
        result = SpacingType.safe_from_str("", SpacingType.NORMAL,print_on_err=False)
        assert result == "normal"

    @patch("spacing_type.log_info")
    def test_does_not_log_when_print_on_err_false(self, mock_log_info):
        SpacingType.safe_from_str("invalid", SpacingType.NORMAL,print_on_err=False)
        mock_log_info.assert_not_called()
