"""Color themes for the Plots in Jupyter Notebooks."""
from typing import List

from spectrafit.api.notebook_model import ColorAPI
from spectrafit.api.notebook_model import FontAPI


__fira_code__ = "Fira Code"


class DraculaColor(ColorAPI):
    """Dracula color theme for SpectraFit.

    !!! info "Dracula Color"

        The [Dracula Color](https://draculatheme.com/contribute) is a color theme is
        used for the dark mode of the `SpectraFit` application. This color theme is
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
    bars: List[str] = ["#803C62", "#FFC4E6", "#FF79C6", "#806273", "#CC609D"]
    lines: List[str] = ["#805C36", "#FFDCB8", "#FFB86C", "#806E5C", "#CC9356"]
    components: str = "#ff79c6"
    paper: str = "#282a36"
    plot: str = "#282a36"
    color: str = "#f8f8f2"
    grid: str = "#f8f8f2"
    line: str = "#6272a4"
    zero_line: str = "#8be9fd"
    ticks: str = "#f8f8f2"
    font: str = "#f8f8f2"


class DraculaFont(FontAPI):
    """Dracula font theme for SpectraFit.

    !!! info "Dracula Font"

        The [Dracula Font](https://draculatheme.com/contribute) is a font theme is
        used for the dark mode of the `SpectraFit` application. This font theme is
        used in the following way:

        * Font Family	"Fira Code" &rarr; **family**
        * Font Size	12 &rarr; **size**
        * Font Color dracula white &rarr; **color**

        See also: https://github.com/tonsky/FiraCode
    """

    family: str = __fira_code__
    size: int = 12
    color: str = "#f8f8f2"


class ColorBlindColor(ColorAPI):
    """Color blind theme for SpectraFit."""

    intensity: str = "#1f77b4"
    residual: str = "#ff7f0e"
    fit: str = "#d62728"
    bars: List[str] = ["#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    lines: List[str] = ["#8c564b", "#e377c2", "#7f7f7f", "#d62728", "#9467bd"]
    components: str = "#2ca02c"
    paper: str = "#ffffff"
    plot: str = "#ffffff"
    color: str = "#000000"
    grid: str = "#d9d9d9"
    line: str = "#d9d9d9"
    zero_line: str = "#1f77b4"
    ticks: str = "#000000"
    font: str = "#000000"


class ColorBlindFont(FontAPI):
    """Color blind font theme for SpectraFit."""

    family: str = "Open Sans"
    size: int = 12
    color: str = "#000000"


class MoonAkiColor(ColorAPI):
    """MoonAki dark color theme for SpectraFit."""

    intensity: str = "#f92672"
    residual: str = "#fd971f"
    fit: str = "#a6e22e"
    bars: List[str] = ["#66d9ef", "#ae81ff", "#f92672", "#a6e22e", "#fd971f"]
    lines: List[str] = ["#f92672", "#a6e22e", "#fd971f", "#66d9ef", "#ae81ff"]
    components: str = "#ae81ff"
    paper: str = "#272822"
    plot: str = "#272822"
    color: str = "#f8f8f2"
    grid: str = "#49483e"
    line: str = "#49483e"
    zero_line: str = "#66d9ef"
    ticks: str = "#f8f8f2"
    font: str = "#f8f8f2"


class MoonAkiFont(FontAPI):
    """MoonAki dark font theme for SpectraFit."""

    family: str = "Monaco"
    size: int = 12
    color: str = "#f8f8f2"


class DevOpsDarkColor(ColorAPI):
    """GitHub dark color inspired theme for SpectraFit.

    Please check, https://github.com/primer/github-vscode-theme
    """

    intensity: str = "#1e4f8a"
    residual: str = "#d73a49"
    fit: str = "#22863a"
    bars: List[str] = ["#005cc5", "#6f42c1", "#d73a49", "#22863a", "#d73a49"]
    lines: List[str] = ["#d73a49", "#22863a", "#d73a49", "#005cc5", "#6f42c1"]
    components: str = "#d73a49"
    paper: str = "#0d1117"
    plot: str = "#0d1117"
    color: str = "#c9d1d9"
    grid: str = "#30363d"
    line: str = "#30363d"
    zero_line: str = "#005cc5"
    ticks: str = "#c9d1d9"
    font: str = "#c9d1d9"


class DevOpsDarkFont(FontAPI):
    """GitHub dark font inspired theme for SpectraFit.

    Please check, https://github.com/primer/github-vscode-theme
    """

    family: str = __fira_code__
    size: int = 12
    color: str = "#c9d1d9"


class DevOpsLightColor(ColorAPI):
    """GitHub light color inspired theme for SpectraFit.

    Please check, https://github.com/primer/github-vscode-theme
    """

    intensity: str = "#1e4f8a"
    residual: str = "#d73a49"
    fit: str = "#d73a49"
    bars: List[str] = ["#005cc5", "#6f42c1", "#d73a49", "#22863a", "#d73a49"]
    lines: List[str] = ["#d73a49", "#22863a", "#d73a49", "#005cc5", "#6f42c1"]
    components: str = "#22863a"
    paper: str = "#ffffff"
    plot: str = "#ffffff"
    color: str = "#000000"
    grid: str = "#d9d9d9"
    line: str = "#d9d9d9"
    zero_line: str = "#005cc5"
    ticks: str = "#000000"
    font: str = "#000000"


class DevOpsLightFont(FontAPI):
    """GitHub light font inspired theme for SpectraFit.

    Please check, https://github.com/primer/github-vscode-theme
    """

    family: str = __fira_code__
    size: int = 12
    color: str = "#000000"
