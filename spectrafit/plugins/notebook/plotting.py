"""DataFrame plotting utilities for Jupyter notebooks.

This module contains the DataFramePlot class for plotting dataframes
in various formats in Jupyter notebooks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.express as px

from plotly.subplots import make_subplots

from spectrafit.api.notebook_model import PlotAPI
from spectrafit.api.tools_model import ColumnNamesAPI


if TYPE_CHECKING:
    import pandas as pd

    from plotly.graph_objects import Figure


class DataFramePlot:
    """Class to plot a dataframe."""

    def plot_2dataframes(
        self,
        args_plot: PlotAPI,
        df_1: pd.DataFrame,
        df_2: pd.DataFrame | None = None,
    ) -> None:
        """Plot two dataframes.

        !!! info "About the plot"

            The plot is a combination of two plots. The first plot can be the
            residual plot of a fit or the _modified_ data. The second plot can be the
            fit or the original data.

        !!! missing "`line_dash_map`"

            Currently, the `line_dash_map` is not working, and the dash is not
            plotted. This is likely due to the columns not being labeled in the
            dataframe.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df_1 (pd.DataFrame): First dataframe to plot, which will generate
                a fit plot with residual plot. The ratio is 70% to 20% with
                10% space in between.
            df_2 (Optional[pd.DataFrame], optional): Second optional dataframe to
                plot for comparison. In this case, the ratio between the first
                and second plot will be the same. Defaults to None.

        """
        if df_2 is None:
            fig = self._plot_single_dataframe(args_plot, df_1)
        else:
            fig = self._plot_two_dataframes(args_plot, df_1, df_2)

        fig.show(
            config={
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": "plot_of_2_dataframes",
                    "scale": 4,
                },
            },
        )

    def _plot_single_dataframe(self, args_plot: PlotAPI, df: pd.DataFrame) -> Figure:
        """Plot a single dataframe with residuals."""
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.05,
        )

        residual_fig = self._create_residual_plot(df, args_plot)
        fit_fig = self._create_fit_plot(df, args_plot)

        for trace in residual_fig["data"]:
            fig.add_trace(trace, row=1, col=1)
        for trace in fit_fig["data"]:
            fig.add_trace(trace, row=2, col=1)

        self._update_plot_layout(fig, args_plot, df_2_provided=False)
        return fig

    def _plot_two_dataframes(
        self,
        args_plot: PlotAPI,
        df_1: pd.DataFrame,
        df_2: pd.DataFrame,
    ) -> Figure:
        """Plot two dataframes for comparison."""
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.05,
        )

        fig1 = px.line(df_1, x=args_plot.x, y=args_plot.y)
        fig2 = px.line(df_2, x=args_plot.x, y=args_plot.y)

        for trace in fig1["data"]:
            fig.add_trace(trace, row=1, col=1)
        for trace in fig2["data"]:
            fig.add_trace(trace, row=2, col=1)

        self._update_plot_layout(fig, args_plot, df_2_provided=True)
        return fig

    def _create_residual_plot(self, df: pd.DataFrame, args_plot: PlotAPI) -> Figure:
        """Create the residual plot."""
        return px.line(
            df,
            x=ColumnNamesAPI().energy,
            y=ColumnNamesAPI().residual,
            color_discrete_sequence=[args_plot.color.residual],
        )

    def _create_fit_plot(self, df: pd.DataFrame, args_plot: PlotAPI) -> Figure:
        """Create the fit plot."""
        y_columns = df.columns.drop(
            [ColumnNamesAPI().energy, ColumnNamesAPI().residual],
        )
        color_map = {
            ColumnNamesAPI().intensity: args_plot.color.intensity,
            ColumnNamesAPI().fit: args_plot.color.fit,
            **dict.fromkeys(
                y_columns.drop([ColumnNamesAPI().intensity, ColumnNamesAPI().fit]),
                args_plot.color.components,
            ),
        }
        line_dash_map = {
            ColumnNamesAPI().intensity: "solid",
            ColumnNamesAPI().fit: "longdash",
            **dict.fromkeys(
                y_columns.drop([ColumnNamesAPI().intensity, ColumnNamesAPI().fit]),
                "dash",
            ),
        }
        return px.line(
            df,
            x=ColumnNamesAPI().energy,
            y=y_columns,
            color_discrete_map=color_map,
            line_dash_map=line_dash_map,
        )

    def _update_plot_layout(
        self,
        fig: Figure,
        args_plot: PlotAPI,
        df_2_provided: bool,
    ) -> None:
        """Update the plot layout."""
        height = args_plot.size[1][0]
        self.update_layout_axes(fig, args_plot, height)

        xaxis_title = self.title_text(
            name=args_plot.xaxis_title.name,
            unit=args_plot.xaxis_title.unit,
        )
        yaxis_title = self.title_text(
            name=args_plot.yaxis_title.name,
            unit=args_plot.yaxis_title.unit,
        )

        fig.update_xaxes(title_text=xaxis_title, row=1, col=1)
        fig.update_xaxes(title_text=xaxis_title, row=2, col=1)

        if not df_2_provided:
            residual_title = self.title_text(
                name=args_plot.residual_title.name,
                unit=args_plot.residual_title.unit,
            )
            fig["layout"]["yaxis1"].update(domain=[0.8, 1])
            fig["layout"]["yaxis2"].update(domain=[0, 0.7])
            fig.update_yaxes(title_text=residual_title, row=1, col=1)
            fig.update_yaxes(title_text=yaxis_title, row=2, col=1)

            # Apply y-axis inversion if requested (for main spectrum)
            if args_plot.yaxis_title.invert:
                fig.update_yaxes(autorange="reversed", row=2, col=1)
        else:
            fig.update_yaxes(title_text=yaxis_title, row=1, col=1)
            fig.update_yaxes(title_text=yaxis_title, row=2, col=1)

            # Apply y-axis inversion if requested (for both plots in this layout)
            if args_plot.yaxis_title.invert:
                fig.update_yaxes(autorange="reversed", row=1, col=1)
                fig.update_yaxes(autorange="reversed", row=2, col=1)

    def plot_dataframe(self, args_plot: PlotAPI, df: pd.DataFrame) -> None:
        """Plot the dataframe according to the PlotAPI arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df (pd.DataFrame): Dataframe to plot.

        """
        fig = px.line(df, x=args_plot.x, y=args_plot.y)
        height = args_plot.size[1][0]
        self.update_layout_axes(fig, args_plot, height)

        fig.update_xaxes(
            title_text=self.title_text(
                name=args_plot.xaxis_title.name,
                unit=args_plot.xaxis_title.unit,
            ),
        )
        fig.update_yaxes(
            title_text=self.title_text(
                name=args_plot.yaxis_title.name,
                unit=args_plot.yaxis_title.unit,
            ),
        )
        fig.show(
            config={
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": "plot_dataframe",
                    "scale": 4,
                },
            },
        )

    def plot_global_fit(self, args_plot: PlotAPI, df: pd.DataFrame) -> None:
        """Plot the global dataframe according to the PlotAPI arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df (pd.DataFrame): Dataframe to plot.

        """
        num_fits = df.columns.str.startswith(ColumnNamesAPI().fit).sum()
        for i in range(1, num_fits + 1):
            cols = [col for col in df.columns if col.endswith(f"_{i}")]
            cols.append(ColumnNamesAPI().energy)
            df_subset = df[cols].rename(
                columns={
                    f"{ColumnNamesAPI().intensity}_{i}": ColumnNamesAPI().intensity,
                    f"{ColumnNamesAPI().fit}_{i}": ColumnNamesAPI().fit,
                    f"{ColumnNamesAPI().residual}_{i}": ColumnNamesAPI().residual,
                },
            )
            self.plot_2dataframes(args_plot, df_subset)

    def plot_metric(
        self,
        args_plot: PlotAPI,
        df_metric: pd.DataFrame,
        bar_criteria: str | list[str],
        line_criteria: str | list[str],
    ) -> None:
        """Plot the metric according to the PlotAPI arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df_metric (pd.DataFrame): Metric dataframe to plot.
            bar_criteria (Union[str, List[str]]): Criteria to plot as bars.
            line_criteria (Union[str, List[str]]): Criteria to plot as lines.

        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig_bar = px.bar(
            df_metric,
            y=bar_criteria,
            color_discrete_sequence=args_plot.color.bars,
        )
        fig_line = px.line(
            df_metric,
            y=line_criteria,
            color_discrete_sequence=args_plot.color.lines,
        )
        fig_line.update_traces(mode="lines+markers", yaxis="y2")

        for trace in fig_bar.data:
            fig.add_trace(trace)
        for trace in fig_line.data:
            fig.add_trace(trace)

        fig.update_layout(xaxis_type="category")
        height = args_plot.size[1][1]
        self.update_layout_axes(fig, args_plot, height)

        fig.update_xaxes(
            title_text=self.title_text(
                name=args_plot.run_title.name,
                unit=args_plot.run_title.unit,
            ),
        )
        fig.update_yaxes(
            title_text=self.title_text(
                name=args_plot.metric_title.name_0,
                unit=args_plot.metric_title.unit_0,
            ),
            secondary_y=False,
        )
        fig.update_yaxes(
            title_text=self.title_text(
                name=args_plot.metric_title.name_1,
                unit=args_plot.metric_title.unit_1,
            ),
            secondary_y=True,
        )
        fig.show(
            config={
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": "plot_metric",
                    "scale": 4,
                },
            },
        )

    def update_layout_axes(
        self,
        fig: Figure,
        args_plot: PlotAPI,
        height: int,
    ) -> Figure:
        """Update the layout of the plot.

        Args:
            fig (Figure): Figure to update.
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            height (int): Height of the plot.

        Returns:
            Figure: Updated figure.

        """
        fig.update_layout(
            title=args_plot.title,
            legend_title=args_plot.legend_title,
            legend=args_plot.legend.model_dump(),
            font=args_plot.font.model_dump(),
            showlegend=args_plot.show_legend,
            width=args_plot.size[0],
            height=height,
            paper_bgcolor=args_plot.color.paper,
            plot_bgcolor=args_plot.color.plot,
        )

        minor_ticks = self.get_minor(args_plot)

        fig.update_xaxes(
            minor=minor_ticks,
            gridcolor=args_plot.color.grid,
            linecolor=args_plot.color.line,
            zerolinecolor=args_plot.color.zero_line,
            color=args_plot.color.color,
        )
        fig.update_yaxes(
            minor=minor_ticks,
            gridcolor=args_plot.color.grid,
            linecolor=args_plot.color.line,
            zerolinecolor=args_plot.color.zero_line,
            color=args_plot.color.color,
        )
        return fig

    @staticmethod
    def title_text(name: str, unit: str | None = None) -> str:
        """Return the title text.

        Args:
            name (str): Name of the variable.
            unit (Optional[str], optional): Unit of the variable. Defaults to None.

        Returns:
            str: Title text.

        """
        return f"{name} [{unit}]" if unit else name

    def get_minor(self, args_plot: PlotAPI) -> dict[str, str | bool]:
        """Get the minor axis arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.

        Returns:
            Dict[str, Union[str, bool]]: Dictionary with the minor axis arguments.

        """
        return {
            "tickcolor": args_plot.color.ticks,
            "showgrid": args_plot.grid.show,
            "ticks": args_plot.grid.ticks,
            "griddash": args_plot.grid.dash,
        }
