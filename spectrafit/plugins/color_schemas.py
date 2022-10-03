"""Color Schemas for the Plots in Jupyter Notebooks."""
from pydantic import BaseModel


class DraculaColor(BaseModel, frozen=True):
    """Dracula color schema for SpectraFit.

    !!! info "Dracula Color"

        The [Dracula Color](https://draculatheme.com/contribute) is a color schema is
        used for the dark mode of the `SpectraFit` application. This color schema is
        used in the following way:

        * Background    #282a36 &rarr; **paper**, **plot**
        * Current Line	#44475a &rarr; _not used_
        * Foreground	#f8f8f2 &rarr; **color**, **grid**, **ticks**,  **font**
        * Comment	#6272a4 &rarr; **line**
        * Cyan	#8be9fd &rarr; **zero_line**
        * Green	#50fa7b &rarr; **fit**
        * Orange	#ffb86c &rarr; _not used_
        * Pink	#ff79c6 &rarr; **components**
        * Purple	#bd93f9 &rarr; **intensity**
        * Red	#ff5555 &rarr; **residual**
        * Yellow	#f1fa8c &rarr; _not used_

    """

    intensity: str = "#bd93f9"
    residual: str = "#ff5555"
    fit: str = "#50fa7b"
    components: str = "#ff79c6"
    paper: str = "#282a36"
    plot: str = "#282a36"
    color: str = "#f8f8f2"
    grid: str = "#f8f8f2"
    line: str = "#6272a4"
    zero_line: str = "#8be9fd"
    ticks: str = "#f8f8f2"
    font: str = "#f8f8f2"


class DraculaFont(BaseModel, frozen=True):
    """Dracula font schema for SpectraFit.

    !!! info "Dracula Font"

        The [Dracula Font](https://draculatheme.com/contribute) is a font schema is
        used for the dark mode of the `SpectraFit` application. This font schema is
        used in the following way:

        * Font Family	"Fira Code" &rarr; **family**
        * Font Size	12 &rarr; **size**
        * Font Color dracula white &rarr; **color**

        See also: https://github.com/tonsky/FiraCode
    """

    family: str = "Fira Code"
    size: int = 12
    color: str = "#f8f8f2"
