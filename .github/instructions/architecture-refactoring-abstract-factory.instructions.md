---
applyTo: "spectrafit/**/*.py"
---

# Abstract Factory Pattern Implementation for SpectraFit

## Overview

Implement the Abstract Factory pattern to create families of related model objects without specifying their concrete classes. This will improve code organization, maintainability, and extensibility for SpectraFit's various model types.

## Key Benefits

- **Consistency**: Ensure related models are created together
- **Flexibility**: Easy to add new model families
- **Decoupling**: Client code doesn't depend on concrete model classes
- **Validation**: Centralized parameter validation and model setup

## Implementation Structure

### 1. Interface Definitions (`spectrafit/interfaces/`)

Create abstract base classes for model interfaces:

```python
# spectrafit/interfaces/model_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from lmfit import Model

class ModelInterface(ABC):
    """Abstract interface for all SpectraFit models."""

    @abstractmethod
    def create_model(self, params: Dict[str, Any]) -> Model:
        """Create and configure the LMfit model."""
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate model parameters according to SpectraFit conventions."""
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameter structure for this model type."""
        pass

# spectrafit/interfaces/factory_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from .model_interface import ModelInterface

class ModelFactoryInterface(ABC):
    """Abstract factory interface for creating model families."""

    @abstractmethod
    def create_peak_model(self, model_type: str, params: Dict[str, Any]) -> ModelInterface:
        """Create peak models (gaussian, lorentzian, pseudovoigt, etc.)."""
        pass

    @abstractmethod
    def create_background_model(self, model_type: str, params: Dict[str, Any]) -> ModelInterface:
        """Create background models (linear, polynomial, exponential, etc.)."""
        pass

    @abstractmethod
    def create_composite_model(self, components: list) -> ModelInterface:
        """Create composite models from multiple components."""
        pass

    @abstractmethod
    def get_supported_models(self) -> Dict[str, list]:
        """Return dictionary of supported model types by category."""
        pass
```

### 2. Concrete Model Implementations (`spectrafit/models/`)

Refactor existing models to implement the ModelInterface:

```python
# spectrafit/models/peak_models.py
from typing import Dict, Any
from lmfit import Model
from lmfit.models import GaussianModel, LorentzianModel, PseudoVoigtModel
from ..interfaces.model_interface import ModelInterface

class GaussianModelImpl(ModelInterface):
    """Gaussian peak model implementation."""

    def create_model(self, params: Dict[str, Any]) -> Model:
        model = GaussianModel()
        # Apply SpectraFit parameter conventions
        for param_name, param_config in params.items():
            if param_name in model.param_names:
                model.set_param_hint(
                    param_name,
                    value=param_config.get('value'),
                    min=param_config.get('min'),
                    max=param_config.get('max'),
                    vary=param_config.get('vary', True)
                )
        return model

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        required_params = {'amplitude', 'center', 'sigma'}
        return all(param in params for param in required_params)

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'amplitude': {'max': 2, 'min': 0, 'vary': True, 'value': 1},
            'center': {'max': 2, 'min': -2, 'vary': True, 'value': 0},
            'sigma': {'max': 0.1, 'min': 0.01, 'vary': True, 'value': 0.05}
        }

class PseudoVoigtModelImpl(ModelInterface):
    """PseudoVoigt peak model implementation."""

    def create_model(self, params: Dict[str, Any]) -> Model:
        model = PseudoVoigtModel()
        # Convert SpectraFit FWHM parameters to LMfit parameters
        for param_name, param_config in params.items():
            if param_name == 'fwhmg':
                # Convert FWHM Gaussian to sigma
                model.set_param_hint('sigma', **param_config)
            elif param_name == 'fwhml':
                # Set Lorentzian component
                model.set_param_hint('gamma', **param_config)
            elif param_name in model.param_names:
                model.set_param_hint(param_name, **param_config)
        return model

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        required_params = {'amplitude', 'center', 'fwhmg', 'fwhml'}
        return all(param in params for param in required_params)

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'amplitude': {'max': 2, 'min': 0, 'vary': True, 'value': 1},
            'center': {'max': 2, 'min': -2, 'vary': True, 'value': 0},
            'fwhmg': {'max': 0.1, 'min': 0.02, 'vary': True, 'value': 0.01},
            'fwhml': {'max': 0.1, 'min': 0.01, 'vary': True, 'value': 0.01}
        }
```

### 3. Factory Implementations (`spectrafit/factories/`)

Create concrete factories for different model families:

