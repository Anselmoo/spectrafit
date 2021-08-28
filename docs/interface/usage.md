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
5. The attributes `minimizer` and `optimizer` have to be also defined, because
   they control the optimization algorithm of lmfit. For information see
   [lmfit.mininizer][5]. The input file has to contain the following lines:
   ```json
      "parameters": {
      "minimizer": { "nan_policy": "propagate", "calc_covar": true },
      "optimizer": { "max_nfev": 1000, "method": "leastsq" }
      }
   ```
6. Starting `SpectraFit` via:
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

## Advanced Usage

In case of advanced usage of `SpectraFit`, the following steps are necessary:

1.  Define the settings in the input file as shown below:
    ```json
    {
    "settings": {
    "column": [0, 1],
    "decimal": ".",
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
    "version": false,
    "noplot": false
    }
    ```
    If the settings are pre-defined in the input file, the corresponding command
    line arguments will be automatically replaced with them. If they are not
    defined, the command line arguments or their default values will be use.
    This allows to run faster `SpectraFit` and also be consistent in the fitting
    procedure in case of larger studies. For the detail mechanism of overwriting
    the settings, please see the API documentation of [Command Line Module][4]
2.  Another advanced feature of `SpectraFit` is to define the fit as project,
    which can become very useful in case of versioning the fitting project. For
    using `SpectraFit` as a project, the project details have to be defined as
    attributes. The attributes are `project name`, `project details`,
    `keywords`, as shown in the snippet below:
    ```json
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
        }
    ```
    All three attributes are strings, the `project name` should be ideally a
    single name with no spaces. The `project details` can be longer text, and
    the `keywords` should be a list of strings for tagging in a database.
3.  The input file can be extended with more parameters, which are not necessary
    and optional in case of the confidence intervals. In general, the keywords
    of the lmfit `minimizer` function are supported. For more information please
    check the module [lmfit.mininizer][5]. The attributes have to be initialized
    with the keyword `parameters` as shown below:

    ```json
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
     }
    ```

    !!! warning "About confidence interval calculations"

        The calculations of the confidence intervals depends on the number of
        features and `maxiter`. Consequently, the confidence interval calculations
        should be only used for the final fit to put the calculation time low.

## Configurations

In terms of the configuration of `SpectraFit`, configurations depends on
[`lmfit package`](https://lmfit.github.io/lmfit-py/fitting.html).Most of the
provided features of `lmfit` can be used. The configurations can be called as
attributes of `optimizer` and `minimizer` as shown in [Standard Usage][7] #5.
For the individualization of the configuration, please use the keywords of
`lmfit` [minimizer module][8] and also check the API section `SpectraFit`'s
[fitting routine][6].

## Input Files

The input file of `SpectraFit` are dictionary-like objects. The input file can
be one of these three types:

- [x] [json](https://en.wikipedia.org/wiki/JSON)
- [x] [toml](https://en.wikipedia.org/wiki/TOML)
- [x] [yaml](https://en.wikipedia.org/wiki/YAML)

Especially, the `toml` and `yaml` files are very useful for the configuration of
`SpectraFit` due to their structure and simplicity.
https://www.convertsimple.com allows easily to convert between these three file
types.

??? example "Reference Input in `JSON`"

    ```json
    {
      "settings": {
        "column": [0, 1],
        "decimal": ".",
        "energy_start": 0,
        "energy_stop": 8,
        "header": null,
        "infile": "spectrafit/test/rixs_fecl4.txt",
        "outfile": "fit_results",
        "oversampling": false,
        "noplot": false,
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

[4]:
  ../../api/spectrafit_api/#spectrafit.spectrafit.extracted_from_command_line_runner
[5]:
  https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#module-lmfit.minimizer
[6]: ../../api/spectrafit_api/#spectrafit.spectrafit.fitting_routine
[7]: /spectrafit/interface/usage/#standard-usage
[8]:
  https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#module-lmfit.minimizer
