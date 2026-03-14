"""Notebook-facing fit session facade over canonical pipeline results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from spectrafit.api.notebook_model import FnameAPI
from spectrafit.jupyter.config_io import export_notebook_config_toml
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.plot_config import PlotConfig
from spectrafit.plotting import PlotSpectra
from spectrafit.reporting.service import project_canonical_report


if TYPE_CHECKING:
    from plotly.graph_objects import Figure

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.core.pipeline import FittingResult
    from spectrafit.models.results.fit_result import FitResult


@dataclass(frozen=True, slots=True)
class FitSession:
    """Notebook-first facade with simple plots, tables, and bundled exports."""

    pipeline_result: FittingResult
    source_dataframe: pd.DataFrame
    name: str = "spectrafit"

    @property
    def config(self) -> UnifiedFittingConfig:
        """Return a defensive copy of the validated fit config."""
        return self.pipeline_result.config.model_copy(deep=True)

    @property
    def fit_result(self) -> FitResult:
        """Return the canonical typed fit result."""
        return self.pipeline_result.fit_result

    @property
    def solver_results(self) -> SolverResults:
        """Return notebook-style projections over the canonical fit result."""
        return SolverResults(result=self.fit_result)

    @property
    def summary(self) -> dict[str, float | None]:
        """Return summary fit statistics as a plain notebook-friendly mapping."""
        return project_canonical_report(self.fit_result).summary.model_dump()

    def summary_frame(self) -> pd.DataFrame:
        """Return summary fit statistics as a one-row dataframe."""
        return pd.DataFrame([self.summary])

    @property
    def metrics(self) -> pd.DataFrame:
        """Return the canonical notebook metrics table."""
        return self.solver_results.current_metric.copy(deep=True)

    @property
    def peaks(self) -> pd.DataFrame:
        """Return the canonical notebook peaks table."""
        return self.solver_results.peaks_projection.to_dataframe().copy(deep=True)

    @property
    def parameters(self) -> pd.DataFrame:
        """Return the fitted parameters as a flat dataframe."""
        return pd.DataFrame(
            [
                parameter.model_dump(mode="json", exclude_none=True)
                for parameter in self.fit_result.parameters
            ]
        )

    @property
    def dataframe(self) -> pd.DataFrame:
        """Return the fitted dataframe with residual and component columns."""
        return self.pipeline_result.df.copy(deep=True)

    def figure(self) -> Figure:
        """Build the canonical Plotly figure for the fit."""
        return PlotSpectra(
            df=self.pipeline_result.df,
            config=self._plot_config(),
        ).figure()

    def plot(self) -> Figure:
        """Display the current fit and return the figure for further tweaking."""
        figure = self.figure()
        figure.show()
        return figure

    def save(
        self,
        folder: str | Path,
        *,
        name: str | None = None,
    ) -> tuple[Path, ...]:
        """Write the bundled notebook artifact set to ``folder``."""
        base_name = name or self.name
        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)

        fit_csv = output_dir / f"fit_{base_name}.csv"
        metric_csv = output_dir / f"metric_{base_name}.csv"
        peaks_csv = output_dir / f"peaks_{base_name}.csv"
        fit_html = output_dir / f"fit_{base_name}.html"
        report_toml = output_dir / f"report_{base_name}.toml"
        lock_path = output_dir / f"{base_name}.lock"

        self.pipeline_result.df.to_csv(fit_csv, index=False)
        self.metrics.to_csv(metric_csv, index=False)
        self.peaks.to_csv(peaks_csv, index=False)
        PlotSpectra(
            df=self.pipeline_result.df,
            config=self._plot_config(),
        ).write_html(fit_html)
        ExportResults().export_report(
            project_canonical_report(self.fit_result).model_dump(
                mode="json",
                exclude_none=True,
            ),
            args=FnameAPI(
                fname=base_name,
                prefix="report",
                suffix="toml",
                folder=str(output_dir),
            ),
        )
        export_notebook_config_toml(self.config, lock_path, force=True)
        return (fit_csv, metric_csv, peaks_csv, fit_html, report_toml, lock_path)

    def to_config(self) -> UnifiedFittingConfig:
        """Return a defensive copy of the validated fit config."""
        return self.config

    def to_toml(self, path: str | Path, *, force: bool = False) -> Path:
        """Write the current fit config to a TOML file."""
        resolved_path = Path(path)
        export_notebook_config_toml(self.config, resolved_path, force=force)
        return resolved_path

    def _repr_html_(self) -> str:
        """Render a compact HTML summary for notebook display."""
        return self.summary_frame().to_html(index=False)

    def _plot_config(self) -> PlotConfig:
        """Build the shared static plotting config for this session."""
        return PlotConfig(
            noplot=True,
            global_fitting=self.pipeline_result.config.context.mode,
            data_statistic=self.pipeline_result.data_statistic,
        )
