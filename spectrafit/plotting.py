"""Plot fit results with shared Plotly builders."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from plotly.colors import qualitative

from spectrafit._plot_builders import FitPlotStyle
from spectrafit._plot_builders import build_global_fit_figure
from spectrafit._plot_builders import build_local_fit_figure
from spectrafit.api.tools_model import ColumnNamesAPI
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.plot_config import PlotConfig


if TYPE_CHECKING:
    import pandas as pd

    from plotly.graph_objects import Figure


class PlotSpectra:
    """Plotting of the fit results."""

    def __init__(
        self,
        df: pd.DataFrame,
        config: PlotConfig | None = None,
    ) -> None:
        """Initialize the PlotSpectra class.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``), as well
                as the best fit and the corresponding residuum. It will be extended
                by the single contribution of the model.
            config: Typed plot configuration.  Defaults to :class:`PlotConfig()`.

        """
        self.df = df
        self.config = config or PlotConfig()

    def __call__(self) -> None:
        """Plot the data and the fit."""
        if self.config.noplot:
            return
        self.figure().show()

    def figure(self) -> Figure:
        """Build the configured Plotly figure for the fit dataframe."""
        return (
            self.plot_global_spectra()
            if self.config.global_fitting != FittingMode.STANDARD
            else self.plot_local_spectra()
        )

    def write_html(self, output_path: str | Path) -> Path:
        """Write the configured Plotly figure as a standalone HTML artifact."""
        resolved_output = Path(output_path)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        self.figure().write_html(
            resolved_output,
            full_html=True,
            include_plotlyjs=True,
        )
        return resolved_output

    @staticmethod
    def _style() -> FitPlotStyle:
        return FitPlotStyle(component_colors=tuple(qualitative.Plotly[2:]))

    @staticmethod
    def _apply_layout(figure: Figure) -> Figure:
        columns = ColumnNamesAPI()
        figure.update_layout(template="plotly_white", hovermode="x unified")
        figure.update_xaxes(title_text=columns.energy)
        return figure

    def plot_global_spectra(self) -> Figure:
        """Build a Plotly figure for global fitting."""
        return self._apply_layout(
            build_global_fit_figure(
                self.df,
                data_statistic=self.config.data_statistic,
                style=self._style(),
            )
        )

    def plot_local_spectra(self) -> Figure:
        """Build a Plotly figure for local fitting."""
        return self._apply_layout(build_local_fit_figure(self.df, style=self._style()))
