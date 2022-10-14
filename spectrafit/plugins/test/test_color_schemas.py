"""Test of the color schemas."""

from spectrafit.plugins.color_schemas import DraculaColor
from spectrafit.plugins.color_schemas import DraculaFont


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


def test_dracula_font() -> None:
    """Test the dracula font schema."""
    font = DraculaFont()
    assert font.family == "Fira Code"
    assert font.size == 12
    assert font.color == "#f8f8f2"
