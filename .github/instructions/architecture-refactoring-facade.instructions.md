---
applyTo: "spectrafit/**/*.py"
---

# Facade Pattern Implementation for SpectraFit

## Overview

Implement the Facade pattern to provide simplified, unified interfaces to SpectraFit's complex subsystems. This will hide the complexity of analyzers, solvers, utilities, and model creation while maintaining full functionality and backward compatibility.

## Key Benefits

- **Simplification**: Hide complex subsystem interactions
- **Unified API**: Single entry point for common operations
- **Maintainability**: Easier to modify internal implementations
- **User Experience**: Simplified interface for end users
- **Backward Compatibility**: Existing code continues to work

## Implementation Structure

### 1. Core Facade Interface (`spectrafit/facades/`)

Create the main facade that orchestrates all SpectraFit operations:

```python
# spectrafit/facades/spectrafit_facade.py
from typing import Dict, Any, Optional, Union, List
import pandas as pd
from pathlib import Path

from ..analyzers.correlation import CorrelationAnalyzer
from ..analyzers.statistics import StatisticsAnalyzer
from ..solvers.fit_solver import FitSolver
from ..models.model_manager import ModelManager
from ..utilities.data_loader import DataLoader
from ..utilities.validator import ConfigValidator
from ..plotting import PlottingService
from ..report import ReportGenerator

class SpectraFitFacade:
    """
    Unified facade for SpectraFit operations.

    Provides a simplified interface to all SpectraFit functionality including
    data loading, model fitting, analysis, plotting, and reporting.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize facade with optional configuration."""
        self.config = config or {}
        self._data_loader = DataLoader()
        self._validator = ConfigValidator()
        self._model_manager = ModelManager()
        self._solver = FitSolver()
        self._correlation_analyzer = CorrelationAnalyzer()
        self._stats_analyzer = StatisticsAnalyzer()
        self._plotter = PlottingService()
        self._reporter = ReportGenerator()

        # Cache for loaded data and results
        self._data_cache = {}
        self._results_cache = {}

    def load_data(self,
                  data_path: Union[str, Path],
                  config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load and validate data with optional configuration.

        Args:
            data_path: Path to data file (CSV, JSON, etc.)
            config_path: Optional path to configuration file (JSON, YAML, TOML)

        Returns:
            Dictionary containing loaded data and metadata
        """
        # Load configuration if provided
        if config_path:
            config = self._data_loader.load_config(config_path)
            self.config.update(config)

        # Load and validate data
        data = self._data_loader.load_data(data_path)
        validation_result = self._validator.validate_data(data, self.config)

        if not validation_result.is_valid:
            raise ValueError(f"Data validation failed: {validation_result.errors}")

        # Cache loaded data
        cache_key = str(data_path)
        self._data_cache[cache_key] = {
            'data': data,
            'metadata': validation_result.metadata,
            'config': self.config.copy()
        }

        return self._data_cache[cache_key]

    def fit_spectrum(self,
                     data: Optional[Dict[str, Any]] = None,
                     data_path: Optional[Union[str, Path]] = None,
                     config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform spectrum fitting with automatic model creation and optimization.

        Args:
            data: Pre-loaded data dictionary
            data_path: Path to data file (if data not provided)
            config: Fitting configuration (overrides instance config)

        Returns:
            Complete fitting results including parameters, statistics, and metadata
        """
        # Load data if not provided
        if data is None:
            if data_path is None:
                raise ValueError("Either data or data_path must be provided")
            data = self.load_data(data_path)

        # Merge configuration
        fit_config = self.config.copy()
        if config:
            fit_config.update(config)

        # Create models using factory pattern
        models = self._model_manager.create_models_from_config(fit_config)

        # Setup solver with minimizer and optimizer settings
        solver_config = {
            'minimizer': fit_config.get('minimizer', {}),
            'optimizer': fit_config.get('optimizer', {})
        }
        self._solver.configure(solver_config)

        # Perform fitting
        fit_result = self._solver.fit(
            data=data['data'],
            models=models,
            config=fit_config
        )

        # Generate comprehensive results
        results = {
            'fit_result': fit_result,
            'parameters': self._extract_parameters(fit_result),
            'statistics': self._stats_analyzer.calculate_fit_statistics(fit_result),
            'metadata': {
                'config': fit_config,
                'models_used': [str(model) for model in models],
                'convergence': fit_result.success
            }
        }

        # Cache results
        cache_key = id(data)
        self._results_cache[cache_key] = results

        return results

    def analyze_fit(self,
                    fit_results: Dict[str, Any],
                    analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Perform comprehensive analysis of fitting results.

        Args:
            fit_results: Results from fit_spectrum()
            analysis_type: Type of analysis ('correlation', 'statistics', 'full')

        Returns:
            Analysis results including correlations, confidence intervals, etc.
        """
        analysis = {}

        if analysis_type in ['correlation', 'full']:
            analysis['correlation'] = self._correlation_analyzer.analyze(
                fit_results['fit_result']
            )

        if analysis_type in ['statistics', 'full']:
            analysis['statistics'] = self._stats_analyzer.detailed_analysis(
                fit_results['fit_result']
            )
            analysis['confidence_intervals'] = self._stats_analyzer.confidence_intervals(
                fit_results['fit_result']
            )

        if analysis_type == 'full':
            analysis['residuals'] = self._stats_analyzer.residual_analysis(
                fit_results['fit_result']
            )
            analysis['goodness_of_fit'] = self._stats_analyzer.goodness_of_fit(
                fit_results['fit_result']
            )

        return analysis

    def create_plots(self,
                     fit_results: Dict[str, Any],
                     plot_types: List[str] = None,
                     save_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Generate plots for fitting results.

        Args:
            fit_results: Results from fit_spectrum()
            plot_types: List of plot types ('fit', 'residuals', 'correlation', etc.)
            save_path: Optional path to save plots

        Returns:
            Dictionary of generated plots
        """
        if plot_types is None:
            plot_types = ['fit', 'residuals', 'components']

        plots = {}

        for plot_type in plot_types:
            if plot_type == 'fit':
                plots['fit'] = self._plotter.plot_fit_result(
                    fit_results['fit_result']
                )
            elif plot_type == 'residuals':
                plots['residuals'] = self._plotter.plot_residuals(
                    fit_results['fit_result']
                )
            elif plot_type == 'components':
                plots['components'] = self._plotter.plot_components(
                    fit_results['fit_result']
                )
            elif plot_type == 'correlation':
                plots['correlation'] = self._plotter.plot_correlation_matrix(
                    fit_results['fit_result']
                )

        # Save plots if path provided
        if save_path:
            self._plotter.save_plots(plots, save_path)

        return plots

    def generate_report(self,
                        fit_results: Dict[str, Any],
                        analysis_results: Optional[Dict[str, Any]] = None,
                        output_format: str = 'json',
                        save_path: Optional[Union[str, Path]] = None) -> Union[Dict, str]:
        """
        Generate comprehensive report of fitting and analysis results.

        Args:
            fit_results: Results from fit_spectrum()
            analysis_results: Optional results from analyze_fit()
            output_format: Report format ('json', 'csv', 'html')
            save_path: Optional path to save report

        Returns:
            Report data in requested format
        """
        # Perform analysis if not provided
        if analysis_results is None:
            analysis_results = self.analyze_fit(fit_results, 'full')

        # Generate report
        report = self._reporter.generate_comprehensive_report(
            fit_results=fit_results,
            analysis_results=analysis_results,
            format=output_format
        )

        # Save report if path provided
        if save_path:
            self._reporter.save_report(report, save_path, output_format)

        return report

    def complete_workflow(self,
                          data_path: Union[str, Path],
                          config_path: Optional[Union[str, Path]] = None,
                          output_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Execute complete SpectraFit workflow from data to report.

        Args:
            data_path: Path to data file
            config_path: Optional path to configuration file
            output_dir: Optional directory for saving outputs

        Returns:
            Complete workflow results
        """
        # Step 1: Load data
        data = self.load_data(data_path, config_path)

        # Step 2: Fit spectrum
        fit_results = self.fit_spectrum(data=data)

        # Step 3: Analyze results
        analysis_results = self.analyze_fit(fit_results, 'full')

        # Step 4: Create plots
        plots = self.create_plots(fit_results)

        # Step 5: Generate report
        report = self.generate_report(fit_results, analysis_results, 'json')

        # Save outputs if directory provided
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save plots
            self._plotter.save_plots(plots, output_path / 'plots')

            # Save report
            self._reporter.save_report(report, output_path / 'report.json', 'json')

            # Save additional formats
            csv_report = self.generate_report(fit_results, analysis_results, 'csv')
            self._reporter.save_report(csv_report, output_path / 'results.csv', 'csv')

        return {
            'data': data,
            'fit_results': fit_results,
            'analysis_results': analysis_results,
            'plots': plots,
            'report': report
        }

    def _extract_parameters(self, fit_result) -> Dict[str, Any]:
        """Extract parameters in SpectraFit format."""
        params = {}
        for name, param in fit_result.params.items():
            params[name] = {
                'value': param.value,
                'stderr': param.stderr,
                'min': param.min,
                'max': param.max,
                'vary': param.vary
            }
        return params
```

