As already mentioned in section [Input Files][1], `SpectraFit` can read input
files in different formats. The input file format is specified by the file
extension, which can be `*.json`, `*.yaml`, `*.yml`, or `*.toml`.

!!! tip "fitting_input.toml"

    The standard input file for `SpectraFit` is called `fitting_input.toml`; other specific inpute files has to be explicitly defined by `-i` or `--input`.


    ```shell
    spectrafit data.txt
    ```

    The command above is enough if `fitting_input.toml` is provided in the same
    folder.

## JSON-Input

```shell
spectrafit data.txt -i example_1.json
```

```json
{
  "fitting": {
    "description": {
      "project_name": "Example1",
      "project_details": "Example 1",
      "keywords": [
        "2D-Spectra",
        "fitting",
        "curve-fitting",
        "peak-fitting",
        "spectrum"
      ]
    },
    "parameters": {
      "minimizer": {
        "nan_policy": "propagate",
        "calc_covar": true
      },
      "optimizer": {
        "max_nfev": 1000,
        "method": "leastsq"
      },
      "report": {
        "min_correl": 0.0
      }
    },
    "peaks": {
      "1": {
        "pseudovoigt": {
          "amplitude": {
            "max": 2,
            "min": 0,
            "vary": true,
            "value": 1
          },
          "center": {
            "max": 2,
            "min": -2,
            "vary": true,
            "value": 0
          },
          "fwhmg": {
            "max": 0.5,
            "min": 0.02,
            "vary": true,
            "value": 0.1
          },
          "fwhml": {
            "max": 0.5,
            "min": 0.01,
            "vary": true,
            "value": 0.1
          }
        }
      }
    }
  }
}
```

## YAML- or YML-Input

```shell
spectrafit data.txt -i example_1.yaml
```

```yaml
---
fitting:
  description:
    project_name: Example1
    project_details: Example 1
    keywords:
      - 2D-Spectra
      - fitting
      - curve-fitting
      - peak-fitting
      - spectrum
  parameters:
    minimizer:
      nan_policy: propagate
      calc_covar: true
    optimizer:
      max_nfev: 1000
      method: leastsq
    report:
      min_correl: 0
  peaks:
    "1":
      pseudovoigt:
        amplitude:
          max: 2
          min: 0
          vary: true
          value: 1
        center:
          max: 2
          min: -2
          vary: true
          value: 0
        fwhmg:
          max: 0.5
          min: 0.02
          vary: true
          value: 0.1
        fwhml:
          max: 0.5
          min: 0.01
          vary: true
          value: 0.1
```

## TOML-Input

```shell
spectrafit data.txt -i example_1.toml
```

```toml
[fitting.description]
project_name = "Example1"
project_details = "Example 1"
keywords = [
  "2D-Spectra",
  "fitting",
  "curve-fitting",
  "peak-fitting",
  "spectrum"
]

[fitting.parameters.minimizer]
nan_policy = "propagate"
calc_covar = true

[fitting.parameters.optimizer]
max_nfev = 1_000
method = "leastsq"

[fitting.parameters.report]
min_correl = 0

[fitting.peaks.1.pseudovoigt.amplitude]
max = 2
min = 0
vary = true
value = 1

[fitting.peaks.1.pseudovoigt.center]
max = 2
min = -2
vary = true
value = 0

[fitting.peaks.1.pseudovoigt.fwhmg]
max = 0.5
min = 0.02
vary = true
value = 0.1

[fitting.peaks.1.pseudovoigt.fwhml]
max = 0.5
min = 0.01
vary = true
value = 0.1
```

[1]: ../../interface/usage/#input-files
