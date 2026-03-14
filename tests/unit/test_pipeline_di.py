"""Unit tests for pipeline dependency injection and factories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lmfit import Minimizer
from lmfit import Parameters
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.core.pipeline import PipelineDependencies
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.core.postprocessing import PostProcessingResult
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.output_config import OutputConfig
from spectrafit.models.preprocess_result import PreprocessResult
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.split_frame import SplitFrame


MINIMAL_COMPONENTS: dict[str, object] = {
    "components": [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                "center": {"min": -1, "max": 1, "value": 0.0, "vary": True},
                "fwhmg": {"min": 0.1, "max": 2.0, "value": 0.7, "vary": True},
            },
        }
    ],
    "column": {"x": "energy", "y": "intensity"},
    "minimizer": {"nan_policy": "propagate", "calc_covar": True},
    "optimizer": {"max_nfev": 1000, "method": "leastsq"},
    "context": {"mode": "standard"},
}


@dataclass(slots=True)
class FakeSolver:
    """Minimal solver stub for dependency-injected pipeline tests."""

    minimizer: Minimizer
    result: object
    bundle: object | None = None

    def solve(self) -> tuple[Minimizer, object]:
        return self.minimizer, self.result


def _build_config() -> UnifiedFittingConfig:
    return UnifiedFittingConfig.from_dict(MINIMAL_COMPONENTS)


def _build_minimizer() -> Minimizer:
    params = Parameters()
    params.add("scale", value=1.0)
    return Minimizer(
        lambda pars, target: np.array([pars["scale"].value - target], dtype=np.float64),
        params=params,
        fcn_args=(1.0,),
    )


def _build_post_result(df: pd.DataFrame) -> PostProcessingResult:
    return PostProcessingResult(
        df=df,
        fit_insights=FitInsights(),
        confidence_interval=ConfidenceResults(settings=False),
        linear_correlation=SplitFrame.empty(),
        fit_result_data=SplitFrame.empty(),
        regression_metrics=SplitFrame.empty(),
        descriptive_statistic=SplitFrame.empty(),
    )


@pytest.mark.unit
def test_fitting_pipeline_uses_injected_collaborators(tmp_path: Path) -> None:
    config = _build_config()
    data_cfg = DataConfig(infile=tmp_path / "in.csv")
    loaded_df = pd.DataFrame({"energy": [0.0], "intensity": [1.0]})
    preprocessed_df = pd.DataFrame({"energy": [0.5], "intensity": [2.0]})
    preprocess_result = PreprocessResult(
        df=preprocessed_df,
        data_statistic=SplitFrame.empty(),
    )
    minimizer = _build_minimizer()
    solver_result = minimizer.minimize(method="leastsq")
    post_result = _build_post_result(preprocessed_df)
    calls: list[str] = []

    def data_config_factory(pipeline_config: UnifiedFittingConfig) -> DataConfig:
        assert pipeline_config is config
        calls.append("data-config")
        return data_cfg

    def data_loader(loader_config: DataConfig) -> pd.DataFrame:
        assert loader_config is data_cfg
        calls.append("load-data")
        return loaded_df

    def preprocessor(df: pd.DataFrame, pipeline_config: UnifiedFittingConfig) -> PreprocessResult:
        assert df is loaded_df
        assert pipeline_config is config
        calls.append("preprocess")
        return preprocess_result

    def solver_factory(df: pd.DataFrame, pipeline_config: UnifiedFittingConfig) -> FakeSolver:
        assert df is preprocessed_df
        assert pipeline_config is config
        calls.append("build-solver")
        return FakeSolver(minimizer=minimizer, result=solver_result)

    def postprocess_runner(
        df: pd.DataFrame,
        injected_minimizer: Minimizer,
        injected_result: object,
        pipeline_config: UnifiedFittingConfig,
        bundle: object | None,
    ) -> PostProcessingResult:
        assert df is preprocessed_df
        assert injected_minimizer is minimizer
        assert injected_result is solver_result
        assert pipeline_config is config
        assert bundle is None
        calls.append("postprocess")
        return post_result

    pipeline = FittingPipeline(
        request=FittingRequest.from_config(config),
        deps=PipelineDependencies(
            data_config_factory=data_config_factory,
            data_loader=data_loader,
            preprocessor=preprocessor,
            solver_factory=solver_factory,
            postprocess_runner=postprocess_runner,
        ),
    )

    result = pipeline.run()

    assert calls == [
        "data-config",
        "load-data",
        "preprocess",
        "build-solver",
        "postprocess",
    ]
    assert result.post is post_result
    assert result.df.equals(post_result.df)
    assert result.data_statistic == preprocess_result.data_statistic


@pytest.mark.unit
def test_fitting_routine_pipeline_uses_injected_report_emitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _build_config()
    loaded_df = pd.DataFrame({"energy": [0.0], "intensity": [1.0]})
    preprocess_result = PreprocessResult(
        df=loaded_df,
        data_statistic=SplitFrame.empty(),
    )
    minimizer = _build_minimizer()
    solver_result = minimizer.minimize(method="leastsq")
    post_result = _build_post_result(loaded_df)
    fit_result_sentinel = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "spectrafit.core.pipeline.FittingResult.to_fit_result",
        lambda _self: fit_result_sentinel,
    )

    def report_emitter(*, fit_result: object, data_statistic: SplitFrame, verbose: int) -> None:
        captured["fit_result"] = fit_result
        captured["data_statistic"] = data_statistic
        captured["verbose"] = verbose

    deps = PipelineDependencies(
        data_config_factory=lambda _config: DataConfig(infile=Path("in.csv")),
        data_loader=lambda _data_config: loaded_df,
        preprocessor=lambda _df, _config: preprocess_result,
        solver_factory=lambda _df, _config: FakeSolver(
            minimizer=minimizer,
            result=solver_result,
        ),
        postprocess_runner=lambda _df, _minimizer, _result, _config, _bundle: post_result,
        report_emitter=report_emitter,
    )

    result = fitting_routine_pipeline(
        request=FittingRequest.from_config(config, output=OutputConfig(verbose=2)),
        deps=deps,
    )

    assert result.post is post_result
    assert captured == {
        "fit_result": fit_result_sentinel,
        "data_statistic": preprocess_result.data_statistic,
        "verbose": 2,
    }