### 2. Specialized Facades for Different Use Cases

Create specialized facades for specific workflows:

```python
# spectrafit/facades/fitting_facade.py
class FittingFacade:
    """Simplified facade focused on fitting operations."""

    def __init__(self):
        self._main_facade = SpectraFitFacade()

    def quick_fit(self, data_path: str, model_type: str = 'auto') -> Dict[str, Any]:
        """Perform quick fitting with automatic model selection."""
        # Auto-generate configuration based on data
        config = self._generate_auto_config(data_path, model_type)
        return self._main_facade.fit_spectrum(data_path=data_path, config=config)

    def batch_fit(self, data_files: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fit multiple spectra with the same configuration."""
        results = []
        for data_file in data_files:
            result = self._main_facade.fit_spectrum(data_path=data_file, config=config)
            results.append(result)
        return results

# spectrafit/facades/analysis_facade.py
class AnalysisFacade:
    """Simplified facade focused on analysis operations."""

    def __init__(self):
        self._main_facade = SpectraFitFacade()

    def compare_fits(self, fit_results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple fitting results."""
        pass

    def parameter_sensitivity(self, data_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parameter sensitivity."""
        pass
```

### 3. Legacy API Facade

Create a facade that maintains compatibility with existing API:

```python
# spectrafit/facades/legacy_facade.py
class LegacyAPIFacade:
    """Facade that maintains compatibility with existing SpectraFit API."""

    def __init__(self):
        self._main_facade = SpectraFitFacade()

    def run_spectrafit(self, input_file: str, output_dir: str = ".", **kwargs):
        """Legacy method that mimics original SpectraFit behavior."""
        # Map legacy parameters to new facade
        config = self._convert_legacy_config(kwargs)

        # Execute workflow
        results = self._main_facade.complete_workflow(
            data_path=input_file,
            output_dir=output_dir,
            config=config
        )

        # Return in legacy format
        return self._format_legacy_output(results)
```

