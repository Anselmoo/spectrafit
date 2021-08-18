## Standard Usage

In case of the standard usage of `SpectraFit`, the following steps are
necessary:

1. Having a structured textfile available with or without header. Preferred
   fileformat can be `.csv` or `.txt`; however every file with a consistent
   separation is supported.
   ```sql
           -1.600000000000000089e+00	0.000000000000000000e+00
           -1.583333333333333481e+00	3.891050583657595843e-03
           -1.566666666666666874e+00	3.973071404922200699e-03
           -1.550000000000000266e+00	4.057709648331829684e-03
           -1.533333333333333659e+00	4.145077720207249357e-03
           -1.516666666666667052e+00	4.235294117647067993e-03
   ```
2. A wide range of pre-defined separators can be choosen: `,`, `;`, `:`, `|`,
   `\t`, `s+`, ` `
3. Having an input file available as [json](https://en.wikipedia.org/wiki/JSON),
   [toml](https://en.wikipedia.org/wiki/TOML), or
   [yaml](https://en.wikipedia.org/wiki/YAML). The input file has to have at
   least the initial parameters for the peaks. More options are in the default
   settings not necessary, but can be activated by extending the objects in the
   input file.
4. More command line arguments can be seen by activating the `-h` \ ``--help`
   flag.
5. Starting `SpectraFit` via:
   ```shell
   spectrafit data_file.txt input_file.json
   ```

!!! info "Peak definition in the input file"

    In the input file, the peaks has to be define as nested objects, as seen below:

    ```json
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
            "max": 0.1,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          },
          "fwhm_l": {
            "max": 0.1,
            "min": 0.01,
            "vary": true,
            "value": 0.01
          }
        }
      },
    ```

    First, peaks have to be declared in the input file. Every peak contains a
    number as string; like "1" for peak #1. Next, the type of peak has to be
    defined in the input. The following peak types are available:

    - [Gaussian](https://en.wikipedia.org/wiki/Gaussian_function)
    - [Lorentzian](https://en.wikipedia.org/wiki/Cauchy_distribution)
        also known as Cauchy distribution
    - [Voigt](https://en.wikipedia.org/wiki/Voigt_profile)
    - [Pseudo Voigt][1]
    - Exponential
    - [Powerlaw][2] (also known as Log-parabola)
    - Linear
    - Constant
    - [Error Function](https://en.wikipedia.org/wiki/Error_function)
    - [Arcus Tangens][3]
    - Logarithmic
    [1]: https://en.wikipedia.org/wiki/Voigt_profile#Pseudo-Voigt_approximation
    [2]: https://en.wikipedia.org/wiki/Power_law
    [3]: https://en.wikipedia.org/wiki/Inverse_trigonometric_functions

    More information about the models, please see the
    [Section Models](../../doc/models/). For every model, the attributes have
    to be defined. The attributes are in case of the `pseudovoigt` model:

    1. `Amplitude`: The amplitude of the distribution function.
    2. `Center`: The center of the distribution function.
    3. `FWHM`: The full width half maximum of the Gaussian distribution
    4. `FWHM`: The full width half maximum of the Lorentzian distribution

    Each attribute has sub-attributes, which are __always__:

    1. `max`: the maximum value of the attribute
    2. `min`: the minimum value of the attribute
    3. `vary`: if the attribute should be varied during the fit
    4. `value`: the initial value of the attribute

    At the moment, no default attributes are defined for the models, but this
    will come in a future release.

In summary, for using

## Advanced Usage

```json
{
  "settings": {
    "column": [0, 1],
    "decimal": ".",
    "disp": false,
    "energy_start": 0,
    "energy_stop": 8,
    "header": null,
    "infile": "spectrafit/test/rixs_fecl4.txt",
    "outfile": "fit_results",
    "oversampling": false,
    "seperator": "\t",
    "shift": 0,
    "smooth": 0,
    "verbose": false,
    "version": false
  },
  "fitting": {
    "description": {
      "project_name": "Template",
      "project_details": "Template for testing",
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
      "report": { "min_correl": 0.0 },
      "conf_interval": {
        "p_names": null,
        "sigmas": null,
        "trace": true,
        "maxiter": 200,
        "verbose": false,
        "prob_func": null
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
          "fwhm_g": {
            "max": 0.1,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          },
          "fwhm_l": {
            "max": 0.1,
            "min": 0.01,
            "vary": true,
            "value": 0.01
          }
        }
      },
      "2": {
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
            "max": 0.1,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          },
          "fwhm_l": {
            "max": 0.1,
            "min": 0.01,
            "vary": true,
            "value": 0.01
          }
        }
      },
      "3": {
        "constant": {
          "amplitude": {
            "max": 2,
            "min": 0.01,
            "vary": true,
            "value": 1
          }
        }
      },
      "4": {
        "gaussian": {
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
            "max": 0.1,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          }
        }
      }
    }
  }
}
```