```python
# spectrafit/factories/spectral_factory.py
from typing import Dict, Any, Type
from ..interfaces.factory_interface import ModelFactoryInterface
from ..interfaces.model_interface import ModelInterface
from ..models.peak_models import (
    GaussianModelImpl, LorentzianModelImpl, PseudoVoigtModelImpl
)
from ..models.background_models import (
    LinearBackgroundImpl, PolynomialBackgroundImpl
)

class SpectralModelFactory(ModelFactoryInterface):
    """Factory for creating spectroscopic models."""

    def __init__(self):
        self._peak_models = {
            'gaussian': GaussianModelImpl,
            'lorentzian': LorentzianModelImpl,
            'pseudovoigt': PseudoVoigtModelImpl,
        }
        self._background_models = {
            'linear': LinearBackgroundImpl,
            'polynomial': PolynomialBackgroundImpl,
        }

    def create_peak_model(self, model_type: str, params: Dict[str, Any]) -> ModelInterface:
        if model_type not in self._peak_models:
            raise ValueError(f"Unsupported peak model: {model_type}")

        model_class = self._peak_models[model_type]
        model_instance = model_class()

        # Validate parameters
        if not model_instance.validate_parameters(params):
            raise ValueError(f"Invalid parameters for {model_type} model")

        return model_instance

    def create_background_model(self, model_type: str, params: Dict[str, Any]) -> ModelInterface:
        if model_type not in self._background_models:
            raise ValueError(f"Unsupported background model: {model_type}")

        model_class = self._background_models[model_type]
        model_instance = model_class()

        if not model_instance.validate_parameters(params):
            raise ValueError(f"Invalid parameters for {model_type} model")

        return model_instance

    def create_composite_model(self, components: list) -> ModelInterface:
        # Implementation for combining multiple models
        pass

    def get_supported_models(self) -> Dict[str, list]:
        return {
            'peaks': list(self._peak_models.keys()),
            'backgrounds': list(self._background_models.keys())
        }

# spectrafit/factories/analytical_factory.py
class AnalyticalModelFactory(ModelFactoryInterface):
    """Factory for creating analytical chemistry models."""

    def __init__(self):
        self._peak_models = {
            'chromatographic_peak': ChromatographicPeakImpl,
            'mass_spec_peak': MassSpecPeakImpl,
        }

    # Similar implementation pattern...
```

### 4. Factory Registry (`spectrafit/factories/registry.py`)

Create a registry system for managing different factories:

```python
from typing import Dict, Type, Optional
from ..interfaces.factory_interface import ModelFactoryInterface
from .spectral_factory import SpectralModelFactory
from .analytical_factory import AnalyticalModelFactory

class FactoryRegistry:
    """Registry for managing model factories."""

    def __init__(self):
        self._factories: Dict[str, Type[ModelFactoryInterface]] = {
            'spectral': SpectralModelFactory,
            'analytical': AnalyticalModelFactory,
        }
        self._instances: Dict[str, ModelFactoryInterface] = {}

    def register_factory(self, name: str, factory_class: Type[ModelFactoryInterface]):
        """Register a new factory type."""
        self._factories[name] = factory_class

    def get_factory(self, name: str) -> ModelFactoryInterface:
        """Get factory instance (singleton pattern)."""
        if name not in self._instances:
            if name not in self._factories:
                raise ValueError(f"Unknown factory type: {name}")
            self._instances[name] = self._factories[name]()
        return self._instances[name]

    def list_factories(self) -> list:
        """List available factory types."""
        return list(self._factories.keys())

# Global registry instance
factory_registry = FactoryRegistry()
```

### 5. Integration with Existing API

Update existing API to use the factory pattern:

```python
# spectrafit/api/model_creation.py
from typing import Dict, Any, Optional
from ..factories.registry import factory_registry

def create_model_from_config(config: Dict[str, Any], factory_type: str = 'spectral'):
    """Create models from SpectraFit configuration using factory pattern."""
    factory = factory_registry.get_factory(factory_type)

    models = []

    # Process peaks configuration
    if 'peaks' in config:
        for peak_id, peak_config in config['peaks'].items():
            for model_type, params in peak_config.items():
                model = factory.create_peak_model(model_type, params)
                models.append(model)

    # Process background configuration
    if 'background' in config:
        for bg_type, bg_params in config['background'].items():
            model = factory.create_background_model(bg_type, bg_params)
            models.append(model)

    return models
```

## Migration Steps

### Phase 1: Interface Creation

1. Create interface definitions in `spectrafit/interfaces/`
2. Define abstract base classes for models and factories
3. Ensure type hints and documentation are complete

### Phase 2: Model Refactoring

1. Refactor existing model implementations to use interfaces
2. Ensure parameter validation follows SpectraFit conventions
3. Maintain backward compatibility with existing API

### Phase 3: Factory Implementation

1. Create concrete factory classes
2. Implement factory registry system
3. Add support for model discovery and validation

### Phase 4: API Integration

1. Update existing API methods to use factories
2. Provide migration path for existing code
3. Add comprehensive error handling

### Phase 5: Testing and Documentation

1. Create unit tests for all factory components
2. Update documentation with new patterns
3. Provide examples and migration guides

## Best Practices

- Follow SpectraFit parameter conventions (max, min, vary, value)
- Ensure all models support minimizer and optimizer settings
- Maintain compatibility with existing JSON/YAML/TOML input formats
- Use type hints and comprehensive docstrings
- Implement proper error handling with informative messages
- Follow PEP8 and project coding standards

## Example Usage

```python
from spectrafit.factories.registry import factory_registry

# Get spectral factory
factory = factory_registry.get_factory('spectral')

# Create peak model
peak_params = {
    'amplitude': {'max': 2, 'min': 0, 'vary': True, 'value': 1},
    'center': {'max': 2, 'min': -2, 'vary': True, 'value': 0},
    'fwhmg': {'max': 0.1, 'min': 0.02, 'vary': True, 'value': 0.01},
    'fwhml': {'max': 0.1, 'min': 0.01, 'vary': True, 'value': 0.01}
}

model = factory.create_peak_model('pseudovoigt', peak_params)
lmfit_model = model.create_model(peak_params)
```

Source:

- https://github.com/faif/python-patterns/blob/master/patterns/creational/abstract_factory.py
- https://refactoring.guru/design-patterns/abstract-factory/python/example#lang-features
