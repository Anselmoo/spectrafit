In this example, the command-line interface of `SpectraFit` is used to fit a
single peak of the spectrum, as shown below.

```shell
spectrafit data.txt -i example_1.json -o example_1
```

![_](img/Figure_1.png)

In case of using the energy ranges, the spectra will be limited to the defined
energy ranges of `-e0` and `-e1`.

```shell
spectrafit data.txt -i example_1.json -o example_1 -e0 -1 -e1 +1
```

![_](img/Figure_2.png)

The input file has to look like the following:

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
      "minimizer": { "nan_policy": "propagate", "calc_covar": true },
      "optimizer": { "max_nfev": 1000, "method": "leastsq" },
      "report": { "min_correl": 0.0 }
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
          "fwhm_g": {
            "max": 0.5,
            "min": 0.02,
            "vary": true,
            "value": 0.1
          },
          "fwhm_l": {
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
