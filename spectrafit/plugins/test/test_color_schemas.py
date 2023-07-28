"""Test of the color schemas."""

from typing import Tuple
from typing import Type

import pytest

from spectrafit.api.notebook_model import ColorAPI
from spectrafit.api.notebook_model import FontAPI
from spectrafit.plugins.color_schemas import ColorBlindColor
from spectrafit.plugins.color_schemas import ColorBlindFont
from spectrafit.plugins.color_schemas import DevOpsDarkColor
from spectrafit.plugins.color_schemas import DevOpsDarkFont
from spectrafit.plugins.color_schemas import DevOpsLightColor
from spectrafit.plugins.color_schemas import DevOpsLightFont
from spectrafit.plugins.color_schemas import DraculaColor
from spectrafit.plugins.color_schemas import DraculaFont
from spectrafit.plugins.color_schemas import MoonAkiColor
from spectrafit.plugins.color_schemas import MoonAkiFont


def test_dracula_color() -> None:
    """Test the dracula color schema."""
    color = DraculaColor()
    assert color.intensity == "#bd93f9"
    assert color.residual == "#ff5555"
    assert color.fit == "#50fa7b"
    assert color.components == "#ff79c6"
    assert color.paper == "#282a36"
    assert color.plot == "#282a36"
    assert color.color == "#f8f8f2"
    assert color.grid == "#f8f8f2"
    assert color.line == "#6272a4"
    assert color.zero_line == "#8be9fd"
    assert color.ticks == "#f8f8f2"
    assert color.font == "#f8f8f2"
    # check is type of ColorAPI
    assert isinstance(color, ColorAPI)


def test_dracula_font() -> None:
    """Test the dracula font schema."""
    font = DraculaFont()
    assert font.family == "Fira Code"
    assert font.size == 12
    assert font.color == "#f8f8f2"
    # check is type of FontAPI
    assert isinstance(font, FontAPI)


@pytest.mark.parametrize(
    "color_font",
    [
        (DraculaColor, DraculaFont),
        (DevOpsLightColor, DevOpsLightFont),
        (DevOpsDarkColor, DevOpsDarkFont),
        (MoonAkiColor, MoonAkiFont),
        (ColorBlindColor, ColorBlindFont),
    ],
)
def test_color_schemas(color_font: Tuple[Type[ColorAPI], Type[FontAPI]]) -> None:
    """Test the color schemas."""
    color_schema, font_schema = color_font
    color = color_schema()
    font = font_schema()
    assert isinstance(color, ColorAPI)
    assert isinstance(font, FontAPI)
