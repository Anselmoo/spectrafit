"""MCP Server plugin for GitHub Copilot integration with SpectraFit.

This plugin implements a Model Context Protocol (MCP) server that allows GitHub Copilot
to perform spectral analysis through natural language interactions with SpectraFit.
"""

from __future__ import annotations

import asyncio
import json
import logging

from io import StringIO
from typing import Any

import numpy as np
import pandas as pd

from scipy.signal import find_peaks

from spectrafit.plugins.notebook import SpectraFitNotebook


# Try to import MCP dependencies, gracefully handle if not available
try:
    import mcp.server.stdio

    from mcp import types
    from mcp.server import Server

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Define stub classes for type checking when MCP is not available
    Server = None  # type: ignore
    types = None  # type: ignore


logger = logging.getLogger(__name__)

# Constants
MIN_DATA_POINTS = 10


class SpectraFitMCPServer:
    """MCP Server for SpectraFit integration with GitHub Copilot.

    This server provides tools and resources for spectral analysis through
    the Model Context Protocol, enabling natural language interactions with
    SpectraFit's powerful fitting engine.
    """

    def __init__(self) -> None:
        """Initialize the SpectraFit MCP Server.

        Raises:
            ImportError: If MCP dependencies are not available.
        """
        if not MCP_AVAILABLE:
            msg = (
                "MCP dependencies are not available. "
                "Please install with: pip install spectrafit[mcp]"
            )
            raise ImportError(msg)

        self.server = Server("spectrafit")
        self._setup_tools()
        self._setup_resources()

    def _setup_tools(self) -> None:
        """Set up MCP tools for spectral analysis."""

        @self.server.call_tool()
        async def fit_spectrum(arguments: dict[str, Any]) -> list[types.TextContent]:
            """Perform complete spectral fitting with comprehensive results.

            Args:
                arguments: Dictionary containing:
                    - data: CSV data with 'Energy' and 'Intensity' columns
                    - model: Peak model configuration
                    - technique: Spectroscopic technique (optional)
                    - minimizer_settings: Minimizer configuration (optional)
                    - optimizer_settings: Optimizer configuration (optional)

            Returns:
                List of text content with fitting results.
            """
            try:
                # Parse input data
                data_str = arguments.get("data", "")
                if not data_str:
                    return [
                        types.TextContent(
                            type="text",
                            text=(
                                "Error: No data provided. Please provide CSV data with "
                                "'Energy' and 'Intensity' columns."
                            ),
                        )
                    ]

                # Load data from CSV string
                df = pd.read_csv(StringIO(data_str))

                # Validate required columns
                if not {"Energy", "Intensity"}.issubset(df.columns):
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: Data must contain 'Energy' and 'Intensity' columns.",
                        )
                    ]

                # Get model configuration
                model_config = arguments.get("model", {})
                if not model_config:
                    return [
                        types.TextContent(
                            type="text", text="Error: No model configuration provided."
                        )
                    ]

                # Initialize SpectraFit notebook
                technique = arguments.get("technique", "general")
                notebook = SpectraFitNotebook(
                    df=df,
                    x_column="Energy",
                    y_column="Intensity",
                    title=f"{technique.title()} Spectral Fit",
                )

                # Prepare solver settings
                solver_settings = {}
                if "minimizer_settings" in arguments:
                    solver_settings["minimizer"] = arguments["minimizer_settings"]
                if "optimizer_settings" in arguments:
                    solver_settings["optimizer"] = arguments["optimizer_settings"]

                # Perform fitting
                notebook.fitting(
                    initial_model=[model_config],
                    show_plot=False,
                    show_metric=False,
                    show_df=False,
                    solver_settings=solver_settings if solver_settings else None,
                )

                # Extract results
                fit_results = notebook.args
                results_summary = self._format_fit_results(fit_results)

                return [
                    types.TextContent(
                        type="text",
                        text=f"Spectral fitting completed successfully:\n\n{results_summary}",
                    )
                ]

            except Exception as e:
                logger.exception("Error in fit_spectrum tool")
                return [
                    types.TextContent(
                        type="text", text=f"Error performing spectral fit: {e!s}"
                    )
                ]

        @self.server.call_tool()
        async def auto_peak_detection(
            arguments: dict[str, Any],
        ) -> list[types.TextContent]:
            """Automatic peak detection with suggested model generation.

            Args:
                arguments: Dictionary containing:
                    - data: CSV data with 'Energy' and 'Intensity' columns
                    - prominence: Peak prominence threshold (optional)
                    - height: Peak height threshold (optional)
                    - distance: Minimum distance between peaks (optional)
                    - width: Peak width constraints (optional)
                    - technique: Spectroscopic technique for model suggestions (optional)

            Returns:
                List of text content with detected peaks and suggested models.
            """
            try:
                # Parse input data
                data_str = arguments.get("data", "")
                if not data_str:
                    return [
                        types.TextContent(type="text", text="Error: No data provided.")
                    ]

                df = pd.read_csv(StringIO(data_str))

                # Validate columns
                if not {"Energy", "Intensity"}.issubset(df.columns):
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: Data must contain 'Energy' and 'Intensity' columns.",
                        )
                    ]

                x = df["Energy"].to_numpy()
                y = df["Intensity"].to_numpy()

                # Peak detection parameters
                prominence = arguments.get("prominence")
                height = arguments.get("height")
                distance = arguments.get("distance")
                width = arguments.get("width")

                # Perform peak detection
                peaks, properties = find_peaks(
                    y,
                    prominence=prominence,
                    height=height,
                    distance=distance,
                    width=width,
                )

                if len(peaks) == 0:
                    return [
                        types.TextContent(
                            type="text",
                            text="No peaks detected. Try adjusting the detection parameters.",
                        )
                    ]

                # Generate peak information
                peak_positions = x[peaks]
                peak_intensities = y[peaks]

                # Get technique-specific suggestions
                technique = arguments.get("technique", "general")
                suggested_models = self._generate_technique_models(
                    peak_positions, peak_intensities, technique
                )

                # Format results
                results = "Peak Detection Results:\n"
                results += f"Found {len(peaks)} peaks\n\n"

                for i, (pos, intensity) in enumerate(
                    zip(peak_positions, peak_intensities)
                ):
                    results += f"Peak {i + 1}: Position = {pos:.2f}, Intensity = {intensity:.2f}\n"

                results += f"\n\nSuggested {technique} model configuration:\n"
                results += json.dumps(suggested_models, indent=2)

                return [types.TextContent(type="text", text=results)]

            except Exception as e:
                logger.exception("Error in auto_peak_detection tool")
                return [
                    types.TextContent(
                        type="text", text=f"Error in peak detection: {e!s}"
                    )
                ]

        @self.server.call_tool()
        async def generate_fit_model(
            arguments: dict[str, Any],
        ) -> list[types.TextContent]:
            """Generate technique-specific model templates.

            Args:
                arguments: Dictionary containing:
                    - technique: Spectroscopic technique (raman, uv-vis, xps, ir, moessbauer)
                    - num_peaks: Number of peaks to include (optional)
                    - energy_range: Energy range [min, max] (optional)
                    - peak_positions: Specific peak positions (optional)

            Returns:
                List of text content with model template.
            """
            try:
                technique = arguments.get("technique", "raman").lower()
                num_peaks = arguments.get("num_peaks", 3)
                energy_range = arguments.get("energy_range")
                peak_positions = arguments.get("peak_positions", [])

                # Generate technique-specific model
                model_template = self._create_technique_template(
                    technique, num_peaks, energy_range, peak_positions
                )

                results = f"Model template for {technique.upper()} spectroscopy:\n\n"
                results += json.dumps(model_template, indent=2)

                return [types.TextContent(type="text", text=results)]

            except Exception as e:
                logger.exception("Error in generate_fit_model tool")
                return [
                    types.TextContent(
                        type="text", text=f"Error generating model template: {e!s}"
                    )
                ]

        @self.server.call_tool()
        async def validate_spectral_data(
            arguments: dict[str, Any],
        ) -> list[types.TextContent]:
            """Validate spectral data format and quality.

            Args:
                arguments: Dictionary containing:
                    - data: CSV data to validate
                    - technique: Expected spectroscopic technique (optional)

            Returns:
                List of text content with validation results and recommendations.
            """
            try:
                data_str = arguments.get("data", "")
                if not data_str:
                    return [
                        types.TextContent(
                            type="text", text="Error: No data provided for validation."
                        )
                    ]

                df = pd.read_csv(StringIO(data_str))

                # Perform validation
                validation_results = self._validate_data_quality(df)
                technique = arguments.get("technique", "general")

                # Add technique-specific validation
                if technique != "general":
                    technique_validation = self._validate_technique_data(df, technique)
                    validation_results.update(technique_validation)

                # Format results
                results = "Data Validation Results:\n\n"
                for category, checks in validation_results.items():
                    results += f"{category.upper()}:\n"
                    for check, status in checks.items():
                        status_symbol = "✓" if status["passed"] else "✗"
                        results += f"  {status_symbol} {check}: {status['message']}\n"
                    results += "\n"

                return [types.TextContent(type="text", text=results)]

            except Exception as e:
                logger.exception("Error in validate_spectral_data tool")
                return [
                    types.TextContent(type="text", text=f"Error validating data: {e!s}")
                ]

    def _setup_resources(self) -> None:
        """Set up MCP resources for SpectraFit information."""

        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available SpectraFit resources."""
            return [
                types.Resource(
                    uri="spectrafit://models/fitting-functions",
                    name="Available Fitting Functions",
                    description=(
                        "JSON list of available peak and background functions in SpectraFit"
                    ),
                    mimeType="application/json",
                ),
                types.Resource(
                    uri="spectrafit://examples/sample-data",
                    name="Sample Spectral Data",
                    description="CSV sample spectral data for testing",
                    mimeType="text/csv",
                ),
                types.Resource(
                    uri="spectrafit://config/default-parameters",
                    name="Default Parameters",
                    description="JSON configuration templates for different techniques",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read SpectraFit resource content."""
            if uri == "spectrafit://models/fitting-functions":
                return self._get_fitting_functions()
            if uri == "spectrafit://examples/sample-data":
                return self._get_sample_data()
            if uri == "spectrafit://config/default-parameters":
                return self._get_default_parameters()
            msg = f"Unknown resource: {uri}"
            raise ValueError(msg)

    def _format_fit_results(self, fit_results: dict[str, Any]) -> str:
        """Format fitting results for display."""
        results = []

        # Add fit statistics
        if "fit_insights" in fit_results:
            insights = fit_results["fit_insights"]

            if "statistics" in insights:
                stats = insights["statistics"]
                results.append("FIT STATISTICS:")
                results.append(f"  R² = {stats.get('r_squared', 'N/A')}")
                results.append(
                    f"  Reduced χ² = {stats.get('reduced_chi_squared', 'N/A')}"
                )
                results.append(f"  AIC = {stats.get('aic', 'N/A')}")
                results.append(f"  BIC = {stats.get('bic', 'N/A')}")
                results.append("")

            if "variables" in insights:
                results.append("FITTED PARAMETERS:")
                variables = insights["variables"]
                for peak_name, params in variables.items():
                    results.append(f"  {peak_name}:")
                    for param_name, param_info in params.items():
                        value = param_info.get("value", "N/A")
                        stderr = param_info.get("stderr", "N/A")
                        results.append(f"    {param_name}: {value} ± {stderr}")
                    results.append("")

        return "\n".join(results)

    def _generate_technique_models(
        self, positions: np.ndarray, intensities: np.ndarray, technique: str
    ) -> dict[str, Any]:
        """Generate technique-specific model suggestions."""
        technique_defaults = {
            "raman": {"function": "lorentzian", "fwhm_range": (5, 50)},
            "uv-vis": {"function": "gaussian", "fwhm_range": (10, 100)},
            "xps": {"function": "voigt", "fwhm_range": (0.5, 5)},
            "ir": {"function": "lorentzian", "fwhm_range": (2, 30)},
            "moessbauer": {"function": "lorentzian", "fwhm_range": (0.1, 2)},
        }

        defaults = technique_defaults.get(technique, technique_defaults["raman"])
        function = defaults["function"]
        fwhm_min, fwhm_max = defaults["fwhm_range"]

        peaks = {}
        for i, (pos, intensity) in enumerate(zip(positions, intensities)):
            peak_name = str(i + 1)
            estimated_fwhm = min(max(abs(pos) * 0.02, fwhm_min), fwhm_max)

            peaks[peak_name] = {
                function: {
                    "amplitude": {
                        "max": float(intensity * 2),
                        "min": 0,
                        "vary": True,
                        "value": float(intensity),
                    },
                    "center": {
                        "max": float(pos + 20),
                        "min": float(pos - 20),
                        "vary": True,
                        "value": float(pos),
                    },
                }
            }

            # Add appropriate width parameters
            if function in ["gaussian", "lorentzian"]:
                peaks[peak_name][function]["fwhm"] = {
                    "max": fwhm_max,
                    "min": fwhm_min,
                    "vary": True,
                    "value": estimated_fwhm,
                }
            elif function == "voigt":
                peaks[peak_name][function]["fwhmg"] = {
                    "max": fwhm_max,
                    "min": fwhm_min,
                    "vary": True,
                    "value": estimated_fwhm,
                }
                peaks[peak_name][function]["fwhml"] = {
                    "max": fwhm_max,
                    "min": fwhm_min,
                    "vary": True,
                    "value": estimated_fwhm,
                }

        return {"peaks": peaks}

    def _create_technique_template(
        self,
        technique: str,
        num_peaks: int,
        energy_range: list[float] | None = None,
        peak_positions: list[float] | None = None,
    ) -> dict[str, Any]:
        """Create technique-specific model templates."""
        technique_specs = {
            "raman": {
                "function": "lorentzian",
                "energy_range": [200, 4000],
                "fwhm_range": [5, 50],
                "default_positions": [500, 1000, 1500],
            },
            "uv-vis": {
                "function": "gaussian",
                "energy_range": [200, 800],
                "fwhm_range": [10, 100],
                "default_positions": [300, 450, 600],
            },
            "xps": {
                "function": "voigt",
                "energy_range": [0, 1500],
                "fwhm_range": [0.5, 5],
                "default_positions": [285, 400, 530],
            },
            "ir": {
                "function": "lorentzian",
                "energy_range": [400, 4000],
                "fwhm_range": [2, 30],
                "default_positions": [1000, 1500, 3000],
            },
            "moessbauer": {
                "function": "lorentzian",
                "energy_range": [-10, 10],
                "fwhm_range": [0.1, 2],
                "default_positions": [-1, 0, 1],
            },
        }

        spec = technique_specs.get(technique, technique_specs["raman"])

        if not peak_positions:
            # Generate evenly spaced positions
            range_min, range_max = energy_range or spec["energy_range"]
            positions = np.linspace(range_min, range_max, num_peaks + 2)[1:-1]
        else:
            positions = peak_positions[:num_peaks]

        function = spec["function"]
        fwhm_min, fwhm_max = spec["fwhm_range"]

        template = {
            "description": {
                "project_name": f"{technique.upper()} Spectral Analysis",
                "project_details": f"Template for {technique} spectroscopy",
                "keywords": [technique, "fitting", "spectral-analysis"],
            },
            "minimizer": {"nan_policy": "propagate", "calc_covar": True},
            "optimizer": {"max_nfev": 1000, "method": "leastsq"},
            "peaks": {},
        }

        for i, pos in enumerate(positions):
            peak_name = str(i + 1)
            estimated_fwhm = (fwhm_min + fwhm_max) / 2

            template["peaks"][peak_name] = {
                function: {
                    "amplitude": {"max": 100, "min": 0, "vary": True, "value": 50},
                    "center": {
                        "max": float(pos + 50),
                        "min": float(pos - 50),
                        "vary": True,
                        "value": float(pos),
                    },
                }
            }

            # Add width parameters based on function type
            if function in ["gaussian", "lorentzian"]:
                template["peaks"][peak_name][function]["fwhm"] = {
                    "max": fwhm_max,
                    "min": fwhm_min,
                    "vary": True,
                    "value": estimated_fwhm,
                }
            elif function == "voigt":
                template["peaks"][peak_name][function]["fwhmg"] = {
                    "max": fwhm_max,
                    "min": fwhm_min,
                    "vary": True,
                    "value": estimated_fwhm,
                }
                template["peaks"][peak_name][function]["fwhml"] = {
                    "max": fwhm_max,
                    "min": fwhm_min,
                    "vary": True,
                    "value": estimated_fwhm,
                }

        return template

    def _validate_data_quality(
        self, df: pd.DataFrame
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Validate basic data quality."""
        validation = {"format": {}, "data_quality": {}, "recommendations": {}}

        # Format validation
        required_cols = {"Energy", "Intensity"}
        has_required = required_cols.issubset(df.columns)
        validation["format"]["required_columns"] = {
            "passed": has_required,
            "message": "Has Energy and Intensity columns"
            if has_required
            else "Missing required columns",
        }

        if has_required:
            # Check for numeric data
            energy_numeric = pd.api.types.is_numeric_dtype(df["Energy"])
            intensity_numeric = pd.api.types.is_numeric_dtype(df["Intensity"])

            validation["format"]["numeric_data"] = {
                "passed": energy_numeric and intensity_numeric,
                "message": "Data columns are numeric"
                if energy_numeric and intensity_numeric
                else "Non-numeric data detected",
            }

            # Data quality checks
            energy_monotonic = (
                df["Energy"].is_monotonic_increasing
                or df["Energy"].is_monotonic_decreasing
            )
            validation["data_quality"]["energy_monotonic"] = {
                "passed": energy_monotonic,
                "message": "Energy values are monotonic"
                if energy_monotonic
                else "Energy values are not monotonic",
            }

            has_nan = df[["Energy", "Intensity"]].isna().any().any()
            validation["data_quality"]["no_missing_values"] = {
                "passed": not has_nan,
                "message": "No missing values"
                if not has_nan
                else "Contains missing values",
            }

            # Check data range
            num_points = len(df)
            validation["data_quality"]["sufficient_points"] = {
                "passed": num_points >= MIN_DATA_POINTS,
                "message": f"{num_points} data points"
                + (
                    " (sufficient)"
                    if num_points >= MIN_DATA_POINTS
                    else " (consider more data)"
                ),
            }

        return validation

    def _validate_technique_data(
        self, df: pd.DataFrame, technique: str
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Validate technique-specific data requirements."""
        technique_ranges = {
            "raman": {"min": 100, "max": 4500, "unit": "cm⁻¹"},
            "uv-vis": {"min": 180, "max": 1000, "unit": "nm"},
            "xps": {"min": 0, "max": 2000, "unit": "eV"},
            "ir": {"min": 300, "max": 4500, "unit": "cm⁻¹"},
            "moessbauer": {"min": -15, "max": 15, "unit": "mm/s"},
        }

        validation = {"technique_specific": {}}

        if technique in technique_ranges and "Energy" in df.columns:
            spec = technique_ranges[technique]
            energy_min, energy_max = df["Energy"].min(), df["Energy"].max()

            in_range = (energy_min >= spec["min"] - 50) and (
                energy_max <= spec["max"] + 50
            )
            validation["technique_specific"]["energy_range"] = {
                "passed": in_range,
                "message": f"Energy range {energy_min:.1f}-{energy_max:.1f} {spec['unit']}"
                + (
                    " is appropriate"
                    if in_range
                    else f" (expected {spec['min']}-{spec['max']} {spec['unit']})"
                ),
            }

        return validation

    def _get_fitting_functions(self) -> str:
        """Get list of available fitting functions."""
        functions = {
            "peak_functions": [
                "gaussian",
                "lorentzian",
                "voigt",
                "pseudovoigt",
                "pearson1",
                "pearson2",
                "pearson3",
                "pearson4",
                "orcagaussian",
            ],
            "background_functions": [
                "linear",
                "constant",
                "exponential",
                "power",
                "polynom2",
                "polynom3",
            ],
            "step_functions": ["atan_step", "erf_step", "log_step", "heaviside"],
            "convolution_functions": ["cgaussian", "clorentzian", "cvoigt"],
            "moessbauer_functions": [
                "moessbauer_singlet",
                "moessbauer_doublet",
                "moessbauer_sextet",
                "moessbauer_octet",
            ],
        }
        return json.dumps(functions, indent=2)

    def _get_sample_data(self) -> str:
        """Get sample spectral data for testing."""
        # Generate sample Raman spectrum
        rng = np.random.default_rng()
        energy = np.linspace(200, 3500, 1000)
        intensity = (
            50 * np.exp(-(((energy - 1000) / 50) ** 2))  # Peak 1
            + 30 * np.exp(-(((energy - 1500) / 30) ** 2))  # Peak 2
            + 40 * np.exp(-(((energy - 2800) / 40) ** 2))  # Peak 3
            + rng.normal(0, 2, len(energy))  # Noise
            + 5  # Baseline
        )

        df = pd.DataFrame({"Energy": energy, "Intensity": intensity})
        return df.to_csv(index=False)

    def _get_default_parameters(self) -> str:
        """Get default parameter templates."""
        templates = {
            "raman": {
                "description": {
                    "project_name": "Raman Spectroscopy",
                    "keywords": ["raman", "vibrational", "spectroscopy"],
                },
                "minimizer": {"nan_policy": "propagate", "calc_covar": True},
                "optimizer": {"max_nfev": 1000, "method": "leastsq"},
                "energy_range": [200, 4000],
                "typical_fwhm": [5, 50],
                "recommended_function": "lorentzian",
            },
            "uv-vis": {
                "description": {
                    "project_name": "UV-Vis Spectroscopy",
                    "keywords": ["uv-vis", "electronic", "absorption"],
                },
                "minimizer": {"nan_policy": "propagate", "calc_covar": True},
                "optimizer": {"max_nfev": 1000, "method": "leastsq"},
                "energy_range": [200, 800],
                "typical_fwhm": [10, 100],
                "recommended_function": "gaussian",
            },
            "xps": {
                "description": {
                    "project_name": "X-ray Photoelectron Spectroscopy",
                    "keywords": ["xps", "photoelectron", "surface"],
                },
                "minimizer": {"nan_policy": "propagate", "calc_covar": True},
                "optimizer": {"max_nfev": 1000, "method": "leastsq"},
                "energy_range": [0, 1500],
                "typical_fwhm": [0.5, 5],
                "recommended_function": "voigt",
            },
        }
        return json.dumps(templates, indent=2)

    async def run(self) -> None:
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            msg = (
                "MCP dependencies are not available. "
                "Please install with: pip install spectrafit[mcp]"
            )
            raise ImportError(msg)

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


def command_line_runner() -> None:
    """Run the MCP server from the command line."""
    try:
        server = SpectraFitMCPServer()
        asyncio.run(server.run())
    except ImportError:
        logger.exception("MCP dependencies not available")
        logger.info("To install MCP support, run: pip install spectrafit[mcp]")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception:
        logger.exception("Error running MCP server")


if __name__ == "__main__":
    command_line_runner()
