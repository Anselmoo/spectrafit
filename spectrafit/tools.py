"""Collection of essential tools for running SpectraFit."""

from __future__ import annotations

import gzip
import json
import pickle
import sys

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import numpy as np
import pandas as pd
import tomli
import yaml

from lmfit.confidence import ConfidenceInterval
from lmfit.minimizer import MinimizerException

from spectrafit.api.tools_model import ColumnNamesAPI
from spectrafit.models.builtin import calculated_model
from spectrafit.report import RegressionMetrics
from spectrafit.report import fit_report_as_dict


if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from lmfit import Minimizer


class PreProcessing:
    """Summarized all pre-processing-filters  together."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize PreProcessing class.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        self.df = df
        self.args = args

    def __call__(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Apply all pre-processing-filters.

        Returns:
            pd.DataFrame: DataFrame containing the input data (`x` and `data`), which
                 are optionally:

                    1. shrinked to a given range
                    2. shifted
                    3. linear oversampled
                    4. smoothed
            Dict[str,Any]: Adding a descriptive statistics to the input dictionary.

        """
        df_copy: pd.DataFrame = self.df.copy()
        self.args["data_statistic"] = df_copy.describe(
            percentiles=np.arange(0.1, 1.0, 0.1).tolist(),
        ).to_dict(orient="split")
        try:
            if isinstance(self.args["energy_start"], (int, float)) or isinstance(
                self.args["energy_stop"],
                (int, float),
            ):
                df_copy = self.energy_range(df_copy, self.args)
            if self.args["shift"]:
                df_copy = self.energy_shift(df_copy, self.args)
            if self.args["oversampling"]:
                df_copy = self.oversampling(df_copy, self.args)
            if self.args["smooth"]:
                df_copy = self.smooth_signal(df_copy, self.args)
        except KeyError:
            sys.exit(1)
        return (df_copy, self.args)

    @staticmethod
    def energy_range(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Select the energy range for fitting.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are shrinked according to the energy range.

        """
        energy_start: int | float = args["energy_start"]
        energy_stop: int | float = args["energy_stop"]

        df_copy = df.copy()
        if isinstance(energy_start, (int, float)) and isinstance(
            energy_stop,
            (int, float),
        ):
            return df_copy.loc[
                (df[args["column"][0]] >= energy_start)
                & (df[args["column"][0]] <= energy_stop)
            ]
        if isinstance(energy_start, (int, float)):
            return df_copy.loc[df[args["column"][0]] >= energy_start]
        if isinstance(energy_stop, (int, float)):
            return df_copy.loc[df[args["column"][0]] <= energy_stop]
        return None  # pragma: no cover

    @staticmethod
    def energy_shift(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Shift the energy axis by a given value.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are energy-shifted by the given value.

        """
        df_copy: pd.DataFrame = df.copy()
        df_copy.loc[:, args["column"][0]] = (
            df[args["column"][0]].to_numpy() + args["shift"]
        )
        return df_copy

    @staticmethod
    def oversampling(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Oversampling the data to increase the resolution of the data.

        !!! note "About Oversampling"
            In this implementation of oversampling, the data is oversampled by the
             factor of 5. In case of data with only a few points, the increased
             resolution should allow to easier solve the optimization problem. The
             oversampling based on a simple linear regression.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are oversampled by the factor of 5.

        """
        x_values = np.linspace(
            df[args["column"][0]].min(),
            df[args["column"][0]].max(),
            5 * df.shape[0],
        )
        y_values = np.interp(
            x_values,
            df[args["column"][0]].to_numpy(),
            df[args["column"][1]].to_numpy(),
        )
        return pd.DataFrame({args["column"][0]: x_values, args["column"][1]: y_values})

    @staticmethod
    def smooth_signal(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Smooth the intensity values.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are smoothed by the given value.

        """
        box = np.ones(args["smooth"]) / args["smooth"]
        df_copy: pd.DataFrame = df.copy()
        df_copy.loc[:, args["column"][1]] = np.convolve(
            df[args["column"][1]].to_numpy(),
            box,
            mode="same",
        )
        return df_copy


class PostProcessing:
    """Post-processing of the dataframe."""

    def __init__(
        self,
        df: pd.DataFrame,
        args: dict[str, Any],
        minimizer: Minimizer,
        result: Any,
    ) -> None:
        """Initialize PostProcessing class.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.
            minimizer (Minimizer): The minimizer class.
            result (Any): The result of the minimization of the best fit.

        """
        self.args = args
        self.df = self.rename_columns(df=df)
        self.minimizer = minimizer
        self.result = result
        self.data_size = self.check_global_fitting()

    def __call__(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Call the post-processing."""
        self.make_insight_report()
        self.make_residual_fit()
        self.make_fit_contributions()
        self.export_correlation2args()
        self.export_results2args()
        self.export_regression_metrics2args()
        self.export_desprective_statistic2args()
        return (self.df, self.args)

    def check_global_fitting(self) -> int | None:
        """Check if the global fitting is performed.

        !!! note "About Global Fitting"
            In case of the global fitting, the data is extended by the single
            contribution of the model.

        Returns:
            Optional[int]: The number of spectra of the global fitting.

        """
        if self.args["global_"]:
            return max(
                int(self.result.params[i].name.split("_")[-1])
                for i in self.result.params
            )
        return None

    def rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename the columns of the dataframe.

        Rename the columns of the dataframe to the names defined in the input file.

        Args:
            df (pd.DataFrame): DataFrame containing the original input data, which are
                 individually pre-named.

        Returns:
            pd.DataFrame: DataFrame containing renamed columns. All column-names are
                 lowered. In case of a regular fitting, the columns are named `energy`
                 and `intensity`. In case of a global fitting, `energy` stays `energy`
                 and `intensity` is extended by a `_`  and column index; like: `energy`
                 and `intensity_1`, `intensity_2`, `intensity_...` depending on
                 the dataset size.

        """
        if self.args["global_"]:
            return df.rename(
                columns={
                    col: (
                        ColumnNamesAPI().energy
                        if i == 0
                        else f"{ColumnNamesAPI().intensity}_{i}"
                    )
                    for i, col in enumerate(df.columns)
                },
            )
        return df.rename(
            columns={
                df.columns[0]: ColumnNamesAPI().energy,
                df.columns[1]: ColumnNamesAPI().intensity,
            },
        )

    def make_insight_report(self) -> None:
        """Make an insight-report of the fit statistic.

        !!! note "About Insight Report"

            The insight report based on:

                1. Configurations
                2. Statistics
                3. Variables
                4. Error-bars
                5. Correlations
                6. Covariance Matrix
                7. _Optional_: Confidence Interval

            All of the above are included in the report as dictionary in `args`.

        """
        self.args["fit_insights"] = fit_report_as_dict(
            inpars=self.result,
            settings=self.minimizer,
            modelpars=self.result.params,
        )
        if self.args["conf_interval"]:
            try:
                _min_rel_change = self.args["conf_interval"].pop("min_rel_change", None)
                ci = ConfidenceInterval(
                    self.minimizer,
                    self.result,
                    **self.args["conf_interval"],
                )
                if _min_rel_change is not None:
                    ci.min_rel_change = _min_rel_change
                    self.args["conf_interval"]["min_rel_change"] = _min_rel_change

                trace = self.args["conf_interval"].get("trace")

                if trace is True:
                    self.args["confidence_interval"] = (ci.calc_all_ci(), ci.trace_dict)
                else:
                    self.args["confidence_interval"] = ci.calc_all_ci()

            except (MinimizerException, ValueError, KeyError):
                self.args["confidence_interval"] = {}

    def make_residual_fit(self) -> None:
        r"""Make the residuals of the model and the fit.

        !!! note "About Residual and Fit"

            The residual is calculated by the difference of the best fit `model` and
            the reference `data`. In case of a global fitting, the residuals are
            calculated for each `spectra` separately plus an avaraged global residual.

            $$
            \mathrm{residual} = \mathrm{model} - \mathrm{data}
            $$
            $$
            \mathrm{residual}_{i} = \mathrm{model}_{i} - \mathrm{data}_{i}
            $$
            $$
            \mathrm{residual}_{avg} = \frac{ \sum_{i}
                \mathrm{model}_{i} - \mathrm{data}_{i}}{i}
            $$

            The fit is defined by the difference sum of fit and reference data. In case
            of a global fitting, the residuals are calculated for each `spectra`
            separately.
        """
        df_copy: pd.DataFrame = self.df.copy()
        if self.args["global_"]:
            residual = self.result.residual.reshape((-1, self.data_size)).T
            for i, _residual in enumerate(residual, start=1):
                df_copy[f"{ColumnNamesAPI().residual}_{i}"] = _residual
                df_copy[f"{ColumnNamesAPI().fit}_{i}"] = (
                    self.df[f"{ColumnNamesAPI().intensity}_{i}"].to_numpy() + _residual
                )
            df_copy[f"{ColumnNamesAPI().residual}_avg"] = np.mean(residual, axis=0)
        else:
            residual = self.result.residual
            df_copy[ColumnNamesAPI().residual] = residual
            df_copy[ColumnNamesAPI().fit] = (
                self.df[ColumnNamesAPI().intensity].to_numpy() + residual
            )
        self.df = df_copy

    def make_fit_contributions(self) -> None:
        """Make the fit contributions of the best fit model.

        !!! info "About Fit Contributions"
            The fit contributions are made independently of the local or global fitting.
        """
        self.df = calculated_model(
            params=self.result.params,
            x=self.df.iloc[:, 0].to_numpy(),
            df=self.df,
            global_fit=self.args["global_"],
        )

    def export_correlation2args(self) -> None:
        """Export the correlation matrix to the input file arguments.

        !!! note "About Correlation Matrix"

            The linear correlation matrix is calculated from and for the pandas
            dataframe and divided into two parts:

            1. Linear correlation matrix
            2. Non-linear correlation matrix (coming later ...)

        !!! note "About reading the correlation matrix"

            The correlation matrix is stored in the `args` as a dictionary with the
            following keys:

            * `index`
            * `columns`
            * `data`

            For re-reading the data, it is important to use the following code:

            >>> import pandas as pd
            >>> pd.DataFrame(**args["linear_correlation"])

            Important is to use the generator function for access the three keys and
            their values.
        """
        self.args["linear_correlation"] = self.df.corr().to_dict(orient="split")

    def export_results2args(self) -> None:
        """Export the results of the fit to the input file arguments."""
        self.args["fit_result"] = self.df.to_dict(orient="split")

    def export_regression_metrics2args(self) -> None:
        """Export the regression metrics of the fit to the input file arguments.

        !!! note "About Regression Metrics"
            The regression metrics are calculated by the `statsmodels.stats.diagnostic`
            module.
        """
        self.args["regression_metrics"] = RegressionMetrics(self.df)()

    def export_desprective_statistic2args(self) -> None:
        """Export the descriptive statistic of the spectra, fit, and contributions."""
        self.args["descriptive_statistic"] = self.df.describe(
            percentiles=np.arange(0.1, 1, 0.1).tolist(),
        ).to_dict(orient="split")


class SaveResult:
    """Saving the result of the fitting process."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize SaveResult class.

        !!! note "About SaveResult"

            The SaveResult class is responsible for saving the results of the
            optimization process. The results are saved in the following formats:

            1. JSON (default) for all results and meta data of the fitting process.
            2. CSV for the results of the optimization process.

        !!! note "About the output `CSV`-file"

            The output files are seperated into three classes:

                1. The `results` of the optimization process.
                2. The `correlation analysis` of the optimization process.
                3. The `error analysis` of the optimization process.

            The result outputfile contains the following information:

                1. The column names of the energy axis (`x`) and the intensity values
                (`data`)
                2. The name of the column containing the energy axis (`x`)
                3. The name of the column containing the intensity values (`data`)
                4. The name of the column containing the best fit (`best_fit`)
                5. The name of the column containing the residuum (`residuum`)
                6. The name of the column containing the model contribution (`model`)
                7. The name of the column containing the error of the model
                    contribution (`model_error`)
                8. The name of the column containing the error of the best fit
                    (`best_fit_error`)
                9. The name of the column containing the error of the residuum
                    (`residuum_error`)

            The `correlation analysis` file contains the following information about all
            attributes of the model:

                1. Energy
                2. Intensity or Intensities (global fitting)
                3. Residuum
                4. Best fit
                5. Model contribution(s)

            The `error analysis` file contains the following information about all model
            attributes vs:

                1. Initial model values
                2. Current model values
                3. Best model values
                4. Residuum / error relative to the best fit
                5. Residuum / error relative to the absolute fit

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        self.df = df
        self.args = transform_nested_types(args)

    def __call__(self) -> None:
        """Call the SaveResult class."""
        self.save_as_json()
        self.save_as_csv()

    def save_as_csv(self) -> None:
        """Save the the fit results to csv files.

        !!! note "About saving the fit results"
            The fit results are saved to csv files and are divided into three different
            categories:

                1. The `results` of the optimization process.
                2. The `correlation analysis` of the optimization process.
                3. The `error analysis` of the optimization process.
        """
        _fname = Path(f"{self.args['outfile']}_fit.csv")
        self.df.to_csv(_fname, index=False)
        pd.DataFrame(**self.args["linear_correlation"]).to_csv(
            Path(f"{self.args['outfile']}_correlation.csv"),
            index=True,
            index_label="attributes",
        )
        pd.DataFrame.from_dict(self.args["fit_insights"]["variables"]).to_csv(
            Path(f"{self.args['outfile']}_components.csv"),
            index=True,
            index_label="attributes",
        )

    def save_as_json(self) -> None:
        """Save the fitting result as json file."""
        if self.args["outfile"]:
            with Path(f"{self.args['outfile']}_summary.json").open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(transform_nested_types(self.args), f, indent=4)
        else:
            msg = "No output file provided!"
            raise FileNotFoundError(msg)


def read_input_file(fname: Path) -> MutableMapping[str, Any]:
    """Read the input file.

    Read the input file as `toml`, `json`, or `yaml` files and return as a dictionary.

    Args:
        fname (str): Name of the input file.

    Raises:
        OSError: If the input file is not supported.

    Returns:
        dict: Return the input file arguments as a dictionary with additional
             information beyond the command line arguments.

    """
    fname = Path(fname)

    if fname.suffix == ".toml":
        with fname.open("rb") as f:
            args = tomli.load(f)
    elif fname.suffix == ".json":
        with fname.open(encoding="utf-8") as f:
            args = json.load(f)
    elif fname.suffix in {".yaml", ".yml"}:
        with fname.open(encoding="utf-8") as f:
            args = yaml.load(f, Loader=yaml.FullLoader)
    else:
        msg = (
            f"ERROR: Input file {fname} has not supported file format.\n"
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        )
        raise OSError(
            msg,
        )
    return args


def load_data(args: dict[str, str]) -> pd.DataFrame:
    """Load the data from a txt file.

    !!! note "About the data format"

        Load data from a txt file, which can be an ASCII file as txt, csv, or
        user-specific but rational file. The file can be separated by a delimiter.

        In case of 2d data, the columns has to be defined. In case of 3D data, all
        columns are considered as data.

    Args:
        args (Dict[str,str]): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        pd.DataFrame: DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.

    """
    try:
        if args["global_"]:
            return pd.read_csv(
                args["infile"],
                sep=args["separator"],
                header=args["header"],
                dtype=np.float64,
                decimal=args["decimal"],
                comment=args["comment"],
            )
        return pd.read_csv(
            args["infile"],
            sep=args["separator"],
            header=args["header"],
            usecols=args["column"],
            dtype=np.float64,
            decimal=args["decimal"],
            comment=args["comment"],
        )
    except ValueError:
        sys.exit(1)


def check_keywords_consistency(
    check_args: MutableMapping[str, Any],
    ref_args: dict[str, Any],
) -> None:
    """Check if the keywords are consistent.

    Check if the keywords are consistent between two dictionaries. The two dictionaries
    are reference keywords of the `cmd_line_args` and the `args` of the `input_file`.

    Args:
        check_args (MutableMapping[str, Any]): First dictionary to be checked.
        ref_args (Dict[str,Any]): Second dictionary to be checked.

    Raises:
        KeyError: If the keywords are not consistent.

    """
    for key in check_args:
        if key not in ref_args:
            msg = f"ERROR: The {key} is not parameter of the `cmd-input`!"
            raise KeyError(msg)


def unicode_check(f: Any, encoding: str = "latin1") -> Any:
    """Check if the pkl file is encoded in unicode.

    Args:
        f (Any): The pkl file to load.
        encoding (str, optional): The encoding to use. Defaults to "latin1".

    Returns:
        Any: The pkl file, which can be a nested dictionary containing raw data,
            metadata, and other information.

    """
    try:
        data_dict = pickle.load(f)
    except UnicodeDecodeError:  # pragma: no cover
        data_dict = pickle.load(f, encoding=encoding)
    return data_dict


def pkl2any(pkl_fname: Path, encoding: str = "latin1") -> Any:
    """Load a pkl file and return the data as a any type of data or object.

    Args:
        pkl_fname (Path): The pkl file to load.
        encoding (str, optional): The encoding to use. Defaults to "latin1".

    Raises:
        ValueError: If the file format is not supported.

    Returns:
        Any: Data or objects, which can contain various data types supported by pickle.

    """
    if pkl_fname.suffix == ".gz":
        with gzip.open(pkl_fname, "rb") as f:
            return unicode_check(f, encoding=encoding)
    elif pkl_fname.suffix == ".pkl":
        with pkl_fname.open("rb") as f:
            return unicode_check(f, encoding=encoding)
    else:
        choices = [".pkl", ".pkl.gz"]
        msg = (
            f"File format '{pkl_fname.suffix}' is not supported. "
            f"Supported file formats are: {choices}"
        )
        raise ValueError(msg)


def pure_fname(fname: Path) -> Path:
    """Return the filename without the suffix.

    Pure filename without the suffix is implemented to avoid the problem with
    multiple dots in the filename like `test.pkl.gz` or `test.tar.gz`.
    The `stem` attribute of the `Path` class returns the filename without the
    suffix, but it also removes only the last suffix. Hence, the `test.pkl.gz`
    will be returned as `test.pkl` and not as `test`. This function returns
    the filename without the suffix. It is implemented recursively to remove
    all suffixes.

    Args:
        fname (Path): The filename to be processed.

    Returns:
        Path: The filename without the suffix.

    """
    _fname = fname.parent / fname.stem
    return pure_fname(_fname) if _fname.suffix else _fname


def exclude_none_dictionary(value: dict[str, Any]) -> dict[str, Any]:
    """Exclude `None` values from the dictionary.

    Args:
        value (Dict[str, Any]): Dictionary to be processed to
            exclude `None` values.

    Returns:
        Dict[str, Any]: Dictionary without `None` values.

    """
    if isinstance(value, list):
        return [exclude_none_dictionary(v) for v in value if v is not None]
    if isinstance(value, dict):
        return {
            k: exclude_none_dictionary(v) for k, v in value.items() if v is not None
        }
    return value


def transform_nested_types(value: dict[str, Any]) -> dict[str, Any]:
    """Transform nested types numpy values to python values.

    Args:
        value (Dict[str, Any]): Dictionary to be processed to
            transform numpy values to python values.

    Returns:
        Dict[str, Any]: Dictionary with python values.

    """
    if isinstance(value, list):
        return [transform_nested_types(v) for v in value]
    if isinstance(value, tuple):
        return tuple(transform_nested_types(v) for v in value)
    if isinstance(value, dict):
        return {k: transform_nested_types(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return transform_nested_types(value.tolist())
    if isinstance(value, (np.int32, np.int64)):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return float(value) if isinstance(value, np.float64) else value
