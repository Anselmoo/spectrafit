"""Test of the Tools Model API."""

from __future__ import annotations

import pytest

from pydantic import ValidationError

from spectrafit.api.tools_model import AutopeakAPI


def test_raise_autopeak() -> None:
    """Test for raising exception of Autopeak Model."""
    with pytest.raises(ValidationError) as excinfo:
        AutopeakAPI(not_=2)  # type: ignore
    assert "not_" in str(excinfo.value)
    assert excinfo.type is ValidationError
