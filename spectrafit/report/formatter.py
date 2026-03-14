"""Frozen dict-format report helpers for legacy import paths.

Canonical fit-result ownership now lives in typed post-processing models and
:mod:`spectrafit.reporting.service`. This module only retains dict-shaped
compatibility buffers for callers that still import the legacy formatter API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from warnings import warn

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.results.fit_result import ComputationalMeta
from spectrafit.models.results.fit_result import ErrorbarDiagnostics
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import FitStatistics
from spectrafit.report._warnings import warn_meassage
from spectrafit.reporting.service import project_canonical_report


if TYPE_CHECKING:
    from lmfit import Minimizer
    from lmfit import Parameter
    from lmfit import Parameters
    from lmfit.minimizer import minimize

type FitReportBuffer = dict[str, dict[str, object]]  # intentional: frozen Layer 4
"""Buffer dict holding fit report sections: configurations, statistics, variables, etc."""


class ReportConfigurations(BaseModel):
    """Typed compatibility projection for legacy report configuration fields."""

    model_config = ConfigDict(extra="forbid")

    fitting_method: str = ""
    function_evals: int = 0
    data_points: int = 0
    variable_names: list[str] = Field(default_factory=list)
    variable_numbers: int = 0
    degree_of_freedom: int = 0


class ReportStatistics(BaseModel):
    """Typed compatibility projection for legacy goodness-of-fit fields."""

    model_config = ConfigDict(extra="forbid")

    chi_square: float = 0.0
    reduced_chi_square: float = 0.0
    akaike_information: float = 0.0
    bayesian_information: float = 0.0


class ReportVariableEntry(BaseModel):
    """Typed compatibility projection for one variable entry."""

    model_config = ConfigDict(extra="forbid")

    init_value: float | str | None = None
    model_value: float | None = None
    best_value: float | None = None
    error_relative: float | None = None
    error_absolute: float | None = None


class ReportErrorbars(BaseModel):
    """Typed compatibility projection for legacy errorbar issue flags."""

    model_config = ConfigDict(extra="forbid")

    at_initial_value: str | None = None
    at_boundary: str | None = None


class LegacyFitReport(BaseModel):
    """Typed projection that preserves the frozen ``fit_report_as_dict`` contract."""

    model_config = ConfigDict(extra="forbid")

    configurations: ReportConfigurations = Field(default_factory=ReportConfigurations)
    statistics: ReportStatistics = Field(default_factory=ReportStatistics)
    variables: dict[str, ReportVariableEntry] = Field(default_factory=dict)
    errorbars: ReportErrorbars = Field(default_factory=ReportErrorbars)
    correlations: dict[str, dict[str, float]] = Field(default_factory=dict)
    covariance_matrix: dict[str, dict[str, float]] = Field(default_factory=dict)
    computational: ComputationalMeta = Field(default_factory=ComputationalMeta)

    def to_buffer(self) -> FitReportBuffer:
        """Project the typed compatibility model to the frozen dict contract."""
        return {
            "configurations": self.configurations.model_dump(
                mode="json",
                exclude_none=True,
            ),
            "statistics": self.statistics.model_dump(mode="json", exclude_none=True),
            "variables": {
                name: entry.model_dump(mode="json", exclude_none=True)
                for name, entry in self.variables.items()
            },
            "errorbars": self.errorbars.model_dump(mode="json", exclude_none=True),
            "correlations": self.correlations,
            "covariance_matrix": self.covariance_matrix,
            "computational": self.computational.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }


def _build_fit_insights(
    result: minimize,
    settings: Minimizer | None = None,
) -> FitInsights:
    """Build canonical typed fit insights from runtime lmfit state."""
    return FitInsights.from_minimizer_result(
        result,
        max_nfev=(
            int(getattr(settings, "max_nfev", 0) or 0) if settings is not None else None
        ),
        nan_policy=(
            str(getattr(settings, "nan_policy", "raise"))
            if settings is not None
            else None
        ),
        scale_covar=(
            bool(settings.scale_covar)
            if settings is not None and hasattr(settings, "scale_covar")
            else None
        ),
        calc_covar=(
            bool(settings.calc_covar)
            if settings is not None and hasattr(settings, "calc_covar")
            else None
        ),
    )


def _warn_for_errorbar_diagnostics(diagnostics: ErrorbarDiagnostics) -> None:
    """Emit legacy warning messages from typed diagnostics."""
    for message in diagnostics.warning_messages():
        warn(warn_meassage(msg=message), stacklevel=3)


def _build_report_variables(
    *,
    result: minimize,
    fit_insights: FitInsights,
    modelpars: Parameters | None,
) -> dict[str, ReportVariableEntry]:
    """Build typed compatibility variable entries."""
    variables: dict[str, ReportVariableEntry] = {}
    for name, parameter in result.params.items():
        fit_variable = fit_insights.variables.get(name)
        model_param = (
            modelpars[name] if modelpars is not None and name in modelpars else None
        )

        error_absolute: float | None = None
        if fit_variable is not None and fit_variable.stderr is not None:
            if fit_variable.best_value == 0:
                error_absolute = float("inf")
            elif fit_variable.best_value is not None:
                error_absolute = (
                    abs(fit_variable.stderr / fit_variable.best_value) * 100
                )

        variables[name] = ReportVariableEntry(
            init_value=get_init_value(parameter, model_param),
            model_value=(
                float(model_param.value)
                if model_param is not None
                else fit_variable.model_value
                if fit_variable is not None
                else None
            ),
            best_value=fit_variable.best_value if fit_variable is not None else None,
            error_relative=fit_variable.stderr if fit_variable is not None else None,
            error_absolute=error_absolute,
        )
    return variables


def _build_legacy_fit_report(
    *,
    result: minimize,
    settings: Minimizer | None = None,
    modelpars: Parameters | None = None,
) -> LegacyFitReport:
    """Build the frozen compatibility report from typed projection models."""
    fit_statistics = FitStatistics.from_minimizer_result(result)
    fit_insights = _build_fit_insights(result, settings)
    fit_result = FitResult(
        statistics=fit_statistics,
        fit_insights=fit_insights,
    )
    report_schema = project_canonical_report(fit_result)
    _warn_for_errorbar_diagnostics(report_schema.solver.computational.diagnostics)

    return LegacyFitReport(
        configurations=ReportConfigurations(
            fitting_method=report_schema.statistics.method,
            function_evals=report_schema.statistics.nfev,
            data_points=report_schema.statistics.ndata,
            variable_names=list(result.var_names or result.params.keys()),
            variable_numbers=report_schema.statistics.nvarys,
            degree_of_freedom=report_schema.statistics.nfree,
        ),
        statistics=ReportStatistics(
            chi_square=report_schema.summary.chi_square or 0.0,
            reduced_chi_square=report_schema.summary.reduced_chi_square or 0.0,
            akaike_information=report_schema.summary.akaike_information or 0.0,
            bayesian_information=report_schema.summary.bayesian_information or 0.0,
        ),
        variables=_build_report_variables(
            result=result,
            fit_insights=fit_result.fit_insights,
            modelpars=modelpars,
        ),
        errorbars=ReportErrorbars.model_validate(
            report_schema.solver.computational.diagnostics.report_mapping()
        ),
        correlations=report_schema.solver.component_correlation,
        covariance_matrix=report_schema.solver.covariance_matrix,
        computational=report_schema.solver.computational,
    )


def fit_report_as_dict(
    inpars: minimize,
    settings: Minimizer,
    modelpars: Parameters | None = None,
) -> FitReportBuffer:
    """Generate the best fit report as dictionary.

    !!! info "About `fit_report_as_dict`"

        The report contains the best-fit values for the parameters and their
        uncertainties and correlations. The report is generated as dictionary and
        consists of the following three main criteria:

            1. Fit Statistics
            2. Fit variables
            3. Fit correlations

    Args:
        inpars (minimize): Input Parameters from a fit or the  Minimizer results
             returned from a fit.
        settings (Minimizer): The lmfit `Minimizer`-class as a general minimizer
                for curve fitting and optimization. It is required to extract the
                initial settings of the fit.
        modelpars (Parameters, optional): Known Model Parameters.
            Defaults to None.

    Returns:
         FitReportBuffer: The report as a dictionary.

    """
    return _build_legacy_fit_report(
        result=inpars,
        settings=settings,
        modelpars=modelpars,
    ).to_buffer()


def get_init_value(
    param: Parameter,
    modelpars: Parameter | None = None,
) -> float | str:
    """Get the initial value of a parameter.

    Args:
        param (Parameter): The Parameter to extract the initial value from.
        modelpars (Parameter, optional): Known Model Parameters. Defaults to None.

    Returns:
        float | str: The initial value.

    """
    if param.init_value is not None:
        return param.init_value
    if param.expr is not None:
        return f"As expressed value: {param.expr}"
    if modelpars is not None and param.name in modelpars:
        return modelpars[param.name].value
    return f"As fixed value: {param.value}"


def _extracted_computational_from_results(
    result: minimize,
    settings: Minimizer,
    buffer: FitReportBuffer,
) -> FitReportBuffer:
    """Extract the computational from the results.

    Args:
        result (minimize): Input Parameters from a fit or the  Minimizer results
            returned from a fit.
        settings (Minimizer): The lmfit `Minimizer`-class as a general minimizer
                for curve fitting and optimization. It is required to extract the
                initial settings of the fit.
        buffer (FitReportBuffer): The buffer to store the results.

    Returns:
        FitReportBuffer: The buffer with updated results.

    """
    legacy_report = _build_legacy_fit_report(result=result, settings=settings)
    buffer["computational"] = legacy_report.computational.model_dump(
        mode="json",
        exclude_none=True,
    )
    buffer["errorbars"] = legacy_report.errorbars.model_dump(
        mode="json",
        exclude_none=True,
    )
    return buffer


def _extracted_gof_from_results(
    result: minimize,
    buffer: FitReportBuffer,
    params: Parameters,
) -> tuple[minimize, FitReportBuffer, Parameters]:
    """Extract the goodness of fit from the results.

    Args:
        result (minimize): Input Parameters from a fit or the  Minimizer results
        buffer (FitReportBuffer): The buffer to store the results.
        params (Parameters): The parameters of the fit.

    Returns:
        minimize: The results.
        FitReportBuffer: The buffer with updated results.
        Parameters: The parameters.

    """
    legacy_report = _build_legacy_fit_report(result=result)
    buffer["configurations"] = legacy_report.configurations.model_dump(
        mode="json",
        exclude_none=True,
    )
    buffer["statistics"] = legacy_report.statistics.model_dump(
        mode="json",
        exclude_none=True,
    )
    buffer["errorbars"] = legacy_report.errorbars.model_dump(
        mode="json",
        exclude_none=True,
    )
    return result, buffer, params


__all__ = [
    "FitReportBuffer",
    "_extracted_gof_from_results",
    "fit_report_as_dict",
    "get_init_value",
]
