"""Plotting of the fit results.

!!! info "About the Font Cache"

    For avoiding problems with the font cache, the font cache is rebuilt at the
    beginning of the program. This can take a few seconds. If you want to avoid
    this, you can comment out the line `matplotlib.font_manager._rebuild()` in
    the `plotting.py` file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import matplotlib.font_manager
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.widgets import MultiCursor

from spectrafit.api.tools_model import ColumnNamesAPI


if TYPE_CHECKING:
    import pandas as pd


matplotlib.font_manager.findfont("serif", rebuild_if_missing=True)

sns.set_theme(style="whitegrid")
color = sns.color_palette("Paired")


class PlotSpectra:
    """Plotting of the fit results."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any] | None = None) -> None:
        """Initialize the PlotSpectra class.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str, Any], optional): The input file arguments as a dictionary
                 with additional information beyond the command line arguments. Only
                 needed for global fitting. Defaults to None.

        """
        self.df = df
        self.args = args

    def __call__(self) -> None:
        """Plot the data and the fit."""
        if self.args is not None:
            if not self.args["noplot"]:
                if self.args["global_"]:
                    self.plot_global_spectra()
                else:
                    self.plot_local_spectra()
            plt.show()

    def plot_global_spectra(self) -> None:
        """Plot spectra for global fitting.

        !!! info "Plotting of the global spectra"

            The plotting routine for global fitting is similar to the local plotting
            routine, but the spectra are plotted in a grid spectra plot. The first
            row of the grid plot contains the residuals of each single fit, the
            second row the best fit of the model with single peak contributions.
        """
        n_spec: int = len(list(self.args["data_statistic"])) - 1 if self.args else 1
        _, axs = plt.subplots(
            nrows=2,
            ncols=n_spec,
            sharex=True,
            figsize=(9, 9),
            gridspec_kw={"height_ratios": [1, 2]},
        )

        for i in range(n_spec):
            axs[0, i].set_title(f"Spectrum #{i + 1}")
            sns.regplot(
                x=ColumnNamesAPI().energy,
                y=f"{ColumnNamesAPI().residual}_{i + 1}",
                data=self.df,
                ax=axs[0, i],
                color=color[5],
            )
            axs[1, i] = sns.lineplot(
                x=ColumnNamesAPI().energy,
                y=f"{ColumnNamesAPI().intensity}_{i + 1}",
                data=self.df,
                ax=axs[1, i],
                color=color[1],
            )
            axs[1, i] = sns.lineplot(
                x=ColumnNamesAPI().energy,
                y=f"fit_{i + 1}",
                data=self.df,
                ax=axs[1, i],
                ls="--",
                color=color[0],
            )
            peaks = [
                peak
                for peak in self.df.columns
                if not peak.startswith(tuple(ColumnNamesAPI().model_dump().values()))
                and peak.endswith(f"_{i + 1}")
            ]
            color_peaks = sns.color_palette("rocket", len(peaks))
            for j, peak in enumerate(peaks):
                axs[1, i] = sns.lineplot(
                    x=ColumnNamesAPI().energy,
                    y=peak,
                    data=self.df,
                    ax=axs[1, i],
                    ls=":",
                    color=color_peaks[j],
                )

        plt.tight_layout()

    def plot_local_spectra(self) -> None:
        """Plot spectra for local fitting.

        `plot_spectra` performs a dual split plot. In the upper part, the residuum is
        plotted together with a linear regression line. This means, if the linear
        regression is a flat line, the fit and spectra are identically.
        In the lower part, the fit is plotted together with the original spectra. Also
        the single contributions of the fit are drawn.

        !!! info "About Plotting"

            `plot_spectra` is a wrapper around the `seaborn.lineplot` and
            `seaborn.regplot` function. Furthermore, the `MultiCursor` widget is used
            to create an interactive plot, for picking the energy and intensity of the
            spectrum. the `MultiCursor` widget is a part of the `matplotlib` library
            and can be used for both, the residual plot and the spectrum plot.


        ![_](../../images/image001.png)
        > The upper part shows the residuum and the linear regression line. The lower
        > part shows the fit and the single contributions of the fit.
        """
        fig, (ax1, ax2) = plt.subplots(
            2,
            sharex=True,
            figsize=(9, 9),
            gridspec_kw={"height_ratios": [1, 2]},
        )
        ax1 = sns.regplot(
            x=ColumnNamesAPI().energy,
            y=ColumnNamesAPI().residual,
            data=self.df,
            ax=ax1,
            color=color[5],
        )
        ax2 = sns.lineplot(
            x=ColumnNamesAPI().energy,
            y=ColumnNamesAPI().intensity,
            data=self.df,
            ax=ax2,
            color=color[1],
        )
        ax2 = sns.lineplot(
            x=ColumnNamesAPI().energy,
            y=ColumnNamesAPI().fit,
            data=self.df,
            ax=ax2,
            ls="--",
            color=color[0],
        )
        peaks = [
            peak
            for peak in self.df.columns
            if peak not in list(ColumnNamesAPI().model_dump().values())
        ]
        color_peaks = sns.color_palette("rocket", len(peaks))
        for i, peak in enumerate(peaks):
            ax2 = sns.lineplot(
                x=ColumnNamesAPI().energy,
                y=peak,
                data=self.df,
                ax=ax2,
                ls=":",
                color=color_peaks[i],
            )

        _ = MultiCursor(
            fig.canvas,
            (ax1, ax2),
            color=color[4],
            ls="--",
            lw=1,
            horizOn=True,
        )
