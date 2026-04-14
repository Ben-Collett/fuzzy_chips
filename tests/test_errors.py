import pytest
from errors import parse_assumed_casing_error_message
from casing import Casing


class TestParseAssumedCasingErrorMessage:
    def test_returns_expected_message(self):
        result = parse_assumed_casing_error_message("invalid", Casing.NORMAL)
        assert "invalid" in result
        assert "Casing.NORMAL" in result
