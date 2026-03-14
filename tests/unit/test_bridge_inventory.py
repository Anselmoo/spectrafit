"""Static bridge-inventory regression tests for v1→v2 migration boundaries."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import subprocess
import sys
import warnings

from pathlib import Path

import pandas as pd
import pytest
import spectrafit.adapters.data_config_args as data_config_args_adapter
import spectrafit.cli._callbacks as cli_callbacks
import spectrafit.cli._status as cli_status
import spectrafit.cli.commands.fit as cli_fit
import spectrafit.cli.commands.report as cli_report
import spectrafit.jupyter.export as jupyter_export
import spectrafit.jupyter.solver as jupyter_solver
import spectrafit.models.data_config as data_config_model
import spectrafit.models.solver as solver_models

from spectrafit.api import notebook_model
from spectrafit.generators import synthetic as synthetic_generator
from spectrafit.jupyter import config_io
from spectrafit.jupyter import result_projection
from spectrafit.models import parameter_builder
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult


def _count_named_calls(module: object, function_name: str) -> int:
    source = inspect.getsource(module)
    tree = ast.parse(source)
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == function_name
    )


def _top_level_definition_names(module: object) -> set[str]:
    source = inspect.getsource(module)
    tree = ast.parse(source)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _import_legacy_report_module(module_name: str) -> object:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        return importlib.import_module(module_name)


@pytest.mark.unit
def test_data_config_model_drops_legacy_args_adapter() -> None:
    """Canonical DataConfig model should not own legacy args-dict adaptation."""
    model_source = inspect.getsource(data_config_model)
    adapter_source = inspect.getsource(data_config_args_adapter)

    assert "from_args_dict" not in model_source
    assert "def data_config_from_args_dict" in adapter_source


@pytest.mark.unit
def test_legacy_core_export_module_is_removed() -> None:
    """The dead SaveResult-era export module should stay deleted."""
    assert importlib.util.find_spec("spectrafit.core.export") is None


@pytest.mark.unit
def test_builtin_solver_shim_module_is_removed() -> None:
    """Internal builtin solver shim should stay deleted once callers move over."""
    assert importlib.util.find_spec("spectrafit.models.functions.builtin") is None


@pytest.mark.unit
def test_api_package_imports_without_adapter_preload() -> None:
    """The API package should import directly without relying on adapter import order."""
    result = subprocess.run(  # noqa: S603 - fixed interpreter/module invocation
        [sys.executable, "-c", "import spectrafit.api"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.unit
def test_notebook_model_uses_public_plotly_color_api() -> None:
    """Notebook plotting config should not depend on Plotly private modules."""
    notebook_source = inspect.getsource(notebook_model)

    assert "_plotly_utils" not in notebook_source
    assert "from plotly.colors" in notebook_source


@pytest.mark.unit
def test_adapter_ingress_imports_without_core_cycle() -> None:
    """Adapter config ingress should import in a fresh process without cycles."""
    result = subprocess.run(  # noqa: S603 - fixed interpreter/module invocation
        [sys.executable, "-c", "import spectrafit.adapters.unified_config_input"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.unit
def test_v1_migration_imports_without_adapter_cycle() -> None:
    """Legacy migration helpers should import in a fresh process without cycles."""
    result = subprocess.run(  # noqa: S603 - fixed interpreter/module invocation
        [
            sys.executable,
            "-c",
            "from spectrafit.adapters.v1_config_migration import migrate_v1_payload",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.unit
def test_migrate_v1_cli_help_runs_without_import_cycle() -> None:
    """Migration CLI help should remain usable in a fresh interpreter."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "migrate_v1_config.py"
    result = subprocess.run(  # noqa: S603 - fixed interpreter/module invocation
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Read a legacy v1 config and emit a validated v2 config file." in result.stdout


@pytest.mark.unit
@pytest.mark.parametrize(
    "module",
    [
        config_io,
        jupyter_export,
        result_projection,
        jupyter_solver,
    ],
)
def test_editable_bridge_modules_do_not_use_cast(module: object) -> None:
    """Editable bridge modules should not recover structure via cast()."""
    assert _count_named_calls(module, "cast") == 0


@pytest.mark.unit
def test_result_bridge_does_not_use_cast() -> None:
    """result_bridge must not recover structure via cast()."""
    from spectrafit.core import result_bridge

    assert _count_named_calls(result_bridge, "cast") == 0


@pytest.mark.unit
def test_result_bridge_does_not_use_save_result() -> None:
    """result_bridge must not directly call SaveResult."""
    from spectrafit.core import result_bridge

    source = inspect.getsource(result_bridge)
    tree = ast.parse(source)
    save_result_nodes = [
        node
        for node in ast.walk(tree)
        if (isinstance(node, ast.Name) and node.id == "SaveResult")
        or (isinstance(node, ast.Attribute) and node.attr == "SaveResult")
    ]
    assert save_result_nodes == []


@pytest.mark.unit
def test_cli_report_is_not_a_report_renderer() -> None:
    """CLI report command should delegate formatting to shared reporting services."""
    source = inspect.getsource(cli_report)
    assert "render_report(" in source
    assert "def _generate_text_report" not in source
    assert "def _generate_markdown_report" not in source
    assert "def _generate_json_report" not in source


@pytest.mark.unit
def test_cli_status_is_owned_by_cli_package() -> None:
    """CLI version/status wiring should not import the frozen report printer."""
    callback_source = inspect.getsource(cli_callbacks)
    fit_source = inspect.getsource(cli_fit)
    status_source = inspect.getsource(cli_status)

    assert "PrintingStatus" not in callback_source
    assert "PrintingStatus" not in fit_source
    assert "spectrafit.report" not in callback_source
    assert "spectrafit.report" not in fit_source
    assert "from spectrafit import __version__" in status_source


@pytest.mark.unit
def test_legacy_report_package_uses_internal_support_modules() -> None:
    """Legacy report internals should share local helpers instead of cross-importing."""
    legacy_report_confidence = _import_legacy_report_module(
        "spectrafit.report.confidence"
    )
    legacy_report_formatter = _import_legacy_report_module(
        "spectrafit.report.formatter"
    )
    legacy_report_printer = _import_legacy_report_module("spectrafit.report.printer")

    confidence_source = inspect.getsource(legacy_report_confidence)
    formatter_source = inspect.getsource(legacy_report_formatter)
    printer_source = inspect.getsource(legacy_report_printer)

    assert "PrintingResults" not in confidence_source
    assert "from spectrafit.report._table import print_tabulate_df" in confidence_source
    assert "from spectrafit.report._warnings import warn_meassage" in formatter_source
    assert "from spectrafit.report._table import print_tabulate_df" in printer_source
    assert "from spectrafit.reporting.service import VERBOSE_DETAILED" in printer_source


@pytest.mark.unit
def test_solver_orchestration_drops_legacy_solver_args_bridge() -> None:
    """Notebook orchestration should no longer define dict-based solver args adapters."""
    from spectrafit.jupyter import solver_orchestration

    source = inspect.getsource(solver_orchestration)
    assert "def build_fit_result" not in source
    assert "LegacySolverArgs" not in source
    assert "build_solver_args" not in source


@pytest.mark.unit
def test_solver_models_use_canonical_solver_config() -> None:
    """Core solver should depend on canonical solver config models, not API DTOs."""
    source = inspect.getsource(solver_models)
    assert "SolverConfig" in source
    assert "SolverModelsAPI" not in source
    assert "def solve(" in source
    assert "def __call__(" not in source
    assert "self._is_global" not in source


@pytest.mark.unit
def test_solver_orchestration_resolves_canonical_solver_config() -> None:
    """Notebook orchestration should construct canonical solver config internally."""
    from spectrafit.jupyter import solver_orchestration

    source = inspect.getsource(solver_orchestration.resolve_solver_options)
    assert "SolverConfig" in source
    assert "SolverModelsAPI(" not in source
    assert "normalize_conf_interval_value" in inspect.getsource(
        solver_orchestration.normalize_conf_interval
    )


@pytest.mark.unit
def test_result_bridge_does_not_depend_on_conf_interval_api() -> None:
    """Runtime result bridge should normalize only canonical CI shapes internally."""
    from spectrafit.core import result_bridge

    source = inspect.getsource(result_bridge)
    assert "ConfIntervalAPI" not in source


@pytest.mark.unit
def test_conf_interval_api_is_quarantined_to_notebook_input_only() -> None:
    """ConfIntervalAPI should stay out of config/export bridges."""
    from spectrafit.jupyter import core

    assert "ConfIntervalAPI" not in inspect.getsource(config_io)
    assert "ConfIntervalAPI" not in inspect.getsource(jupyter_export)
    assert "ConfIntervalAPI" in inspect.getsource(core.SpectraFitNotebook.solver_model)


@pytest.mark.unit
def test_solver_callers_use_named_solve_api() -> None:
    """Pipeline owns solve execution; notebook should delegate into the pipeline."""
    from spectrafit.core import pipeline
    from spectrafit.jupyter import core

    pipeline_source = inspect.getsource(pipeline.FittingPipeline)
    notebook_solver_source = inspect.getsource(core.SpectraFitNotebook.solver_model)

    assert "solver.solve()" in pipeline_source
    assert "solver()" not in pipeline_source
    assert "FittingPipeline(" in notebook_solver_source
    assert ".run()" in notebook_solver_source
    assert "solver.solve()" not in notebook_solver_source


@pytest.mark.unit
def test_parameter_builder_exposes_explicit_build_api_only() -> None:
    """Parameter builder should expose only the canonical build-based API."""
    builder_source = inspect.getsource(parameter_builder)

    assert "def build(" in builder_source
    assert "def return_params" not in builder_source
    assert "def df_to_numvalues" not in builder_source


@pytest.mark.unit
def test_wave1_foundation_uses_canonical_global_naming_helpers() -> None:
    """Foundation modules should delegate global suffix construction centrally."""
    builder_source = inspect.getsource(parameter_builder)
    solver_source = inspect.getsource(solver_models)
    from spectrafit.core import postprocessing

    postprocessing_source = inspect.getsource(postprocessing)

    assert "global_lmfit_param_name" in builder_source
    assert "dataset_scoped_name" in builder_source
    assert "global_contribution_name" in solver_source
    assert "residual_for_dataset" in postprocessing_source
    assert "fit_for_dataset" in postprocessing_source


@pytest.mark.unit
def test_synthetic_generator_reuses_canonical_payload_types() -> None:
    """Synthetic boundary should import shared parameter/payload aliases."""
    source = inspect.getsource(synthetic_generator)

    assert "from spectrafit.models.types import CanonicalComponentInput" in source
    assert "from spectrafit.models.types import CanonicalSpectraFitInput" in source
    assert "from spectrafit.models.types import LegacySpectraFitInput" in source
    assert "class ComponentInputPayload" not in source
    assert "class ParamBoundsDict" not in source


@pytest.mark.unit
def test_notebook_return_dataframe_aliases_are_removed() -> None:
    """Notebook should not keep zero-usage return_* dataframe aliases."""
    from spectrafit.jupyter.core import SpectraFitNotebook

    removed_aliases = (
        "return_pre_statistic",
        "return_df_org",
        "return_df_pre",
        "return_df",
        "return_df_fit",
    )

    for alias in removed_aliases:
        assert not hasattr(SpectraFitNotebook, alias)


@pytest.mark.unit
def test_legacy_alias_modules_stay_definition_free() -> None:
    """Thin compatibility modules should remain import-only quarantine surfaces."""
    legacy_report_metrics = _import_legacy_report_module("spectrafit.report.metrics")
    legacy_report_warnings = _import_legacy_report_module("spectrafit.report._warnings")

    assert _top_level_definition_names(legacy_report_metrics) == set()
    assert _top_level_definition_names(legacy_report_warnings) == set()


@pytest.mark.unit
def test_model_parameters_shim_module_is_removed() -> None:
    """Legacy model_parameters shim should stay deleted after the v2.x removal."""
    assert importlib.util.find_spec("spectrafit.models.model_parameters") is None


@pytest.mark.unit
def test_solver_uses_canonical_parameter_builder_module() -> None:
    """Solver internals should depend on the explicit builder module."""
    source = inspect.getsource(solver_models)
    assert "from spectrafit.models.parameter_builder import ParameterBuilder" in source
    assert (
        "from spectrafit.models.model_parameters import ModelParameters" not in source
    )


@pytest.mark.unit
def test_internal_runtime_modules_do_not_import_builtin_solver_shim() -> None:
    """Pipeline, post-processing, and notebook code should use canonical solver imports."""
    from spectrafit.core import pipeline
    from spectrafit.core import postprocessing
    from spectrafit.jupyter import core

    assert "spectrafit.models.functions.builtin" not in inspect.getsource(pipeline)
    assert "spectrafit.models.functions.builtin" not in inspect.getsource(
        postprocessing
    )
    assert "spectrafit.models.functions.builtin" not in inspect.getsource(core)


@pytest.mark.unit
def test_result_projection_does_not_dump_variable_models_for_iteration() -> None:
    """Peak projection should iterate typed result fields without model_dump()."""
    source = inspect.getsource(result_projection)
    assert "model_dump()" not in source
    assert "VariableFitResult.model_fields" in source


@pytest.mark.unit
def test_metric_projection_uses_typed_projection_model() -> None:
    """Metric projection should stay on typed notebook models until DataFrame output."""
    source = inspect.getsource(result_projection)
    assert "NotebookMetricProjection" in source
    assert "SolverReportProjection" in source
    assert "project_solver_report(" in source
    assert "SolverResults(" not in source


@pytest.mark.unit
def test_append_peaks_dataframe_projects_variable_fields() -> None:
    """Peak projection should preserve variable field values in the DataFrame."""
    fit_result = FitResult(
        fit_insights=FitInsights(
            variables={
                "p1": VariableFitResult(
                    init_value=1.0,
                    model_value=1.1,
                    best_value=1.2,
                    stderr=0.01,
                )
            }
        )
    )

    projected = result_projection.append_peaks_dataframe(pd.DataFrame(), fit_result)
    assert projected.loc[0, ("p1", "init_value")] == pytest.approx(1.0)
    assert projected.loc[0, ("p1", "best_value")] == pytest.approx(1.2)


@pytest.mark.unit
def test_append_metric_dataframe_projects_averaged_metrics() -> None:
    """Metric projection should average typed regression rows before presentation."""
    fit_result = FitResult(
        fit_insights=FitInsights(statistics={"chi_square": 1.5}),
        data_summary={
            "regression_metrics": {
                "index": ["mean_squared_error"],
                "columns": ["fit_a", "fit_b"],
                "data": [[2.0, 4.0]],
            }
        },
    )

    projected = result_projection.append_metric_dataframe(pd.DataFrame(), fit_result)
    assert projected.loc[0, "chi_square"] == pytest.approx(1.5)
    assert projected.loc[0, "mean_squared_error"] == pytest.approx(3.0)


@pytest.mark.unit
def test_notebook_core_uses_solver_projection_models_for_tables() -> None:
    """Notebook table updates should read typed projections from SolverResults."""
    from spectrafit.jupyter import core

    update_metric_source = inspect.getsource(core.SpectraFitNotebook.update_metric)
    update_peaks_source = inspect.getsource(core.SpectraFitNotebook.update_peaks)

    assert "self._solver_results.metric_projection" in update_metric_source
    assert "self._solver_results.peaks_projection" in update_peaks_source
    assert "append_metric_dataframe" not in update_metric_source
    assert "append_peaks_dataframe" not in update_peaks_source


@pytest.mark.unit
def test_jupyter_export_uses_shared_solver_projection() -> None:
    """Notebook report export should build solver payloads from the shared service."""
    source = inspect.getsource(jupyter_export)
    assert "self._solver.canonical_report" in source
    assert "ReportAPI" not in source
    assert "self._solver.report_projection" not in source
    assert "self._solver.get_gof" not in source
    assert "self._solver.get_regression_metrics" not in source


@pytest.mark.unit
def test_jupyter_export_uses_single_notebook_export_adapter() -> None:
    """Notebook export should keep only one notebook adapter over canonical reporting."""
    source = inspect.getsource(jupyter_export)
    assert "NotebookExportDocument" in source
    assert "ReportInputDocument" not in source
    assert "ReportMethodDocument" not in source
    assert "ReportOutputDocument" not in source
    assert "_transform_nested_types" not in source


@pytest.mark.unit
def test_jupyter_export_drops_legacy_initial_model_spec_bridge() -> None:
    """Notebook export should own typed components, not the legacy model-spec alias."""
    source = inspect.getsource(jupyter_export)
    assert "LegacyModelSpec" not in source
    assert "normalize_components(" in source


@pytest.mark.unit
def test_reporting_service_accepts_splitframe_not_dict_runtime_stats() -> None:
    """Shared reporting should keep runtime preprocessing data on SplitFrame."""
    import spectrafit.reporting.service as reporting_service

    source = inspect.getsource(reporting_service)
    assert "SplitFrame | dict[str, object]" not in source
    assert ".to_split_dict()" not in source


@pytest.mark.unit
def test_result_projection_uses_splitframe_directly() -> None:
    """Notebook metric projection should read typed SplitFrame models directly."""
    source = inspect.getsource(result_projection)
    assert "SplitFrame.coerce(" not in source


@pytest.mark.unit
def test_pipeline_no_longer_imports_legacy_printing_results() -> None:
    """Pipeline runtime output should stay on the shared typed reporting service."""
    from spectrafit.core import pipeline

    source = inspect.getsource(pipeline)
    assert "PrintingResults" not in source
    assert "emit_runtime_report" in source


@pytest.mark.unit
def test_postprocessing_no_longer_uses_legacy_fit_report_formatter() -> None:
    """Post-processing should build typed fit insights directly from lmfit results."""
    from spectrafit.core import postprocessing

    source = inspect.getsource(postprocessing)
    assert "fit_report_as_dict" not in source
    assert "FitInsights.from_minimizer_result" in source


@pytest.mark.unit
def test_postprocessing_uses_runtime_regression_metrics_module() -> None:
    """Post-processing should import regression metrics from core, not report."""
    from spectrafit.core import postprocessing

    source = inspect.getsource(postprocessing)
    assert "from spectrafit.core.regression_metrics import RegressionMetrics" in source
    assert "from spectrafit.report import RegressionMetrics" not in source


@pytest.mark.unit
def test_reporting_service_does_not_import_frozen_report_package() -> None:
    """Canonical reporting service must not depend on frozen report shims."""
    import spectrafit.reporting.service as reporting_service

    source = inspect.getsource(reporting_service)
    assert "spectrafit.report" not in source


@pytest.mark.unit
def test_fit_report_kwargs_documents_canonical_reporting_owner() -> None:
    """Shared report kwargs docs should point callers at canonical reporting APIs."""
    from spectrafit.models import types

    source = inspect.getsource(types)
    assert "spectrafit.report.confidence.FitReport" not in source
    assert "spectrafit.reporting.service" in source


@pytest.mark.unit
def test_report_package_documents_frozen_public_surface() -> None:
    """Legacy report package should keep its frozen exports explicit."""
    legacy_report = _import_legacy_report_module("spectrafit.report")

    assert legacy_report.__doc__ is not None
    assert "v2.x" in legacy_report.__doc__
    assert "v3.0.0" in legacy_report.__doc__
    assert legacy_report.__all__ == [
        "CORREL_HEAD",
        "VERBOSE_DETAILED",
        "VERBOSE_REGULAR",
        "CIReport",
        "FitReport",
        "PrintingResults",
        "PrintingStatus",
        "RegressionMetrics",
        "_extracted_gof_from_results",
        "fit_report_as_dict",
        "get_init_value",
        "warn_meassage",
    ]


@pytest.mark.unit
def test_report_package_import_emits_future_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Importing the frozen report package should signal the deprecation boundary."""
    for module_name in list(sys.modules):
        if module_name == "spectrafit.report" or module_name.startswith(
            "spectrafit.report."
        ):
            monkeypatch.delitem(sys.modules, module_name, raising=False)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy_report = importlib.import_module("spectrafit.report")

    future_warnings = [
        warning for warning in caught if issubclass(warning.category, FutureWarning)
    ]
    assert future_warnings
    message = str(future_warnings[0].message)
    assert "spectrafit.report is a frozen legacy compatibility layer" in message
    assert "spectrafit.reporting" in message
    assert "v3.0.0" in message
    assert hasattr(legacy_report, "FitReport")


@pytest.mark.unit
def test_legacy_report_submodules_keep_quarantine_boundaries() -> None:
    """Legacy report submodules should document their frozen public surfaces."""
    legacy_report_confidence = _import_legacy_report_module(
        "spectrafit.report.confidence"
    )
    legacy_report_formatter = _import_legacy_report_module(
        "spectrafit.report.formatter"
    )
    legacy_report_printer = _import_legacy_report_module("spectrafit.report.printer")
    legacy_report_metrics = _import_legacy_report_module("spectrafit.report.metrics")

    assert "spectrafit.reporting.service" in (legacy_report_confidence.__doc__ or "")
    assert "compatibility buffers" in (legacy_report_formatter.__doc__ or "")
    assert "spectrafit.reporting.service" in (legacy_report_printer.__doc__ or "")
    assert "spectrafit.core.regression_metrics" in (legacy_report_metrics.__doc__ or "")

    assert legacy_report_confidence.__all__ == ["CIReport", "FitReport"]
    assert legacy_report_formatter.__all__ == [
        "FitReportBuffer",
        "_extracted_gof_from_results",
        "fit_report_as_dict",
        "get_init_value",
    ]
    assert legacy_report_printer.__all__ == [
        "CORREL_HEAD",
        "VERBOSE_DETAILED",
        "VERBOSE_REGULAR",
        "PrintingResults",
        "PrintingStatus",
    ]


@pytest.mark.unit
def test_legacy_printer_delegates_to_shared_report_service() -> None:
    """Legacy printer should bridge legacy inputs into the shared typed report service."""
    legacy_report_printer = _import_legacy_report_module("spectrafit.report.printer")

    source = inspect.getsource(legacy_report_printer)
    assert "pp.pprint(" not in source
    assert "build_fit_result_from_runtime" in source
    assert "emit_runtime_report" in source
    assert "spectrafit.report.confidence" not in source


@pytest.mark.unit
def test_legacy_formatter_projects_typed_report_models() -> None:
    """Legacy formatter should project from typed compatibility models."""
    legacy_report_formatter = _import_legacy_report_module("spectrafit.report.formatter")

    source = inspect.getsource(legacy_report_formatter)
    assert "class LegacyFitReport" in source
    assert "class ReportConfigurations" in source
    assert "class ReportStatistics" in source
    assert 'buffer["computational"]["' not in source
    assert 'buffer["statistics"]["' not in source
    assert "FitInsights.from_minimizer_result" in source


@pytest.mark.unit
def test_legacy_confidence_projects_typed_report_models() -> None:
    """Legacy confidence helpers should build typed compatibility documents."""
    legacy_report_confidence = _import_legacy_report_module("spectrafit.report.confidence")

    source = inspect.getsource(legacy_report_confidence)
    assert "class ConfidenceTableDocument" in source
    assert "class FitReportDocument" in source
    assert "self.report: dict[" not in source


@pytest.mark.unit
def test_result_bridge_reuses_typed_postprocessing_models() -> None:
    """Result bridge should reuse typed post-processing fields instead of rebuilding them."""
    from spectrafit.core import result_bridge

    source = inspect.getsource(result_bridge.build_fit_result_from_runtime)
    assert "post_result.fit_insights" in source
    assert "post_result.confidence_interval" in source
    assert "FitInsights.from_minimizer_result" not in source


@pytest.mark.unit
def test_notebook_config_loader_delegates_to_canonical_ingress() -> None:
    """Notebook config loading should delegate to the canonical config facade."""
    from spectrafit.jupyter import config_io

    source = inspect.getsource(config_io.load_notebook_config)
    assert "UnifiedFittingConfig.from_file(" in source
    assert "load_config_payload(" not in source
    assert ".model_validate(" not in source


@pytest.mark.unit
def test_report_service_uses_typed_json_documents() -> None:
    """Shared report service should build typed JSON payload documents."""
    from spectrafit.reporting import service

    source = inspect.getsource(service)
    assert "class CanonicalReportSchema" in source
    assert "def project_canonical_report" in source
    assert "class RuntimeReportPayload" in source
    assert "class JsonReportDocument" in source
    assert "model_dump_json(indent=2)" in source


@pytest.mark.unit
def test_postprocessing_does_not_use_positional_column_access() -> None:
    """Post-processing should use explicit source columns, not positional indexing."""
    from spectrafit.core import postprocessing

    source = inspect.getsource(postprocessing)
    assert "df.columns[0]" not in source
    assert "df.columns[1]" not in source
    assert "iloc[:, 0]" not in source


@pytest.mark.unit
def test_notebook_fit_delegates_to_pipeline_runtime() -> None:
    """Notebook fits should delegate solving/postprocessing through the pipeline."""
    from spectrafit.jupyter import core

    source = inspect.getsource(core.SpectraFitNotebook.solver_model)
    assert "FittingPipeline(" in source
    assert "_build_runtime_pipeline_deps()" in source
    assert "pipeline_result.fit_result" in source
    assert "solver = deps.solver_factory(" not in source


@pytest.mark.unit
def test_notebook_legacy_side_effect_shims_use_getattr_dispatch() -> None:
    """Notebook legacy side-effect shims should dispatch centrally, not via properties."""
    from spectrafit.jupyter import core

    source = inspect.getsource(core)
    assert "def __getattr__(self, name: str) -> object:" in source
    assert "@property  # intentional: export compat shim (R8 will deprecate)" not in source
    assert "@property  # intentional: plot compat shim (R8 will deprecate)" not in source
    assert "@property  # intentional: report compat shim (R8 will deprecate)" not in source
