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

# About RIXS Plugins


## About PKL Converter and Visualizer

```python
from spectrafit.plugins.pkl_converter import PklConverter
from spectrafit.plugins.pkl_visualizer import PklVisualizer
```

## About RIXS Converter and Visualizer

```python
from spectrafit.plugins.rixs_converter import RIXSConverter
from spectrafit.plugins.rixs_visualizer import RIXSVisualizer
```

<!-- #region -->
### Example code as a Python module:

```python
    from spectrafit.plugins.pkl_converter import PklConverter
    from spectrafit.plugins.rixs_converter import RIXSConverter
    from spectrafit.plugins.rixs_visualizer import RIXSApp

    pkl_data = PklConverter.convert(
        infile="test.pkl",
    )
    PklConverter().save(
        data=pkl_data,
        outfile="test_rixs.npz",
        export_format="npz",
    )
    rixs_data = RIXSConverter.convert(
        infile="test_rixs.npz",
    )
    RIXSApp(**rixs_data).app_run()
```
<!-- #endregion -->
