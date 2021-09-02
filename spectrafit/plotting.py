"""Plotting of the fit results."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from matplotlib.widgets import MultiCursor


sns.set_theme(style="whitegrid")
color = sns.color_palette("Paired")


def plot_spectra(df: pd.DataFrame) -> None:
    """Plot spectra with seaborn and matplotlib.

    `plot_spectra` performs a dual split plot. In the upper part, the residuum is
     plotted together with a linear regression line. This means, if the linear
     regression is a flat line, the fit and spectra are identically.
     In the lower part, the fit is plotted together with the original spectra. Also
     the single contributions of the fit are drawn.

    !!! info "About Plotting"

        `plot_spectra` is a wrapper around the `seaborn.lineplot` and `seaborn.regplot`
         function. Furthermore, the `MultiCursor` widget is used to create an
         interactive plot, for picking the energy and intensity of the spectrum. the
         `MultiCursor` widget is a part of the `matplotlib` library and can be used for
         both, the residual plot and the spectrum plot.


    ![_](../../images/image001.png)
    > The upper part shows the residuum and the linear regression line. The lower part
    shows the fit and the single contributions of the fit.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
    """
    fig, (ax1, ax2) = plt.subplots(
        2, sharex=True, figsize=(9, 9), gridspec_kw={"height_ratios": [1, 2]}
    )
    ax1 = sns.regplot(x="energy", y="residual", data=df, ax=ax1, color=color[5])
    ax2 = sns.lineplot(x="energy", y="intensity", data=df, ax=ax2, color=color[1])
    ax2 = sns.lineplot(x="energy", y="fit", data=df, ax=ax2, ls="--", color=color[0])
    peaks = [
        peak
        for peak in df.columns
        if peak not in ["residual", "energy", "intensity", "fit"]
    ]
    color_peaks = sns.color_palette("rocket", len(peaks))
    for i, peak in enumerate(peaks):
        ax2 = sns.lineplot(
            x="energy", y=peak, data=df, ax=ax2, ls=":", color=color_peaks[i]
        )

    _ = MultiCursor(fig.canvas, (ax1, ax2), color=color[4], ls="--", lw=1, horizOn=True)
    plt.show()
