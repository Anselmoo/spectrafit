---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.0
  kernelspec:
    display_name: .venv
    language: python
    name: python3
---

# Test of the RIXS Map visualization tool

For visualization of the RIXS map, we use the `RixsMap` class. The class is initialized with the RIXS map data and the energy axis. The energy axis is a list of two elements: the first element is the energy axis of the RIXS map, the second element is the energy axis of the RIXS map after the energy loss correction. The energy axis is in units of eV.

```python
import numpy as np
from spectrafit.plugins.rixs_visualizer import RIXSApp
from spectrafit.api.rixs_model import SizeRatioAPI
```

## Initialization

For visualization of a RIXS map, we use the `RIXSApp` class. The class only requires the _incident_ and _emission_ energy as 1D arrays.
The RIXS map itself has to be stored as a 2D meshgrid of intensities. By default the RIXS map is assumed to be in units of eV.

> Information "it is an early version of the RIXS map visualization tool"


```python
from typing import Tuple


def sin2_as_rixsmap() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create a RIXS map with a sinusoidal intensity."""
    incident_energy = np.linspace(0, 10, 100)
    emission_energy = np.linspace(0, 10, 100)
    grid = np.meshgrid(incident_energy, emission_energy)
    rixs_map = np.sin(grid[0]) * np.sin(grid[1])
    return incident_energy, emission_energy, rixs_map
```

```python
_app = RIXSApp(
    incident_energy=sin2_as_rixsmap()[0],
    emission_energy=sin2_as_rixsmap()[1],
    rixs_map=sin2_as_rixsmap()[2],
    # For avoiding issues with a too large inline visualization, please downsizing the RIXS map size
    size=SizeRatioAPI(size=(200, 200)),
    mode="inline",
    jupyter_dash=True,
)
```

```python
_app.app_run()
```

![_](https://github.com/Anselmoo/spectrafit/blob/9f46aac202a6edfe8d063ecd46fadd3c14a6e28d/docs/examples/images/Figure_9_4.png?raw=true)
