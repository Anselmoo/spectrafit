"""Unit tests for explicit SpectraFitNotebook side-effect methods and property shims."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest
import spectrafit.jupyter.core as jupyter_core

from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import PipelineDependencies
from spectrafit.core.postprocessing import PostProcessingResult
from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.peak_models import Component
from spectrafit.models.preprocess_result import PreprocessResult
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.split_frame import SplitFrame


def _notebook_stub() -> SpectraFitNotebook:
    """Create a lightweight SpectraFitNotebook instance without running ``__init__``."""
    return object.__new__(SpectraFitNotebook)


class TestSideEffectMethods:
    """Method-first API for side effects."""

    @pytest.mark.unit
    def test_y_column_normalizes_runtime_state_to_canonical_list(self) -> None:
        notebook = _notebook_stub()
        notebook.y_column = "bootstrap"
        notebook.fitting_mode = FittingMode.STANDARD
        notebook.n_datasets = 1

        notebook.y_column = "signal"

        assert notebook.y_columns == ["signal"]
        assert notebook.y_column == "signal"
        assert notebook.fitting_mode == FittingMode.STANDARD
        assert notebook.n_datasets == 1

        notebook.y_column = ["signal_a", "signal_b"]

        assert notebook.y_columns == ["signal_a", "signal_b"]
        assert notebook.y_column == ["signal_a", "signal_b"]
        assert notebook.fitting_mode == FittingMode.GLOBAL
        assert notebook.n_datasets == 2

    @pytest.mark.unit
    def test_preprocess_df_updates_dataframe_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        notebook = _notebook_stub()
        notebook.df = pd.DataFrame({"x": [0.0, 1.0], "y": [2.0, 3.0]})
        notebook.x_column = "x"
        notebook.y_column = "y"
        notebook.preprocessing_config = PreprocessingConfig(
            shift=0.5,
            smooth=0,
            oversampling=False,
            energy_start=None,
            energy_stop=None,
        )

        processed_df = pd.DataFrame({"x": [0.5, 1.5], "y": [2.0, 3.0]})
        captured: dict[str, object] = {}

        def fake_preprocess(df: pd.DataFrame, config: object) -> PreprocessResult:
            captured["df"] = df
            captured["config"] = config
            return PreprocessResult(
                df=processed_df,
                data_statistic={"data": [[1.0]], "index": [0], "columns": ["rows"]},
            )

        monkeypatch.setattr(jupyter_core, "preprocess", fake_preprocess)

        notebook.preprocess_df()

        pd.testing.assert_frame_equal(notebook.df, processed_df)
        pd.testing.assert_frame_equal(notebook.df_pre, processed_df)
        assert notebook.pre_statistic["columns"] == ["rows"]
        assert captured["df"] is not None
        assert captured["config"] is not None
        assert captured["config"].column.x == "x"
        assert captured["config"].column.y == "y"
        assert captured["config"].preprocessing == notebook.preprocessing_config

    @pytest.mark.unit
    def test_export_active_df_calls_export_with_act_prefix(self) -> None:
        notebook = _notebook_stub()
        notebook.df = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.export_args_df = FnameAPI(fname="results", suffix="csv")
        notebook.export_df = MagicMock()

        notebook.export_active_df()

        assert notebook.export_args_df.prefix == "act"
        notebook.export_df.assert_called_once_with(df=notebook.df, args=notebook.export_args_df)

    @pytest.mark.unit
    def test_args_pre_mutation_updates_canonical_preprocessing_state(self) -> None:
        notebook = _notebook_stub()
        notebook.x_column = "x"
        notebook.y_column = "y"
        notebook.preprocessing_config = PreprocessingConfig(shift=0.5, smooth=1)
        notebook.initial_model = [
            {
                "gaussian": {
                    "amplitude": {
                        "value": 1.0,
                        "vary": True,
                        "min": 0.0,
                        "max": 2.0,
                    },
                    "center": {
                        "value": 0.0,
                        "vary": True,
                        "min": -1.0,
                        "max": 1.0,
                    },
                    "fwhmg": {
                        "value": 0.2,
                        "vary": True,
                        "min": 0.02,
                        "max": 0.5,
                    },
                }
            }
        ]
        notebook.settings_solver_models = SolverModelsAPI()
        notebook.fitting_mode = FittingMode.STANDARD

        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.args_pre"):
            notebook.args_pre.shift = 1.25
        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.args_pre"):
            notebook.args_pre.smooth = 3

        assert notebook.preprocessing_config.shift == pytest.approx(1.25)
        assert notebook.preprocessing_config.smooth == 3
        assert notebook.args_to_config().preprocessing == notebook.preprocessing_config

    @pytest.mark.unit
    def test_args_pre_reassignment_updates_canonical_preprocessing_and_columns(self) -> None:
        notebook = _notebook_stub()
        notebook.x_column = "energy"
        notebook.y_column = "signal"
        notebook.preprocessing_config = PreprocessingConfig()
        notebook.initial_model = [
            {
                "gaussian": {
                    "amplitude": {
                        "value": 1.0,
                        "vary": True,
                        "min": 0.0,
                        "max": 2.0,
                    },
                    "center": {
                        "value": 0.0,
                        "vary": True,
                        "min": -1.0,
                        "max": 1.0,
                    },
                    "fwhmg": {
                        "value": 0.2,
                        "vary": True,
                        "min": 0.02,
                        "max": 0.5,
                    },
                }
            }
        ]
        notebook.settings_solver_models = SolverModelsAPI()
        notebook.fitting_mode = FittingMode.STANDARD

        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.args_pre"):
            compat_args = notebook.args_pre
        compat_args.shift = 0.75
        compat_args.energy_start = 280.0
        compat_args.column = ["energy_ev", "signal_a", "signal_b"]
        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.args_pre"):
            notebook.args_pre = compat_args

        assert notebook.preprocessing_config.shift == pytest.approx(0.75)
        assert notebook.preprocessing_config.energy_start == pytest.approx(280.0)
        assert notebook.x_column == "energy_ev"
        assert notebook.y_column == ["signal_a", "signal_b"]
        assert notebook.args_to_config().preprocessing == notebook.preprocessing_config

    @pytest.mark.unit
    def test_initial_model_is_future_warned_compatibility_shim(self) -> None:
        notebook = _notebook_stub()
        notebook.initial_components = [
            Component.model_validate(
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {"value": 0.0, "vary": True},
                    },
                }
            )
        ]

        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.initial_model"):
            legacy_initial_model = notebook.initial_model

        assert legacy_initial_model == [
            {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True},
                    "center": {"value": 0.0, "vary": True},
                }
            }
        ]

        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.initial_model"):
            notebook.initial_model = [
                {
                    "lorentzian": {
                        "amplitude": {"value": 0.5, "vary": True},
                        "center": {"value": -1.0, "vary": True},
                    }
                }
            ]

        assert [component.model for component in notebook.initial_components] == [
            "lorentzian"
        ]

    @pytest.mark.unit
    def test_plot_original_calls_plot_dataframe(self) -> None:
        notebook = _notebook_stub()
        notebook.df_org = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.args_plot = MagicMock()
        notebook.plot_dataframe = MagicMock()

        notebook.plot_original()

        notebook.plot_dataframe.assert_called_once_with(
            args_plot=notebook.args_plot,
            df=notebook.df_org,
        )

    @pytest.mark.unit
    def test_generate_fit_report_calls_export_report(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        notebook = _notebook_stub()
        notebook.args_desc = MagicMock()
        notebook.initial_model = [
            {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True},
                    "center": {"value": 0.0, "vary": True},
                }
            }
        ]
        notebook.x_column = "x"
        notebook.y_column = "y"
        notebook.preprocessing_config = PreprocessingConfig()
        notebook.settings_solver_models = MagicMock()
        notebook.export_args_out = FnameAPI(fname="report", suffix="lock")
        notebook.__dict__["_solver_results"] = MagicMock()
        notebook.df_org = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.df_pre = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.df_fit = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.export_report = MagicMock()
        captured: dict[str, object] = {}

        class FakeExportReport:
            def __init__(self, **kwargs: object) -> None:
                captured.update(kwargs)

            def __call__(self) -> dict[str, bool]:
                return {"ok": True}

        monkeypatch.setattr(jupyter_core, "ExportReport", FakeExportReport)

        notebook.generate_fit_report()

        notebook.export_report.assert_called_once_with(
            report={"ok": True},
            args=notebook.export_args_out,
        )
        assert captured["description"] is notebook.args_desc
        assert captured["fname"] == notebook.export_args_out
        assert captured["solver"] is notebook.__dict__["_solver_results"]
        assert "initial_model" not in captured
        assert "pre_processing" not in captured
        assert "settings_solver_models" not in captured
        assert "column" not in captured

    @pytest.mark.unit
    def test_generate_fit_report_requires_solved_state(self) -> None:
        notebook = _notebook_stub()

        with pytest.raises(
            RuntimeError,
            match="Run solver_model\\(\\) before generating a fit report\\.",
        ):
            notebook.generate_fit_report()

    @pytest.mark.unit
    def test_update_metric_requires_solved_state(self) -> None:
        notebook = _notebook_stub()

        with pytest.raises(
            RuntimeError,
            match="Run solver_model\\(\\) before updating metric tables\\.",
        ):
            notebook.update_metric()

    @pytest.mark.unit
    def test_update_peaks_requires_solved_state(self) -> None:
        notebook = _notebook_stub()

        with pytest.raises(
            RuntimeError,
            match="Run solver_model\\(\\) before updating peak tables\\.",
        ):
            notebook.update_peaks()

    @pytest.mark.unit
    def test_plot_current_metric_requires_metric_state(self) -> None:
        notebook = _notebook_stub()
        notebook.df_metric = pd.DataFrame()

        with pytest.raises(
            RuntimeError,
            match="Run solver_model\\(\\) before plotting notebook metrics\\.",
        ):
            notebook.plot_current_metric()

    @pytest.mark.unit
    def test_export_preprocessed_df_requires_preprocessed_state(self) -> None:
        notebook = _notebook_stub()
        notebook.df_pre = pd.DataFrame()

        with pytest.raises(
            RuntimeError,
            match="Run preprocess_df\\(\\) before exporting preprocessed notebook data\\.",
        ):
            notebook.export_preprocessed_df()

    @pytest.mark.unit
    def test_export_metric_df_requires_metric_state(self) -> None:
        notebook = _notebook_stub()
        notebook.df_metric = pd.DataFrame()

        with pytest.raises(
            RuntimeError,
            match="Run solver_model\\(\\) before exporting notebook metrics\\.",
        ):
            notebook.export_metric_df()

    @pytest.mark.unit
    def test_export_peaks_df_requires_peak_state(self) -> None:
        notebook = _notebook_stub()
        notebook.df_peaks = pd.DataFrame()

        with pytest.raises(
            RuntimeError,
            match="Run solver_model\\(\\) before exporting notebook peaks\\.",
        ):
            notebook.export_peaks_df()

    @pytest.mark.unit
    def test_solver_model_uses_pipeline_dependencies_factories(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        notebook = _notebook_stub()
        notebook.df = pd.DataFrame({"x": [0.0, 1.0], "y": [1.0, 2.0]})
        notebook.x_column = "x"
        notebook.y_column = "y"
        notebook.fitting_mode = FittingMode.STANDARD
        notebook.settings_solver_models = SolverModelsAPI()
        notebook.args_to_config = MagicMock(
            return_value=UnifiedFittingConfig.from_dict(
                {
                    "components": [
                        {
                            "id": "p1",
                            "model": "gaussian",
                            "parameters": {
                                "amplitude": {
                                    "min": 0,
                                    "max": 2,
                                    "value": 1.0,
                                    "vary": True,
                                },
                                "center": {
                                    "min": -1,
                                    "max": 1,
                                    "value": 0.0,
                                    "vary": True,
                                },
                                "fwhmg": {
                                    "min": 0.1,
                                    "max": 2.0,
                                    "value": 0.7,
                                    "vary": True,
                                },
                            },
                        }
                    ],
                    "column": {"x": "x", "y": "y"},
                }
            )
        )
        notebook.update_metric = MagicMock()
        notebook.update_peaks = MagicMock()
        notebook.plot_fit_df = MagicMock()
        notebook.plot_current_metric = MagicMock()
        notebook.interactive_display = MagicMock()

        minimizer = MagicMock(name="minimizer")
        result = MagicMock(name="result")
        solver_calls: dict[str, object] = {}

        class FakeSolver:
            bundle = None

            def solve(self) -> tuple[MagicMock, MagicMock]:
                return minimizer, result

        def solver_factory(
            df: pd.DataFrame,
            config: UnifiedFittingConfig,
        ) -> FakeSolver:
            solver_calls["df"] = df
            solver_calls["config"] = config
            return FakeSolver()

        def forbidden_preprocessor(
            _df: pd.DataFrame,
            _config: UnifiedFittingConfig,
        ) -> PreprocessResult:
            msg = "solver_model() should not re-run notebook preprocessing"
            raise AssertionError(msg)

        post_result = PostProcessingResult(
            df=notebook.df.copy(),
            fit_insights=FitInsights(),
            confidence_interval=ConfidenceResults(settings=False),
            linear_correlation=SplitFrame.empty(),
            fit_result_data=SplitFrame.empty(),
            regression_metrics=SplitFrame.empty(),
            descriptive_statistic=SplitFrame.empty(),
        )
        postprocess_calls: dict[str, object] = {}

        def postprocess_runner(
            df: pd.DataFrame,
            injected_minimizer: MagicMock,
            injected_result: MagicMock,
            config: UnifiedFittingConfig,
            bundle: object | None,
        ) -> PostProcessingResult:
            postprocess_calls["df"] = df
            postprocess_calls["minimizer"] = injected_minimizer
            postprocess_calls["result"] = injected_result
            postprocess_calls["config"] = config
            postprocess_calls["bundle"] = bundle
            return post_result

        notebook.__dict__["_pipeline_deps"] = PipelineDependencies(
            preprocessor=forbidden_preprocessor,
            solver_factory=solver_factory,
            postprocess_runner=postprocess_runner,
        )

        fit_result = MagicMock(name="fit_result")

        class FakePipeline:
            def __init__(self, *, request: object, deps: PipelineDependencies) -> None:
                self.request = request
                self.deps = deps

            def run(self) -> SimpleNamespace:
                df = self.deps.data_loader(self.deps.data_config_factory(self.request.config))
                pre_result = self.deps.preprocessor(df, self.request.config)
                minimizer, result = self.deps.solver_factory(
                    pre_result.df,
                    self.request.config,
                ).solve()
                post_result = self.deps.postprocess_runner(
                    pre_result.df,
                    minimizer,
                    result,
                    self.request.config,
                    None,
                )
                return SimpleNamespace(
                    df=post_result.df,
                    data_statistic=pre_result.data_statistic,
                    fit_result=fit_result,
                )

        monkeypatch.setattr(jupyter_core, "FittingPipeline", FakePipeline)
        monkeypatch.setattr(jupyter_core, "SolverResults", MagicMock(return_value=MagicMock()))

        notebook.solver_model(
            initial_model=[],
            show_plot=False,
            show_metric=False,
            show_df=False,
            show_peaks=False,
        )

        assert solver_calls["df"] is notebook.df
        assert solver_calls["config"] is postprocess_calls["config"]
        assert solver_calls["config"].minimizer == notebook.settings_solver_models.minimizer
        assert solver_calls["config"].optimizer == notebook.settings_solver_models.optimizer
        assert postprocess_calls == {
            "df": notebook.df,
            "minimizer": minimizer,
            "result": result,
            "config": solver_calls["config"],
            "bundle": None,
        }
        pd.testing.assert_frame_equal(notebook.df_fit, post_result.df)
        assert notebook.fit_result is fit_result
        notebook.update_metric.assert_called_once_with()
        notebook.update_peaks.assert_called_once_with()

    @pytest.mark.unit
    def test_solver_model_normalizes_conf_interval_api_to_canonical_config(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        notebook = _notebook_stub()
        notebook.df = pd.DataFrame({"x": [0.0], "y": [1.0]})
        notebook.x_column = "x"
        notebook.y_column = "y"
        notebook.fitting_mode = FittingMode.STANDARD
        notebook.settings_solver_models = SolverModelsAPI()
        notebook.args_to_config = MagicMock(
            return_value=UnifiedFittingConfig.from_dict(
                {
                    "components": [
                        {
                            "id": "p1",
                            "model": "gaussian",
                            "parameters": {
                                "amplitude": {
                                    "min": 0,
                                    "max": 2,
                                    "value": 1.0,
                                    "vary": True,
                                },
                                "center": {
                                    "min": -1,
                                    "max": 1,
                                    "value": 0.0,
                                    "vary": True,
                                },
                                "fwhmg": {
                                    "min": 0.1,
                                    "max": 2.0,
                                    "value": 0.7,
                                    "vary": True,
                                },
                            },
                        }
                    ],
                    "column": {"x": "x", "y": "y"},
                }
            )
        )
        notebook.update_metric = MagicMock()
        notebook.update_peaks = MagicMock()
        notebook.plot_fit_df = MagicMock()
        notebook.plot_current_metric = MagicMock()
        notebook.interactive_display = MagicMock()

        class FakeSolver:
            bundle = None

            def solve(self) -> tuple[MagicMock, SimpleNamespace]:
                return MagicMock(name="minimizer"), SimpleNamespace()

        post_result = PostProcessingResult(
            df=notebook.df.copy(),
            fit_insights=FitInsights(),
            confidence_interval=ConfidenceResults(settings=False),
            linear_correlation=SplitFrame.empty(),
            fit_result_data=SplitFrame.empty(),
            regression_metrics=SplitFrame.empty(),
            descriptive_statistic=SplitFrame.empty(),
        )

        notebook.__dict__["_pipeline_deps"] = PipelineDependencies(
            solver_factory=lambda _df, _config: FakeSolver(),
            postprocess_runner=lambda _df, _minimizer, _result, _config, _bundle: post_result,
        )

        class FakePipeline:
            def __init__(self, *, request: object, deps: PipelineDependencies) -> None:
                self.request = request
                self.deps = deps

            def run(self) -> SimpleNamespace:
                df = self.deps.data_loader(self.deps.data_config_factory(self.request.config))
                pre_result = self.deps.preprocessor(df, self.request.config)
                self.deps.solver_factory(pre_result.df, self.request.config).solve()
                post_result = self.deps.postprocess_runner(
                    pre_result.df,
                    MagicMock(name="minimizer"),
                    SimpleNamespace(),
                    self.request.config,
                    None,
                )
                return SimpleNamespace(
                    df=post_result.df,
                    data_statistic=pre_result.data_statistic,
                    fit_result=MagicMock(),
                )

        monkeypatch.setattr(jupyter_core, "FittingPipeline", FakePipeline)
        monkeypatch.setattr(jupyter_core, "SolverResults", MagicMock(return_value=MagicMock()))

        notebook.solver_model(
            initial_model=[],
            conf_interval=ConfIntervalAPI(maxiter=25, trace=False),
            show_plot=False,
            show_metric=False,
            show_df=False,
            show_peaks=False,
        )

        resolved_ci = notebook.__dict__["_resolved_ci"]
        assert isinstance(resolved_ci, ConfIntervalConfig)
        assert resolved_ci.maxiter == 25
        assert resolved_ci.trace is False


class TestLegacyPropertyShims:
    """Compatibility properties delegate to method-first APIs."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("property_name", "method_name"),
        [
            ("pre_process", "preprocess_df"),
            ("export_df_act", "export_active_df"),
            ("export_df_fit", "export_fit_dataframe"),
            ("export_df_org", "export_original_df"),
            ("export_df_pre", "export_preprocessed_df"),
            ("export_df_metric", "export_metric_df"),
            ("export_df_peaks", "export_peaks_df"),
            ("plot_original_df", "plot_original"),
            ("plot_current_df", "plot_current"),
            ("plot_preprocessed_df", "plot_preprocessed"),
            ("generate_report", "generate_fit_report"),
        ],
    )
    def test_legacy_property_shims_warn_and_delegate(
        self,
        property_name: str,
        method_name: str,
    ) -> None:
        notebook = _notebook_stub()
        method_mock = MagicMock()
        setattr(notebook, method_name, method_mock)

        with pytest.warns(
            FutureWarning,
            match=rf"SpectraFitNotebook\.{property_name}.*{method_name}",
        ):
            getattr(notebook, property_name)

        method_mock.assert_called_once_with()

    @pytest.mark.unit
    def test_display_preprocessed_df_requires_preprocessed_state(self) -> None:
        notebook = _notebook_stub()
        notebook.df_pre = pd.DataFrame()

        with pytest.raises(
            RuntimeError,
            match="Run preprocess_df\\(\\) before displaying preprocessed notebook data\\.",
        ):
            notebook.display_preprocessed_df()

    @pytest.mark.unit
    def test_global_alias_warns_and_updates_canonical_fitting_mode(self) -> None:
        notebook = _notebook_stub()
        notebook.fitting_mode = FittingMode.STANDARD

        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.global_"):
            notebook.global_ = FittingMode.GLOBAL

        assert notebook.fitting_mode == FittingMode.GLOBAL
        assert notebook.is_global is True
        with pytest.warns(FutureWarning, match=r"SpectraFitNotebook\.global_"):
            assert notebook.global_ == FittingMode.GLOBAL