### 4. Integration with Existing CLI

Update the command-line interface to use facades:

```python
# spectrafit/app/cli.py (updated)
from ..facades.spectrafit_facade import SpectraFitFacade
from ..facades.legacy_facade import LegacyAPIFacade

def main():
    """Updated main CLI function using facade pattern."""
    args = parse_arguments()

    if args.legacy_mode:
        # Use legacy facade for backward compatibility
        facade = LegacyAPIFacade()
        facade.run_spectrafit(args.input, args.output, **vars(args))
    else:
        # Use new facade for enhanced functionality
        facade = SpectraFitFacade()
        results = facade.complete_workflow(
            data_path=args.input,
            config_path=args.config,
            output_dir=args.output
        )

        if args.verbose:
            print_workflow_summary(results)
```

### 5. Plugin Integration Facade

Create facade for managing plugins and extensions:

```python
# spectrafit/facades/plugin_facade.py
class PluginFacade:
    """Facade for managing SpectraFit plugins and extensions."""

    def __init__(self):
        self._plugin_manager = PluginManager()
        self._main_facade = SpectraFitFacade()

    def load_plugins(self, plugin_dir: str):
        """Load plugins from directory."""
        pass

    def execute_with_plugins(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with plugin enhancements."""
        pass
```

## Migration Strategy

### Phase 1: Core Facade Development

1. Implement `SpectraFitFacade` with basic functionality
2. Create simple wrapper methods for existing subsystems
3. Ensure all core operations work through facade

### Phase 2: Specialized Facades

1. Create specialized facades for different use cases
2. Implement legacy compatibility facade
3. Update CLI to optionally use facades

### Phase 3: Advanced Features

1. Add batch processing capabilities
2. Implement plugin integration facade
3. Create workflow templates and presets

### Phase 4: Migration and Deprecation

1. Update documentation to promote facade usage
2. Add deprecation warnings to direct subsystem access
3. Provide migration guides for existing code

## Best Practices

- **Maintain Backward Compatibility**: Existing code should continue to work
- **Progressive Enhancement**: Add facade methods gradually
- **Error Handling**: Provide clear, informative error messages
- **Configuration Management**: Support all existing configuration formats
- **Type Safety**: Use comprehensive type hints
- **Documentation**: Provide extensive docstrings and examples
- **Testing**: Ensure facades don't break existing functionality

## Example Usage

### Simple Fitting

```python
from spectrafit.facades import SpectraFitFacade

facade = SpectraFitFacade()

# Complete workflow in one call
results = facade.complete_workflow(
    data_path="spectrum.csv",
    config_path="config.json",
    output_dir="results/"
)

print(f"Fit successful: {results['fit_results']['metadata']['convergence']}")
```

### Step-by-step Workflow

```python
from spectrafit.facades import SpectraFitFacade

facade = SpectraFitFacade()

# Step-by-step approach
data = facade.load_data("spectrum.csv", "config.json")
fit_results = facade.fit_spectrum(data=data)
analysis = facade.analyze_fit(fit_results, 'full')
plots = facade.create_plots(fit_results, ['fit', 'residuals'])
report = facade.generate_report(fit_results, analysis, 'json')
```

### Legacy Compatibility

```python
from spectrafit.facades import LegacyAPIFacade

legacy_facade = LegacyAPIFacade()

# Works exactly like the old API
legacy_facade.run_spectrafit(
    input_file="spectrum.csv",
    output_dir="results/",
    model_type="pseudovoigt"
)
```

Source:

- https://github.com/faif/python-patterns/blob/master/patterns/structural/facade.py
- https://refactoring.guru/design-patterns/facade/python/example
